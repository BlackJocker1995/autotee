from pathlib import Path
import re
import os
from loguru import logger
from typing import Dict, List, Callable, Any
from langchain.tools import tool
import subprocess # Replace pexpect with subprocess
from langchain_core.tools import BaseTool # Import BaseTool

def create_java_tools(java_project_path: str, rust_project_path: str) -> List[BaseTool]: # Correct return type hint
    """
    Factory function to create Java-specific project tools.
    These tools will have project_path bound via closure.

    Args:
        project_path: The root path of the Java project.

    Returns:
        A list of configured Java tool functions.
    """
    _java_project_path = java_project_path
    _rust_project_path = rust_project_path
    logger.info(f"Creating Java tools with project_path: {_java_project_path}")

    @tool
    def verify_output_consistency() -> str:
        """
        Verify output consistency between Java and Rust compiled code.
        """
        import subprocess
        import os

        java_project_path = _java_project_path
        rust_project_path = _rust_project_path

        # Compile Java code
        javac_cmd = ["javac", "Test.java"]
        try:
            javac_proc = subprocess.run(javac_cmd, cwd=java_project_path, capture_output=True, text=True)
            if javac_proc.returncode != 0:
                return f"Java compilation failed: {javac_proc.stderr.strip()}"
        except Exception as e:
            return f"Java compilation exception: {str(e)}"

        # Execute Java code
        java_cmd = ["java", "Test"]
        try:
            java_proc = subprocess.run(java_cmd, cwd=java_project_path, capture_output=True, text=True)
            if java_proc.returncode != 0:
                return f"Java execution failed: {java_proc.stderr.strip()}"
            java_output = java_proc.stdout.strip()
        except Exception as e:
            return f"Java execution exception: {str(e)}"

        # Compile Rust code
        cargo_cmd = ["cargo", "build", "--bin", "tee"]
        try:
            cargo_proc = subprocess.run(cargo_cmd, cwd=rust_project_path, capture_output=True, text=True)
            if cargo_proc.returncode != 0:
                return f"Rust build failed: {cargo_proc.stderr.strip()}"
        except Exception as e:
            return f"Rust build exception: {str(e)}"

        # Execute Rust code
        rust_executable = os.path.join(rust_project_path, "target", "debug", "tee")
        try:
            rust_proc = subprocess.run([rust_executable], capture_output=True, text=True)
            if rust_proc.returncode != 0:
                return f"Rust execution failed: {rust_proc.stderr.strip()}"
            rust_output = rust_proc.stdout.strip()
        except Exception as e:
            return f"Rust execution exception: {str(e)}"

        # Compare outputs
        if java_output == rust_output:
            return "The output is consistent."
        else:
            return f"Inconsistent output: Java output is '{java_output}', Rust output is '{rust_output}'."



    # Return the list of Java-specific tool functions
    return [
        verify_output_consistency,
    ]
def create_python_tools(python_project_path: str, rust_project_path: str) -> List[BaseTool]:
    """
    Factory function to create Python-specific project tools.
    These tools will have project_path bound via closure.

    Args:
        python_project_path: The root path of the Python project.
        rust_project_path: The root path of the Rust project.

    Returns:
        A list of configured Python tool functions.
    """
    _python_project_path = python_project_path
    _rust_project_path = rust_project_path
    logger.info(f"Creating Python tools with project_path: {_python_project_path}")

    @tool
    def verify_output_consistency() -> str:
        """
        Verify output consistency between Python and Rust compiled code.
        """
        import subprocess
        import os

        python_project_path = _python_project_path
        rust_project_path = _rust_project_path

        # Check Python syntax by compiling
        py_file = "test.py"
        py_compile_cmd = ["python3", "-m", "py_compile", py_file]
        try:
            py_compile_proc = subprocess.run(py_compile_cmd, cwd=python_project_path, capture_output=True, text=True)
            if py_compile_proc.returncode != 0:
                return f"Python syntax check failed: {py_compile_proc.stderr.strip()}"
        except Exception as e:
            return f"Python syntax check exception: {str(e)}"

        # Execute Python code
        python_cmd = ["python3", py_file]
        try:
            python_proc = subprocess.run(python_cmd, cwd=python_project_path, capture_output=True, text=True)
            if python_proc.returncode != 0:
                return f"Python execution failed: {python_proc.stderr.strip()}"
            python_output = python_proc.stdout.strip()
        except Exception as e:
            return f"Python execution exception: {str(e)}"

        # Compile Rust code
        cargo_cmd = ["cargo", "build", "--bin", "tee"]
        try:
            cargo_proc = subprocess.run(cargo_cmd, cwd=rust_project_path, capture_output=True, text=True)
            if cargo_proc.returncode != 0:
                return f"Rust build failed: {cargo_proc.stderr.strip()}"
        except Exception as e:
            return f"Rust build exception: {str(e)}"

        # Execute Rust code
        rust_executable = os.path.join(rust_project_path, "target", "debug", "tee")
        try:
            rust_proc = subprocess.run([rust_executable], capture_output=True, text=True)
            if rust_proc.returncode != 0:
                return f"Rust execution failed: {rust_proc.stderr.strip()}"
            rust_output = rust_proc.stdout.strip()
        except Exception as e:
            return f"Rust execution exception: {str(e)}"

        # Compare outputs
        if python_output == rust_output:
            return "The output is consistent."
        else:
            return f"Inconsistent output: Python output is '{python_output}', Rust output is '{rust_output}'."

    return [
        verify_output_consistency,
    ]