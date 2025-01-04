import os

from loguru import logger

from LLM.llmodel import OpenAIModel
from build.build_assistance import TestAssistance
from static.projectUtil import list_directories




if __name__ == '__main__':
    # codescan = OllamaModel("qwen2.5-coder:32b")
    codescan = OpenAIModel("gpt-4o")
    base_path = "/home/rdhan/data/dataset/python_mul_case"

    overwrite = False

    dirs = list_directories(base_path)

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")

        project_path = os.path.join(base_path, dir_item)

        test_assistance = TestAssistance.class_generator("python")

        test_assistance.build_test_mul(project_path, "test.py", overwrite)
