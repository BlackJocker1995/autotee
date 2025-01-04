import os
import json
import random


def read_json_files(base_path):
    positive_path = os.path.join(base_path, 'positive.json')
    negative_path = os.path.join(base_path, 'negative.json')

    with open(positive_path, 'r', encoding='utf-8') as pos_file:
        positive_list = json.load(pos_file)

    with open(negative_path, 'r', encoding='utf-8') as neg_file:
        negative_list = json.load(neg_file)

    return positive_list, negative_list


def sample_negative_list(positive_list, negative_list):
    num_samples = len(positive_list)
    sampled_negative_list = random.sample(negative_list, min(num_samples, len(negative_list)))
    return sampled_negative_list


def label_and_merge_lists(positive_list, sampled_negative_list):
    labeled_positive = [(item, 1) for item in positive_list]
    labeled_negative = [(item, 0) for item in sampled_negative_list]
    combined_list = labeled_positive + labeled_negative
    return combined_list


def save_to_file(combined_list, output_path):
    # Convert the list of tuples to a list of dictionaries for JSON serialization
    json_serializable_list = [{'data': item[0], 'label': item[1]} for item in combined_list]

    with open(output_path, 'w', encoding='utf-8') as out_file:
        json.dump(json_serializable_list, out_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    base_path = "/home/rdhan/data/dataset/python"
    overwrite = True

    positive_list, negative_list = read_json_files(base_path)
    sampled_negative_list = sample_negative_list(positive_list, negative_list)
    combined_list = label_and_merge_lists(positive_list, sampled_negative_list)

    output_path = os.path.join(base_path, 'combined_labeled_data.json')
    save_to_file(combined_list, output_path)
