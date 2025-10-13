from ctypes import util
from pathlib import Path
import re
import os
import shutil # Import shutil for directory removal
from loguru import logger
from typing import Dict, List, Callable, Any, Optional, Union
from langchain.tools import tool
import subprocess # Replace pexpect with subprocess
from jinja2 import Environment, FileSystemLoader
from analyzers.jacoco.jacoco_analyzer import JacocoAnalyzer
from utils import file_utils
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import BaseTool



finish_str = "[Terminate] Unit test passed. Terminate the current task immediately!"


class MavenExecuteUnitTestTool(BaseTool):
    name: str = "execute_unit_test"
    description: str = '''
    Executes specified Java unit tests using Maven within the project path.
    Optional
    This tool runs the 'mvn clean test' command. 'Tests run: X, Failures: 0, Errors: 0, Skipped: 0' means unit test pass without error, where X is the number of tests run.
    It captures the command output, removes ANSI escape codes, and checks for lines containing '[ERROR]'.
    If errors are found, it returns the error lines; otherwise, it returns a success message.
    '''

    project_root_path:str
    is_end_point:bool

    def __init__(self, project_root_path: str, is_end_point: bool, **kwargs):
        super().__init__(project_root_path = project_root_path, is_end_point = is_end_point, **kwargs)

    def _extract_error_lines(self, output: str, project_path: str) -> str:
            """Extract meaningful error lines from Maven output, filtering out helper messages."""
            invalid_phrases = [
                "To see the full stack trace of the errors, re-run Maven with the -e switch.",
                "Re-run Maven using the -X switch to enable full debug logging.",
                "For more information about the errors and possible solutions, please read the following articles:",
                "[Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException"
            ]

            error_lines = []
            for line in output.splitlines():
                if "[ERROR]" in line:
                    if line.strip() == "[ERROR]" or any(phrase in line for phrase in invalid_phrases):
                        continue
                    cleaned_line = line.replace(f"{project_path}/", "")
                    error_lines.append(cleaned_line)

            return "\n".join(error_lines) if error_lines else ""

    def _extract_success_message(self, output: str) -> str:
        """Extract a success message from Maven output."""
        build_success_match = re.search(r'\\[INFO\\] BUILD SUCCESS', output)
        test_summary_match = re.search(r'Tests run:\\s*(\\d+),\\s*Failures:\\s*(\\d+),\\s*Errors:\\s*(\\d+),\\s*Skipped:\\s*(\\d+)', output)

        if build_success_match and test_summary_match:
            groups = test_summary_match.groups()
            return f"{finish_str} Summary: Tests run: {groups[0]}, Failures: {groups[1]}, Errors: {groups[2]}, Skipped: {groups[3]}"
        elif build_success_match:
            return finish_str
        else:
            simple_test_summary = re.search(r'Tests run:\\s*(\\d+)', output)
            if simple_test_summary:
                return f"{finish_str} Summary: Tests run: {simple_test_summary.group(1)}"
            return ""


    def _run(self) -> str:
        command = "" # Initialize for exception handling
        try:
            command = f'mvn clean test'
            logger.debug(f"Executing command: {command} in {self.project_root_path}")

            process = subprocess.run(command, cwd=self.project_root_path, capture_output=True, text=True, shell=True, timeout=300)
            output = process.stdout + "\n" + process.stderr # Combine stdout and stderr
            exit_status = process.returncode


            if output:
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                cleaned_output = ansi_escape.sub('', output)

                error_lines = self._extract_error_lines(cleaned_output, self.project_root_path)

                if error_lines:
                    return f"Unit test execution finished with errors:\n{error_lines}"
                elif exit_status != 0:
                    return f"Unit test execution failed (exit status {exit_status}). Check logs or full output for details."
                else:
                    success_message = self._extract_success_message(cleaned_output)
                    if success_message:
                        return success_message
                    else:
                        return f"{finish_str}. Unit test pass. " if self.is_end_point else "Unit test pass. "

            elif exit_status != 0:
                 err_output = process.stderr.strip()
                 return f"Unit test execution failed (exit status {exit_status}).{' Output: ' + err_output if err_output else ' No output.'}"
            else:
                return f"{finish_str}. (no significant output captured). " if self.is_end_point else "(no significant output captured)."

        except subprocess.TimeoutExpired:
             logger.error(f"Command '{command}' timed out after 300 seconds.")
             return f"Error: Command execution timed out."
        except Exception as e:
             logger.exception(f"An unexpected error occurred during Java unit test execution")
             return f"An unexpected error occurred during Java unit test execution: {e}"


class JacocoCoverageReport(BaseModel):
    line_coverage: float = Field(..., description="Overall line coverage percentage.")
    branch_coverage: float = Field(..., description="Overall branch coverage percentage.")
    uncovered_lines_by_file: Dict[str, List[int]] = Field(..., description="Dictionary where keys are file paths (relative to project root) and values are lists of uncovered line numbers.")
    uncovered_branches_by_file: Dict[str, List[int]] = Field(..., description="Dictionary where keys are file paths (relative to project root) and values are lists of lines with uncovered branches.")

class JacocCoverageTool(BaseTool):
    name: str = "java_coverage"
    description: str = '''
    A tool for calculating JaCoCo code coverage for Java projects.
    This tool executes the Maven command 'mvn clean test jacoco:report' to generate a JaCoCo report,
    then parses the generated XML report to extract line and branch coverage data.
    '''

    project_root_path:str

    def __init__(self, project_root_path: str, **kwargs):
        super().__init__(project_root_path = project_root_path, **kwargs)


    def _run(self) -> Union[JacocoCoverageReport, str]:
        """
        Executes JaCoCo coverage analysis.
        Runs the Maven command to generate a JaCoCo report, then parses the report to get coverage data.

        Returns:
            JacocoCoverageReport: A structured object containing overall line and branch coverage,
            and detailed uncovered lines and branches by file.
        """
        try:
            # Construct and execute the Maven command to generate the JaCoCo report
            command = f'mvn clean test jacoco:report'
            logger.debug(f"Executing command: {command} in {self.project_root_path}")
            try:
                # Run the Maven command. If it times out, a TimeoutExpired exception will be caught.
                subprocess.run(command, cwd=self.project_root_path, capture_output=True, text=True, shell=True, timeout=300)

                # Parse the JaCoCo report
                csv_report_path = os.path.join(self.project_root_path, 'target', 'site','jacoco','jacoco.csv')
                xml_report_path = os.path.join(self.project_root_path, 'target', 'site','jacoco','jacoco.xml')
                if not os.path.exists(csv_report_path):
                    return "JaCoCo CSV report not found. May be code is not correct or empty. Run execute_unit_test at first."
                if not os.path.exists(xml_report_path):
                    return "JaCoCo XML report not found. May be code is not correct or empty. Run execute_unit_test at first."

            except Exception as e:
                logger.error(f"Error during Maven command execution or report file check: {e}")
                return f"Error during Maven command execution or report file check: {e}"

            overall_coverage_data = JacocoAnalyzer.parse_jacoco_report(csv_report_path)
            uncovered_data = JacocoAnalyzer.parse_jacoco_report_content(xml_report_path)

            # Separate uncovered lines and branch uncovered lines
            uncovered_lines_by_file = {file_path: data['uncovered'] for file_path, data in uncovered_data.items()}
            uncovered_branches_by_file = {file_path: data['branch_uncovered'] for file_path, data in uncovered_data.items()}

            return JacocoCoverageReport(
                line_coverage=overall_coverage_data.get('line_coverage', 0.0),
                branch_coverage=overall_coverage_data.get('branch_coverage', 0.0),
                uncovered_lines_by_file=uncovered_lines_by_file,
                uncovered_branches_by_file=uncovered_branches_by_file
            )

        except subprocess.TimeoutExpired:
             logger.error(f"Command timed out after 300 seconds.")
             return "Error: Command execution timed out."
        except Exception as e:
             logger.exception(f"An unexpected error occurred during Java unit test execution")
             return f"An unexpected error occurred during Java unit test execution: {e}"


class LinkJava2Rust(BaseTool):
    model_config = ConfigDict(extra='allow') # Allow extra fields for Jinja2 environments
    name: str = "link_java2rust"
    description: str = '''
    A tool for linking Java functions to Rust implementations to check test input consistency.
    This tool reads Java and Rust templates and adapts them for different function signatures.
    '''
    
    project_root_path: str
    
    def __init__(self, project_root_path: str, **kwargs):
        super().__init__(project_root_path = project_root_path, **kwargs)
        self.java_template_dir = os.path.join(project_root_path, 'utils', 'java')
        self.rust_template_dir = os.path.join(project_root_path, 'utils', 'rust')
        self.java_env = Environment(loader=FileSystemLoader(self.java_template_dir))
        self.rust_env = Environment(loader=FileSystemLoader(self.rust_template_dir))
        self.rust_env.filters['java_to_rust_type'] = self._java_to_rust_type

    def _generate_java_code(self, function_name: str, arguments: dict, return_type: str) -> str:
        """Generate Java code by adapting the template using Jinja2."""
        try:
            template = self.java_env.get_template('java_link_template.java')
            
            signature_params = [f"{param_type} {param_name}" for param_name, param_type in arguments.items()]
            
            return_type_mapping = {
                'int': 'getAsInt',
                'String': 'getAsString',
                'boolean': 'getAsBoolean',
                'double': 'getAsDouble',
                'float': 'getAsFloat',
                'long': 'getAsLong'
            }
            getter_method = return_type_mapping.get(return_type, 'getAsString')

            return template.render(
                function_name=function_name,
                arguments=arguments,
                return_type=return_type,
                signature_params=', '.join(signature_params),
                getter_method=getter_method
            )
        except Exception as e:
            logger.error(f"Failed to generate Java code with Jinja2: {e}")
            return ""

    def _generate_rust_code(self, function_name: str, arguments: dict, return_type: str) -> str:
        """Generate Rust code by adapting the template using Jinja2."""
        try:
            template = self.rust_env.get_template('main.rs')
            
            return template.render(
                function_name=function_name,
                arguments=arguments,
                return_type=return_type,
                rust_return_type=self._java_to_rust_type(return_type) # Pass directly
            )
        except Exception as e:
            logger.error(f"Failed to generate Rust code with Jinja2: {e}")
            return ""

    def _run(self, function_name: str, arguments: dict, return_type: str) -> str:
        """
        Generate adapted Java and Rust code for function linking.
        
        Args:
            function_name: Name of the function to link
            arguments: Dictionary of argument names and their Java types
            return_type: Java return type of the function
            
        Returns:
            String containing generated Java and Rust code
        """
        try:
            # 1. Read java template and rust template
            java_code = self._generate_java_code(function_name, arguments, return_type)
            rust_code = self._generate_rust_code(function_name, arguments, return_type)
            
            if not java_code or not rust_code:
                return "Failed to generate linking code. Check if template files exist."
            
            # 3. Return generated template results
            result = f"""Generated Java-Rust Linking Code for function '{function_name}'

Function Signature: {return_type} {function_name}({', '.join([f'{param_type} {param_name}' for param_name, param_type in arguments.items()])})

=== JAVA CODE ===
{java_code}

=== RUST CODE ===
{rust_code}

=== MANUAL ADJUSTMENTS NEEDED ===
For Java code:
- Update parameter construction in the JSON request (lines 33-41)
  Current template handles: seed (int) and input (byte[])
  You need to adjust for your parameters: {', '.join([f'{param_name} ({param_type})' for param_name, param_type in arguments.items()])}

For Rust code:
- Update the Params struct (lines 13-16) to match your parameters
- Update parameter extraction (lines 51-52)
- Update function call (line 55)

Additional step:
- Implement the actual Rust function in lib.rs:
  pub fn {function_name}({', '.join([f'{param_name}: {self._java_to_rust_type(param_type)}' for param_name, param_type in arguments.items()])}) -> {self._java_to_rust_type(return_type)} {{
      // TODO: Implement the actual logic
      todo!()
  }}

=== TEMPLATE NOTES ===
- Java template provides working example for 'hash' function with (byte[], int) parameters
- Rust template provides working example for 'hash' function with (Vec<u8>, i32) parameters
- Adapt the marked sections in both templates according to your function signature"""
            
            return result
            
        except Exception as e:
            logger.exception(f"Error generating Java-Rust linking code: {e}")
            return f"Error generating Java-Rust linking code: {e}"

    def _java_to_rust_type(self, java_type: str) -> str:
        """Convert Java type to Rust type."""
        type_mapping = {
            'int': 'i32',
            'Integer': 'i32',
            'byte[]': 'Vec<u8>',
            'String': 'String',
            'boolean': 'bool',
            'Boolean': 'bool',
            'double': 'f64',
            'Double': 'f64',
            'float': 'f32',
            'Float': 'f32',
            'long': 'i64',
            'Long': 'i64'
        }
        return type_mapping.get(java_type, 'String')