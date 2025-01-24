import abc
import ast
import os
import re
from pathlib import Path
from abc import abstractmethod
from typing import Optional, Type, List, Set, Dict, Any, Pattern
from functools import lru_cache

import numpy as np
import itertools
import signal

import javalang
from loguru import logger

from build.build_dynamic import CodeDynamic


class ProgramCode(object):
    """Base class for program code analysis and processing."""
    
    def __init__(self) -> None:
        """Initialize ProgramCode with default values."""
        self.match_pattern: str = ""
        self.file_exec: str = ""

    def find_specific_files(self, directory: str) -> List[str]:
        """
        Find all files with the specified extension in the given directory.

        Args:
            directory (str): Path to the directory to search

        Returns:
            List[str]: List of file paths matching the extension
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return []

        return [
            str(path)
            for path in Path(directory).rglob(f"*.{self.file_exec}")
            if path.is_file()
        ]
    
    def ast_code_from_files(self, file_paths: List[str]) -> List[str]:
        """
        Extract code blocks from multiple files using the provided pattern matcher.

        Args:
            file_paths (List[str]): List of file paths to process
            code_pattern (Any): Pattern matcher object with match_fun_block method

        Returns:
            List[str]: List of matched code blocks
        """
        if not file_paths:
            return []

        return list(itertools.chain.from_iterable(
            self.extract_leaf_node(file_path)
            for file_path in file_paths
        ))
        
    
    def extract_leaf_node(self, file_path: str) -> List[str]:
        """
        Extract code blocks from a single file using the provided pattern matcher.

        Args:
            file_path (str): Path to the file to process
            code_pattern (Any): Pattern matcher object with match_fun_block method

        Returns:
            List[str]: List of matched code blocks
        """
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return []

    
        # Try UTF-8 first, fallback to ISO-8859-1 if needed
        encodings = ['utf-8', 'iso-8859-1']
        for encoding in encodings:

            with open(file_path, 'r', encoding=encoding) as file:
                texts = file.read()
                match_result = self.match_leaf_block(texts)
                return match_result if match_result is not None else []
    
    @abstractmethod
    def match_leaf_block(self, code: str) -> List[str]:
        """
        Match leaf blocks in the given code.
        A leaf block is a function/method that doesn't call other functions/methods.

        Args:
            code (str): The code to analyze

        Returns:
            List[str]: List of matched leaf blocks
        """
        try:
            tree = ast.parse(code)
            leaf_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if this function calls other functions
                    has_function_calls = any(
                        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        for n in ast.walk(node)
                    )

                    if not has_function_calls:
                        # Get the function's source code
                        function_code = ast.get_source_segment(code, node)
                        if function_code:
                            leaf_functions.append(function_code)

            return leaf_functions
        except SyntaxError:
            return []
    
class JavaCode(ProgramCode):
    def __init__(self) -> None:
        super().__init__()
        self.file_exec = "java"
        
    def match_leaf_block(self, code: str) -> List[str]:
        try:
            # Parse Java code into AST
            tree = javalang.parse.parse(code)

            # First pass: collect all user-defined method names
            method_names = set()
            for path, node in tree:
                if isinstance(node, javalang.tree.MethodDeclaration):
                    # Include parameter count to handle method overloads
                    method_names.add(f"{node.name}:{len(node.parameters)}")

            # Second pass: find leaf methods
            leaf_methods = []
            for path, node in tree:
                if isinstance(node, javalang.tree.MethodDeclaration):
                    # Check if this method calls any user-defined methods
                    has_user_method_calls = any(
                        isinstance(n, javalang.tree.MethodInvocation) and 
                        n.member in method_names
                        for n in node.children
                    )

                    if not has_user_method_calls:
                        # Get the method's source code
                        try:
                            # Get the method's starting line
                            start_line = node.position.line - 1
                            lines = code.splitlines()
                            
                            # Find the method's opening brace
                            method_start = start_line
                            while method_start < len(lines) and '{' not in lines[method_start]:
                                method_start += 1
                            
                            # Find the matching closing brace
                            brace_count = 1
                            method_end = method_start + 1
                            while method_end < len(lines) and brace_count > 0:
                                brace_count += lines[method_end].count('{')
                                brace_count -= lines[method_end].count('}')
                                method_end += 1
                            
                            # Extract the complete method
                            method_code = "\n".join(lines[start_line:method_end])
                        except (AttributeError, IndexError):
                            continue
                        leaf_methods.append(method_code)
                       
            return leaf_methods
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
            logger.warning(f"Error parsing Java code: {e}")
            logger.debug(f"Problematic code segment: {code[:50]}...")
            return []
        
class PythonCode(ProgramCode):
    def __init__(self) -> None:
        super().__init__()
        self.file_exec = "py"
        
    def match_leaf_block(self, code: str) -> List[str]:
        try:
            tree = ast.parse(code)
            leaf_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if this function calls other functions
                    has_function_calls = any(
                        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        for n in ast.walk(node)
                    )

                    if not has_function_calls:
                        # Get the function's source code
                        function_code = ast.get_source_segment(code, node)
                        if function_code:
                            leaf_functions.append(function_code)

            return leaf_functions
        except SyntaxError:
            return []