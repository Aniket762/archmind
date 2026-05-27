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
    