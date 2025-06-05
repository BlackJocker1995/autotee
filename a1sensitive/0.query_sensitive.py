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


def query_sensitive(agent: LLModel, dir_item: str, in_name: str, out_name: str) -> None:
    codes = read_code_block(dir_item, in_name)
    out = []

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        block = code["block"]

        if len(block) > 10240:
            logger.debug("Over size, skip...")
            continue

        # Check first line (only in dataset generation)
        # if not any(sub in block.splitlines()[0].lower() for sub in
        #            ['token', 'password', 'credential', 'hash', 'cyber', 'key', 'serialize', 'enc', 'dec', 'chip',
        #             'verif', 'sign']):
        #     continue
        
        # 新接口：每次新建 chat runnable
        chat = agent.create_chat(system_prompt="", output_format=None)
        if "Yes" not in chat.invoke({"input": SensitiveSearchScenario.get_question1() + f"``` {block} ```"}):
            continue

        chat_json = agent.create_chat(system_prompt="", output_format=Output.StructureAnswer)
        result_json = chat_json.invoke({"input": SensitiveSearchScenario.get_question3()})
        if not result_json or getattr(result_json, "result", ['']) == ['']:
            continue

        type_list = result_json.result
        logger.debug(f"{block} ---- {type_list}")

        sensitive_dict = {}
        for type_item in type_list:
            chat_type = agent.create_chat(system_prompt="", output_format=Output.OutputStrListFormat)
            result_json = chat_type.invoke({"input": SensitiveSearchScenario.get_question4(type_item)})
            if result_json and getattr(result_json, "result", None):
                sensitive_dict[type_item] = result_json.result

        if sensitive_dict:
            code.update({"sensitive": sensitive_dict})
            logger.debug(f"Detail: {sensitive_dict}")
            out.append(code)

    # save_code_block(dir_item, out, out_name)


if __name__ == '__main__':
    # codescan = OpenAIModel("gpt-4o")
    config = LLMConfig(provider="ollama", model="qwen2.5-coder:32b")
    agent = LLModel.from_config(config)
    overwrite = False
    in_name = f"java"
    out_name = f"{agent.get_description()}_sen"

    dirs = list_directories("/home/rdhan/data/dataset/java")

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        if not overwrite and os.path.exists(f"{dir_item}/{out_name}.json"):
            continue
        query_sensitive(agent, dir_item, in_name, out_name)
