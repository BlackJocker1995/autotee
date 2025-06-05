import os.path
from typing import Optional, Dict

from build.build_dynamic import BuildConfig, RustDynamic, JavaDynamic, CodeDynamic
from static.get_env import return_env

def contains_star(arr):
    for item in arr:
        if '*' in item:
            return True
    return False

class CodeConvertBuildTestScenario():

    @classmethod
    def prompt_code_analysis(cls, code:str):
        return f"What does this piece of code accomplish? {code}"

    @classmethod
    def prompt_convert_example(cls, languages:str, convert_example_str_list:list[str]):
        out =  (f"Convert this {languages} code to Rust. "
                f"Their structure and the functions employed may differ."
                f"Note that it should be public. For example, ")
        for item in convert_example_str_list:
            out += item
        return out


    @classmethod
    def prompt_convert_and_build_prompt(cls, language:str) -> str:
        return (f"I will give you a block of {language} code; "
                f"Please follow its code logic and convert it into Rust program code."
                f"Please note that it is necessary to ensure that the functionality remains the same, "
                f"and some functions can be substituted with those provided by Rust."
                f"Ensure that the input and output remain unchanged.")
