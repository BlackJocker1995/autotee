
from typing import Optional, Dict

from pydantic import Field

from LLM.action import Scenario
from static.code_match import determine_language_by_extension


class SensitiveSearchScenario(Scenario):


    sensitive_handle = {
        "cryptography": "Encryption, Decryption, Signature, Verification, Hash, Seed, Random",
        "data serialization" : "Serialization, Deserialization"
    }



    @classmethod
    def get_sensitive_operation_2str(cls):
        return str.format("[ {} ]", ", ".join(cls.sensitive_handle))

    @classmethod
    def get_question1(cls) -> str:
        question1 = (
            f"This is the source code of the function. "
            f"If it meets all the specified conditions, please respond with **Yes**; "
            f"otherwise, respond with **No**. "
            f"Conditions1: The input (if have) and output types are base types, such as String, int, or byte[]."
            f"Conditions2: this code snippet use or implement any operation among {list(cls.sensitive_handle.keys())}."
            f"Specifically, ")
        for it in cls.sensitive_handle.keys():
            question1 += f"{it} contains {cls.sensitive_handle[it]} ;"
        return question1

    # @classmethod
    # def get_question2(cls) -> str:
    #     return ("Does this code utilize the operation, or does it implement the operation?"
    #             " Only answer **utilize** or **implement**")

    @classmethod
    def get_question3(cls) -> str:
        return ("Which specific subcategories type is it involve in? Like Hash,Serialization... "
                "note cryptography and data serialization are not subcategories.")

    @classmethod
    def get_question4(cls, que: str) -> str:
        return rf"List the code statements that involved in {que}."



    class Actions(Scenario.Actions):
        @staticmethod
        def static_code_structure(file_path, method_name):
            """
            Trace the source structure of a function named "method_name".
            :param file_path: the source file where other method call "method_name".
            :param method_name: name of the method to be traced.
            :return: source structure of "method_name"
            """
            # certain which program language is used
            code_class = determine_language_by_extension(file_path)

            # match and return
            return code_class.search_code_source(file_path, method_name)
