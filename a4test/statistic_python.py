import json
import os
from collections import defaultdict

from loguru import logger

from LLM.LLModel import OpenAIModel
from static.projectUtil import list_directories

if __name__ == '__main__':
    # codescan = OllamaModel("qwen2.5-coder:14b")
    codescan = OpenAIModel("gpt-4o")

    if "qwen2.5" in codescan.client_model:
        name = "qwen2.5"
    else:
        name = "gpt"

    base_path = "/home/rdhan/data/dataset/python"
    source_path = "/home/rdhan/tee"

    overwrite = False

    dirs = list_directories(base_path)
    out = []
    for project_path in dirs:
        code_file_path = os.path.join(project_path, "code_file")

        dirs = list_directories(code_file_path)
        dirs = [it for it in dirs if it.endswith("_python")]
        for dir_item in dirs:
            item = dict()
            logger.info(f"Switch to {dir_item}.")
            codescan.re_init_chat()

            if not "_python" in dir_item:
                continue

            hash_index = os.path.basename(dir_item)[:8]
            java_path_dir = os.path.join(code_file_path, dir_item)
            for name in ["gpt"]:
                executable = os.path.join(code_file_path, f"{hash_index}_rust_{name}")
                consistent = os.path.join(code_file_path, f"{hash_index}_rust_{name}_yes")

                item["executable"] = os.path.exists(executable)
                item["consistent"] = os.path.exists(consistent)

                type_json_path = os.path.join(java_path_dir, "type.json")
                if not os.path.exists(type_json_path):
                    item["list"] = None
                    continue

                try:
                    with open(type_json_path, "r") as f:
                        tmp = json.load(f)
                    item["list"] = tmp
                    out.append(item)
                except Exception as e:
                    item["list"] = None
                    continue

    # Define the desired order of types
    ordered_types = [
        "Encryption", "Decryption", "Signature", "Verification",
        "Hash", "Seed", "Random", "Serialization", "Deserialization"
    ]

    categories = defaultdict(lambda: {'total': 0, 'executable': 0, 'consistent': 0})

    data = out
    for entry in data:
        if entry['list']:
            types = entry['list']['type_list']
            # Process types in the specified order
            for t in ordered_types:
                if t in types:
                    categories[t]['total'] += 1
                    if entry['executable']:
                        categories[t]['executable'] += 1
                    if entry['consistent']:
                        categories[t]['consistent'] += 1

    print("Category Analysis:")
    for category in ordered_types:
        counts = categories[category]
        total = counts['total']
        executable_percent = (counts['executable'] / total) * 100 if total > 0 else 0
        consistent_percent = (counts['consistent'] / total) * 100 if total > 0 else 0
        print(f"Category: {category}")
        print(f"  Total: {total}")
        print(f"  Executable: {counts['executable']} ({executable_percent:.2f}%)")
        print(f"  Consistent: {counts['consistent']} ({consistent_percent:.2f}%)")
        print()
