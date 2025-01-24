import os
import json
import shutil

from static.projectUtil import list_directories, save_code_block
from loguru import logger

def find_common_blocks(directory):
    """
    Finds common code blocks across JSON files in a directory.
    
    // 在目录中查找JSON文件中的公共代码块
    Args:
        directory (str): Path to directory containing JSON files with code blocks
        
    Returns:
        list: List of dictionaries containing unique code blocks and their metadata
    """
    block_dict = {}

    # Traverse files in directory // 遍历文件夹中的文件
    for filename in os.listdir(directory):
        if filename.endswith('_sen.json'):
            filepath = os.path.join(directory, filename)

            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)

                for item in data:
                    if not 'sensitive' in item:
                        continue
                    block = item.get('block')
                    if block:
                        # Skip if block already in dictionary // 如果block已经在字典中，跳过
                        if block not in block_dict:
                            block_dict[block] = item

    # Return dictionary of all common blocks // 返回所有共有block的字典
    return list(block_dict.values())


def process_directory(directory_path):
    dirs = list_directories(directory_path)

    for dir_item in dirs:
        out = find_common_blocks(dir_item)
        if len(out) == 0:
            shutil.rmtree(dir_item)
            continue

        logger.info(f"Switch to {dir_item} - Have {len(out)}.")
        save_code_block(dir_item, out, "sen_vote")


# Usage example // 使用示例
if __name__ == "__main__":
    # Modify paths as needed // 根据需要修改路径
    java_directory = "/home/rdhan/data/dataset/java" 
    python_directory = "/home/rdhan/data/dataset/python"

    process_directory(java_directory)
    process_directory(python_directory)