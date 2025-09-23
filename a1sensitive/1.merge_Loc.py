import os
import json
from loguru import logger
import math

def read_sen_vote_json(directory):
    """
    Reads the content of sen_vote.json file in a directory.
    Args:
        directory (str): Path to the directory containing sen_vote.json
    Returns:
        dict or None: Content of the JSON file, or None if file not found or error occurs
    """
    filepath = os.path.join(directory, "sen_manual.json")
    if not os.path.exists(filepath):
        logger.warning(f"sen_vote.json not found in {directory}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(f"Successfully read sen_vote.json from {directory}")
            return data
    except Exception as e:
        logger.error(f"Error reading sen_vote.json from {directory}: {e}")
        return None

def get_loc_from_sen_vote(sen_vote_data):
    """
    统计sen_vote.json中所有item的block字段代码行数总和
    Args:
        sen_vote_data (list): sen_vote.json内容（应为json array）
    Returns:
        int: Loc总数
    """
    if not isinstance(sen_vote_data, list):
        return 0
    loc_sum = 0
    for item in sen_vote_data:
        code = item.get("block", "")
        # 统计非空行
        loc_sum += sum(1 for line in code.splitlines() if line.strip())
    return loc_sum

if __name__ == "__main__":
    base_directory_path = "/home/rdhan/data/dataset/java" # Or python, or another base path

    if not os.path.isdir(base_directory_path):
        logger.error(f"Base directory not found: {base_directory_path}")
    else:
        logger.info(f"Processing subdirectories in: {base_directory_path}")
        loc_list = []
        for item_name in os.listdir(base_directory_path):
            item_path = os.path.join(base_directory_path, item_name)
            if os.path.isdir(item_path):
                logger.info(f"Processing subdirectory: {item_path}")
                sen_vote_data = read_sen_vote_json(item_path)
                if sen_vote_data:
                    loc = get_loc_from_sen_vote(sen_vote_data)
                    logger.info(f"Loc in {item_path}: {loc}")
                    loc_list.append(loc)
                else:
                    logger.warning(f"Failed to read sen_vote.json or file not found in {item_path}.")

        if loc_list:
            max_loc = max(loc_list)
            min_loc = min(loc_list)
            avg_loc = sum(loc_list) / len(loc_list)
            if len(loc_list) > 1:
                variance = sum([(x - avg_loc) ** 2 for x in loc_list]) / (len(loc_list) - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0

            logger.info(f"统计结果：")
            logger.info(f"最大Loc: {max_loc}")
            logger.info(f"最小Loc: {min_loc}")
            logger.info(f"平均Loc: {avg_loc:.2f}")
            logger.info(f"方差: {variance if len(loc_list) > 1 else 0.0:.2f}")
            logger.info(f"标准差: {std_dev:.2f}")
        else:
            logger.info("No sen_vote.json files found or processed.")