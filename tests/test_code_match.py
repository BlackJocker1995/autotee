import unittest
from unittest.mock import MagicMock, patch, mock_open, PropertyMock
import os
from pathlib import Path
import sys


# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from static.code_match import ProgramCode, JavaCode, PythonCode, JAVA_LANGUAGE, PYTHON_LANGUAGE

# Mock tree_sitter and its language bindings
# This needs to be done before any class that imports them is defined
# For testing purposes, we'll ensure JAVA_LANGUAGE and PYTHON_LANGUAGE are not None
# In a real scenario, you might mock the tree_sitter.Language and Parser classes directly.

# Mock tree_sitter_java and tree_sitter_python to prevent ModuleNotFoundError
sys.modules['tree_sitter_java'] = MagicMock()
sys.modules['tree_sitter_python'] = MagicMock()

# Ensure the mocked language objects are not None for tests
sys.modules['tree_sitter_java'].language.return_value = MagicMock()
sys.modules['tree_sitter_python'].language.return_value = MagicMock()

class TestProgramCode(unittest.TestCase):

    def setUp(self):
        self.program_code = ProgramCode()

    def test_load_language_java(self):
        # Test loading Java language
        if JAVA_LANGUAGE is None:
            self.skipTest("JAVA_LANGUAGE is not loaded, skipping test.")
        self.program_code._load_language("java")
        self.assertIsNotNone(self.program_code.parser)
        self.assertEqual(self.program_code.language_module, JAVA_LANGUAGE)

    def test_load_language_python(self):
        # Test loading Python language
        if PYTHON_LANGUAGE is None:
            self.skipTest("PYTHON_LANGUAGE is not loaded, skipping test.")
        self.program_code._load_language("python")
        self.assertIsNotNone(self.program_code.parser)
        self.assertEqual(self.program_code.language_module, PYTHON_LANGUAGE)

    def test_load_language_unsupported(self):
        # Test unsupported language
        with self.assertRaises(ValueError):
            self.program_code._load_language("unsupported")

    def test_load_language_module_not_loaded(self):
        # Test when language module is None (e.g., tree-sitter failed to load)
        with patch('static.code_match.JAVA_LANGUAGE', None):
            self.program_code.parser = None # Reset parser to force reload
            with self.assertRaises(ValueError):
                self.program_code._load_language("java")

    @patch('static.code_match.ProgramCode._load_language')
    @patch('static.code_match.Parser')
    def test_parse(self, MockParser, mock_load_language):
        mock_parser_instance = MockParser.return_value
        mock_tree_root_node = MagicMock()
        mock_tree = MagicMock()
        mock_tree.root_node = mock_tree_root_node
        mock_parser_instance.parse.return_value = mock_tree
        
        self.program_code.parser = mock_parser_instance # Manually set the mocked parser
        
        code = "def func(): pass"
        lang_name = "python"
        result = self.program_code.parse(code, lang_name)
        
        mock_load_language.assert_called_once_with(lang_name)
        mock_parser_instance.parse.assert_called_once_with(code.encode("utf8"))
        self.assertEqual(result, mock_tree_root_node)

    def test_parse_parser_not_initialized(self):
        with patch('static.code_match.JAVA_LANGUAGE', None):
            with patch('static.code_match.PYTHON_LANGUAGE', None):
                self.program_code.parser = None
                with self.assertRaises(ValueError):
                    self.program_code.parse("some code", "python")

    @patch('os.path.exists', return_value=True)
    @patch('pathlib.Path.rglob')
    def test_find_specific_files(self, mock_rglob, mock_exists):
        self.program_code.file_exec = "py"
        
        # Create mock Path objects
        mock_path_py1 = MagicMock(spec=Path)
        mock_path_py1.suffix = ".py"
        mock_path_py1.__str__ = MagicMock(return_value="/test/dir/file1.py")
        mock_path_py1.is_file = PropertyMock(return_value=True)

        mock_path_py2 = MagicMock(spec=Path)
        mock_path_py2.suffix = ".py"
        mock_path_py2.__str__ = MagicMock(return_value="/test/dir/subdir/file2.py")
        mock_path_py2.is_file = PropertyMock(return_value=True)

        mock_path_txt = MagicMock(spec=Path)
        mock_path_txt.suffix = ".txt"
        mock_path_txt.__str__ = MagicMock(return_value="/test/dir/other.txt")
        mock_path_txt.is_file = PropertyMock(return_value=False) # This should be filtered out

        mock_rglob.return_value = [
            mock_path_py1,
            mock_path_py2,
            mock_path_txt
        ]
        
        result = self.program_code.find_specific_files("/test/dir")
        self.assertEqual(result, ["/test/dir/file1.py", "/test/dir/subdir/file2.py"])
        mock_exists.assert_called_once_with("/test/dir")
        mock_rglob.assert_called_once_with("*.py")
        # Assert that is_file was called on each mock Path object
        mock_path_py1.is_file.assert_called_once()
        mock_path_py2.is_file.assert_called_once()
        mock_path_txt.is_file.assert_called_once()

    @patch('os.path.exists', return_value=False)
    def test_find_specific_files_directory_not_exists(self, mock_exists):
        self.program_code.file_exec = "py"
        result = self.program_code.find_specific_files("/nonexistent/dir")
        self.assertEqual(result, [])
        mock_exists.assert_called_once_with("/nonexistent/dir")

    @patch('static.code_match.ProgramCode.extract_leaf_node')
    def test_ast_code_from_files(self, mock_extract_leaf_node):
        file_paths = ["file1.py", "file2.py"]
        mock_extract_leaf_node.side_effect = [
            ["func1_code", "func2_code"],
            ["func3_code"]
        ]
        
        result = self.program_code.ast_code_from_files(file_paths)
        self.assertEqual(result, ["func1_code", "func2_code", "func3_code"])
        self.assertEqual(mock_extract_leaf_node.call_count, 2)
        mock_extract_leaf_node.assert_any_call("file1.py")
        mock_extract_leaf_node.assert_any_call("file2.py")

    def test_ast_code_from_files_empty_list(self):
        result = self.program_code.ast_code_from_files([])
        self.assertEqual(result, [])

class TestJavaCode(unittest.TestCase):
    def setUp(self):
        self.java_code = JavaCode()
        # Mock the language module and parser for JavaCode tests
        self.mock_java_language = MagicMock()
        self.mock_parser = MagicMock()
        self.java_code.language_module = self.mock_java_language
        self.java_code.parser = self.mock_parser

    def test_match_leaf_block_non_java_language(self):
        result = self.java_code.match_leaf_block("dummy_path.java", "some code", MagicMock(), "python")
        self.assertEqual(result, [])

    def test_match_leaf_block_java_no_calls(self):
        file_path = "test_java_file.java"
        code = """
        class MyClass {
            public static void methodA() {
                System.out.println("Hello");
            }
            public static void methodB() {
                int x = 10;
            }
        }
        """
        # For actual tree-sitter parsing, we need the real parser
        program_code_instance = ProgramCode()
        program_code_instance._load_language("java")
        root_node = program_code_instance.parse(code, "java")

        java_code_instance = JavaCode()
        java_code_instance.language_module = program_code_instance.language_module
        java_code_instance.parser = program_code_instance.parser

        leaf_methods = java_code_instance.match_leaf_block(file_path, code, root_node, "java")
        self.assertEqual(len(leaf_methods), 2)
        self.assertIn('public static void methodA() {\n                System.out.println("Hello");\n            }', leaf_methods[0]['code'])
        self.assertEqual(leaf_methods[0]['file_path'], file_path)
        self.assertEqual(leaf_methods[0]['start_line'], 3)
        self.assertEqual(leaf_methods[0]['end_line'], 5)
        self.assertIn('public static void methodB() {\n                int x = 10;\n            }', leaf_methods[1]['code'])
        self.assertEqual(leaf_methods[1]['file_path'], file_path)
        self.assertEqual(leaf_methods[1]['start_line'], 6)
        self.assertEqual(leaf_methods[1]['end_line'], 8)

    def test_match_leaf_block_java_with_calls(self):
        file_path = "test_java_file.java"
        code = """
        class MyClass {
            public static void methodA() {
                System.out.println("Hello");
            }
            public static void methodB() {
                methodA();
            }
            public static void methodC() {
                methodA();
                System.out.println("World");
            }
        }
        """
        program_code_instance = ProgramCode()
        program_code_instance._load_language("java")
        root_node = program_code_instance.parse(code, "java")

        java_code_instance = JavaCode()
        java_code_instance.language_module = program_code_instance.language_module
        java_code_instance.parser = program_code_instance.parser

        leaf_methods = java_code_instance.match_leaf_block(file_path, code, root_node, "java")
        self.assertEqual(len(leaf_methods), 1)
        self.assertIn('public static void methodA() {\n                System.out.println("Hello");\n            }', leaf_methods[0]['code'])
        self.assertEqual(leaf_methods[0]['file_path'], file_path)
        self.assertEqual(leaf_methods[0]['start_line'], 3)
        self.assertEqual(leaf_methods[0]['end_line'], 5)

    def test_match_leaf_block_java_overloaded_methods(self):
        file_path = "test_java_file.java"
        code = """
        class MyClass {
            public static void methodA() {
                System.out.println("Hello");
            }
            public static void methodA(int x) {
                methodA(); // Calls methodA()
            }
            public static void methodB() {
                methodA(1); // Calls methodA(int)
            }
        }
        """
        program_code_instance = ProgramCode()
        program_code_instance._load_language("java")
        root_node = program_code_instance.parse(code, "java")

        java_code_instance = JavaCode()
        java_code_instance.language_module = program_code_instance.language_module
        java_code_instance.parser = program_code_instance.parser

        leaf_methods = java_code_instance.match_leaf_block(file_path, code, root_node, "java")
        self.assertEqual(len(leaf_methods), 1)
        self.assertIn('public static void methodA() {\n                System.out.println("Hello");\n            }', leaf_methods[0]['code'])
        self.assertEqual(leaf_methods[0]['file_path'], file_path)
        self.assertEqual(leaf_methods[0]['start_line'], 3)
        self.assertEqual(leaf_methods[0]['end_line'], 5)

class TestPythonCode(unittest.TestCase):
    def setUp(self):
        self.python_code = PythonCode()
        # Mock the language module and parser for PythonCode tests
        self.mock_python_language = MagicMock()
        self.mock_parser = MagicMock()
        self.python_code.language_module = self.mock_python_language
        self.python_code.parser = self.mock_parser

    def test_match_leaf_block_non_python_language(self):
        result = self.python_code.match_leaf_block("dummy_path.py", "some code", MagicMock(), "java")
        self.assertEqual(result, [])

    def test_match_leaf_block_python_no_calls(self):
        file_path = "test_python_file.py"
        code = """
def func_a():
    print("Hello")

def func_b():
    x = 10
"""
        program_code_instance = ProgramCode()
        program_code_instance._load_language("python")
        root_node = program_code_instance.parse(code, "python")

        python_code_instance = PythonCode()
        python_code_instance.language_module = program_code_instance.language_module
        python_code_instance.parser = program_code_instance.parser

        leaf_functions = python_code_instance.match_leaf_block(file_path, code, root_node, "python")
        self.assertEqual(len(leaf_functions), 2)
        self.assertIn('def func_a():\n    print("Hello")', leaf_functions[0]['code'])
        self.assertEqual(leaf_functions[0]['file_path'], file_path)
        self.assertEqual(leaf_functions[0]['start_line'], 2)
        self.assertEqual(leaf_functions[0]['end_line'], 3)
        self.assertIn('def func_b():\n    x = 10', leaf_functions[1]['code'])
        self.assertEqual(leaf_functions[1]['file_path'], file_path)
        self.assertEqual(leaf_functions[1]['start_line'], 5)
        self.assertEqual(leaf_functions[1]['end_line'], 6)

    def test_match_leaf_block_python_with_calls(self):
        file_path = "test_python_file.py"
        code = """
def func_a():
    print("Hello")

def func_b():
    func_a()

def func_c():
    func_a()
    print("World")
"""
        program_code_instance = ProgramCode()
        program_code_instance._load_language("python")
        root_node = program_code_instance.parse(code, "python")

        python_code_instance = PythonCode()
        python_code_instance.language_module = program_code_instance.language_module
        python_code_instance.parser = program_code_instance.parser

        leaf_functions = python_code_instance.match_leaf_block(file_path, code, root_node, "python")
        self.assertEqual(len(leaf_functions), 1)
        self.assertIn('def func_a():\n    print("Hello")', leaf_functions[0]['code'])
        self.assertEqual(leaf_functions[0]['file_path'], file_path)
        self.assertEqual(leaf_functions[0]['start_line'], 2)
        self.assertEqual(leaf_functions[0]['end_line'], 3)

    def test_match_leaf_block_python_method_calls(self):
        file_path = "test_python_file.py"
        code = """
class MyClass:
    def method_a(self):
        print("Hello")

    def method_b(self):
        self.method_a()

def outside_func():
    print("Outside")
"""
        program_code_instance = ProgramCode()
        program_code_instance._load_language("python")
        root_node = program_code_instance.parse(code, "python")

        python_code_instance = PythonCode()
        python_code_instance.language_module = program_code_instance.language_module
        python_code_instance.parser = program_code_instance.parser

        leaf_functions = python_code_instance.match_leaf_block(file_path, code, root_node, "python")
        self.assertEqual(len(leaf_functions), 2)
        self.assertIn('def method_a(self):\n        print("Hello")', leaf_functions[0]['code'])
        self.assertEqual(leaf_functions[0]['file_path'], file_path)
        self.assertEqual(leaf_functions[0]['start_line'], 3)
        self.assertEqual(leaf_functions[0]['end_line'], 4)
        self.assertIn('def outside_func():\n    print("Outside")', leaf_functions[1]['code'])
        self.assertEqual(leaf_functions[1]['file_path'], file_path)
        self.assertEqual(leaf_functions[1]['start_line'], 9)
        self.assertEqual(leaf_functions[1]['end_line'], 10)


if __name__ == '__main__':
    unittest.main()