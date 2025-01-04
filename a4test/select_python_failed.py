import os
import re
import shutil
from loguru import logger
from static.projectUtil import list_directories


def copy_directories_to_target(original_dirs, source_base_path, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for dir_name in original_dirs:
        source_dir = os.path.join(source_base_path, dir_name)
        target_path = os.path.join(target_directory, os.path.basename(dir_name))

        if os.path.exists(source_dir):
            if not os.path.exists(target_path):
                shutil.copytree(source_dir, target_path)
                logger.info(f"Copied {source_dir} to {target_path}")
            else:
                logger.warning(f"Target directory {target_path} already exists. Skipping.")
        else:
            logger.warning(f"Source directory {source_dir} does not exist. Skipping.")


if __name__ == '__main__':
    source_base_path = "/home/rdhan/data/dataset/python"
    target_directory = "/home/rdhan/data/dataset/python_type_test"

    dirs = list_directories(source_base_path)
    original_dirs = []

    for dir_item in dirs:
        logger.info(f"Switch to {dir_item}.")
        tee_file_path = os.path.join(dir_item, "code_file")
        subdirs = list_directories(tee_file_path)

        # Find directories with '_qwen2.5_failed' using regex
        for subdir in subdirs:
            if subdir.endswith("_qwen2.5_failed"):
                match = re.match(r"(.+)_rust_qwen2.5_failed", subdir)
                if match:
                    original_dir_name = match.group(1) + "_python"
                    original_dirs.append(original_dir_name)

    # Copy the original directories to the target directory
    copy_directories_to_target(original_dirs, source_base_path, target_directory)
