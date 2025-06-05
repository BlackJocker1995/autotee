import os
import json

def list_directories(base_path):
    # List all directories in the base_path
    return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/python"
    overwrite =True

    dirs = list_directories(base_path)
    out = []

    for dir_item in dirs:
        project_path = os.path.join(base_path, dir_item)
        file_path = os.path.join(project_path, "python.json")

        # Check if the file exists before attempting to open it
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Extract only the 'block' content
                blocks = [item['block'] for item in data if 'block' in item]
                out.extend(blocks)

    # Read the positive.json file
    positive_file_path = os.path.join(base_path, 'positive.json')
    if os.path.exists(positive_file_path):
        with open(positive_file_path, 'r', encoding='utf-8') as pos_file:
            positive_data = json.load(pos_file)
            positive_set = set(positive_data)

        # Remove items in out that are also in positive_data
        out = [item for item in out if item not in positive_set]

    # Output the combined data
    out_file_path = os.path.join(base_path, 'negative.json')
    if os.path.exists(out_file_path) and not overwrite:
        exit()

    # Save the output to a JSON file
    with open(out_file_path, 'w', encoding="utf-8") as json_file:
        json.dump(out, json_file, indent=4)
