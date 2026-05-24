# domain models -> networkx digraph
# pydantic->networkx : running algo
# networkx->pydantic : serialization post modification

import networkx as nx
from typing import Any
from app.domain.architecture import ArchitectureGraph
from app.domain.nodes import Node, NodeType
from app.domain.edges import Edge,ConnectionType

class GraphBuilder:
    #pydantic->nx
    @staticmethod
    def build(architecture:ArchitectureGraph) ->nx.graph:
        graph = nx.Graph(
            name=architecture.name,
            graph_id = architecture.graph_id,
            description = architecture.description
        )

        for node_id, node in architecture.nodes.items():
            graph.add_node(
                node_id,
                data=node,
                label = node.name,
                node_type=node.node_type.value,
                max_rps = node.max_rps,
                is_stateful = node.is_stateful,
                critical = node.critcal
            )

        for edge in architecture.edges:
            graph.add_edge(
                edge.source_id,
                edge.target_id,
                data=edge,
                connection_type=edge.connection_type.value,
                weight = edge.max_rps,
                latency=edge.latency_ms,
            )

        return graph
    
    #nx->pydantic
    @staticmethod
    def to_architecture(graph:nx.DiGraph)->ArchitectureGraph:
        nodes: dict[str,Node] = {}
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id].get("data")
            if node_data is None:
                ValueError(
                    f"node {node_id} missing data, GraphBuilder.build created this"
                )
            nodes[node_id] = node_data

        edges:list[Edge] = []
        for source,target in graph.edges():
            edge_data = graph.edges[source,target].get("data")
            if edge_data is None:
                raise ValueError(
                    f"edge {source},{target} missing data,  GraphBuilder.build created this"
                )
            edges.append(edge_data)
        
        return ArchitectureGraph(
            graph_id=graph.graph.get("graph_id", ""),
            name=graph.graph.get("name", "Converted Graph"),
            description=graph.graph.get("description", ""),
            nodes=nodes,
            edges=edges,
        )
    
    @staticmethod
    def get_node_data(graph:nx.DiGraph, node_id:str) -> Node|None:
        if node_id not in graph:
            return None
        return graph.nodes[node_id].get("data")
    
    @staticmethod
    def get_edge_data(graph: nx.DiGraph, source_id: str, target_id: str) -> Edge| None:
        if not graph.has_edge(source_id, target_id):
            return None
        return graph.edges[source_id, target_id].get("data")
    
    @staticmethod
    def add_node_to_graph(graph: nx.DiGraph, node: Node) -> nx.DiGraph:
        graph.add_node(
            node.node_id,
            data=node,
            label=node.name,
            node_type=node.node_type.value,
            max_rps=node.max_rps,
            is_stateful=node.is_stateful,
            critical=node.critical,
        )
        return graph
    
    @staticmethod
    def add_edge_to_graph(graph: nx.DiGraph, edge: Edge) -> nx.DiGraph:
        if edge.source_id not in graph:
            raise ValueError(f"source node {edge.source_id} not in graph")
        if edge.target_id not in graph:
            raise ValueError(f"target node {edge.target_id} not in graph")
 
        graph.add_edge(
            edge.source_id,
            edge.target_id,
            data=edge,
            connection_type=edge.connection_type.value,
            weight=edge.max_rps,
            latency=edge.latency_ms,
        )
        return graph
    
    @staticmethod
    def remove_node_from_graph(graph: nx.DiGraph, node_id: str) -> nx.DiGraph:
        if node_id not in graph:
            raise ValueError(f"node {node_id} not found in graph")
        graph.remove_node(node_id)
        return graph