from contextvars import ContextVar
from functools import wraps
from math import e
import os
import re
import sys
from loguru import logger
import pexpect
import os
from langchain_core.messages import AIMessage, ToolMessage
from loguru import logger



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
        # Extended regex to remove both CSI and OSC sequences (including hyperlinks)
        ansi_escape = re.compile(
            r'\x1B\[[0-?]*[ -/]*[@-~]'  # CSI sequences
            r'|'
            r'\x1B\][^\x1B\x07]*(?:\x07|\x1B\\)'  # OSC sequences (e.g. hyperlinks)
        )
        clean_output = ansi_escape.sub('', out_text or '')

        # Split the string into lines
        lines = clean_output.splitlines()

        # Filter out lines that start with "Building"
        filtered_lines = [line for line in lines if not any(line.lstrip().startswith(prefix) for prefix in ("Building", "Adding", "Compiling"))]

        # Recombine the remaining lines into a single string
        return '\n'.join(filtered_lines)
    except Exception as e:
        return f"Running error: {e}"


