import os
import json

from static.projectUtil import list_directories, save_code_block
from loguru import logger

def find_common_blocks(directory):
    """
    Finds common code blocks across JSON files in a directory.
    
    Args:
        directory (str): Path to directory containing JSON files with code blocks
        
    Returns:
        list: List of dictionaries containing unique code blocks and their metadata
    """
    block_dict = {}

    # 遍历文件夹中的文件
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
                        # 如果block已经在字典中，跳过
                        if block not in block_dict:
                            block_dict[block] = item

    # 返回所有共有block的字典
    return list(block_dict.values())


# 使用示例
directory_path = "/home/rdhan/data/dataset/java"
dirs = list_directories("/home/rdhan/data/dataset/java")

for dir_item in dirs:
    out = find_common_blocks(dir_item)
    logger.info(f"Switch to {dir_item} - Have {len(out)}.")
    save_code_block(dir_item, out, "sen_vote")
