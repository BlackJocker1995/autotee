from LLM.action import Scenario
from LLM.llmodel import OllamaModel
from LLM.react import LModelReAct
from static.code_match import JavaCode, determine_language_by_extension

class TEEUnsupportedSearchScenario(Scenario):
    class Que2(Scenario.OutputForm):
        result:list[str]

    class Que3(Scenario.OutputForm):
        result:list[str]


    unsupported_operation = {
        "Complex mathematical numbers":"Complex mathematical numbers",
        "Random number generator" : "Generate a random number.",
        "File reading and writing" : "For instance, FileRead, FileWrite, FileStream, FileOpen",
        "Regular expressions" : "For instance, Regular expression matching, Regular expression searching, Regular expression finding.",
        "Multithreading" : "For instance, Initiating multithreading, Thread synchronization, Thread communication."
    }



    question2 = (
        rf"""Which types are involved in this code snippet among {list(unsupported_operation.keys())}?""")
       #   Your output should be a string in json format.
       #  The json format that the output needs to follow:
       #  {Que2.model_json_schema()}
       # When outputting, **return the json string directly**, no additional output is required.
       #  Do not include any additional information in the output, just return the json string.
       #  Your Answer must not contain (```json**\n)
       #  Your output will be used to create an BaseModel object using BaseModel.model_validate_json.
        #""")

    question3 = (
        f"List the code statements that are ")

    @classmethod
    def get_unsupported_operation_2str(cls) -> str:
        return str.format("[ {} ]", ", ".join(cls.unsupported_operation))

    @classmethod
    def get_question1(cls) -> str:
        question1 = (
            f"Does this code snippet explicitly involves in any statements related to {list(cls.unsupported_operation.keys())}? "
            f"For instance, ")
        for it in cls.unsupported_operation.keys():
            question1 += f"<{it}> like {cls.unsupported_operation[it]} ...;"
        question1 += f"Only answer **No** or **Yes**."
        return question1

    @classmethod
    def get_question2(cls) -> str:
        return  rf"Which types are involved in this code snippet among {list(cls.unsupported_operation.keys())}?"

    @classmethod
    def get_question3(cls, que:str) -> str:
        return rf"{cls.question3} involved in {que}."


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



