from tqdm import tqdm

from static.projectUtil import list_directories, short_hash

import os
from loguru import logger


def list_directories(directory_path):
    """返回指定路径下的所有目录"""
    try:
        return [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    except Exception as e:
        logger.error(f"Error listing directories: {e}")
        return []

def process_sen_manual(dir_item:str, sen_votes:list[dict], overwrite:bool):
    json_file = os.path.join(dir_item, "code_file")
    if not os.path.exists(java_file_path):
        os.makedirs(java_file_path)

    for code in tqdm(sen_votes):

        hash_index = short_hash(code["block"])


        current_file_path = os.path.join(java_file_path, f"{hash_index}_java")
        if not os.path.exists(current_file_path):
            os.makedirs(current_file_path)

        main_file = os.path.join(current_file_path, "main.java")
        # skip
        if os.path.exists(main_file) and overwrite:
            continue

        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code["block"])

def main(overwrite=False):
    directory_path = "/home/rdhan/data/dataset/java"
    dirs = list_directories(directory_path)

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        json_file = os.path.join(directory_path,dir_item,"sen_manual.json")
        if not os.path.exists(json_file):
            try:
                os.removedirs(os.path.join(directory_path,dir_item,"code_file"))
            except Exception as e:
                pass
if __name__ == "__main__":
    main()

