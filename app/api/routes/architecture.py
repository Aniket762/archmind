from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.domain.architecture import ArchitectureGraph
from app.domain.nodes import Node, NodeType
from app.domain.edges import Edge
from app.ai.planner import ArchitecturePlanner
from app.graph.builder import GraphBuilder
from app.graph.analyzer import GraphAnalyzer, AnalysisSummary, CriticalNode, CycleInfo
from app.api.dependencies import get_planner, get_graph_builder


router = APIRouter(prefix="/architecture", tags=["architecture"])

#request schema
class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="natural language description of the system design problem"
    )
    analyze: bool = Field(
        default=True,
        description="whether to run structural analysis after generation"
    )


class AddNodeRequest(BaseModel):
    node: Node = Field(..., description="The node to add")


class AddEdgeRequest(BaseModel):
    edge: Edge = Field(..., description="The edge to add")


class RemoveNodeRequest(BaseModel):
    node_id: str = Field(..., description="ID of the node to remove")


class RemoveEdgeRequest(BaseModel):
    edge_id: str = Field(..., description="ID of the edge to remove")

#response schema
class AnalysisWarning(BaseModel):
    level: str = Field(
        ...,
        description="'info', 'warning', or 'error'"
    )
    message: str = Field(...)


class CriticalNodeResponse(BaseModel):
    node_id: str
    node_name: Optional[str] = None
    betweenness_score: float
    in_degree: int
    out_degree: int
    reason: str


class CycleResponse(BaseModel):
    nodes: list[str]
    length: int
    formatted: str


class AnalysisResponse(BaseModel):
    node_count: int
    edge_count: int
    density: float
    is_dag: bool
    is_connected: bool
    component_count: int
    
    critical_nodes: list[CriticalNodeResponse] = Field(default_factory=list)
    potential_spofs: list[str] = Field(default_factory=list)
    cycles: list[CycleResponse] = Field(default_factory=list)
    isolated_nodes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    architecture: ArchitectureGraph
    analysis: Optional[AnalysisResponse] = None


class ArchitectureResponse(BaseModel):
    architecture: ArchitectureGraph


class DependencyResponse(BaseModel):
    node_id: str
    node_name: Optional[str] = None
    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)
    transitive_upstream: list[str] = Field(default_factory=list)
    transitive_downstream: list[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    graph_id: str
    name: str
    node_count: int
    edge_count: int
    is_dag: bool
    critical_node_count: int
    spof_count: int
    cycle_count: int

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "architecture-api"}


@router.post("/generate", response_model=GenerateResponse)
async def generate_architecture(
    request: GenerateRequest,
    planner: ArchitecturePlanner = Depends(get_planner),
    builder: GraphBuilder = Depends(get_graph_builder),
) -> GenerateResponse:
    try:
        architecture = await planner.plan(request.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI planner failed: {str(e)}"
        )

    analysis_response = None
    if request.analyze:
        try:
            nx_graph = builder.build(architecture)
            analyzer = GraphAnalyzer(nx_graph)
            analysis = analyzer.analyze()
            analysis_response = _analysis_to_response(architecture, analysis)
        except Exception as e:
            print(f"Analysis failed: {e}")

    return GenerateResponse(
        architecture=architecture,
        analysis=analysis_response
    )

@router.get("/{graph_id}")
async def get_architecture(graph_id: str) -> dict:
    raise HTTPException(
        status_code=501,
        detail="Architecture retrieval not yet implemented. See Step 9."
    )


@router.post("/{graph_id}/nodes", response_model=ArchitectureResponse)
async def add_node_to_architecture(
    graph_id: str,
    request: AddNodeRequest,
) -> ArchitectureResponse:
    raise HTTPException(
        status_code=501,
        detail="Node addition not yet implemented. See Step 9."
    )


@router.post("/{graph_id}/edges", response_model=ArchitectureResponse)
async def add_edge_to_architecture(
    graph_id: str,
    request: AddEdgeRequest,
) -> ArchitectureResponse:
    raise HTTPException(
        status_code=501,
        detail="Edge addition not yet implemented. See Step 9."
    )


@router.delete("/{graph_id}/nodes/{node_id}", response_model=ArchitectureResponse)
async def remove_node_from_architecture(
    graph_id: str,
    node_id: str,
) -> ArchitectureResponse:
    raise HTTPException(
        status_code=501,
        detail="Node removal not yet implemented. See Step 9."
    )


@router.delete("/{graph_id}/edges/{edge_id}", response_model=ArchitectureResponse)
async def remove_edge_from_architecture(
    graph_id: str,
    edge_id: str,
) -> ArchitectureResponse:
    raise HTTPException(
        status_code=501,
        detail="Edge removal not yet implemented. See Step 9."
    )

@router.post("/{graph_id}/analyze", response_model=AnalysisResponse)
async def analyze_architecture(
    graph_id: str,
    builder: GraphBuilder = Depends(get_graph_builder),
) -> AnalysisResponse:
    raise HTTPException(
        status_code=501,
        detail="Analysis API not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/summary", response_model=SummaryResponse)
async def get_architecture_summary(graph_id: str) -> SummaryResponse:
    raise HTTPException(
        status_code=501,
        detail="Summary API not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/nodes")
async def list_nodes(
    graph_id: str,
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
) -> dict:
    raise HTTPException(
        status_code=501,
        detail="Node listing not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/nodes/{node_id}/dependencies", response_model=DependencyResponse)
async def get_node_dependencies(
    graph_id: str,
    node_id: str,
    builder: GraphBuilder = Depends(get_graph_builder),
) -> DependencyResponse:
    raise HTTPException(
        status_code=501,
        detail="Dependency analysis not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/spofs")
async def get_spofs(graph_id: str) -> dict:
    raise HTTPException(
        status_code=501,
        detail="SPOF listing not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/cycles")
async def get_cycles(graph_id: str) -> dict:
    raise HTTPException(
        status_code=501,
        detail="Cycle listing not yet implemented. See Step 9."
    )


@router.get("/{graph_id}/critical-nodes")
async def get_critical_nodes(graph_id: str) -> dict:
    raise HTTPException(
        status_code=501,
        detail="Critical nodes listing not yet implemented. See Step 9."
    )

def _analysis_to_response(
    architecture: ArchitectureGraph,
    analysis: AnalysisSummary
) -> AnalysisResponse:
    critical_nodes_response = [
        CriticalNodeResponse(
            node_id=cn.node_id,
            node_name=architecture.get_node(cn.node_id).name
            if architecture.get_node(cn.node_id) else None,
            betweenness_score=cn.betweenness_score,
            in_degree=cn.in_degree,
            out_degree=cn.out_degree,
            reason=cn.reason,
        )
        for cn in analysis.critical_nodes
    ]

    cycles_response = [
        CycleResponse(
            nodes=c.nodes,
            length=c.length,
            formatted=c.formatted,
        )
        for c in analysis.cycles
    ]

    return AnalysisResponse(
        node_count=analysis.node_count,
        edge_count=analysis.edge_count,
        density=analysis.density,
        is_dag=analysis.is_dag,
        is_connected=analysis.is_connected,
        component_count=analysis.component_count,
        critical_nodes=critical_nodes_response,
        potential_spofs=analysis.potential_spofs,
        cycles=cycles_response,
        isolated_nodes=analysis.isolated_nodes,
        warnings=analysis.warnings,
    )