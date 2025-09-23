import os
import re

from loguru import logger
from tqdm import tqdm

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
from LLM.scenarios.sensitive_search import SensitiveSearchScenario
from static.projectUtil import read_code_block, list_directories


def extract_content_fun(text):
    pattern = r'\*\*(.*?)\*\*'
    matches = re.findall(pattern, text)
    return matches


def _should_skip_block(block: str) -> bool:
    if len(block) > 10240:
        logger.debug("Over size, skip...")
        return True

    # Check first line (only in dataset generation)
    if not any(sub in block.splitlines()[0].lower() for sub in
               ['token', 'password', 'credential', 'hash', 'cyber', 'key', 'serialize', 'enc', 'dec', 'chip',
                'verif', 'sign']):
        return True
    return False


def _perform_initial_sensitive_check(agent: LLModel, block: str) -> bool:
    chat = agent.create_chat(system_prompt="", output_format=None)
    return "Yes" in chat.invoke({"input": SensitiveSearchScenario.get_question1() + f"``` {block} ```"})


def _get_sensitive_types(agent: LLModel):
    chat_json = agent.create_chat(system_prompt="", output_format=Output.String)
    result_json = chat_json.invoke({"input": SensitiveSearchScenario.get_question3()})
    if not result_json or getattr(result_json, "result", ['']) == ['']:
        return None
    return result_json.result


def _get_sensitive_details_for_type(agent: LLModel, type_item: str):
    chat_type = agent.create_chat(system_prompt="", output_format=Output.StringList)
    result_json = chat_type.invoke({"input": SensitiveSearchScenario.get_question4(type_item)})
    if result_json and getattr(result_json, "result", None):
        return result_json.result
    return None


def query_sensitive(agent: LLModel, dir_item: str, in_name: str, out_name: str) -> None:
    codes = read_code_block(dir_item, in_name)
    out = []

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        block = code["block"]

        if _should_skip_block(block):
            continue

        if not _perform_initial_sensitive_check(agent, block):
            continue

        type_list = _get_sensitive_types(agent)
        if not type_list:
            continue

        logger.debug(f"{block} ---- {type_list}")

        sensitive_dict = {}
        for type_item in type_list:
            details = _get_sensitive_details_for_type(agent, type_item)
            if details:
                sensitive_dict[type_item] = details

        if sensitive_dict:
            code.update({"sensitive": sensitive_dict})
            logger.debug(f"Detail: {sensitive_dict}")
            out.append(code)

    # save_code_block(dir_item, out, out_name)


if __name__ == '__main__':
    # codescan = OpenAIModel("gpt-4o")
    config = LLMConfig(provider="ollama", model="qwen2.5-coder:32b")
    agent = LLModel.from_config(config)
    overwrite = True
    in_name = "java"
    out_name = LLModel.get_short_name("qwen2.5-coder:32b")

    dirs = list_directories("/home/rdhan/data/dataset/java")

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        if not overwrite and os.path.exists(f"{dir_item}/{out_name}.json"):
            continue
        query_sensitive(agent, dir_item, in_name, out_name)
