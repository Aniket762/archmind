import networkx as nx
from dataclasses import dataclass, field

@dataclass
class SimulationResult:
    total_rps:int
    bottleneck_nodes: list[str]
    overloaded_edges: list[str]
    warnings: list[str]

class SimulationEngine:
    def __init__(self, graph : nx.DiGraph) -> None: 
        self.graph = graph
    
    def run(self, incoming_rps: int = 1000) -> SimulationResult:
        return SimulationResult(
            total_rps=incoming_rps,
            bottleneck_nodes=[],
            overloaded_edges=[],
            warnings=["simulation engine not yet implemented"],
        )