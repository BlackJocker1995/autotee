import os
import re
import shutil
import subprocess
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Type
import xml.etree.ElementTree as ET

import pexpect
from loguru import logger

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Output
from LLM.scenarios.generate_test_case import GenerateMulTestCaseScenario, GenerateOneTestCaseScenario
from static.get_env import return_env


@dataclass
class BuildConfig:
    """Configuration for build process"""
    language: str
    exec_extension: str
    test_file_name: str
    project_path: Optional[str] = None
    project_name: Optional[str] = None


class CodeDynamic:
    """Base class for dynamic code building and testing across multiple languages.

    This class provides core functionality for building, testing, and modifying code
    projects in various programming languages. It serves as an abstract base class
    that language-specific implementations (Java, Python, Rust) inherit from.

    Attributes:
        env (dict): Environment variables for the build process
        languages (str): Target programming language
        exec (str): File extension for executable files
        test_file_name (str): Default name for test files
        project_path (str): Path to the project directory
    """

    def __init__(self, config: BuildConfig):
        """Initialize the CodeDynamic instance.

        Args:
            config (BuildConfig): Configuration for the build process
        """
        self.config = config
        self._init_environment()

    def _init_environment(self) -> None:
        """Initialize build environment"""
        self.env = return_env()
        self.env['PATH'] = os.getenv('WORKPATH') + self.env.get('PATH', '')

    @abstractmethod
    def build_target(self, target_file: str):
        """Build the specified target file.

        :param target_file: Path to the target file to build
        :type target_file: str
        :returns: Build output or success message
        :rtype: str
        """
        pass

    @abstractmethod
    def modify_judgment(self, result) -> bool:
        """Determine if build output requires modifications.

        :param result: Build output to analyze
        :type result: str
        :returns: True if modifications are needed, False otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    def compile_project(self, path_dir: str, file_name: str) -> str:
        """Compile the project at the specified path.

        :param path_dir: Directory containing project files
        :type path_dir: str
        :param file_name: Main file to compile
        :type file_name: str
        :returns: Compilation output or success message
        :rtype: str
        """
        pass

    @abstractmethod
    def is_build_target_exit(self, file_name: str) -> bool:
        """Check if build target exists.

        :param file_name: Name of file to check
        :type file_name: str
        :returns: True if target exists, False otherwise
        :rtype: bool
        """
        pass

    @classmethod
    def run_cmd(cls, cmd: list[str], exe_env: str) -> str:
        """Execute a shell command and return its output.

        :param cmd: Command to execute as list of arguments
        :type cmd: list[str]
        :param exe_env: Working directory to execute command in
        :type exe_env: str
        :returns: Command output with ANSI escape sequences and build messages removed
        :rtype: str
        :raises Exception: If command execution fails
        """
        try:
            # Keep command as list to avoid bytes argument warning
            child = pexpect.spawn(cmd[0], args=cmd[1:], cwd=exe_env, timeout=30, encoding='utf-8')
            # Wait for the command to finish
            child.expect(pexpect.EOF)
            out_text = child.before
            logger.debug(out_text)

            # Remove ANSI escape sequences from output
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            clean_output = ansi_escape.sub('', out_text)

            # Split the string into lines
            lines = clean_output.splitlines()

            # Filter out lines that start with "Building"
            filtered_lines = [line for line in lines if not line.lstrip().startswith("Building")]

            # Recombine the remaining lines into a single string
            return '\n'.join(filtered_lines)
        except Exception as e:
            return f"Running error: {e}"

    def read_file_code(self, file_name: str) -> str:
        """Read and return the contents of a file.

        :param file_name: Name of file to read
        :type file_name: str
        :returns: Contents of the file as a string
        :rtype: str
        :raises IOError: If file cannot be read
        """
        with open(os.path.join(self.config.project_path, file_name), "r", encoding="utf-8") as f:
            return f.read()

    def write_file_code(self, file_name: str, code: str):
        """Write code to a file.

        :param file_name: Name of file to write to
        :type file_name: str
        :param code: Code content to write
        :type code: str
        :raises IOError: If file cannot be written
        """
        with open(os.path.join(self.config.project_path, file_name), "w", encoding="utf-8") as f:
            f.write(code)

    def set_project_path(self, project_path: str):
        """Set the project working directory.

        :param project_path: Path to set as project directory
        :type project_path: str
        """
        self.config.project_path = project_path

    def delete_file(self, file: str) -> None:
        """Delete a file from the project's source directory.

        :param file: Name of file to delete
        :type file: str
        :raises PermissionError: If lacking permissions to delete file
        :raises OSError: For other file system errors
        """
        file_path = os.path.join(self.config.project_path, self.config.project_name, "src", f"{file}")

        # Check if the file exists before attempting to delete it
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"The file {file} does not exist and cannot be deleted.")

    def design_test_cases(self, agent: "LLModel", code: str, multiple: bool = False) -> str:
        """Generate one or multiple test cases using an LLM agent.
        
        :param agent: Language model agent to generate test cases
        :type agent: LLModel
        :param code: Code to generate test cases for
        :type code: str
        :param multiple: Whether to generate multiple test cases, defaults to False
        :type multiple: bool
        :returns: Single test case string if multiple=False, list of test cases if multiple=True
        :rtype: str
        """
        # Choose scenario based on multiple flag
        if multiple:
            scenario = GenerateMulTestCaseScenario.class_generator(self.config.language, "mul_case")
            system_prompt = scenario.mul_case_system_prompt(self.config.language)
        else:
            scenario = GenerateOneTestCaseScenario.class_generator(self.config.language, "one_case")
            system_prompt = scenario.one_case_system_prompt(self.config.language)
            
        # 新接口：用 create_chat 生成 chat runnable
        chat = agent.create_chat(system_prompt=system_prompt, output_format=Output.OutputCodeFormat)
        out_code = chat.invoke({"input": scenario.query_prompt(code)})
        
        # Return appropriate format based on multiple flag
        return out_code.code if hasattr(out_code, "code") else out_code

    def build_test_case(self, agent: "LLModel", max_rounds=2):
        """Build and test a test case using an LLM agent.

        :param agent: Language model agent to use for test case generation
        :type agent: LLModel
        :param max_rounds: Maximum number of build attempts, defaults to 2
        :type max_rounds: int
        :returns: None if build succeeds within max_rounds
        :returns: None if build fails after max_rounds (project directory will be removed)
        :raises IOError: If unable to read/write test files
        """
        with open(os.path.join(self.config.project_path, "Test.java"), "r", encoding="utf-8") as f:
            code = f.read()

        for it in range(max_rounds):
            output = self.build_target()
            if not self.modify_judgment(output):
                return
            else:
                result = agent.query_json(code + f"\n {output}", Output.OutputCodeFormat)
                with open(os.path.join(self.config.project_path,
                                       f"{self.config.test_file_name}.{self.config.exec_extension}"), "w",
                          encoding="utf-8") as f:
                    f.write(result.code)

        shutil.rmtree(self.config.project_path)
        logger.info(f"{self.config.project_path} failed, rm!")

    def build_file_with_fix(self, file_name, max_round=5) -> bool:
        """Attempt to build a file with automatic fixes using an LLM.

        :param file_name: Name of the file to build
        :type file_name: str
        :param max_round: Maximum number of build attempts, defaults to 5
        :type max_round: int
        :returns: True if build succeeds, False if all attempts fail
        :raises IOError: If unable to read/write the file
        :raises RuntimeError: If LLM fails to generate fixes
        """
        agent = OpenAIModel("gpt-4o")
        for i in range(max_round):
            # read
            code = self.read_file_code(file_name)
            # builds
            output = self.build_target(file_name)
            if output == "success":
                logger.info("Build pass!")
                return True
            else:
                logger.info("Try build again.")
                result = agent.query_json(code + f"{output}, if code use log output, you can change to print",
                                          Output.OutputCodeFormat)
                with open(os.path.join(self.config.project_path, file_name), "w", encoding="utf-8") as f:
                    f.write(result.code)
        return False

    @staticmethod
    def class_generator(language: str, project_path: str = None, project_name: str = None):
        class_dict = {
            "java": JavaDynamic,
            "python": PythonDynamic,
            "rust": RustDynamic
        }
        return class_dict[language](
            BuildConfig(language=language, exec_extension="", test_file_name="", project_path=project_path,
                        project_name=project_name))


class RustDynamic(CodeDynamic):

    def __init__(self, config: BuildConfig):
        super().__init__(config)
        self.config.language = "rust"
        self.config.exec_extension = "rs"
        self.config.test_file_name = "test"

    def modify_judgment(self, result) -> bool:
        pass

    def compile_project(self, path_dir: str, file_name: str) -> str:
        pass

    def is_build_target_exit(self, file_name) -> bool:
        target = os.path.join(self.config.project_name, self.config.project_name, "src", file_name)
        return os.path.exists(target)

    def clear_dependencies(self):
        """
        Clear all dependencies in the Cargo.toml file.

        This function reads the `Cargo.toml` file from the specified project path,
        locates the `[dependencies]` section, and removes all lines following this section.

        :returns: True if the operation was successful, False if the file was not found
                  or an error occurred during the process.
        :rtype: bool

        :raises ValueError: If no `[dependencies]` section is found in the `Cargo.toml` file.
        :raises FileNotFoundError: If the `Cargo.toml` file does not exist at the specified path.
        :raises Exception: For any other errors that occur during file operations.
        """
        try:
            # Open the Cargo.toml file for reading
            with open(os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml'), 'r') as file:
                lines = file.readlines()

            # Find the [dependencies] section
            dependencies_index = None
            for i, line in enumerate(lines):
                if line.strip() == "[dependencies]":
                    dependencies_index = i
                    break

            if dependencies_index is None:
                raise ValueError("No [dependencies] section found in Cargo.toml")

            # Truncate the file content from the [dependencies] section onward
            lines = lines[:dependencies_index + 1]

            # Write the truncated lines back to the file
            with open(os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml'), 'w') as file:
                file.writelines(lines)

            logger.info("Cleared all dependencies in Cargo.toml.")
            return True
        except FileNotFoundError:
            logger.warning(
                f"File {os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml')} not found.")
            return False
        except Exception as e:
            logger.warning(f"An error occurred: {e}")
            return False

    def write_file_code(self, file_name: str, code: str) -> None:
        """Write code to a file in the Rust project's src directory.

        :param file_name: Name of the file to write
        :type file_name: str
        :param code: Code content to write
        :type code: str
        :raises IOError: If file cannot be written
        """
        with open(os.path.join(self.config.project_path, self.config.project_name, "src", f"{file_name}"), 'w',
                  encoding='utf-8') as f:
            f.write(code)

    def read_file_code(self, file_name: str) -> str:
        """
         Reads the content of a specified file within the project directory.

         This function opens a file located in the `src` directory of the project,
         reads its content, and returns it as a string. The file is opened with
         UTF-8 encoding to ensure proper handling of text data.

         :param file_name:
         :type file_name: str
         :return: The content of the file.
         :rtype: str

         :raises FileNotFoundError: If the specified file does not exist.
         :raises IOError: If an I/O error occurs during file access.
         """
        with open(os.path.join(self.config.project_path, self.config.project_name, "src", f"{file_name}"), 'r',
                  encoding='utf-8') as f:
            code = f.read()
        return code

    @staticmethod
    def split_message(message: str):
        """
          Splits a message into blocks based on a specific format pattern.

          This method uses a regular expression to identify and extract blocks of text
          from the input message. Each block starts with a format identifier followed by
          square brackets and a colon, and continues until a double newline or the end of
          the string is reached.

          :param message: The input message string to be split into blocks.
          :type message: str

          :return: A list of strings, where each string is a block extracted from the message.
        """
        # Regular expression pattern to match blocks starting with any format
        pattern = r'([a-zA-Z]+\[[^\]]+\]:.*?)(?=\n\n|\Z)'

        # Find matches
        matches = re.findall(pattern, message, re.DOTALL)

        # Output results as a list
        matches_list = [match.strip() for match in matches]

        return matches_list

    def new_lib(self):
        """Create a new Rust library project.

        Creates a new Rust library project using cargo new --lib command.
        The project will be created in the current project path.

        :raises Exception: If cargo command fails
        """
        cmd = ["cargo", "new", "--lib", ]
        self.run_cmd(cmd, exe_env=self.config.project_path)

    def new_project(self):
        """Create a new Rust binary project.

        Creates a new Rust binary project using cargo new command if it doesn't already exist.
        The project will be created in the current project path with the configured project name.

        :raises ValueError: If project_path or project_name is not set
        :raises Exception: If cargo command fails
        """
        if not self.config.project_path or not self.config.project_name:
            raise ValueError("Project path and name must be set before creating new project")
            
        if not os.path.exists(os.path.join(self.config.project_path, self.config.project_name)):
            cmd = ["cargo", "new", self.config.project_name]
            self.run_cmd(cmd, exe_env=self.config.project_path)

    def cargo_init(self):
        """Initialize a new Rust project in an existing directory.

        Initializes a new Rust project using cargo init command in the configured project directory.
        This is useful when working with existing directories that need to be converted to Rust projects.

        :raises Exception: If cargo command fails
        """
        cmd = ["cargo", "init", self.config.project_name]
        self.run_cmd(cmd, exe_env=os.path.join(self.config.project_path, self.config.project_name))

    def build_check(self) -> str:
        """Check the Rust project for errors or warnings.

        Runs cargo check to analyze the project for compilation errors and warnings
        without producing an executable. This is useful for quick feedback during development.

        :returns: String containing the check results. Returns "Check pass. The project is executable."
                 if successful, otherwise returns the error output.
        :rtype: str
        :raises Exception: If cargo check command fails
        """
        cmd = ["cargo", "check"]
        output = self.run_cmd(cmd, exe_env=os.path.join(self.config.project_path, self.config.project_name))

        # Find the position of "Checking tee v0.1.0" in the output
        marker = " Checking tee v0.1.0 (/home/rdhan/tmp/"
        marker_index = output.find(marker)

        # If the marker is found, remove everything before it
        if (marker_index != -1):
            output = output[marker_index + len(marker):]

        if "Finished `dev` profile" in output and "warning:" not in output:
            return "Check pass. The project is executable."
        else:
            return output

    def build_target(self, target_file: str = "tee") -> str:
        """Build the Rust project using Cargo.

        Compiles the specified target binary using cargo build. Checks for successful
        completion without warnings.

        :param target_file: Name of the binary target to build, defaults to "tee"
        :type target_file: str
        :returns: "success" if build succeeds, otherwise returns the error output
        :rtype: str
        :raises Exception: If cargo build command fails
        """
        cmd = ["cargo", "build", "--bin", target_file]
        output = self.run_cmd(cmd, exe_env=os.path.join(self.config.project_path, self.config.project_name))
        if "Finished `dev` profile" in output and "warning:" not in output:
            return "success"
        else:
            return output

    def execute(self) -> str:
        """Execute the compiled Rust program.

        Runs the compiled binary from the target/debug directory and captures its output.

        :returns: Standard output from the program execution
        :rtype: str
        :raises FileNotFoundError: If the executable cannot be found
        :raises subprocess.SubprocessError: If execution fails
        """
        rust_program = os.path.join(self.config.project_path, self.config.project_name, "target", "debug",
                                    self.config.project_name)
        env = os.environ.copy()
        out = subprocess.run([rust_program], env=env, capture_output=True)
        return out.stdout.decode('utf-8').strip()

    def explain_error_code(self, error_code: str) -> str:
        """Explain a Rust compiler error code.

        Uses rustc --explain to get detailed information about a specific Rust compiler error.

        :param error_code: The Rust error code to explain (e.g., E0382)
        :type error_code: str
        :returns: Explanation text from the Rust compiler
        :rtype: str
        :raises Exception: If rustc command fails
        """
        cmd = ["rustc", "--explain", error_code, "| cat"]
        output = self.run_cmd(cmd, exe_env=os.path.join(self.config.project_path, self.config.project_name))
        return output

    def update_dependency(self, dependencies: list, versions: list = None):
        """
        Update or add dependencies in the Cargo.toml file.

        This function reads the `Cargo.toml` file from the specified project path,
        locates the `[dependencies]` section, and either updates existing dependencies
        or adds new ones based on the provided lists. If no version list is provided,
        each dependency is set to a wildcard version (`*`), indicating that any version
        is acceptable.

        :param dependencies: A list of dependency names to be added or updated.
        :type dependencies: list
        :param versions: An optional list of versions corresponding to each dependency.
                         If not provided, all dependencies will default to version `*`.
        :type versions: list, optional

        :returns: True if the operation was successful, False if the file was not found
                  or an error occurred during the process.
        :rtype: bool

        :raises ValueError: If no [dependencies] section is found in Cargo.toml.
        :raises FileNotFoundError: If the Cargo.toml file does not exist at the specified path.
        :raises Exception: For any other errors that occur during file operations.
        """
        try:
            # Open the Cargo.toml file for reading
            with open(os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml'), 'r') as file:
                lines = file.readlines()

            # Find the [dependencies] section
            dependencies_index = None
            for i, line in enumerate(lines):
                if line.strip() == "[dependencies]":
                    dependencies_index = i
                    break

            if dependencies_index is None:
                raise ValueError("No [dependencies] section found in Cargo.toml")

            if versions is None:
                versions = ['*'] * len(dependencies)

            # Add or update each dependency from the dictionary
            for dependency_name, version in zip(dependencies, versions):
                # Check if the dependency already exists and update it
                updated = False
                for j in range(dependencies_index + 1, len(lines)):
                    if lines[j].strip().startswith(dependency_name):
                        lines[j] = f'{dependency_name} = "*"\n'
                        logger.info(f"Updated dependency '{dependency_name}' to version '{version}' in Cargo.toml.")
                        updated = True
                        break

                # If the dependency does not exist, add it
                if not updated:
                    new_dependency = f'{dependency_name} = "*"\n'
                    lines.insert(dependencies_index + 1, new_dependency)
                    logger.info(f"Added dependency '{dependency_name}' with version '{version}' to Cargo.toml.")

            # Write the updated lines back to the file
            with open(os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml'), 'w') as file:
                file.writelines(lines)
            return True
        except FileNotFoundError:
            logger.warning(
                f"File {os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml')} not found.")
            return False
        except Exception as e:
            logger.warning(f"An error occurred: {e}")
            return False

    def remove_dependency(self, dependency_name: str):
        """
        Remove a dependency from the Cargo.toml file.

        :param dependency_name: The name of the dependency to be removed.
        :type dependency_name: str

        :returns: True if the operation was successful, False otherwise.
        :rtype: bool
        """
        try:
            file_path = os.path.join(self.config.project_path, self.config.project_name, 'Cargo.toml')

            with open(file_path, 'r') as file:
                lines = file.readlines()

            dependencies_index = next((i for i, line in enumerate(lines) if line.strip() == "[dependencies]"), None)
            if dependencies_index is None:
                raise ValueError("No [dependencies] section found in Cargo.toml")

            # Remove the specified dependency if it exists
            lines = [line for i, line in enumerate(lines)
                     if not (i > dependencies_index and line.strip().startswith(dependency_name))]

            with open(file_path, 'w') as file:
                file.writelines(lines)

            logger.info(f"Dependency '{dependency_name}' processed in Cargo.toml.")
            return True
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found.")
            return False
        except Exception as e:
            logger.warning(f"An error occurred: {e}")
            return False


class JavaDynamic(CodeDynamic):

    def __init__(self, config: BuildConfig):
        super().__init__(config)
        self.config.language = "java"
        self.config.exec_extension = "java"
        self.config.test_file_name = "Test"

    def compile_project(self, path_dir: str, file_name: str) -> str:
        """Compile a Java project.

        :param path_dir: Directory containing the Java source files
        :type path_dir: str
        :param file_name: Main Java file to compile
        :type file_name: str
        :returns: Compilation output or success message
        :rtype: str
        :raises Exception: If compilation fails
        """
        pass

    def is_build_target_exit(self, file_name: str) -> bool:
        """Check if a compiled Java class file exists.

        :param file_name: Name of the Java source file to check
        :type file_name: str
        :returns: True if the corresponding .class file exists, False otherwise
        :rtype: bool
        """
        match = re.match(r'(.+).java$', file_name)
        if match:
            name = match.group(1)
            target = os.path.join(self.config.project_path, f"{name}.class")
            return os.path.exists(target)
        return False

    def modify_judgment(self, result) -> bool:
        """Determine if build output requires modifications.

        :param result: Build output to analyze
        :type result: str
        :returns: True if modifications are needed, False otherwise
        :rtype: bool
        """
        pass

    def build_target(self, target_name: str) -> str:
        """Compile a Java source file.

        :param target_name: Name of the Java file to compile
        :type target_name: str
        :returns: "success" if compilation succeeds, otherwise returns error output
        :rtype: str
        :raises Exception: If javac command fails
        """
        cmd = ["javac", target_name]
        output = self.run_cmd(cmd, exe_env=self.config.project_path)
        return "success" if output == "" else output

    def build(self, target_file="Test.java") -> str:
        """Build a Java test file.

        :param target_file: Name of the test file to build, defaults to "Test.java"
        :type target_file: str
        :returns: "success" if build succeeds, otherwise returns error output
        :rtype: str
        :raises Exception: If javac command fails
        """
        cmd = ["javac", target_file]
        output = self.run_cmd(cmd, exe_env=os.path.join(self.config.project_path, self.config.project_name))
        return "success" if output == "" else output

    def execute(self, target_file: str = None) -> str:
        """Execute a compiled Java program.

        :param target_file: Name of the class file to execute, defaults to test file name
        :type target_file: str
        :returns: Standard output from program execution
        :rtype: str
        :raises FileNotFoundError: If class file cannot be found
        :raises subprocess.SubprocessError: If execution fails
        """
        if not target_file:
            target_file = self.config.test_file_name
        env = CodeDynamic.env
        env['CLASSPATH'] = self.config.project_path
        out = subprocess.run(['java', target_file], env=env, capture_output=True)
        return out.stdout.decode('utf-8').strip()

    def run_coverage(self) -> float:
        """Run JaCoCo coverage analysis on Java test file.

        :returns: Coverage percentage as float, or -1 if analysis fails
        :rtype: float
        """
        try:
            # 1. Compile Java files
            logger.info("Compiling Java files...")
            if self.build_target("Test.java") != "success":
                return -1

            # 2. Run program with JaCoCo agent
            logger.info("\nRunning with JaCoCo agent...")
            jacoco_exec = "jacoco.exec"
            subprocess.run([
                'java',
                f'-javaagent:{os.environ.get("JACOCO_AGENT")}=destfile={jacoco_exec}',
                'Test'
            ], check=True, env=self.env, cwd=self.config.project_path)

            # 3. Generate report
            logger.info("\nGenerating coverage report...")
            report_dir = "coverage-report"
            subprocess.run([
                'java', '-jar', os.environ.get('JACOCO_CLI'),
                'report', jacoco_exec,
                '--classfiles', '.',
                '--sourcefiles', '.',
                '--html', report_dir,
                '--xml', 'coverage.xml'
            ], check=True, env=self.env, cwd=self.config.project_path)

            # 4. Parse and display results
            logger.info("\nLine Coverage Results:")
            logger.info("=" * 60)

            tree = ET.parse(os.path.join(self.config.project_path, 'coverage.xml'))
            root = tree.getroot()

            # Find coverage data for Test class
            test_class = root.find('.//class[@name="Test"]')
            if test_class is not None:
                counter = test_class.find('./counter[@type="LINE"]')
                if counter is not None:
                    missed = int(counter.get('missed', 0))
                    covered = int(counter.get('covered', 0))
                    total = missed + covered
                    coverage = (covered / total) * 100 if total > 0 else 0

                    logger.info(f"Coverage Summary for Test.java:")
                    logger.info(f"Line Coverage: {coverage:.2f}%")
                    logger.info(f"Total Lines: {total}")
                    logger.info(f"Covered Lines: {covered}")
                    logger.info(f"Missed Lines: {missed}")

                    logger.info(f"\nDetailed report available at: {report_dir}/index.html")
                    return round(coverage, 2)
                else:
                    logger.info("No line coverage data found")
                    return -1
            else:
                logger.info("Test class not found in coverage data")
                return -1

        except subprocess.CalledProcessError as e:
            logger.info(f"Error: {e}")
            return -1
        except Exception as e:
            logger.info(f"Unexpected error: {e}")
            return -1


class PythonDynamic(CodeDynamic):
    """Python-specific implementation of CodeDynamic for building and testing Python code."""

    def modify_judgment(self, result) -> bool:
        """Determine if Python build output requires modifications.

        :param result: Build output to analyze
        :type result: str
        :returns: True if modifications are needed, False otherwise
        :rtype: bool
        """
        pass

    def compile_project(self, path_dir: str, file_name: str) -> str:
        """Compile a Python project.

        :param path_dir: Directory containing Python source files
        :type path_dir: str
        :param file_name: Main Python file to compile
        :type file_name: str
        :returns: Compilation output or success message
        :rtype: str
        :raises Exception: If compilation fails
        """
        pass

    def is_build_target_exit(self, file_name) -> bool:
        """Check if Python build target exists.

        :param file_name: Name of the file to check
        :type file_name: str
        :returns: True if build target exists, False otherwise
        :rtype: bool
        """
        target = os.path.join(self.config.project_path, "built")
        return os.path.exists(target)

    def __init__(self, config: BuildConfig):
        """Initialize PythonDynamic instance.

        :param config: Configuration for the build process
        :type config: BuildConfig
        """
        super().__init__(config)
        self.config.language = "python"
        self.config.exec_extension = "py"
        self.config.test_file_name = "test"

    def build_target(self, target_name: str) -> str:
        """Build a Python target file.

        :param target_name: Name of the Python file to build
        :type target_name: str
        :returns: "success" if build succeeds, otherwise returns error output
        :rtype: str
        :raises Exception: If build fails
        """
        env = CodeDynamic.env
        python_path = env['PYTHON']
        cmd = [python_path, target_name]
        output = self.run_cmd(cmd, exe_env=self.config.project_path)
        if "Traceback" in output:
            return output
        with open(os.path.join(self.config.project_path, "built"), 'w') as file:
            pass
        return "success"

    def execute(self, target_file: str = None) -> str:
        """Execute a Python script.

        :param target_file: Name of the Python file to execute, defaults to test file
        :type target_file: str
        :returns: Standard output from script execution
        :rtype: str
        :raises FileNotFoundError: If script cannot be found
        :raises subprocess.SubprocessError: If execution fails
        """
        if not target_file:
            target_file = f"{self.config.test_file_name}.py"
        env = CodeDynamic.env
        python_path = env['PYTHON']
        cmd = [python_path, target_file]
        return self.run_cmd(cmd, exe_env=self.config.project_path)

    def run_coverage(self) -> float:
        """Run Python coverage analysis on Python test file.

        Uses the coverage.py package to measure code coverage of Python tests.
        Executes the test file and generates a coverage report.

        :returns: Coverage percentage as float, or -1 if analysis fails
        :rtype: float
        """
        try:
            # Run tests with coverage
            logger.info("Running tests with coverage analysis...")
            cmd = [self.env['PYTHON'], "-m", "coverage", "run", f"{self.config.test_file_name}.py"]
            output = self.run_cmd(cmd, exe_env=self.config.project_path)
            if "Traceback" in output:
                logger.error(f"Test execution failed: {output}")
                return -1

            # Generate coverage report
            logger.info("Generating coverage report...")
            cmd = [self.env['PYTHON'], "-m", "coverage", "report"]
            report = self.run_cmd(cmd, exe_env=self.config.project_path)
            
            # Parse coverage percentage from report
            try:
                # Extract last line containing total coverage
                total_line = report.strip().split('\n')[-1]
                # Parse coverage percentage (typically in format "TOTAL xxx xx%")
                coverage = float(total_line.split()[-1].replace('%', ''))
                logger.info(f"Coverage: {coverage}%")
                return coverage
            except (IndexError, ValueError) as e:
                logger.error(f"Failed to parse coverage report: {e}")
                return -1

        except Exception as e:
            logger.error(f"Coverage analysis failed: {e}")
            return -1
