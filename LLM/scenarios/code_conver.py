import importlib
from typing import Optional, Dict

from pydantic import Field
from tree_sitter import Language, Parser
from LLM.action import Scenario
from LLM.llmodel import OllamaModel, OpenAIModel
from LLM.react import LModelReAct
from static.code_match import determine_language_by_extension, PythonCode, JavaCode
from static.code_parse import ast_bfs_with_call_graph, get_call_graph, get_code_ast


class CodeConvertScenario(Scenario):

    @classmethod
    def get_question1(cls, language:str, target_language:str) -> str:
        return (f"I will give you a block of {language} code; "
                f"Please follow its code logic and convert it into {target_language} program code."
                f"Please note that it is necessary to ensure that the functionality remains the same, "
                f"and some functions can be substituted with those provided by {target_language}."
                f"Ensure that the input and output remain unchanged."

                )

    class Actions(Scenario.Actions):
        @staticmethod
        def static_code_ast(language: str, block: str) -> str:
            """
            Generate an Abstract Syntax Tree (AST) representation of a code block for a specified programming language.

            This static method takes a code block and its corresponding programming language as input,
            and returns a string representation of the Abstract Syntax Tree (AST) for that code block.
            It supports multiple languages by dynamically importing the necessary modules.

            :param language: The programming language of the code block. Supported languages include "python" and "java".
            :type language: str

            :param block: The code block to be parsed into an AST.
            :type block: str

            :returns: A string representation of the Abstract Syntax Tree (AST) for the given code block.
            :rtype: str

            :raises ValueError: If the specified language is not supported.
            :raises ImportError: If the required module for the specified language cannot be imported.
            """

            # choose module
            switch = {
                "python": ('tree_sitter_python', PythonCode),
                "java": ('tree_sitter_java', JavaCode),
                # Add other languages here
            }

            if language not in switch:
                raise ValueError(f"Unsupported language: {language}")

            try:
                module_name, program_module = switch[language]
                module = importlib.import_module(module_name)
            except ImportError:
                raise ImportError(f"Failed to import module for language: {language}")

            # init parser
            parser = Parser(Language(module.language()))
            root = parser.parse(bytes(block, "utf8")).root_node

            call_graph = get_code_ast(root)
            return f"Abstract Syntax Tree: {call_graph}"

