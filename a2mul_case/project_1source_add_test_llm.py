import os

from LLM.llmodel import LLMConfig, LLModel
from build.build_assistance import TestAssistance
from static.get_env import return_env

if __name__ == '__main__':
    config = LLMConfig(provider="ollama", model="qwen2.5-coder:32b")
    codescan = LLModel.from_config(config)
    base_path = "/home/rdhan/data/dataset/java_mul_case"

    env = return_env()
    project_path = os.path.join(base_path, env["BUILD_TARGET"])

    overwrite = False
    test_assistance = TestAssistance.class_generator("java")

    test_assistance.add_multiple_test_cases(codescan, project_path, overwrite)
