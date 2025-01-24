import os
import re

from loguru import logger
from tqdm import tqdm

from LLM.llmodel import LModel, OllamaModel
from LLM.output import Output
from LLM.scenarios.sensitive_search import SensitiveSearchScenario
from static.projectUtil import read_code_block, list_directories


def extract_content_fun(text):
    pattern = r'\*\*(.*?)\*\*'
    matches = re.findall(pattern, text)
    return matches


def query_sensitive(agent: LModel, dir_item: str, in_name: str, out_name: str) -> None:
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
        
        agent.re_init_chat()

        # Ask what LLM can find
        if "Yes" not in agent.query(SensitiveSearchScenario.get_question1() + f"``` {block} ```"):
            continue

        result_json = agent.query_json(SensitiveSearchScenario.get_question3(), Output.StructureAnswer)
        if not result_json or result_json.result == ['']:
            continue

        type_list = result_json.result
        logger.debug(f"{block} ---- {type_list}")

        sensitive_dict = {}
        for type_item in type_list:
            result_json = agent.query_json(SensitiveSearchScenario.get_question4(type_item),
                                           Output.OutputStrListFormat)
            if result_json and result_json.result:
                sensitive_dict[type_item] = result_json.result

        if sensitive_dict:
            code.update({"sensitive": sensitive_dict})
            logger.debug(f"Detail: {sensitive_dict}")
            out.append(code)

    # save_code_block(dir_item, out, out_name)


if __name__ == '__main__':
    # codescan = OpenAIModel("gpt-4o")
    agent = OllamaModel("qwen2.5-coder:32b")
    overwrite = True
    in_name = f"java"
    out_name = f"{agent.client_model}_sen"

    dirs = list_directories("/home/rdhan/data/dataset/java")

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        if not overwrite and os.path.exists(f"{dir_item}/{out_name}.json"):
            continue
        query_sensitive(agent, dir_item, in_name, out_name)
