import abc
import ast
import os
import re
from abc import abstractmethod
from typing import Optional, Type

import javalang
import pexpect
import ray
from loguru import logger

from build.build_dynamic import CodeDynamic


class ProgramCode(object):
    ast_type_map = {
        "definition" : None,
        "call" : None,
    }
    def __init__(self):
        self.match_pattern:str = ""
        self.file_exec:str = ""

    def find_spe_files(self, directory):
        """
        read specific files
        :param directory: subdirectory
        :return:
        """
        code_file = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(f'.{self.file_exec}'):
                    code_file.append(os.path.join(root, file))
        return code_file

    @staticmethod
    def read_code_from_file(file_path):
        # open new file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return ''.join(lines)

    @staticmethod
    @abstractmethod
    def get_method_block_with_name(method_name):
        pass

    @staticmethod
    @abstractmethod
    def locate_method_path(codes:str, method_name:str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_ast_description(codes: str) -> str:
        pass

    @classmethod
    def search_code_source(cls, file_path:str, method_name: str):
        # try to find block in same file
        codes = cls.read_code_from_file(file_path)
        match_result = cls.match_fun(codes, cls.get_method_block_with_name(method_name), file_path)
        if len(match_result) > 0:
            return match_result[0]['block']

        # can not find in the same file, run ast to catch source path.

        # get code source
        path_parts = cls.locate_method_path(codes, method_name)
        # Find the position of 'src' in the root_dir
        src_index = file_path.find('src')
        # Extract the portion before 'src'
        base_dir = file_path[:src_index]
        new_file_path = os.path.join(base_dir, *path_parts) + '.java'

        codes = cls.read_code_from_file(new_file_path)
        match_result = cls.match_fun(codes, cls.get_method_block_with_name(method_name), new_file_path)
        if len(match_result) > 0:
            return new_file_path, match_result[0]['block']


    @classmethod
    def _read_match_block(cls, file_path):
        # open new file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return ''.join(lines)

    @staticmethod
    def _find_matching_brace(code, start_index):
        stack = []
        for i in range(start_index, len(code)):
            if code[i] == '{':
                stack.append('{')
            elif code[i] == '}':
                stack.pop()
                if not stack:
                    return i
        return -1

    @staticmethod
    @abc.abstractmethod
    def test_build(path_dir:str, env) -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def match_fun(code_text: str, file_path: str, method_pattern):
        raise AttributeError('Sub class does not implement this function.')

    @staticmethod
    @abc.abstractmethod
    def match_fun_block_with_name(texts:str, file_path:str, name:str):
        raise AttributeError('Sub class does not implement this function.')

    @staticmethod
    @abc.abstractmethod
    def match_fun_block(texts:str, file_path:str):
        raise AttributeError('Sub class does not implement this function.')

    @staticmethod
    @abc.abstractmethod
    def remove_comments(texts:str):
        raise AttributeError('Sub class does not implement this function.')

class JavaCode(ProgramCode):

    match_pattern = r'\b(public|protected|private|static|final|\s)*[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*\{'
    #     #r'\b(public|protected|private|static|\s)*[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*{'

    ast_type_map = {
        "definition" : "method_declaration",
        "call" : "method_invocation",
    }

    def __init__(self):
        super().__init__()
        self.file_exec = 'java'

    @staticmethod
    def match_fun_block(code_text: str, file_path: str):
        """
        read all function in code_text.
        :param code_text:
        :param file_path:
        :return:
        """
        method_pattern = re.compile(JavaCode.match_pattern)

        return JavaCode.match_fun(code_text, file_path, method_pattern)

    @staticmethod
    def match_fun(code_text: str, file_path: str, method_pattern):
        # Find all potential method signatures
        matches = method_pattern.finditer(code_text)
        if "computeSHA1" in code_text:
            print()
        methods = []

        for match in matches:
            start = match.start()
            # Find the corresponding closing brace
            if not JavaCode.check_special_rule(code_text[match.start():match.end()]):
                end = JavaCode._find_matching_brace(code_text, match.end() - 1)
                if end != -1:
                    methods.append(
                        {"block": code_text[start:end + 1], "start": start, "end": end + 1, "path": file_path}
                    )
        return methods

    @staticmethod
    def check_special_rule(code_text:str):
        if "else if" in code_text:
            return True
        return False


    @staticmethod
    def get_method_block_with_name(method_name):
       return rf'\b(public|protected|private|static|\s)*[\w<>\[\]]+\s+{method_name}\s*\([^)]*\)\s*\{{'

    @staticmethod
    def remove_comments(code):
        # 去除单行注释
        code = re.sub(r'//.*', '', code)
        # 去除多行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    @staticmethod
    def locate_method_path(codes, method_name):
        # AST tree extract
        tree = javalang.parse.parse(codes)

        # check where is method_name
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            if node.member == method_name:
                # find qualifier's source
                for imp in tree.imports:
                    if imp.path.endswith(node.qualifier):
                        return imp.path
        return None

    @staticmethod
    def find_method_in_dir(root_dir):
        target_dir = os.path.join(root_dir, 'com', 'hippo')
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".java"):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        if 'class MyHash' in f.read():
                            print(f"Found MyHash in: {os.path.join(root, file)}")

    @staticmethod
    def get_ast_description(codes):
        pass

    @staticmethod
    def test_build(path_dir, env):
        cmd = ["javac", "Test.java"]
        return CodeDynamic.run_cmd(cmd, exe_env=path_dir)


class PythonCode(ProgramCode):
    @staticmethod
    def locate_method_path(codes: str, method_name: str) -> str:
        pass

    @staticmethod
    def get_ast_description(codes: str) -> str:
        pass

    @staticmethod
    def match_fun_block_with_name(texts: str, file_path: str, name: str):
        pass

    @staticmethod
    def remove_comments(texts: str):
        pass

    match_pattern = r'def\s+\w+\s*\(.*?\):\s*((?:\n\s+.+)+)'

    ast_type_map = {
        "definition": "function_definition",
        "call": "call",
    }

    def __init__(self):
        super().__init__()
        self.file_exec = 'py'

    @staticmethod
    def match_fun_block(code_text: str, file_path: str):
        """
                Matches a function block within the provided code text.

                This method utilizes the `PythonCode.match_fun` function to identify
                and match a function block in the given code text. The `code_text`
                parameter is currently not used in the matching process, as an empty
                string is passed to `match_fun`.

                :param code_text: The code text in which to search for a function block.
                :type code_text: str
                :param file_path: The path of the file containing the code.
                :type file_path: str
                :return: The result of the `PythonCode.match_fun` function call.
                :rtype: Depends on the implementation of `PythonCode.match_fun`
                """
        try:
            return PythonCode.match_fun("", file_path, "")
        except Exception as e:
            return []

    @staticmethod
    def match_fun(code_text: str, file_path: str, method_pattern: str) -> list:
        """
                Matches and extracts function blocks from a Python source file.

                This method reads the source code from the specified file path,
                parses it into an Abstract Syntax Tree (AST), and iterates over
                the nodes to identify function definitions. It extracts the source
                code of each function, excluding those named "main", and returns
                a list of dictionaries containing the function's source code block,
                start line, end line, and file path.

                :param code_text: The code text to be matched (currently unused).
                :type code_text: str
                :param file_path: The path to the Python source file.
                :type file_path: str
                :param method_pattern: A pattern to match methods (currently unused).
                :type method_pattern: str
                :return: A list of dictionaries, each containing details of a function block.
                :rtype: list of dict
                :raises FileNotFoundError: If the specified file does not exist.
                :raises SyntaxError: If the source code contains syntax errors.

                Each dictionary in the returned list contains:
                    - "block": The source code of the function.
                    - "start_line": The starting line number of the function in the file.
                    - "end_line": The ending line number of the function in the file.
                    - "path": The path to the source file.
        """
        with open(file_path, 'r', encoding="utf-8") as file:
            source = file.read()

        # Parse the source code into an AST
        tree = ast.parse(source)

        # Iterate over all nodes in the AST
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

        source_lines = source.splitlines()

        methods = []
        for func in functions:
            # Get the start and end line numbers of the function
            start_line = func.lineno - 1
            end_line = func.end_lineno if hasattr(func, 'end_lineno') else start_line

            # Extract the function body from the source lines
            func_source = "\n".join(source_lines[start_line:end_line])
            if func.name == "main":
                continue
            methods.append(
                {"block": func_source, "start_line": start_line, "end_line": end_line + 1, "path": file_path}
            )

        return methods

    @staticmethod
    def get_method_block_with_name(method_name):
        return rf'\b(public|protected|private|static|\s)*[\w<>\[\]]+\s+{method_name}\s*\([^)]*\)\s*\{{'


def determine_language_by_extension(filename) -> Type[ProgramCode]:
    # Map of file extensions to programming languages
    extension_to_language = {
        '.py': PythonCode,
        '.python': PythonCode,
        '.java': JavaCode,
    }

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # Return the corresponding programming language
    return extension_to_language.get(extension, 'Unknown')

def determine_language_name_by_extension(filename) -> str:
    # Map of file extensions to programming languages
    extension_to_language = {
        '.py': 'python',
        '.java': 'java',
    }

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # Return the corresponding programming language
    return extension_to_language.get(extension, 'Unknown')