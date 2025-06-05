import os

from loguru import logger

from LLM.LLModel import LLMConfig, LLModel
from build.build_assistance import TestAssistance
from static.projectUtil import list_directories

if __name__ == '__main__':
    # codescan = OllamaModel("qwen2.5-coder:32b")
    config = LLMConfig(provider="openai", model="gpt-4o")
    codescan = LLModel.from_config(config)
    base_path = "/home/rdhan/data/dataset/python_mul_case"

    overwrite = False

    dirs = list_directories(base_path)

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")

        project_path = os.path.join(base_path, dir_item)

        test_assistance = TestAssistance.class_generator("python")

        test_assistance.add_multiple_test_cases(codescan, project_path, overwrite)