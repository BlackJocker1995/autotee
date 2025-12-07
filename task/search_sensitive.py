import json
import os
import re
import sys
from typing import Optional, Type

from langchain_core.messages import AIMessage
from loguru import logger
from pydantic import BaseModel, ValidationError
from tqdm import tqdm

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import QuestionBool, SensitiveStatement, SensitiveType
from static.projectUtil import read_code_block, save_code_block
from utils.log_utils import logger, tqdm_logger

BLOCK_SIZE_LIMIT = 5120
LLM_SYSTEM_PROMPT = """You are an expert in code security and TEE (Trusted Execution Environment).
Your task is to identify "leaf functions" that are suitable for porting to a TEE.

A "leaf function" has the following properties:
1.  **Lowest level of the program structure:** It does not depend on other user-defined functions within the project. It can, however, use standard library functions.
2.  **Basic Arguments:** Its argument types are primitive data types (e.g., integers, floating-point numbers) or basic composite structures (e.g., arrays and strings).
3.  **No instance context:** It should not rely on instance variables (e.g., using `this` or `self`).
"""

OUTPUT_NAME_SUFFIX = "_sen"

SENSITIVE_CATEGORIES = "Specifically, cryptography includes [Encryption, Decryption, Signature, Verification, Hash, Seed, Random]; serialization includes [Serialization, Deserialization]."

# Prompts
def get_check_sensitive_prompt(block: str) -> str:
    return (
        "Does this function utilize or implement any operations related to [cryptography, serialization]? "
        f"{SENSITIVE_CATEGORIES}"
        f"``` {block} ```"
        'Your answer must be in a JSON format like `{"answer": true}` or `{"answer": false}`.'
    )

def get_sensitive_type_prompt(block: str) -> str:
    return (
        "Which specific subcategories type is it involve in? "
        f"{SENSITIVE_CATEGORIES}"
        f"``` {block} ```"
        'Your answer must be in a JSON format like `{"type_list": ["Type1", "Type2"]}`.'
    )

def get_sensitive_statements_prompt(block: str, sensitive_types: list[str]) -> str:
    return (
        f"List the code statements that involved in {sensitive_types}: "
        f"{SENSITIVE_CATEGORIES}"
        f"``` {block} ```"
        'Your answer must be in a JSON format like `{"statements": [{"type": "Type1", "statements": ["statement1", "statement2"]}]}`.'
    )





def _invoke_llm_chat(
    agent: LLModel, prompt: str, output_format: Optional[Type[BaseModel]] = None
):
    # Create a chat with structured output if format is provided
    chat = agent.create_stateless_chat(
        system_prompt=LLM_SYSTEM_PROMPT, output_format=output_format
    )

    result = chat.invoke({"messages": [{"role": "user", "content": prompt}]})

    # Manually extract token usage from the AIMessage
    if "messages" in result:
        for message in result["messages"]:
            if isinstance(message, AIMessage) and hasattr(message, "usage_metadata") and message.usage_metadata:
                input_tokens = message.usage_metadata.get("input_tokens", 0)
                completion_tokens = message.usage_metadata.get("output_tokens", 0)
                agent.total_input_tokens += input_tokens
                agent.total_completion_tokens += completion_tokens
                logger.debug(
                    f"Token usage for current invoke: Input={input_tokens}, Completion={completion_tokens}. "
                    f"Total: Input={agent.total_input_tokens}, Completion={agent.total_completion_tokens}"
                )
                break  # Assumes one AIMessage with usage info per call

    if "structured_response" in result:
        return result["structured_response"]
    
    return None 



def query_sensitive_project(
    project_path: str, language: str, llm_config: LLMConfig
) -> None:
    
    in_name = f"{language}_leaf"
    out_name = f"{llm_config.get_description()}{OUTPUT_NAME_SUFFIX}"

    logger.info(f"Switch to {project_path}.")
    input_dir = os.path.join(project_path, "ana_json")
    codes = read_code_block(input_dir, in_name)
    out = []
    processed_blocks = 0

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        try:
            agent = LLModel.from_config(llm_config)
            # Store token counts before processing this code block
            start_input_tokens = agent.total_input_tokens
            start_completion_tokens = agent.total_completion_tokens

            block = code["code"]

            if len(block) > BLOCK_SIZE_LIMIT:
                logger.debug("Over size, skip...")
                continue

            processed_blocks += 1
            # First question
            prompt1 = get_check_sensitive_prompt(block)
            result1_obj = _invoke_llm_chat(
                agent,
                prompt1,
                output_format=QuestionBool,
            )
            # Convert string to boolean
            result1 = result1_obj.answer if result1_obj else False

            if not result1: # The condition now directly uses the boolean result1
                continue

            # Second question
            prompt2 = get_sensitive_type_prompt(block)
            result2 = _invoke_llm_chat(
                agent,
                prompt2,
                output_format=SensitiveType,
            )
            if not result2 or not result2.type_list:
                continue

            sensitive_types = list(set(result2.type_list))

            # Third question
            prompt3 = get_sensitive_statements_prompt(block, sensitive_types)
            result3 = _invoke_llm_chat(
                agent,
                prompt3,
                output_format=SensitiveStatement,
            )

            if not result3 or not result3.statements:
                continue

            # If all three questions pass, retain the item and add the new attributes

            code["sensitive_check"] = result1
            code["sensitive_type"] = sensitive_types
            statements_dict = {item.type: item.statements for item in result3.statements}
            code["sensitive_statements"] = statements_dict
            logger.info(
                f"All sensitive checks passed and statements extracted for function. Sensitive check result: {code}"
            )
            out.append(code)

            # Calculate and log token usage for this session
            session_input_tokens = agent.total_input_tokens - start_input_tokens
            session_completion_tokens = (
                agent.total_completion_tokens - start_completion_tokens
            )
            logger.info(
                f"Session token usage for code block: Input={session_input_tokens}, "
                f"Completion={session_completion_tokens}, "
                f"Total={session_input_tokens + session_completion_tokens}"
            )
        except Exception as e:
            logger.error(f"Error processing code block: {e}")
            continue

    output_dir = os.path.join(project_path, "ana_json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    save_code_block(output_dir, out, out_name)
