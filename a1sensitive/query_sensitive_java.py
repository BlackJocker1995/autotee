import os
import re
from typing import Type

from loguru import logger
from tqdm import tqdm

from LLM.LLModel import OllamaModel, LLModel
from LLM.scenarios.sensitive_search import SensitiveSearchScenario
from static.projectUtil import read_code_block, save_code_block, list_directories


def extract_content_fun(text):
    pattern = r'\*\*(.*?)\*\*'
    matches = re.findall(pattern, text)
    return matches


def query_sensitive(codescan:Type[LLModel], dir_item:str, in_name:str, out_name:str) -> None:
    codes = read_code_block(dir_item, in_name)
    out = []
    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        block = code["block"]
        if len(block) > 10240:
            logger.debug("Over size, skip...")
            continue

        # ask what llm can find
        result = codescan.query(SensitiveSearchScenario.get_question1() + block)

        ###########question1################
        if "Yes" not in result:
            codescan.messages.clear()
            continue

        # ###########question2################
        # result = codescan.query(SensitiveSearchScenario.get_question2())
        # if "utilize" in result:
        #     code.update({"form": "utilize"})
        # elif "implement" in result:
        #     code.update({"form": "implement"})

        ###########question2################
        result_json = codescan.query_json(SensitiveSearchScenario.get_question3(),
                                          SensitiveSearchScenario.Que3)
        if result_json is None:
            continue
        if result_json.result == ['']:
            continue
        # is a list[str]
        type_list = result_json.result
        logger.debug(f"{block} ---- {type_list}")

        sensitive_dict = dict()
        ###########question4################
        for type_item in type_list:
            result_json = codescan.query_json(SensitiveSearchScenario.get_question4(type_item),
                                              SensitiveSearchScenario.Que4)
            # None answer.
            if result_json is None or len(result_json.result) == 0:
                continue
            # is a [str, list[str]]
            sensitive_dict.update({type_item: result_json.result})
        code.update({"sensitive": sensitive_dict})
        logger.debug(f"Detail: {sensitive_dict}")

        out.append(code)
        # clear
        codescan.messages.clear()
    save_code_block(dir_item, out, out_name)

if __name__ == '__main__':
    # codescan = OpenAIModel("gpt-4o")
    codescan = OllamaModel("qwen2.5-coder:7b")
    overwrite = False
    in_name = f"java"
    out_name = f"{codescan.client_model}_sen"

    dirs = list_directories("/home/rdhan/data/dataset/java")

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        if not overwrite and os.path.exists(f"{dir_item}/{out_name}.json"):
            continue
        query_sensitive(codescan, dir_item, in_name, out_name)



