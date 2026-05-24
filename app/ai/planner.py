import logging
import os
from app.domain.architecture import ArchitectureGraph
from app.ai.mock_planner import MockArchitecturePlanner

logger = logging.getLogger(__name__)

try:
    from app.ai.graph_pipeline import ArchitecturePlannerWithLangGraph
    LANGGRAPH_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, will use mock planner")

class ArchitecturePlanner:
    def __init__(self):
        self._use_langgraph = LANGGRAPH_AVAILABLE
        
        if self._use_langgraph:
            try:
                self._langgraph_planner = ArchitecturePlannerWithLangGraph(verbose=True)
                logger.info("initialized LangGraph planner")
            except Exception as e:
                logger.warning(f"failed to initialize LangGraph: {e}")
                self._use_langgraph = False
                self._mock_planner = MockArchitecturePlanner()
                logger.info("initialized mock planner")
        else:
            self._mock_planner = MockArchitecturePlanner()
            logger.info("initialized mock planner")
 
    async def plan(self, prompt: str) -> ArchitectureGraph:
        if len(prompt.strip()) < 10:
            raise ValueError("Prompt must be at least 10 characters")
 
        if self._use_langgraph:
            try:
                result = await self._langgraph_planner.plan(prompt)
                if result is not None:
                    logger.info(f"✓ Generated architecture with LangGraph")
                    return result
            except Exception as e:
                logger.warning(f"LangGraph failed: {e}, falling back to mock")
                self._use_langgraph = False
 
        # fall back to mock planner
        logger.info("using mock planner (keyword-based)")
        try:
            result = await self._mock_planner.plan(prompt)
            return result
        except Exception as e:
            logger.error(f"Both planners failed: {e}")
            raise ValueError(f"Architecture planning failed: {str(e)}")