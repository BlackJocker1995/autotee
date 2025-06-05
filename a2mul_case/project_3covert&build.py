import os

from build.build_assistance import TestAssistance
from static.get_env import return_env

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/java_mul_case"
    env = return_env()
    project_path = os.path.join(base_path, "akto")

    test_assistance = TestAssistance.class_generator("java")

    test_assistance.convert_and_build(project_path, agent_model = "qwen2.5-coder:32b")
