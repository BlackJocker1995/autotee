import os
import shutil

from static.code_match import PythonCode
from static.thread_analysis import read_code_from_files_thread
from static.projectUtil import save_code_block, list_directories
from loguru import logger

if __name__ == '__main__':
    code_ana = PythonCode()

    overwrite = False

    dirs = list_directories("/home/rdhan/data/dataset/python")


    for dir_item in dirs:
        if not overwrite and os.path.exists(f"{dir_item}/python.json"):
           continue
        logger.info(f"Switch to {dir_item}")
        files = code_ana.find_spe_files(dir_item)

        try:
            results = read_code_from_files_thread(files,PythonCode)
        except Exception as e:
            continue

        results = [item for item in results if item["block"].count('\n') > 2]

        results = [item for item in results if item["block"].count('\n') < 128]

        logger.info(f"{dir_item}, We get {len(results)} code blocks.")

        if len(results) == 0:
            shutil.rmtree(dir_item)
            continue
        save_code_block(dir_item, results,"python")
