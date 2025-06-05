import os

from build.build_assistance import TestAssistance
from static.get_env import return_env

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/java_mul_case"
    source_path = "/home/rdhan/tee"

    env = return_env()
    project_path = os.path.join(base_path, env["BUILD_TARGET"])

    overwrite = True

    test_assistance = TestAssistance.class_generator("java")

    test_assistance.build_test_mul(project_path, "Test.java",overwrite)
