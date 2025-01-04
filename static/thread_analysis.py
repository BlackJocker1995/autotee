import itertools
import re
from typing import Type

import numpy as np
import ray
from tqdm import tqdm

from static.code_match import ProgramCode

def read_pattern_code_from_file(file_path, code_pattern:Type[ProgramCode]):
    """
    read code from file
    :param code_pattern:
    :param file_path:
    :return:
    """
    try:
        # Attempt to read the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading with a different encoding, e.g., ISO-8859-1
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            lines = file.readlines()
    # merge
    texts = ''.join(lines)
    match_result = code_pattern.match_fun_block(texts, file_path)
    if match_result is None:
        return []
    return match_result

@ray.remote
def _read_code_from_files(file_paths, code_pattern:Type[ProgramCode]):
    """
    read all text
    :param file_paths:
    :return:
    """
    code_texts = []
    for file_path in file_paths:
        code_texts.extend(read_pattern_code_from_file(file_path, code_pattern))
    return code_texts


def read_code_from_files_thread(file_paths:list[str], code_pattern:Type[ProgramCode],thread=6):
    """
    read all text with multiple threads
    :param code_pattern:
    :param file_paths: file paths
    :param thread: default is six
    :return:
    """
    file_arrays = np.array_split(file_paths, thread)
    ray.init(include_dashboard=False, dashboard_host="127.0.0.1", dashboard_port=8088)
    futures = [_read_code_from_files.remote(file_array, code_pattern) for file_array in file_arrays]
    results = ray.get(futures)

    # list
    merged_list = list(itertools.chain.from_iterable(results))
    ray.shutdown()
    # reduce len(0)
    merged_list = [sublist for sublist in merged_list if len(sublist) > 0]
    return merged_list