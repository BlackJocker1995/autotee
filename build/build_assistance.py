import os
import shutil
from typing import Type

from loguru import logger
from .conversion_examples import JAVA_CONVERSION_EXAMPLES, PYTHON_CONVERSION_EXAMPLES

from LLM.llmodel import LModel, OpenAIModel
from LLM.output import Output
from LLM.react import ReActModel
from LLM.scenarios.code_build import CodeBuildScenario
from LLM.scenarios.code_conver import CodeConvertScenario
from LLM.scenarios.code_convert_test_build import CodeConvertBuildTestScenario
from build.build_dynamic import RustDynamic, CodeDynamic
from static.code_match import PythonCode
from static.get_env import return_env
from static.projectUtil import list_directories, copy_directory


class TestAssistance:
    def __init__(self, language:str):
        self.language = language
        self.exec = ""
        self.test_file_name = ""
        self.convert_example_str_list:list[str] = [""]
        self.code_dynamic:CodeDynamic = CodeDynamic.class_generator(self.language)

    def set_project_path(self, project_path:str):
        self.code_dynamic.project_path = project_path

    def set_project_name(self, project_name:str):
        self.code_dynamic.project_name = project_name

    def list_source_project(self, project_path):
        code_file_path = os.path.join(project_path, "code_file")

        # List all directories within the specified path
        dirs = list_directories(code_file_path)
        return [it for it in dirs if f"_{self.language}" in it]

    def _add_test_cases(self, agent, project_path, overwrite, is_multiple=False):
        """
        Base method for adding test cases
        :param agent: LLM agent instance
        :param project_path: Path to project directory
        :param overwrite: Whether to overwrite existing test files
        :param is_multiple: Whether to add multiple test cases
        :return: None
        """
        dirs = self.list_source_project(project_path)
        for dir_item in dirs:
            try:
                if not f"_{self.exec}" in dir_item:
                    continue
                
                logger.debug(f"Processing directory: {dir_item}")
                path_dir = os.path.join(project_path, "code_file", dir_item)
                main_file = os.path.join(path_dir, f'main.{self.exec}')
                test_file = os.path.join(path_dir, f'{self.test_file_name}.{self.exec}')

                if not self._should_process_test_file(test_file, overwrite, main_file):
                    continue

                agent.re_init_chat()
                source_code = self._read_source_code(main_file)
                
                if is_multiple:
                    self.code_dynamic.set_project_path(project_path)
                    result = self.code_dynamic.design_test_mul_cases(agent, source_code)
                else:
                    result = self.code_dynamic.design_test_case(agent, source_code)
                
                self._write_test_file(test_file, result)
                
            except Exception as e:
                logger.error(f"Error processing {dir_item}: {str(e)}")
                continue

    def _should_process_test_file(self, test_file, overwrite, main_file):
        """Check if test file should be processed"""
        if not overwrite and os.path.exists(test_file):
            logger.debug(f"Skipping existing test file: {test_file}")
            return False
            
        if not os.path.exists(main_file):
            logger.warning(f"Main file missing: {main_file}")
            return False
            
        return True

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
        name = LModel.get_short_name(agent_model)
        source_path = os.path.join(f"/home/rdhan/tmp/{name}/tee")

        code_file_path = os.path.join(project_path, "code_file")

        # List all directories within the specified path
        dirs = list_directories(code_file_path)
        dirs = [it for it in dirs if it.endswith(f"_{self.language}")]
        for dir_item in dirs:
            logger.info(f"Switch to {dir_item}.")
            # Skip directories that do not contain "_" in their name
            if not f"_{self.language}" in dir_item:
                continue

            # Extract a hash index from the directory name for naming Rust files
            hash_index = os.path.basename(dir_item)[:8]
            source_path_dir = os.path.join(code_file_path, dir_item)
            test_file = os.path.join(source_path_dir, f"{self.test_file_name}.{self.exec}")
            rust_path_dir = os.path.join(code_file_path, f"{hash_index}_rust_{name}")
            failed_path_dir = os.path.join(code_file_path, f"{hash_index}_rust_{name}_failed")

            if not overwrite and (os.path.exists(rust_path_dir) or os.path.exists(failed_path_dir)):
                logger.info(f"Skip this {rust_path_dir}")
                continue

            # Check if the main Java file exists; if not, log a warning and skip
            if not os.path.exists(test_file):
                logger.warning(f"Main {self.language} file does not exist, finish previous step first!")
                continue

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
            agent = LModel.class_generator(model_name)

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
            test_file = os.path.join(code_file_path, f"{hash_index}_{self.language}", f'{self.test_file_name}.{self.exec}')
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

            target_rust = RustDynamic(dir_item, "tee")
            target_rust.build_target()

    def _react_convert_build_test(self, code, path_dir, agent_model) -> int:
        rust_project_path = self._get_rust_project_path(agent_model)
        model = self._create_react_model(path_dir, rust_project_path, agent_model)
        
        if not self._analyze_code(model, code):
            return -1
            
        rust_code, rust_dependency = self._convert_code_to_rust(model, code)
        if rust_code is None:
            return -1
            
        self._setup_rust_project(rust_project_path, rust_code)
        
        return self._verify_build_success(model, rust_code)

    def _get_rust_project_path(self, agent_model) -> str:
        """Get the path for the Rust project"""
        return os.path.join(return_env()["tee_build_path"],
                          LModel.get_short_name(agent_model))

    def _create_react_model(self, path_dir, rust_project_path, agent_model):
        """Create and return a ReActModel instance"""
        return ReActModel(
            env_class=CodeConvertBuildTestScenario,
            client_model=agent_model,
            language=self.language,
            source_project_path=path_dir,
            rust_project_path=rust_project_path
        )

    def _analyze_code(self, model, code) -> bool:
        """Analyze the source code and add conversion examples"""
        qus_result = model.agent.query(CodeConvertBuildTestScenario.prompt_code_analysis(code))
        logger.info(qus_result)
        
        model.agent.add_message(
            "user", 
            CodeConvertBuildTestScenario.prompt_convert_example(
                self.language,
                self.convert_example_str_list
            )
        )
        return True

    def _convert_code_to_rust(self, model, code):
        """Convert the source code to Rust"""
        qus_result = model.agent.query_json(
            message=f" Implement this code using Rust with same type input and return. {code}."
                    f"Please note that if it pertains to random methods, consistency can be deemed adequate as long as the format is the same. ",
            output_format=Output.RustCodeWithDepend, 
            remember=True
        )

        if qus_result is None:
            return None, None

        model.agent.messages_memary.pop(2)
        return qus_result.code, qus_result.dependencies

    def _setup_rust_project(self, rust_project_path, rust_code):
        """Set up the Rust project with the converted code"""
        rust_target = RustDynamic(rust_project_path)
        rust_target.new_project()
        rust_target.clear_dependencies()
        rust_target.write_file_code("main.rs", rust_code)

    def _verify_build_success(self, model, rust_code) -> int:
        """Verify if the Rust code builds successfully"""
        qus_result = model.infer_react(
            question=CodeBuildScenario.convert_and_build_prompt(rust_code)
        )
        
        if qus_result != -1:
            logger.info("Success")
            return qus_result
            
        return -1

    def _react_convert(self, code_react, code):
        # Analysis function
        qus_result = code_react.model_agent.query(CodeConvertBuildTestScenario.prompt_code_analysis(code))
        logger.info(qus_result)

        # for item in self.convert_example_str_list:
        code_react.model_agent.add_message("user", CodeConvertBuildTestScenario.prompt_convert_example(self.language,
                                                                                                       self.convert_example_str_list))
        # Covernt
        qus_result = code_react.model_agent.query_json(
            message=f" Implement this code using Rust with same type input and return. ```{code}``` using Rust.",
            output_format=CodeConvertScenario.RustCodeFormatWithDep, remember=True)

        code_react.model_agent.messages_memary.pop(2)

        rust_code = qus_result.code
        rust_dependency = qus_result.dependency

        logger.debug(rust_code)
        # # Write the Rust code to a new project
        rust_target = RustDynamic()
        rust_target.new_project()
        rust_target.delete_file("main.rs")
        rust_target.clear_dependencies()
        rust_target.write_file_code("lib.rs",rust_code)
        rust_target.update_dependency(rust_dependency)
        logger.info(rust_dependency)

        qus_result = code_react.infer_react(question=CodeBuildScenario.convert_and_build_prompt(rust_code),
                                            output_format=CodeBuildScenario.ReactOutputForm)
        if "Get answer" in qus_result:
            logger.info(qus_result)
        else:
            return False

        return True

    def _rust_test_add(self, codescan: Type[LModel], rust_code: str, code: str = "") -> str:
        logger.debug(rust_code)
        message = ("This function code is in lib.rs of tee project. Write a main function."
                   # "The Rust program in main.rs reads input from the command line and forwards it to lib.rs."
                   "Note that the top of code should be 'use tee::{function name}', "
                   "which can import {funcion name} in lib.rs."
                   "And remember, only return the code. ")
        codescan.add_message('user', message)

        if code != "":
            message = f"This is its main fucntino in {self.language} version: ```{code}```"
            codescan.add_message('user', message)

        main_code = codescan.query_json(message=f"Code: ```{rust_code}```",
                                        output_format=Output.OutputCodeFormat)
        main_code = main_code.code

        return main_code

    @staticmethod
    def class_generator(language):
        """
        Generate and return an instance of the appropriate TestAssistance subclass based on the given language.

        :param language: A string representing the programming language (e.g., 'java' or 'python')
        :return: An instance of the corresponding TestAssistance subclass
        """
        # Dictionary mapping language strings to their respective TestAssistance subclasses
        class_dict = {
            "java": JavaTestAssistance,
            "python": PythonTestAssistance
        }
        # Return an instance of the appropriate subclass, initialized with the language
        return class_dict[language](language)

class JavaTestAssistance(TestAssistance):

    def __init__(self, language):
        super().__init__(language)
        self._init_java_config()
        
    def _init_java_config(self):
        """Initialize Java-specific configuration"""
        self.exec = "java"
        self.test_file_name = "Test"
        self.convert_example_str_list = JAVA_CONVERSION_EXAMPLES

class PythonTestAssistance(TestAssistance):
    def __init__(self,language:str):
        super().__init__(language)
        self._init_python_config()
        
    def _init_python_config(self):
        """Initialize Python-specific configuration"""
        self.exec = "py"
        self.test_file_name = "test"
        self.convert_example_str_list = PYTHON_CONVERSION_EXAMPLES

    def design_test_file(self, codescan, source_code):
        message = """
              You are a Python programmer. 
              I will provide you with a code snippet. 
              Please generate a main function to transform this code into a fully executable program.
              Please remember to import the necessary dependencies. 
              If a key is required, please make an attempt to provide one in the corresponding format.
              If a key is involved, you must provide an authentic one.
              And if there needs any token, seed, init_str, use "test".

              Only return the code. 
              """
        codescan.add_message("system", message)

        main_code = codescan.query_json("The function code is: " + source_code, CodeBuildScenario.CodeFormat)
        main_code = main_code.code

        return main_code

    def test_file_build(self, path_dir: str):
        env = return_env()
        if os.path.exists(os.path.join(path_dir, "can.text")):
            return
        codescan = OpenAIModel("gpt-4o")

        with open(os.path.join(path_dir, "test.py"), "r", encoding="utf-8") as f:
            code = f.read()

        output = PythonCode.test_build(path_dir, env=env)
        if ", line" in output:
            logger.info(path_dir)
            result = codescan.query_json(code + f"\n {output}", CodeConvertScenario.CodeFormat)
            with open(os.path.join(path_dir, "test.py"), "w", encoding="utf-8") as f:
                f.write(result.code)

        output = PythonCode.test_build(path_dir, env=env)
        if ", line" in output:
            # raise ValueError(path_dir)
            shutil.rmtree(path_dir)

        with open(os.path.join(path_dir, "can.text"), "w", encoding="utf-8") as f:
            f.write("")
