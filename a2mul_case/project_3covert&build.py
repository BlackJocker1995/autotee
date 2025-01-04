import os

from build.build_assistance import JavaTestAssistance, PythonTestAssistance, TestAssistance
from static.get_env import return_env

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/python_type_test"
    env = return_env()
    project_path = os.path.join(base_path, "ym")

    test_assistance = TestAssistance.class_generator("python")

    test_assistance.convert_and_build(project_path, agent_model = "gpt-4o")
