import re
import os
from loguru import logger
from typing import List, Callable, Any
from langchain.tools import tool
import pexpect
from pydantic import BaseModel, Field
from unidiff import PatchSet
from .language_tools import create_java_tools, create_python_tools
from LLM.llmodel import LLModel
from LLM.llmodel import LLMConfig, LLModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import BaseTool


def run_cmd(cmd: list[str], exe_env: str) -> str:
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
        #logger.debug(f'Executing command: {cmd} in {exe_env}')
        # Check if the execution environment directory exists
        if not os.path.isdir(exe_env):
            error_msg = f"Error: Execution environment directory does not exist: {exe_env}"
            #logger.error(error_msg)
            return error_msg
        # Spawn the command. Keeping cmd as a list avoids potential issues with string formatting and arguments.
        child = pexpect.spawn(cmd[0], args=cmd[1:], cwd=exe_env, env=os.environ, timeout=30, encoding='utf-8')
        # Wait for the command to finish
        child.expect(pexpect.EOF)
        out_text = child.before
        #logger.debug(out_text)

        # Remove ANSI escape sequences from output, ensuring out_text is a string
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        clean_output = ansi_escape.sub('', out_text or '')

        # Split the string into lines
        lines = clean_output.splitlines()

        # Filter out lines that start with "Building"
        filtered_lines = [line for line in lines if not any(line.lstrip().startswith(prefix) for prefix in ("Building", "Adding", "Compiling"))]

        # Recombine the remaining lines into a single string
        return '\n'.join(filtered_lines)
    except Exception as e:
        return f"Running error: {e}"

def create_convert_tools(original_project_path: str, rust_project_path: str, language:str) -> List[BaseTool]:
    """
    Factory function to create common project tools, including file management rooted at project_path.
    Custom tools will have project_path and rust_project_path bound via closure.
    File management tools will operate relative to project_path.

    Args:
        project_path: The root path for the project, used by custom tools and file management.
        rust_project_path: The root path for the Rust project.

    Returns:
        A list of configured common and file management tool functions.
    """

    _original_project_path = original_project_path

    _rust_project_path = rust_project_path

    @tool
    def write_file_with_diff(diff: str, path: str) -> str:
        """
        Description: Apply a unified diff to a file at the specified path relative to the project_path.
        (project_path is bound from the factory function).
        This tool is useful when you need to make specific modifications to a file based on a set of changes
        provided in unified diff format (diff -U3). If you are creating a new file, prioritize using `write_file`.
        If it is to modify the file, use 'write_file_with_diff' first. Use `write_file` as a fallback if applying the diff fails consecutively.

        Parameters:
        - path: (required) The path of the file to apply the diff to (relative to project_path).
        - diff: (required) The diff content in unified format to apply to the file.

        Example: (Same as original docstring)
            ```
            --- src/utils/helper.ts
            +++ src/utils/helper.ts
            @@ -1,9 +1,10 @@
            import { Logger } from '../logger';

            function calculateTotal(items: number[]): number {
            -  return items.reduce((sum, item) => {
            -    return sum + item;
            +  const total = items.reduce((sum, item) => {
            +    return sum + item * 1.1;  // Add 10% markup
            }, 0);
            +  return Math.round(total * 100) / 100;  // Round to 2 decimal places
            }

            export { calculateTotal };
            ```
        Best Practices: (Same as original docstring)
            1. Replace entire code blocks...
            2. Moving code requires two hunks...
            3. One hunk per logical change...
            4. Verify line numbers match...
            5. Include a comment explaining the change...
        """
        full_path = os.path.join(_original_project_path, path)
        if not os.path.exists(full_path):
            return f"File {path} not found relative to project path."
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                original_lines = f.readlines()
        except Exception as e:
            return f"Error reading file {path}: {e}"

        new_lines = original_lines[:]
        try:
            patch = PatchSet(diff)
        except Exception as e:
            return f"Error parsing diff: {e}"

        # Apply patch hunks for the target file
        for patched_file in patch:
            # patched_file.target_file may have a "b/" prefix
            target = patched_file.target_file
            if target.startswith("b/"):
                target = target[2:]
            if target != path:
                continue
            for hunk in patched_file:
                # hunk.source_start is 1-indexed; determine insertion index in file list
                start_index = hunk.source_start - 1
                # Build new block by including context and added lines, excluding removed ones.
                new_hunk_lines = []
                for line in hunk:
                    if line.is_context or line.is_added:
                        new_hunk_lines.append(line.value)
                # Replace the block in new_lines with the new lines from the hunk
                new_lines[start_index:start_index + hunk.source_length] = new_hunk_lines

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return f"Diff applied successfully to {path}."
        except Exception as e:
            return f"Error writing file {path}: {e}"

    @tool
    def cargo_check() -> str:
        """
        Check the Rust project for errors or warnings.
        Runs cargo check to analyze the project for compilation errors and warnings without producing an executable.

        Returns:
            String containing the check results. Returns "Check pass. The project is executable."
            if successful, otherwise returns the error output.
        """
        cmd = ["cargo", "check"]
        output = run_cmd(cmd, exe_env=_rust_project_path)

        # Improved check logic for errors and warnings
        error_pattern = re.compile(r'error(\[|:)', re.IGNORECASE)
        warning_pattern = re.compile(r'warning:', re.IGNORECASE)
        finished_pattern = re.compile(r'Finished dev \[(\w+)\] target', re.IGNORECASE)  # matches like: Finished dev [unoptimized + debuginfo] target(s) in 0.89s

        if finished_pattern.search(output):
            if error_pattern.search(output):
                #logger.debug(f"Cargo check failed with errors:\n{output}")
                return output
            if warning_pattern.search(output):
                #logger.debug(f"Cargo check completed with warnings:\n{output}")
                return output
            #logger.debug("Cargo check passed without errors or warnings.")
            return "Check pass. The rust project is executable."
        else:
            #logger.debug(f"Cargo check did not finish cleanly:\n{output}")
            return output

    @tool
    def cargo_run() -> str:
        """
        Run the Rust project using 'cargo run --lib'.
        Executes the main function in lib.rs and returns the output or error message.

        Returns:
            String containing the run results or error output.
        """
        cmd = ["cargo", "run"]
        output = run_cmd(cmd, exe_env=_rust_project_path)
        return output
    
    @tool
    def read_original_file(path: str) -> str:
        """
        Reads a file from the original project path.

        Parameters:
        - path: (required) The path of the file to read, relative to the original project path.
        """
        full_path = os.path.join(_original_project_path, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file {path} from original project: {e}"

    @tool
    def write_original_file(path: str, content: str) -> str:
        """
        Writes content to a file in the original project path.

        Parameters:
        - path: (required) The path of the file to write to, relative to the original project path.
        - content: (required) The content to write to the file.
        """
        full_path = os.path.join(_original_project_path, path)
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path} in original project."
        except Exception as e:
            return f"Error writing file {path} to original project: {e}"

    @tool
    def list_original_directory(path: str = ".") -> str:
        """
        Lists files and directories in the original project path.

        Parameters:
        - path: (optional) The path of the directory to list, relative to the original project path. Defaults to the root.
        """
        full_path = os.path.join(_original_project_path, path)
        try:
            contents = os.listdir(full_path)
            return "\n".join(contents)
        except Exception as e:
            return f"Error listing directory {path} in original project: {e}"

    @tool
    def read_rust_file(path: str) -> str:
        """
        Reads a file from the Rust project path.

        Parameters:
        - path: (required) The path of the file to read, relative to the Rust project path.
        """
        full_path = os.path.join(_rust_project_path, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file {path} from Rust project: {e}"

    @tool
    def write_rust_file(path: str, content: str) -> str:
        """
        Writes content to a file in the Rust project path.

        Parameters:
        - path: (required) The path of the file to write to, relative to the Rust project path.
        - content: (required) The content to write to the file.
        """
        full_path = os.path.join(_rust_project_path, path)
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path} in Rust project."
        except Exception as e:
            return f"Error writing file {path} to Rust project: {e}"

    @tool
    def list_rust_directory(path: str = ".") -> str:
        """
        Lists files and directories in the Rust project path.

        Parameters:
        - path: (optional) The path of the directory to list, relative to the Rust project path. Defaults to the root.
        """
        full_path = os.path.join(_rust_project_path, path)
        try:
            contents = os.listdir(full_path)
            return "\n".join(contents)
        except Exception as e:
            return f"Error listing directory {path} in Rust project: {e}"


    tools = [
        cargo_run,
        cargo_check,
        write_file_with_diff,
        read_original_file,
        write_original_file,
        list_original_directory,
        read_rust_file,
        write_rust_file,
        list_rust_directory,
    ]

    if language == "java":
        tools.extend(create_java_tools(original_project_path, rust_project_path))
    elif language == "python":
        tools.extend(create_python_tools(original_project_path, rust_project_path))


    #logger.info(f"Created {len(tools)} common tools.")
    return tools

    
