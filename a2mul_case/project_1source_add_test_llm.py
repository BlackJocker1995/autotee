import os

from LLM.llmodel import OpenAIModel
from build.build_assistance import TestAssistance
from static.get_env import return_env

if __name__ == '__main__':
    # codescan = OllamaModel("qwen2.5-coder:32b")
    codescan = OpenAIModel("gpt-4o")
    base_path = "/home/rdhan/data/dataset/java_mul_case"

    env = return_env()
    project_path = os.path.join(base_path, env["BUILD_TARGET"])

    overwrite = False

    agent_model = "gpt-4o"
    test_assistance = TestAssistance.class_generator("java", "gpt-4o")

    test_assistance.add_mul_test_case(codescan, project_path, overwrite)
