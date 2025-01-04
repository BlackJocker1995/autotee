import os
import json
from loguru import logger
from static.projectUtil import list_directories

def list_python_directories(base_path):
    # List all directories in the base path
    all_dirs = list_directories(base_path)
    # Filter directories that end with '_python'
    python_dirs = [d for d in all_dirs if d.endswith('_python')]
    return python_dirs

def read_test_files(python_dirs, base_path):
    test_contents = []
    for dir_item in python_dirs:
        logger.info(f"Switch to {dir_item}.")
        project_path = os.path.join(base_path, dir_item)
        test_file_path = os.path.join(project_path, 'main.py')
        if os.path.isfile(test_file_path):
            with open(test_file_path, 'r') as file:
                content = file.read()
                test_contents.append(content)
    return test_contents

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/python"
    overwrite = True

    dirs = list_directories(base_path)
    out = []
    for dir_item in dirs:
        project_path = os.path.join(base_path, dir_item)

        code_file = os.path.join(project_path, 'code_file')

        # Step 1: List directories ending with '_python'
        python_dirs = list_python_directories(code_file)

        # Step 2: Read 'test.py' files from each directory
        test_contents = read_test_files(python_dirs, base_path)

        if len(test_contents) != 0:
            out.extend(test_contents)

    out_file_path = os.path.join(base_path, 'positive.json')
    if os.path.exists(out_file_path) and not overwrite:
        exit()
    # Save the output to a JSON file
    with open(os.path.join(base_path, 'positive.json'), 'w', encoding = "utf-8") as json_file:
        json.dump(out, json_file, indent=4)
