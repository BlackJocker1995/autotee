
import os

from loguru import logger
from tqdm import tqdm

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
from static.projectUtil import read_code_block, save_code_block

BLOCK_SIZE_LIMIT = 10240
LLM_SYSTEM_PROMPT = """You are an expert in code security and TEE (Trusted Execution Environment).
Your task is to identify "leaf functions" that are suitable for porting to a TEE.

A "leaf function" has the following properties:
1.  **Lowest level of the program structure:** It does not depend on other user-defined functions within the project. It can, however, use standard library functions.
2.  **Basic Arguments:** Its argument types are primitive data types (e.g., integers, floating-point numbers) or basic composite structures (e.g., arrays and strings).
3.  **No instance context:** It should not rely on instance variables (e.g., using `this` or `self`).
"""
INPUT_NAME_PREFIX = "java_leaf"
OUTPUT_NAME_SUFFIX = "_sen"


def _invoke_llm_chat(agent: LLModel, prompt: str, output_format=None):
    if output_format:
        chat = agent.create_chat(system_prompt=LLM_SYSTEM_PROMPT, output_format=output_format)
    else:
        chat = agent.create_chat(system_prompt=LLM_SYSTEM_PROMPT)
    result = chat.invoke({"input": prompt})
    logger.debug(result)
    return result


def query_sensitive_project(project_path: str, language: str, llm_config: LLMConfig) -> None:
    agent = LLModel.from_config(llm_config)
    
    in_name = f"{language}_leaf"
    out_name = f"{agent.get_description()}{OUTPUT_NAME_SUFFIX}"

    logger.info(f"Switch to {project_path}.")
    input_dir = os.path.join(project_path, "ana_json")
    codes = read_code_block(input_dir, in_name)
    out = []

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        block = code["code"]

        if len(block) > BLOCK_SIZE_LIMIT:
            logger.debug("Over size, skip...")
            continue

        # First question
        result1 = _invoke_llm_chat(agent, "This is the source code of the function. If it meets all the specified conditions, please respond with **Yes**; otherwise, respond with **No**." + f"``` {block} ```", output_format=Output.Bool)
        if not result1 or getattr(result1, "answer") == False:
            continue

        # Second question
        result2 = _invoke_llm_chat(agent, "Which specific subcategories type is it involve in?" + f"``` {block} ```", output_format=Output.SensitiveType)
        if not result2:
            continue

        # Third question
        result3 = _invoke_llm_chat(agent, f"List the code statements that involved in {result2}:" + f"``` {block} ```", output_format=Output.SensitiveStatement)
        if not result3:
            continue
        
        # If all three questions pass, retain the item and add the new attributes
        code["sensitive_check"] = result1.answer
        code["sensitive_type"] = result2.type_list
        code["sensitive_statements"] = result3.statements
        out.append(code)
    
    output_dir = os.path.join(project_path, "ana_json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    save_code_block(output_dir, out, out_name)


