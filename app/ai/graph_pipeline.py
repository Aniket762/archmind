import asyncio
import json
import logging
from typing import Any, TypedDict, Optional
from dataclasses import dataclass
 
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
 
from app.domain.architecture import ArchitectureGraph
from app.domain.nodes import Node, NodeType, ScalingStrategy
from app.domain.edges import Edge, ConnectionType
from app.ai.prompts import get_parse_prompt, get_validation_prompt, get_system_prompt

logger = logging.getLogger(__name__)

class ArchitectureState(TypedDict):
    user_prompt: str
    parsed_spec_json: Optional[str] = None
    parsed_spec_dict: Optional[str] = None

    validation_result: Optional[str] = None
    validation_passed:bool = False

    architecture_graph: Optional[ArchitectureGraph] = None

    error_message:Optional[str] = None
    error_step: Optional[str] = None

async def parse_step(state: ArchitectureState)-> ArchitectureState:
    logger.info("parse step: converting prompt to JSON")
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            max_tokens=2000,
        )

        parse_prompt = get_parse_prompt()
        system_prompt = get_system_prompt()

        formatted_prompt = parse_prompt.format(
            user_prompt = state["user_prompt"]
        )

        # msg which we pass to llm
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=formatted_prompt)
        ]

        logger.info("calling llm...")
        response = llm.invoke(messages)
        response_text = response.content

        logger.info("llm response received ({len(response_text)} chars")

        spec_dict = json.loads(response_text)

        state["parsed_spec_dict"] = response_text
        state["parsed_spec_dict"] = spec_dict

        logger.info("parse complete: {spec_dict.get('name', 'unknown')}")

        return state
    
    except json.JSONDecodeError as e:
        logger.error("json parse error: {e}")
        state["error_message"] = f"json parsing failed: {str(e)}"
        state["error_step"] = "parse"
        return state
    
    except Exception as e:
        logger.error("parse step failed:{e}")
        state["error_message"]=str(e)
        state["error_step"] = "parse"
        return state
    
# check for spec issue
async def validate_step(state: ArchitectureGraph) -> ArchitectureGraph:
    logger.info("validate step: spec realism ...")
    if state.get("error_step") == "parse":
        logger.warning("skipping parsing failed")
        return state
    
    try:
        llm=ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=500,
        )

        validation_prompt = get_validation_prompt()
        spec_json = json.dumps(state["parsed_spec_dict"],indent=2)

        formatted_prompt = validation_prompt.format(spec_json=spec_json)

        messages = [
            SystemMessage(content="You are an architecture reviewer"),
            HumanMessage(content=formatted_prompt)
        ]

        logger.info("calling llm for validation...")
        response = llm.invoke(messages)
        validation_text = response.content.strip()

        if "OK" in validation_text.upper():
            state["validaion_passed"]= True
            logger.info("validation passed {validation_text[:50]}")
        else:
            state["validaion_passed"] = False
            logger.warning("validation issue found {validation_text[:100]}")

        state["validaion_passed"] = validation_text
        return state

    except Exception as e:
        logger.error("validation step failed:{e}")
        state["error_message"] = str(e)
        state["error_step"] = "validate"
        return state

# json to domain models
async def convert_step(state: ArchitectureState) -> ArchitectureState:
    logger.info("building domain models...")

    if state.get("error_step"):
        logger.warning("skipping error in {state['error_step']}")
        return state
    
    try:
        spec = state["parsed_spec_dict"]
        arch = ArchitectureGraph(
            name=spec.get("name", "Generated Architecture"),
            description=spec.get("description", ""),
            source_prompt=state["user_prompt"],
            ai_generated=True,
        )
        
        logger.info(f"  Converting {len(spec.get('nodes', []))} nodes...")
        for node_spec in spec.get("nodes", []):
            node = Node(
                name=node_spec["name"],
                node_type=NodeType(node_spec["node_type"]),
                description=node_spec.get("description", ""),
                max_rps=node_spec.get("max_rps", 1000),
                replicas=node_spec.get("replicas", 1),
                latency_ms=node_spec.get("latency_ms", 50),
                scaling_strategy=ScalingStrategy(
                    node_spec.get("scaling_strategy", "none")
                ),
                critical=node_spec.get("critical", False),
                tags=node_spec.get("tags", []),
            )
            arch.add_node(node)
        
        logger.info(f"  converting {len(spec.get('edges', []))} edges...")
        for edge_spec in spec.get("edges", []):
            source_name = edge_spec["source_name"]
            target_name = edge_spec["target_name"]
            
            source_node = next(
                (n for n in arch.iter_nodes() if n.name == source_name),
                None,
            )
            target_node = next(
                (n for n in arch.iter_nodes() if n.name == target_name),
                None,
            )
            
            if not source_node or not target_node:
                raise ValueError(
                    f"Edge references invalid node: {source_name} → {target_name}"
                )
            
            edge = Edge(
                source_id=source_node.node_id,
                target_id=target_node.node_id,
                connection_type=ConnectionType(edge_spec["connection_type"]),
                max_rps=edge_spec.get("max_rps", 1000),
                latency_ms=edge_spec.get("latency_ms", 5),
                label=edge_spec.get("label", ""),
                has_circuit_breaker=edge_spec.get("has_circuit_breaker", False),
                has_retry=edge_spec.get("has_retry", False),
                has_timeout=edge_spec.get("has_timeout", True),
                timeout_ms=edge_spec.get("timeout_ms", None),
            )
            arch.add_edge(edge)
        
        state["architecture_graph"] = arch
        logger.info(f"✓ CONVERT complete: {arch.node_count} nodes, {arch.edge_count} edges")
        
        return state

    except Exception as e:
        logger.error(f"x convert step failed: {e}") 
        state["error_message"] = str(e)
        state["error_step"] = "convert"
        return state

def should_continue(state: ArchitectureState) -> str:
    if state.get("error_step"):
        return "error"
    return "continue"

# graph built
class ArchitecturePlannerWithLangGraph: 
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.graph = self._build_graph()
 
    def build_graph(self):
        graph_builder = StateGraph(ArchitectureState)
        
        graph_builder.add_node("parse", parse_step)
        graph_builder.add_node("validate", validate_step)
        graph_builder.add_node("convert", convert_step)
        
        graph_builder.set_entry_point("parse")
        
        graph_builder.add_edge("parse", "validate")
        graph_builder.add_edge("validate", "convert")
        graph_builder.add_edge("convert", END)
        
        return graph_builder.compile()
 
    async def plan(self, prompt: str) -> ArchitectureGraph:
        logger.info(f"planning from prompt ({len(prompt)} chars)...")
        
        initial_state: ArchitectureState = {
            "user_prompt": prompt,
            "parsed_spec_json": None,
            "parsed_spec_dict": None,
            "validation_result": None,
            "validation_passed": False,
            "architecture_graph": None,
            "error_message": None,
            "error_step": None,
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        if final_state.get("error_message"):
            logger.error(f"✗ Pipeline failed: {final_state['error_message']}")
            raise ValueError(final_state["error_message"])
        
        arch = final_state.get("architecture_graph")
        
        if not arch:
            raise ValueError("Pipeline completed but no architecture generated")
        
        logger.info(f"successfully generated: {arch.name}")
        return arch