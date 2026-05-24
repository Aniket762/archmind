# algos on nx digraph
# analyzes the design created

import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class CriticalNode:
    node_id: str
    reason: str
    betweenness_score: float
    in_degree: int
    out_degree: int

@dataclass
class CycleInfo:
    nodes: List[str]
    length: int
 
    @property
    def formatted(self) -> str:
        return " → ".join(self.nodes + [self.nodes[0]])

# wrap in pydantic model before returning
@dataclass
class AnalysisSummary:
    node_count: int
    edge_count: int
    density: float
 
    is_dag: bool
    is_connected: bool
    component_count: int
 
    critical_nodes: List[CriticalNode] = field(default_factory=list)
    potential_spofs: List[str] = field(default_factory=list)
 
    cycles: List[CycleInfo] = field(default_factory=list)
    isolated_nodes: List[str] = field(default_factory=list)
 
    warnings: List[str] = field(default_factory=list)

class GraphAnalyzer:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph
    
    # entry point
    def analyze(self) -> AnalysisSummary:
        summary = AnalysisSummary(
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
            density=self._calculate_density(),
            is_dag=self.is_dag(),
            is_connected=self.is_weakly_connected(),
            component_count=self.count_components(),
        )
 
        summary.cycles = self.find_cycles()
        summary.isolated_nodes = self.find_isolated_nodes()

        summary.critical_nodes = self.find_critical_nodes()
        summary.potential_spofs = self.find_spofs()
 
        summary.warnings = self._generate_warnings(summary)
 
        return summary
    
    def is_dag(self) -> bool:
        return nx.is_directed_acyclic_graph(self.graph)
    
    def find_cycles(self) -> List[CycleInfo]:
        if self.is_dag():
            return []
        
        try:
            cycles_raw = list(nx.simple_cycles(self.graph))
            return [
                CycleInfo(nodes=cycle, length=len(cycle))
                for cycle in cycles_raw
            ]
        except nx.NetworkXNoCycle:
            return []
    
    def is_weakly_connected(self) -> bool:
        return nx.is_weakly_connected(self.graph)
    
    # cnt component cluster: # island in lc
    def count_components(self) -> int:
        return nx.number_weakly_connected_components(self.graph)

    def get_components(self) -> List[Set[str]]:
        return [
            set(component)
            for component in nx.weakly_connected_components(self.graph)
        ]
    
    '''
    Betweennes: many paths go through this node, high indegree
    threshodl: 0.1 (top 10% of nodes by betweenness)
    '''
    def find_critical_nodes(self, threshold: float = 0.1) -> List[CriticalNode]:
        if self.graph.number_of_nodes() == 0:
            return []
        
        # o(ve) un-wt graphs
        betweenness = nx.betweenness_centrality(self.graph)
        critical_nodes = []
 
        for node_id in self.graph.nodes():
            bc_score = betweenness[node_id]
            in_deg = self.graph.in_degree(node_id)
            out_deg = self.graph.out_degree(node_id)
 
            node_data = self.graph.nodes[node_id].get("data")
            is_flagged = node_data.critical if node_data else False
 
            is_critical = (
                bc_score >= threshold  # high betweenness
                or in_deg >= 3        # many dependencies
                or is_flagged         
            )
 
            if is_critical:
                reasons = []
                if bc_score >= threshold:
                    reasons.append(f"high betweenness ({bc_score:.3f})")
                if in_deg >= 3:
                    reasons.append(f"many dependents ({in_deg})")
                if is_flagged:
                    reasons.append("marked critical")
 
                critical_nodes.append(CriticalNode(
                    node_id=node_id,
                    reason=", ".join(reasons),
                    betweenness_score=bc_score,
                    in_degree=in_deg,
                    out_degree=out_deg,
                ))
 
        critical_nodes.sort(key=lambda n: n.betweenness_score, reverse=True)
        return critical_nodes