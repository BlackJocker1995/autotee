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
    filepath = os.path.join(directory, "sen_vote.json")
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


if __name__ == "__main__":
    # Replace 'base_directory_path' with the actual base directory path
    base_directory_path = "/home/rdhan/data/dataset/java" # Or python, or another base path

    if not os.path.isdir(base_directory_path):
        logger.error(f"Base directory not found: {base_directory_path}")
    else:
        logger.info(f"Processing subdirectories in: {base_directory_path}")
        total_size = 0
        data_count = 0
        sizes = [] # List to store sizes for standard deviation calculation
        for item_name in os.listdir(base_directory_path):
            item_path = os.path.join(base_directory_path, item_name)
            if os.path.isdir(item_path):
                logger.info(f"Processing subdirectory: {item_path}")
                sen_vote_data = read_sen_vote_json(item_path)

                if sen_vote_data:
                    data_size = len(sen_vote_data)
                    logger.info(f"Successfully read sen_vote.json from {item_path}. Data size: {data_size}")
                    total_size += data_size
                    data_count += 1
                    sizes.append(data_size) # Add size to the list
                    # You can process the data here if needed
                    # print(json.dumps(sen_vote_data, indent=4))
                else:
                    logger.warning(f"Failed to read sen_vote.json or file not found in {item_path}.")

        if data_count > 0:
            average_size = total_size / data_count
            logger.info(f"Finished processing. Total data size: {total_size}, Number of files: {data_count}, Average data size: {average_size:.2f}")

            if data_count > 1:
                # Calculate standard deviation
                variance = sum([(x - average_size) ** 2 for x in sizes]) / (data_count - 1)
                std_dev = math.sqrt(variance)
                logger.info(f"Standard deviation of data size: {std_dev:.2f}")
            elif data_count == 1:
                 logger.info("Standard deviation cannot be calculated with only one data point.")
            else:
                 logger.info("No data points to calculate standard deviation.")

        else:
            logger.info("No sen_vote.json files found or processed.")
