from dataclasses import dataclass, field
from typing import Dict, Set, List, Tuple
import networkx as nx
from collections import defaultdict


@dataclass
class NodeLoadData:
    node_id: str
    max_capacity: int
    current_load: int
    percentage_used: float 
    is_overloaded: bool
    expected_latency_ms: float


@dataclass
class EdgeLoadData:
    edge_id: str
    source_id: str
    target_id: str
    max_bandwidth: int
    current_traffic: int
    percentage_used: float
    is_overloaded: bool
    has_resilience: bool


@dataclass
class SimulationResult:
    total_rps: int
    
    bottleneck_nodes: list[str] = field(default_factory=list)
    overloaded_edges: list[str] = field(default_factory=list)
    
    node_loads: Dict[str, NodeLoadData] = field(default_factory=dict)
    edge_loads: Dict[str, EdgeLoadData] = field(default_factory=dict)
    
    cascade_risk_nodes: list[str] = field(default_factory=list)
    latency_critical_paths: list[List[str]] = field(default_factory=list)
    
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    overall_health_score: float = 100.0  
    critical: bool = False


class SimulationEngine:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph
        self.node_loads: Dict[str, int] = defaultdict(int)
        self.edge_loads: Dict[Tuple[str, str], int] = defaultdict(int)

    def run(self, incoming_rps: int = 1000) -> SimulationResult:
        self.node_loads = defaultdict(int)
        self.edge_loads = defaultdict(int)

        entry_points = self._find_entry_points()
        if not entry_points:
            entry_points = [
                node for node in self.graph.nodes()
                if self.graph.in_degree(node) == 0
            ]
        
        if not entry_points:
            entry_points = [
                max(self.graph.nodes(), key=lambda n: self.graph.out_degree(n))
            ]

        load_per_entry = incoming_rps // len(entry_points) if entry_points else incoming_rps
        for entry_point in entry_points:
            self._simulate_traffic_from(entry_point, load_per_entry)

        node_bottlenecks = self.find_bottleneck_nodes()
        edge_overloads = self.find_overloaded_edges()
        cascade_risks = self.find_cascade_risks(node_bottlenecks)
        latency_paths = self._find_latency_critical_paths()

        recommendations = self.generate_recommendations(
            node_bottlenecks, edge_overloads, cascade_risks
        )

        health_score = self.calculate_health_score(
            node_bottlenecks, edge_overloads, cascade_risks
        )

        result = SimulationResult(
            total_rps=incoming_rps,
            bottleneck_nodes=node_bottlenecks,
            overloaded_edges=edge_overloads,
            node_loads=self.build_node_load_data(),
            edge_loads=self.build_edge_load_data(),
            cascade_risk_nodes=cascade_risks,
            latency_critical_paths=latency_paths,
            recommendations=recommendations,
            overall_health_score=health_score,
            critical=len(node_bottlenecks) > 0 or len(edge_overloads) > 0,
        )

        result.warnings = self.generate_warnings(result)

        return result

    def find_entry_points(self) -> List[str]:
        return [
            node for node in self.graph.nodes()
            if self.graph.in_degree(node) == 0
        ]

    def simulate_traffic_from(self, start_node: str, initial_load: int) -> None:
        visited = set()
        queue = [(start_node, initial_load)]

        while queue:
            current_node, current_load = queue.pop(0)

            if current_node in visited:
                continue
            visited.add(current_node)
            self.node_loads[current_node] += current_load
            
            outgoing_edges = list(self.graph.out_edges(current_node))

            if not outgoing_edges:
                continue

            load_per_edge = current_load // len(outgoing_edges)

            for source, target in outgoing_edges:
                self.edge_loads[(source, target)] += load_per_edge
                queue.append((target, load_per_edge))

    def find_bottleneck_nodes(self) -> List[str]:
        bottlenecks = []

        for node_id, load in self.node_loads.items():
            node_data = self.graph.nodes[node_id].get("data")
            if not node_data:
                continue

            effective_capacity = node_data.effective_capacity
            if load > effective_capacity:
                bottlenecks.append(node_id)

        return sorted(bottlenecks)

    def find_overloaded_edges(self) -> List[str]:
        overloaded = []

        for (source, target), traffic in self.edge_loads.items():
            edge_data = self.graph.edges[source, target].get("data")
            if not edge_data:
                continue

            if traffic > edge_data.max_rps:
                overloaded.append(edge_data.edge_id)

        return sorted(overloaded)

    def find_cascade_risks(self, bottleneck_nodes: List[str]) -> List[str]:
        cascade_risks = []

        for bottleneck_node in bottleneck_nodes:
            node_data = self.graph.nodes[bottleneck_node].get("data")
            if not node_data:
                continue

            if not node_data.is_stateful:
                continue

            downstream = list(self.graph.successors(bottleneck_node))
            for downstream_node in downstream:
                edge_data = self.graph.edges[bottleneck_node, downstream_node].get("data")
                if not edge_data:
                    continue

                if edge_data.is_synchronous and not edge_data.has_circuit_breaker:
                    cascade_risks.append(bottleneck_node)
                    break

        return sorted(cascade_risks)

    def find_latency_critical_paths(self) -> List[List[str]]:
        paths = []

        # source to sink path
        sources = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        sinks = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]

        if not sources or not sinks:
            return paths

        for source in sources:
            for sink in sinks:
                try:
                    path = nx.shortest_path(self.graph, source, sink)
                    latency = self._calculate_path_latency(path)

                    # Keep top 3 slowest paths
                    if len(paths) < 3:
                        paths.append(path)
                        paths.sort(
                            key=lambda p: self._calculate_path_latency(p),
                            reverse=True
                        )
                    elif latency > self._calculate_path_latency(paths[-1]):
                        paths[-1] = path
                        paths.sort(
                            key=lambda p: self._calculate_path_latency(p),
                            reverse=True
                        )
                except nx.NetworkXNoPath:
                    continue

        return paths

    def calculate_path_latency(self, path: List[str]) -> int:
        latency = 0
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            edge_data = self.graph.edges[source, target].get("data")
            if edge_data:
                latency += edge_data.latency_ms
            node_data = self.graph.nodes[target].get("data")
            if node_data:
                latency += node_data.latency_ms
        return latency


    def build_node_load_data(self) -> Dict[str, NodeLoadData]:
        data = {}

        for node_id in self.graph.nodes():
            node_obj = self.graph.nodes[node_id].get("data")
            if not node_obj:
                continue

            load = self.node_loads.get(node_id, 0)
            capacity = node_obj.effective_capacity
            percentage = (load / capacity * 100) if capacity > 0 else 0

            if load > capacity:
                queueing_latency = (load - capacity) / capacity * node_obj.latency_ms
            else:
                queueing_latency = 0

            expected_latency = node_obj.latency_ms + queueing_latency

            data[node_id] = NodeLoadData(
                node_id=node_id,
                max_capacity=capacity,
                current_load=load,
                percentage_used=percentage,
                is_overloaded=load > capacity,
                expected_latency_ms=expected_latency,
            )

        return data

    def build_edge_load_data(self) -> Dict[str, EdgeLoadData]:
        data = {}

        for (source, target), traffic in self.edge_loads.items():
            edge_obj = self.graph.edges[source, target].get("data")
            if not edge_obj:
                continue

            max_bandwidth = edge_obj.max_rps
            percentage = (traffic / max_bandwidth * 100) if max_bandwidth > 0 else 0

            data[edge_obj.edge_id] = EdgeLoadData(
                edge_id=edge_obj.edge_id,
                source_id=source,
                target_id=target,
                max_bandwidth=max_bandwidth,
                current_traffic=traffic,
                percentage_used=percentage,
                is_overloaded=traffic > max_bandwidth,
                has_resilience=edge_obj.has_circuit_breaker or edge_obj.has_retry,
            )

        return data

    def generate_recommendations(
        self,
        bottlenecks: List[str],
        overloads: List[str],
        cascade_risks: List[str]
    ) -> List[str]:
        """Generate scaling and optimization recommendations."""
        recommendations = []

        for node_id in bottlenecks:
            node_obj = self.graph.nodes[node_id].get("data")
            if not node_obj:
                continue

            load = self.node_loads[node_id]
            capacity = node_obj.effective_capacity
            ratio = load / capacity

            if node_obj.scaling_strategy.value == "horizontal":
                needed_replicas = int(node_obj.replicas * ratio) + 1
                recommendations.append(
                    f"Scale {node_obj.name} to {needed_replicas} replicas "
                    f"(currently {node_obj.replicas}, load {ratio:.1f}x capacity)"
                )
            elif node_obj.scaling_strategy.value == "vertical":
                scale_factor = ratio
                recommendations.append(
                    f"Upgrade {node_obj.name} capacity {scale_factor:.1f}x "
                    f"(increase max_rps from {node_obj.max_rps} to {int(node_obj.max_rps * scale_factor)})"
                )
            else:
                recommendations.append(
                    f"{node_obj.name} is overloaded but has no scaling strategy. "
                    "Consider making it scalable."
                )

        for edge_id in overloads:
            for (source, target), traffic in self.edge_loads.items():
                edge_obj = self.graph.edges[source, target].get("data")
                if edge_obj and edge_obj.edge_id == edge_id:
                    ratio = traffic / edge_obj.max_rps

                    if not edge_obj.has_circuit_breaker:
                        recommendations.append(
                            f"Add circuit breaker to {source} → {target} "
                            f"to prevent cascade failure"
                        )

                    if not edge_obj.has_retry and edge_obj.is_synchronous:
                        recommendations.append(
                            f"Add retry logic to {source} → {target} "
                            f"to improve reliability"
                        )

                    recommendations.append(
                        f"Increase edge {source} → {target} capacity from "
                        f"{edge_obj.max_rps} to {int(edge_obj.max_rps * ratio + 1000)}"
                    )

        for node_id in cascade_risks:
            node_obj = self.graph.nodes[node_id].get("data")
            if node_obj:
                recommendations.append(
                    f"Add circuit breaker or fallback for {node_obj.name} "
                    f"to prevent cascade failures"
                )

        if not recommendations:
            recommendations.append(
                "No scaling needed at current load. Architecture appears healthy."
            )

        return recommendations

    def calculate_health_score(
        self,
        bottlenecks: List[str],
        overloads: List[str],
        cascade_risks: List[str]
    ) -> float:
        score = 100.0
        score -= len(bottlenecks) * 10
        score -= len(overloads) * 5
        score -= len(cascade_risks) * 15

        return max(0.0, score)

    def generate_warnings(self, result: SimulationResult) -> List[str]:
        warnings = []

        if result.bottleneck_nodes:
            warnings.append(
                f"Found {len(result.bottleneck_nodes)} bottleneck node(s): "
                f"{', '.join(result.bottleneck_nodes)}"
            )

        if result.overloaded_edges:
            warnings.append(
                f"Found {len(result.overloaded_edges)} overloaded edge(s). "
                "Network saturation risk."
            )

        if result.cascade_risk_nodes:
            warnings.append(
                f"Found {len(result.cascade_risk_nodes)} cascade failure risk node(s). "
                "Add circuit breakers and fallbacks."
            )

        isolated = [
            node for node in self.graph.nodes()
            if self.node_loads.get(node, 0) == 0
        ]
        if isolated:
            warnings.append(
                f"{len(isolated)} node(s) received no traffic. "
                "These may be unreachable or unnecessary."
            )

        if not warnings:
            warnings.append(
                "System appears healthy under current load. "
                "All nodes and edges have adequate capacity."
            )

        return warnings