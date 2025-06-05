import json
import os

from loguru import logger

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
from LLM.scenarios.sensitive_search import SensitiveSearchScenario
from static.projectUtil import list_directories


def query_convert(codescan, block):
    # 新接口：每次新建 chat runnable
    chat = codescan.create_chat(system_prompt="", output_format=None)
    result = chat.invoke({"input": SensitiveSearchScenario.get_question1() + f"``` {block} ```"})

    ###########question1################
    if "Yes" not in result:
        # 新接口无需 re_init_chat，直接 return
        return None

    ###########question2################
    chat_json = codescan.create_chat(system_prompt="", output_format=Output.StringList)
    result_json = chat_json.invoke({"input": "Which specific algorithm is it involve in?"})
    if result_json is None:
        return None
    if getattr(result_json, "result", ['']) == ['']:
        return None
    # is a list[str]
    type_list = result_json.result

    sensitive_dict = dict()
    sensitive_dict.update({"type_list": type_list})
    return sensitive_dict

if __name__ == '__main__':
    # codescan = OllamaModel("qwen2.5-coder:14b")
    config = LLMConfig(provider="openai", model="gpt-4o")
    codescan = LLModel.from_config(config)

    if "qwen2.5" in codescan.client_model:
        name = "qwen2.5"
    else:
        name = "gpt"
    # codescan = OllamaModel("qwen2.5:32b")
    # codescan = OpenAIModel("gpt-4o")

    base_path = "/home/rdhan/data/dataset/java_mul_case"
    source_path = "/home/rdhan/tee"

    overwrite = False

    dirs = list_directories(base_path)

    for project_path in dirs:
        code_file_path = os.path.join(project_path, "code_file")

        # List all directories within the specified path
        dirs = list_directories(code_file_path)
        dirs = [it for it in dirs if it.endswith("_java")]
        for dir_item in dirs:
            logger.info(f"Switch to {dir_item}.")
            # clear at first
            codescan.re_init_chat()
            # Skip directories that do not contain "_java" in their name
            if not "_java" in dir_item:
                continue

            # Extract a hash index from the directory name for naming Rust files
            hash_index = os.path.basename(dir_item)[:8]
            java_path_dir = os.path.join(code_file_path, dir_item)
            java_main_file = os.path.join(java_path_dir, "main.java")

            # if os.path.exists(os.path.join(java_path_dir, "type.json")):
            #     continue

            if not os.path.exists(java_main_file):
                continue
            # Open and read the Java main file
            with open(java_main_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Process the Java code to convert it to Rust and extract dependencies
            result = query_convert(codescan, source_code)

            if result is None:
                continue
            else:
                with open(os.path.join(java_path_dir, "alo.json"), "w") as f:
                    json.dump(result, f)