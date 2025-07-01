import os

from loguru import logger

from LLM.llmodel import LLMConfig, LLModel
from build.build_assistance import TestAssistance
from static.projectUtil import list_directories
import numpy as np

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/java_mul_case"

    overwrite = False

    dirs = list_directories(base_path)

    average = []
    
    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")

        project_path = os.path.join(base_path, dir_item)

        test_assistance = TestAssistance.class_generator("java")

        test_assistance.run_test_branch_coverage(project_path)
        
        average.append(test_assistance.calculate_average_coverage(project_path, "branch"))
    
    print(np.mean(average))