from fastapi import Depends
from app.config import Settings, get_settings
from app.ai.planner import ArchitecturePlanner
from app.graph.builder import GraphBuilder
from app.graph.analyzer import GraphAnalyzer
from app.simulation.engine import SimulationEngine
import networkx as nx

def get_planner(settings:Settings=Depends(get_settings)) -> ArchitecturePlanner:
    return ArchitecturePlanner()

def get_graph_builder() -> GraphBuilder:
    return GraphBuilder()