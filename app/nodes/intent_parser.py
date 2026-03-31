"""Node for parsing user intent into structured JSON."""
import json
import logging
from typing import Dict, Any
from app.graph.state import AnalystState
from app.llm.client import LLMClient
from app.llm.prompts import get_intent_parser_prompt

logger = logging.getLogger(__name__)


def parse_intent(state: AnalystState) -> Dict[str, Any]:
    """Parse user question into structured intent JSON."""
    user_question = state.get("user_question", "")
    logger.info(f"[parse_intent] Starting intent parsing for question: {user_question}")
    
    original_response = None
    try:
        llm_client = LLMClient()
        prompt = get_intent_parser_prompt(user_question)
        logger.debug(f"[parse_intent] Prompt: {prompt}")
        
        response = llm_client.chat_completion(prompt)
        original_response = response
        logger.info(f"[parse_intent] LLM response received: {response[:200]}...")
        
        # Extract JSON from response (handle cases where LLM adds extra text)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        logger.debug(f"[parse_intent] Cleaned response: {response}")
        
        intent = json.loads(response)
        logger.info(f"[parse_intent] Successfully parsed intent: {intent}")
        
        return {
            "intent": intent,
            "error": None
        }
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse intent JSON: {str(e)}"
        logger.error(f"[parse_intent] JSON decode error: {error_msg}")
        if original_response:
            logger.error(f"[parse_intent] Original response: {original_response}")
        return {
            "intent": None,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Intent parsing error: {str(e)}"
        logger.error(f"[parse_intent] Exception: {error_msg}", exc_info=True)
        if original_response:
            logger.error(f"[parse_intent] Original response: {original_response}")
        return {
            "intent": None,
            "error": error_msg
        }

