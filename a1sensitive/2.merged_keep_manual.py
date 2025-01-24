import textwrap

from tqdm import tqdm

from static.projectUtil import list_directories, read_code_block, save_code_block

import os
from loguru import logger


def list_directories(directory_path):
    """返回指定路径下的所有目录"""
    try:
        return [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    except Exception as e:
        logger.error(f"Error listing directories: {e}")
        return []

def find_common_blocks(directory):
    """假设这个函数找到并返回目录中的公共代码块"""
    return "common_blocks"

def process_sen_votes(sen_votes):
    """通过用户输入决定保留哪些dict"""
    retained_votes = []
    for vote in tqdm(sen_votes):
        # Remove leading tabs and format the block for better readability
        formatted_block = textwrap.dedent(vote['block'])

        # Update the block in the dictionary
        vote['block'] = formatted_block

        # Print the formatted dictionary
        print(vote['block'])
        while True:
            user_input = input("Do you want to retain this vote? (y/n): ").strip().lower()
            if user_input in ['y', 'n']:
                break
            else:
                print("Please enter 'y' or 'n'.")
        if user_input == 'y':
            retained_votes.append(vote)
    return retained_votes

def main(overwrite=False):
    """Process sensitive votes for specified language"""
    
    language = "java"

    if language == 'java':
        directory_path = "/home/rdhan/data/dataset/java"
    else:
        directory_path = "/home/rdhan/data/dataset/python"

    dirs = list_directories(directory_path)

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        sen_file_path = os.path.join(directory_path, dir_item, "sen_manual.json")

        if os.path.exists(sen_file_path) and not overwrite:
            logger.info(f"Skipping {dir_item} as 'sen_manual.json' file already exists.")
            continue

        sen_votes = read_code_block(os.path.join(directory_path, dir_item), "sen_vote")
        logger.info(f"This project have {len(sen_votes)} codes related to sensitive.")
        processed_votes = process_sen_votes(sen_votes)
        save_code_block(os.path.join(directory_path, dir_item), processed_votes, "sen_manual")

if __name__ == "__main__":
    main()