import os

from loguru import logger
from tqdm import tqdm

from build.build_assistance import TestAssistance
from static.projectUtil import list_directories
# comments test
if __name__ == '__main__':

    base_path = "/home/rdhan/data/dataset/python_type_test_deepseek"

    overwrite = False

    dirs = list_directories(base_path)

    for dir_item in tqdm(dirs):
        logger.info(f"Switch to {dir_item}.")

        project_path = os.path.join(base_path, dir_item)

        test_assistance = TestAssistance.class_generator("python")

        test_assistance.convert_and_build(project_path, agent_model="deepseek-r1")
