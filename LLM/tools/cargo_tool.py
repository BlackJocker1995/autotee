import re
from langchain_core.tools import BaseTool
import os
from utils import file_utils

from utils.cli_utils import run_cmd


finish_str = "[Terminate] Terminate the current task immediately!"



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
            return f"{finish_str}. The project is executable."
        else:
            return output