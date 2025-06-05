from typing import Type, Optional, Dict, Any
from loguru import logger
from pydantic import BaseModel, Field

from LLM.action import Scenario
from LLM.LLModel import LLMConfig, LLModel
from LLM.output import Output
from a4test.test_assistance import timing_decorator
from static.projectUtil import truncate_string

class ReactConfig(BaseModel):
    """Configuration for ReAct model."""
    max_turns: int = Field(default=20, description="Maximum number of turns")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    logging_enabled: bool = Field(default=True, description="Enable detailed logging")

def extract_json(text: str):
    """
    Extract a JSON string from a given text.

    This function attempts to locate and extract a JSON object from the input text.
    It identifies the JSON content by searching for the first opening curly brace `{`
    and the last closing curly brace `}`. The extracted JSON string is then returned,
    with any escaped underscores (`\_`) replaced by regular underscores (`_`).

    :param text: The input text containing the JSON object.
    :type text: str

    :returns: The extracted JSON string if successful, or an error message if an exception occurs.
    :rtype: str

    :raises Exception: If an error occurs during the extraction process, an error message is returned instead.
    """
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        json_content = text[json_start:json_end].replace("\\_", "_")
        return json_content
    except Exception as e:
        return f"Error extracting JSON: {e}"