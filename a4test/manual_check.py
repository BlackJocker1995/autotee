import os
import json
from typing import Type

from loguru import logger
from tqdm import tqdm

from LLM.LLModel import LLModel, OllamaModel, OpenAIModel
from LLM.scenarios.sensitive_search import SensitiveSearchScenario


def read_combined_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as in_file:
        combined_list = json.load(in_file)
    return combined_list

def query_sensitive(codescan:Type[LLModel], code:str) -> bool:
    # clear message at first
    codescan.re_init_chat()

    # ask what llm can find
    result = codescan.query(SensitiveSearchScenario.get_question1() + f"``` {code} ```")

    ###########question1################
    if "Yes" not in result:
        return False

    ###########question2################
    result_json = codescan.query_json(SensitiveSearchScenario.get_question3(),
                                      SensitiveSearchScenario.Que3)
    if result_json is None:
        return False
    if result_json.result == ['']:
        return False
    # is a list[str]
    type_list = result_json.result
    logger.debug(f"{code} ---- {type_list}")

    sensitive_dict = dict()
    ###########question4################
    for type_item in type_list:
        result_json = codescan.query_json(SensitiveSearchScenario.get_question4(type_item),
                                          SensitiveSearchScenario.Que4)
        # None answer.
        if result_json is None or len(result_json.result) == 0:
            return False
    return True


def test():
    base_path = "/home/rdhan/data/dataset/python"
    output_path = os.path.join(base_path, 'combined_labeled_data.json')

    # Read the combined labeled data
    loaded_combined_list = read_combined_file(output_path)

    # List samples and labels
    results = []
    for item in tqdm(loaded_combined_list):
        sample = item['data']
        is_positive = query_sensitive(codescan, sample)
        result_label = "positive" if is_positive else "negative"
        item.update({'result': result_label})
        results.append(item)

    # Optionally, save the results to a file
    results_output_path = os.path.join(base_path, 'qwen_results.json')
    with open(results_output_path, 'w') as results_file:
        json.dump(results, results_file, indent=4)

if __name__ == '__main__':
   test()
