from datetime import datetime,UTC
from typing import Iterator
from pydantic import BaseModel, Field, model_validator
import uuid

from app.domain.nodes import Node, NodeType
from app.domain.edges import Edge,ConnectionType

class ArchitectureGraph(BaseModel):
    graph_id:str = Field(
        default_factory=lambda: f"graph_{uuid.uuid4().hex[:8]}",
        description= "Id for the design"
    )

    name:str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="name of the design"
    )

    description: str = Field(
        default="",
        max_length=2000,
        description="what is the design for"
    )

    created_at: datetime = Field(
        default_factory=lambda:datetime.now(UTC),
        description="design creation"
    )

    nodes: dict[str,Node] = Field(
        default_factory="nodes have id for o1 access"
    )

    edges:list[Edge] = Field(
        default_factory=dict,
        description="directed edges in the design"
    )

    source_prompt:str=Field(
        default="",
        max_length=5000,
        description="og user prompt that generated the design"
    )

    ai_generated:bool = Field(
        default=False,
        description="if ai planner generated it"
    )

    tags:list[str] = Field(
        default_factory=list,
        max_length=20,
        description="design level tags -> microservice, event driven"
    )

    @model_validator(mode="after")
    def validate_edge_references(self) ->"ArchitectureGraph":
        node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(
                     f"Edge {edge.edge_id} references unknown source: {edge.source_id}"
                )
            if edge.target_id not in node_ids:
                raise ValueError(
                    f"Edge {edge.edge_id} references unknown target: {edge.target_id}"
                )
        return self
    
    # Graph builder - fluent api
    def add_node(self,node:Node) -> "ArchitectureGraph":
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already in graph")
        self.nodes[node.node_id] = node
        return self

    def add_edge(self, edge:Edge) ->"ArchitectureGraph":
        if edge.source_id not in self.nodes:
            raise ValueError(f"cannot add edge: source node {edge.source_id} not in graph")
        if edge.target_id not in self.nodes:
            raise ValueError(f"cannot add edge: target node {edge.target_id} not in graph")
        self.edges.append(edge)
        return self 

    # cascade del: remove node + in/out edges
    def remove_node(self,node_id:str) -> "ArchitectureGraph":
        if node_id not in self.nodes:
            raise ValueError(f"node {node_id} not found in graph")
        del self.nodes[node_id]

        # edge del
        self.edges = [
            edge for edge in self.edges
            if edge.source_id != node_id and edge.target_id != node_id
        ]

        return self
    
    def remove_edge(self, edge_id: str) -> "ArchitectureGraph":
        original_count = len(self.edges)
        self.edges = [edge for edge in self.edges if edge.edge_id != edge_id]
        if len(self.edges) == original_count:
            raise ValueError(f"edge {edge_id} not found in graph")
        return self
    
    # design queries
    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id) #o(1)
 
    def get_edge(self, edge_id: str) -> Edge | None: 
        for edge in self.edges: #o(n)
            if edge.edge_id == edge_id:
                return edge
        return None
 
    def find_edges_from(self, source_id: str) -> list[Edge]: #outbound
        return [edge for edge in self.edges if edge.source_id == source_id]
 
    def find_edges_to(self, target_id: str) -> list[Edge]: #inbound
        return [e for e in self.edges if e.target_id == target_id]
 
    def get_neighbors(self, node_id: str, direction: str = "out") -> list[Node]: #out:downstream, in:upstream
        neighbor_ids: set[str] = set()
 
        if direction in {"out", "both"}:
            neighbor_ids.update(
                edge.target_id for edge in self.edges if edge.source_id == node_id
            )
        if direction in {"in", "both"}:
            neighbor_ids.update(
                edge.source_id for edge in self.edges if edge.target_id == node_id
            )
 
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]
 
    def find_nodes_by_type(self, node_type: NodeType) -> list[Node]:
        return [node for node in self.nodes.values() if node.node_type == node_type]
 
    def find_nodes_by_tag(self, tag: str) -> list[Node]:
        tag_lower = tag.lower()
        return [node for node in self.nodes.values() if node.has_tag(tag_lower)]
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    @property
    def is_empty(self) -> bool:
        return self.node_count ==0
    
    '''
    edge/vertices ratio used to determine coupling
    - low density (<2): loosely coupled
    - medium density (2-4): targeted coupling
    - high density (>4): tightly couple
    '''
    @property
    def density(self) -> float:
        if self.node_count ==0:
            return 0.0
        return self.edge_count/self.node_count
    
    @property
    def to_dict(self)->dict:
        return self.model_dump(mode="json")
    
    @classmethod
    def from_dict(cls,data:dict) -> "ArchitectureGraph":
        return cls.model_validate(data)

    def iter_nodes(self)->Iterator[Node]:
        return iter(self.nodes.values())
    
    def iter_edges(self)-> Iterator[Edge]:
        return iter(self.edges)
    
    def summary(self)->str:
        node_types={}
        for node in self.nodes.values():
            node_types[node.node_type.value] = node_types.get(node.node_type.value,0)+1

        type_breakdown = ", ".join(
            f"{count} {nodetype}" for nodetype, count in sorted(node_types.items())
        )
 
        return (
            f"{self.name} ({self.graph_id})\n"
            f"Nodes: {self.node_count} ({type_breakdown})\n"
            f"Edges: {self.edge_count}\n"
            f"Density: {self.density:.2f} edges/node\n"
            f"AI generated: {self.ai_generated}"
        )