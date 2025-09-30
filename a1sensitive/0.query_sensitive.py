import os

from loguru import logger
from tqdm import tqdm

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
from LLM.scenarios.sensitive_search import SensitiveSearchScenario
from static.projectUtil import read_code_block, list_directories, save_code_block

BLOCK_SIZE_LIMIT = 10240
LLM_POSITIVE_RESPONSE = "Yes"
LLM_SYSTEM_PROMPT = ""
LLM_PROVIDER = "vllm"
LLM_MODEL = "Qwen3-coder:30b"
INPUT_NAME_PREFIX = "java_leaf"
DATASET_PATH = "/home/rdhan/data/dataset/test"
OUTPUT_NAME_SUFFIX = "_sen"



def _invoke_llm_chat(agent: LLModel, prompt: str, output_format=None):
    if output_format:
        chat = agent.create_chat(system_prompt=LLM_SYSTEM_PROMPT, output_format=output_format)
    else:
        chat = agent.create_chat(system_prompt=LLM_SYSTEM_PROMPT)
    result = chat.invoke({"input": prompt})
    logger.debug(result)
    return result


def query_sensitive(agent: LLModel, dir_item: str, in_name: str, out_name: str) -> None:
    codes = read_code_block(dir_item, in_name)
    out = []

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        block = code["code"]

        if len(block) > BLOCK_SIZE_LIMIT:
            logger.debug("Over size, skip...")
            continue

        # First question
        result1 = _invoke_llm_chat(agent, "This is the source code of the function. If it meets all the specified conditions, please respond with **Yes**; otherwise, respond with **No**." + f"``` {block} ```", output_format=bool)
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
        code["sensitive_type"] = result2.answer
        code["sensitive_statements"] = result3.answer
        out.append(code)
    
    save_code_block(dir_item, out, out_name)

       
if __name__ == '__main__':
    # codescan = OpenAIModel("gpt-4o")
    config = LLMConfig(provider=LLM_PROVIDER, model=LLM_MODEL)
    agent = LLModel.from_config(config)
    overwrite = False
    in_name = f"{INPUT_NAME_PREFIX}"
    out_name = f"{agent.get_description()}{OUTPUT_NAME_SUFFIX}"

    dirs = list_directories(DATASET_PATH)

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        if not overwrite and os.path.exists(f"{dir_item}/{out_name}.json"):
            continue
        query_sensitive(agent, dir_item, in_name, out_name)
