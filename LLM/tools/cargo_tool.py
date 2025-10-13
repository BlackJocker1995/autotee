import re
from langchain_core.tools import BaseTool
import os

from loguru import logger
from utils import file_utils

from utils.cli_utils import run_cmd


finish_str = "[Terminate] Terminate the current task immediately!"

def cargo_new(project_path:str, lib:bool = True) -> str:
    """
    Create a new Rust project using Cargo within the project directory.
    The new project will be created in a subdirectory named according to `rust_name` (bound from factory function).
    Note that the content included in the initialized lib.rs is default, and you need to change it.
    (project_path and rust_name are bound from the factory function).
    """
    rust_path = os.path.join(project_path, 'rust') # Use bound variables
    if os.path.exists(rust_path):
        return f"Directory '{rust_path}' already exists. Skipping 'cargo new' step."

    cmd = ["cargo", "new", "rust"]
    if lib:
        cmd.append('--lib')

    output = run_cmd(cmd, exe_env=project_path)

    file_to_clear = 'lib.rs' if lib else 'main.rs'
    file_path = os.path.join(rust_path, 'src', file_to_clear)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write('')  # Clear the file content
        #logger.info(f"Cleared default content from {file_path}")
    except Exception as e:
        logger.error(f"Failed to clear content from {file_path}: {e}")
        # Optionally return an error message or let the original output pass through
        # return f"Cargo new succeeded, but failed to clear {file_to_clear}: {e}"
    return output

class CargoCheckTool(BaseTool):
    """
    Tool that checks the Rust project for errors.
    """
    name: str = "cargo_check"
    description: str = '''
    Check the Rust project for errors.
    Runs cargo check to analyze the project for compilation errors and warnings without producing an executable.

    Returns:
        String containing the check results. Returns "Check pass. The project is executable."
        if successful, otherwise returns the error output.
    '''
    project_root_path: str

    def __init__(self, project_root_path: str):
        super().__init__(project_root_path = project_root_path)

    def _run(self) -> str:
        rust_project_path = os.path.join(f"{self.project_root_path}/rust")
        content = file_utils.read_file(f"{self.project_root_path}/rust/src/lib.rs")
        if not content:
            return "project is empty, please write the code into rust/src/lib.rs"
        raw_output = run_cmd(['cargo', 'check'], exe_env=rust_project_path)
        if not isinstance(raw_output, str):
            output = str(raw_output)
        else:
            output = raw_output

        error_pattern = re.compile(r'error(\[|:)', re.IGNORECASE)
        finished_pattern = re.compile(r'Finished\s+`dev`\s+profile', re.IGNORECASE)
        #print(output)
        if finished_pattern.search(output):
            if error_pattern.search(output):
                return output
            return "The rust project is executable."
        else:
            return output