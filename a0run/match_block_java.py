import os

from static.code_match import JavaCode
from static.thread_analysis import read_code_from_files_thread
from static.projectUtil import save_code_block, list_directories
from loguru import logger

if __name__ == '__main__':
    code_ana = JavaCode()

    overwrite = False

    dirs = list_directories("/home/rdhan/data/dataset/java")


    for dir_item in dirs:
        if not overwrite and os.path.exists(f"{dir_item}/java.json"):
           continue

        files = code_ana.find_spe_files(dir_item)

        results = read_code_from_files_thread(files,JavaCode)

        results = [item for item in results if item["block"].count('\n') > 2]

        results = [item for item in results if item["block"].count('\n') < 128]

        logger.info(f"{dir_item}, We get {len(results)} code blocks.")

        save_code_block(dir_item, results,"java")
