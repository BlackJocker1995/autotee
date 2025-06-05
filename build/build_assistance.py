import os
import shutil
from typing import Type, Optional, List
from pathlib import Path
from dataclasses import dataclass, field

from loguru import logger
import pexpect

from build.convert_tools import create_convert_tools
from .conversion_examples import JAVA_CONVERSION_EXAMPLES, PYTHON_CONVERSION_EXAMPLES
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import BaseTool
from langchain.tools import tool
import re
import os

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
# from LLM.react import ReActModel
from LLM.scenarios.code_convert_test_build import CodeConvertBuildTestScenario
from build.build_dynamic import RustDynamic, CodeDynamic, BuildConfig
from static.code_match import PythonCode
from static.get_env import return_env
from static.projectUtil import list_directories, copy_directory


class TestAssistance:
    """Base class for language-specific test assistance"""

    def __init__(self, source_language: str, examples: Optional[list] = None, agent_model: Optional[str] = None):
        self.source_language = source_language
        self.examples = examples or []
        self.agent_model = agent_model
        self.code_dynamic = CodeDynamic.class_generator(source_language)
        # 默认配置
        self.exec = "py" if source_language == "python" else "java"
        self.test_file_name = "test" if source_language == "python" else "Test"
        if not self.examples:
            if source_language == "python":
                self.examples = PYTHON_CONVERSION_EXAMPLES
            elif source_language == "java":
                self.examples = JAVA_CONVERSION_EXAMPLES

    def set_project_path(self, project_path: str):
        self.code_dynamic.config.project_path = project_path

    def set_project_name(self, project_name: str):
        self.code_dynamic.config.project_path = project_name

    def list_source_project(self, project_path):
        code_file_path = os.path.join(project_path, "code_file")
        dirs = list_directories(code_file_path)
        return [it for it in dirs if f"_{self.source_language}" in it]

    def _add_test_cases(self, agent: LLModel, 
                       project_path: Path,
                       overwrite: bool, 
                       is_multiple: bool = False) -> None:
        """Add test cases to project
        
        Args:
            agent: Language model agent
            project_path: Project directory path
            overwrite: Whether to overwrite existing tests
            is_multiple: Whether to generate multiple test cases
        """
        for dir_item in self.list_source_project(project_path):
            #try:
            self._process_test_dir(dir_item, agent, overwrite, is_multiple)
            # except Exception as e:
            #     logger.error(f"Error processing {dir_item}: {str(e)}")

    def _should_process_test_file(self, test_file, overwrite, main_file):
        """Check if test file should be processed"""
        if not overwrite and os.path.exists(test_file):
            logger.debug(f"Skipping existing test file: {test_file}")
            return False
            
        if not os.path.exists(main_file):
            logger.warning(f"Main file missing: {main_file}")
            return False
            
        return True
    
    
    def _process_test_dir(self, dir_item: Path,
                         agent: LLModel,
                         overwrite: bool,
                         is_multiple: bool) -> None:

        main_file = os.path.join(dir_item, f"main.{self.code_dynamic.config.exec_extension}")
        test_file = os.path.join(dir_item, f"test.{self.code_dynamic.config.exec_extension}")
        
        if not self._should_process_test_file(test_file, overwrite, main_file):
            return
            
        source_code = self._read_source_code(main_file)
        result = self.code_dynamic.design_test_cases(agent, source_code, is_multiple)
        self._write_test_file(test_file, result)

    def _read_source_code(self, file_path):
        """Read source code from file"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_test_file(self, file_path, content):
        """Write test file content"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def add_single_test_case(self, agent, project_path, overwrite):
        """Add single test case"""
        self._add_test_cases(agent, project_path, overwrite, is_multiple=False)

    def add_multiple_test_cases(self, agent, project_path, overwrite):
        """Add multiple test cases"""
        self._add_test_cases(agent, project_path, overwrite, is_multiple=True)

    def build_test_one(self, project_path:str, file_name:str, overwrite=False):
        """
        2 step
        :param file_name:
        :param project_path:
        :param overwrite:
        :return:
        """

        dirs = self.list_source_project(project_path)
        for dir_item in dirs:
            logger.info(f"Switch to {dir_item}.")
            path_dir = os.path.join(project_path, "code_file", dir_item)

            if not os.path.exists(path_dir):
                logger.error(f"Init {path_dir} at first")
                continue

            if self.code_dynamic.is_build_target_exit(path_dir, file_name) and not overwrite:
                continue

            self.code_dynamic.build_file_with_fix(path_dir, file_name)

    def build_test_mul(self, project_path:str, file_name:str, overwrite=False):
        # List all source directories in the given project path
        dirs = self.list_source_project(project_path)

        # Iterate over each directory item
        for dir_item in dirs:
            logger.info(f"Switch to {dir_item}.")

            # Construct the full path to the directory
            path_dir = os.path.join(project_path, "code_file", dir_item)

            # Check if the directory exists
            if not os.path.exists(path_dir):
                logger.error(f"Init {path_dir} at first")
                continue  # Skip to the next directory if it doesn't exist

            # Set the current project path to the directory path
            self.set_project_path(str(path_dir))

            # Check if the build target already exists and if overwrite is not allowed
            if self.code_dynamic.is_build_target_exit(file_name) and not overwrite:
                continue  # Skip building if the target exists and overwrite is False

            # Build the file with necessary fixes
            self.code_dynamic.build_file_with_fix(file_name)

    def convert_and_build(self, project_path:str, agent_model:str, overwrite=False):
        """
        3 step
        :param agent_model:
        :param project_path:
        :param overwrite:
        :return:
        """

        # short name
        llm_config = LLMConfig(provider="openai", model=agent_model)
        llm = LLModel.from_config(llm_config)
        name = llm.get_short_name(agent_model)
        source_path = os.path.join(f"/home/rdhan/tmp/{name}/tee")

        code_file_path = os.path.join(project_path, "code_file")

        # List all directories within the specified path
        dirs = list_directories(code_file_path)
        dirs = [it for it in dirs if it.endswith(f"_{self.source_language}")]
        for dir_item in dirs:
            logger.info(f"Switch to {dir_item}.")
            # Skip directories that do not contain "_" in their name
            if not f"_{self.source_language}" in dir_item:
                continue

            # Extract a hash index from the directory name for naming Rust files
            hash_index = os.path.basename(dir_item)[:8]
            source_path_dir = os.path.join(code_file_path, dir_item)
            test_file = os.path.join(source_path_dir, f"{self.test_file_name}.{self.exec}")
            rust_path_dir = os.path.join(code_file_path, f"{hash_index}_rust_{name}")
            failed_path_dir = os.path.join(code_file_path, f"{hash_index}_rust_{name}_failed")

            # if not overwrite and (os.path.exists(rust_path_dir) or os.path.exists(failed_path_dir)):
            #     logger.info(f"Skip this {rust_path_dir}")
            #     continue

            # # Check if the main Java file exists; if not, log a warning and skip
            # if not os.path.exists(test_file):
            #     logger.warning(f"Main {self.source_language} file does not exist, finish previous step first!")
            #     continue

            # Open and read the Java main file
            with open(test_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Process the code to convert it to Rust and extract dependencies
            result = self._react_convert_build_test(source_code, source_path_dir, agent_model)
            if result != -1:
                copy_directory(source_path, rust_path_dir, ["target"])
                os.mkdir(os.path.join(rust_path_dir, f"{result}"))
            else:
                os.mkdir(failed_path_dir)

    def add_case_with_ref(self, project_path:str, model_name:str, overwrite = False):
        """
        4 step
        :param model_name:
        :param project_path:
        :param overwrite:
        :return:
        """
        code_file_path = os.path.join(project_path, "code_file")
        dirs = self.list_source_project(project_path)
        for dir_item in dirs:
            # create agent
            config = LLMConfig(provider='openai', model_name=model_name)
            agent = LLModel.from_config(config)

            # Skip directories that do not contain "_java" in their name
            if (not "_rust_" in dir_item) or ("_yes" in dir_item) or ("_no" in dir_item):
                continue
            logger.info(f"Switch to {dir_item}.")

            # Extract a hash index from the directory name for naming Rust files
            hash_index = os.path.basename(dir_item)[:8]
            basename = os.path.basename(dir_item)
            rust_path_dir = os.path.join(code_file_path, basename)
            rust_lib_file = os.path.join(rust_path_dir, 'tee', 'src', 'lib.rs')
            rust_main_file = os.path.join(rust_path_dir, 'tee', 'src', 'main.rs')
            test_file = os.path.join(code_file_path, f"{hash_index}_{self.config.source_language}", f'{self.test_file_name}.{self.exec}')
            failed_path_dir = os.path.join(code_file_path, f"{basename}_failed")

            if os.path.exists(failed_path_dir) or (not overwrite and os.path.exists(rust_main_file)):
                logger.info(f"Skip this {rust_lib_file}")
                continue

            # Check if the main Java file exists; if not, log a warning and skip
            if not os.path.exists(rust_lib_file):
                logger.warning("Lib rust file does not exist, finish previous step first!")
                continue

            # Open and read the rust main file
            with open(rust_lib_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Open and read the Java main file
            with open(test_file, "r", encoding="utf-8") as f:
                code = f.read()


            result = self._rust_test_add(agent, source_code, code)

            with open(rust_main_file, "w", encoding="utf-8") as f:
                f.write(result)
    
    def rust_test_build(self, project_path:str):
        """
        5 step
        :param project_path:
        :return:
        """
        code_file_path = os.path.join(project_path, "code_file")

        # List all directories within the specified path
        dirs = list_directories(code_file_path)
        dirs = [it for it in dirs if "_rust_" in it]
        for dir_item in dirs:
            # Skip directories that do not contain "_" in their name
            if "failed" in dir_item or "_yes" in dir_item or "_no" in dir_item:
                continue

            if os.path.exists(os.path.join(dir_item, 'tee','target','debug','tee')):
                continue

            logger.info(f"Switch to {dir_item}.")

            target_rust = RustDynamic(BuildConfig(dir_item, "tee"))  # Updated parameter
            target_rust.build_target()

    def _react_convert_build_test(self, code, path_dir, agent_model) -> int:
        """
        Convert, build, and test the given code using a langchain agent.

        :param code: The source code to be converted
        :param path_dir: The directory path of the source code
        :param agent_model: The agent model to be used
        :return: An integer indicating the success (-1) or failure (other values) of the process
        """
        rust_project_path = self._get_rust_project_path(agent_model)
        agent = self._create_react_model(path_dir, rust_project_path, agent_model)  # returns CompiledGraph


        self._setup_rust_project(rust_project_path)
        
        example_prompt = CodeConvertBuildTestScenario.prompt_convert_example(self.source_language, self.examples)
        convert_prompt = (
            f"Here is a conversion example:\n{example_prompt}\n"
            f"Please refer to the above example and convert the following code to Rust, keeping the input and output types the same. {code}\n"
            f"Note: If the code involves random methods, consistency can be considered sufficient as long as the format is the same."
        )
        convert_result = agent.invoke({"input": convert_prompt})
    
        if convert_result is None:
            return False
        return True

    def _get_rust_project_path(self, agent_model) -> str:
        """Get the path for the Rust project"""
        return os.path.join(return_env()["tee_build_path"],
                          LLModel.get_short_name(agent_model))

    def _create_react_model(self, path_dir, rust_project_path, agent_model, test_number=1):
        """
        Create and return a langchain agent (CompiledGraph) instance with project/file management and build tools.
        """
        
        llm_config = LLMConfig(provider="openai", model=agent_model)
        llm = LLModel.from_config(llm_config)

        tools = create_convert_tools(path_dir, rust_project_path, language=self.source_language)

        agent = llm.create_agent(tools)
        return agent

    def _analyze_code(self, agent, code) -> bool:
        """Analyze the source code only"""
        qus_result = agent.invoke({"input": CodeConvertBuildTestScenario.prompt_code_analysis(code)})
        logger.info(qus_result)
        return True

    def _convert_code_to_rust(self, agent, code):
        """Convert the source code to Rust, including example prompt"""
        example_prompt = CodeConvertBuildTestScenario.prompt_convert_example(
            self.config.source_language,
            self.config.examples
        )
        example_prompt_with_note = f"Here is a conversion example:\n{example_prompt}\n"
        prompt = (
            f"{example_prompt_with_note}"
            f"Please refer to the above example and convert the following code to Rust, keeping the input and output types the same. {code}\n"
            f"Note: If the code involves random methods, consistency can be considered sufficient as long as the format is the same."
        )
        qus_result = agent.invoke({"input": prompt})
        if qus_result is None:
            return None, None
        # 假设 qus_result 有 code, dependencies 属性
        return getattr(qus_result, "code", None), getattr(qus_result, "dependencies", None)

    def _setup_rust_project(self, rust_project_path, rust_code):
        """Set up the Rust project with the converted code"""
        rust_target = RustDynamic(BuildConfig(
            language="rust",
            exec_extension="rs",
            test_file_name="main.rs",
            project_path=rust_project_path,
            project_name="tee"
        ))
        rust_target.new_project()
        rust_target.clear_dependencies()
        rust_target.write_file_code("main.rs", rust_code)

    def _verify_build_success(self, agent, rust_code) -> int:
        """Verify if the Rust code builds successfully using agent.invoke"""
        prompt = CodeConvertBuildTestScenario.prompt_convert_and_build_prompt(rust_code)
        result = agent.invoke({"input": prompt})
        # 假设 result 为 int 或有相关属性
        if hasattr(result, "success") and result.success:
            logger.info("Success")
            return 1
        if isinstance(result, int) and result != -1:
            logger.info("Success")
            return result
        logger.warning("Build verification failed.")
        return -1

    def _rust_test_add(self, codescan: Type[LLModel], rust_code: str, code: str = "") -> str:
        logger.debug(rust_code)
        message = ("This function code is in lib.rs of tee project. Write a main function."
                   # "The Rust program in main.rs reads input from the command line and forwards it to lib.rs."
                   "Note that the top of code should be 'use tee::{function name}', "
                   "which can import {funcion name} in lib.rs."
                   "And remember, only return the code. ")
        codescan.add_message('user', message)

        if code != "":
            message = f"This is its main fucntino in {self.config.source_language} version: ```{code}```"
            codescan.add_message('user', message)

        main_code = codescan.query_json(message=f"Code: ```{rust_code}```",
                                        output_format=Output.Code)
        main_code = main_code.code

        return main_code

    def run_test_coverage(self, project_path:str) -> None:
        """Run coverage analysis for all test files in project directories.
        
        Similar pattern to build_test_mul but for coverage analysis.
        
        :param project_path: Root directory containing project files
        :type project_path: str
        :returns: Dictionary mapping directory names to coverage percentages
        :rtype: dict
        """
        # List all source directories in the given project path
        dirs = self.list_source_project(project_path)

        # Iterate over each directory item
        for dir_item in dirs:
            logger.info(f"Running coverage analysis for {dir_item}...")

            # Construct the full path to the directory
            path_dir = os.path.join(project_path, "code_file", dir_item)

            # Check if the directory exists
            if not os.path.exists(path_dir):
                logger.error(f"Directory {path_dir} does not exist")
                continue

            # Set the current project path
            self.set_project_path(str(path_dir))

            # Run coverage analysis 
            if hasattr(self.code_dynamic, 'run_coverage'):
                coverage = self.code_dynamic.run_coverage()
                if coverage:
                    coverage_file = os.path.join(path_dir, "coverage.txt")
                    with open(coverage_file, "w") as f:
                        f.write(f"Coverage: {coverage}%")
            else:
                logger.warning(f"Coverage analysis not supported for {self.config.source_language}")

    def calculate_average_coverage(self, project_path: str) -> float:
        """Calculate average coverage from coverage.txt files in project directories.
        
        :param project_path: Root directory containing project files
        :type project_path: str
        :returns: Average coverage percentage across all directories
        :rtype: float
        """
        dirs = self.list_source_project(project_path)
        coverages = []

        for dir_item in dirs:
            path_dir = os.path.join(project_path, "code_file", dir_item)
            coverage_file = os.path.join(path_dir, "coverage.txt")
            
            if os.path.exists(coverage_file):
                try:
                    with open(coverage_file, "r") as f:
                        content = f.read()
                        # Extract coverage percentage from "Coverage: XX%" format
                        coverage = float(content.split(":")[1].strip().replace("%", ""))
                        coverages.append(coverage)
                except (ValueError, IndexError) as e:
                    logger.error(f"Error reading coverage from {coverage_file}: {str(e)}")
                    continue
        
        if not coverages:
            logger.warning("No coverage data found")
            return 0.0
            
        return sum(coverages) / len(coverages)

    @staticmethod
    def class_generator(language) -> 'TestAssistance':
        """
        Generate and return an instance of the appropriate TestAssistance subclass based on the given language.
        """
        if language == "java":
            return TestAssistance("java", JAVA_CONVERSION_EXAMPLES)
        elif language == "python":
            return TestAssistance("python", PYTHON_CONVERSION_EXAMPLES)
        else:
            return TestAssistance(language)
