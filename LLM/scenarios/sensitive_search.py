import json
import os

from typing import Optional, Dict

from pydantic import Field
# from static.code_match import determine_language_by_extension
def determine_language_by_extension(file_path: str):
    """
    根据文件扩展名判断编程语言类型。
    支持: Python, Java, JavaScript, C++, C, Go, Rust, 其他。
    """
    ext = file_path.lower().split('.')[-1]
    if ext == "py":
        return "python"
    elif ext == "java":
        return "java"
    elif ext in ("js", "jsx"):
        return "javascript"
    elif ext in ("cpp", "cc", "cxx", "hpp", "h"):
        return "cpp"
    elif ext == "c":
        return "c"
    elif ext == "go":
        return "go"
    elif ext == "rs":
        return "rust"
    else:
        return "unknown"


class SensitiveSearchScenario():


    sensitive_handle = {
        "cryptography": "Encryption, Decryption, Signature, Verification, Hash, Seed, Random",
        "data serialization" : "Serialization, Deserialization"
    }



    @classmethod
    def get_sensitive_operation_2str(cls):
        return str.format("[ {} ]", ", ".join(cls.sensitive_handle))

    @classmethod
    def check_sensitive_operation_prompt(cls) -> str:
        with open(os.path.join(os.path.dirname(__file__), 'sensitive_search_prompts.json'), 'r') as f:
            prompts = json.load(f)
        sensitive_keys = list(cls.sensitive_handle.keys())
        sensitive_details = "".join([f"{it} contains {cls.sensitive_handle[it]} ;" for it in sensitive_keys])
        return prompts["question1"].format(sensitive_keys=sensitive_keys, sensitive_details=sensitive_details)
    
    @classmethod
    def get_sensitive_types_prompt(cls) -> str:
        with open(os.path.join(os.path.dirname(__file__), 'sensitive_search_prompts.json'), 'r') as f:
            prompts = json.load(f)
        
        sensitive_subcategories = []
        for key in cls.sensitive_handle:
            sensitive_subcategories.extend([s.strip() for s in cls.sensitive_handle[key].split(',')])
        
        sensitive_subcategories_list = ", ".join(sensitive_subcategories)
        return prompts["question_sensitive_types"].format(sensitive_subcategories_list=sensitive_subcategories_list)

    @classmethod
    def get_sensitive_details_prompt(cls, que: str) -> str:
        with open(os.path.join(os.path.dirname(__file__), 'sensitive_search_prompts.json'), 'r') as f:
            prompts = json.load(f)
        return prompts["question4"].format(query=que)
