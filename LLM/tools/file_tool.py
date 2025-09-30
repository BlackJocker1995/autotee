import pathlib
import shutil
from typing import Callable, Optional
from langchain.tools import tool
from unidiff import PatchSet
import os
from pydantic import BaseModel, Field
from langchain_core.tools.base import ArgsSchema
from langchain_core.tools import BaseTool
from utils import file_utils


class ListProjectStructureTool(BaseTool):
    """
    Tool that recursively lists the directory structure of the project as a tree-formatted string.
    """
    name: str = "list_project_structure"
    description: str = '''
    Recursively lists the directory structure of the project and returns it as a tree-formatted string.

    This tool traverses the entire project directory recursively and generates a
    hierarchical tree-like representation of all directories and files. The output
    displays the project structure in a readable format that shows the nesting
    relationships between different folders and files.
    '''
    project_root_path: str

    def __init__(self, project_root_path: str, **kwargs):
        super().__init__(project_root_path=project_root_path, **kwargs)

    def _run(self) -> str:
        return file_utils.build_recursive_directory_tree_string(self.project_root_path)


class ReadFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to read (relative to project root).")

class ReadFileTool(BaseTool):
    name: str = "read_file"
    args_schema: Optional[ArgsSchema] = ReadFileInput
    description: str = '''
    Reads the content of a file at the specified path relative to the project root.

    Args:
        path (str): The path of the file to read (relative to project root).

    Returns:
        str: The content of the file or an error message.

    Example:
        >>> read_file("src/main.py")
        "print('Hello, World!')"
    '''
    project_root_path: str

    def __init__(self, project_root_path: str, **kwargs):
        super().__init__(project_root_path = project_root_path, **kwargs)
        
    def _run(self, path: str) -> str:
        full_path = os.path.join(self.project_root_path, path)
        if not os.path.exists(full_path):
            return f"File {path} not found relative to project path."
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file {path}: {e}"

class WriteFileInput(BaseModel):
    path: str = Field(..., description="The relative path to the file from the root directory.")
    content: str = Field(..., description="The content to write to the file.")

class WriteFileWithDiffInput(BaseModel):
     diff: str = Field(..., description="The diff content in unified format to apply to the file.")
     path: str = Field(..., description="The path of the file to apply the diff to (relative to project root).")

class WriteFileToolPermissions(BaseTool):
    """
    Tool that writes content to a file at the specified path.
    """
    name: str = "write_file"
    args_schema: Optional[ArgsSchema] = WriteFileInput
    description: str = '''
    Writes content to a file at the specified path relative to the project root.
    This tool is useful for creating new files or overwriting existing ones.

    Args:
        path (str): The relative path to the file from the root directory.
        content (str): The content to write.

    Returns:
        str: Success message or error message.

    Example:
        >>> write_file("src/new_file.py", "Hello")
        "File src/new_file.py written successfully."
    '''
    project_root_path: str
    can_write_checker: Optional[Callable[[pathlib.Path], bool]] = None

    def __init__(self, project_root_path: str, can_write_checker: Optional[Callable[[pathlib.Path], bool]] = None, **kwargs):
        super().__init__(project_root_path=project_root_path, can_write_checker=can_write_checker, **kwargs)

    def _run(self, path: str, content: str) -> str:
        relative_path = pathlib.Path(path)
        full_path = (pathlib.Path(self.project_root_path) / relative_path).resolve()
        
        if not str(full_path).startswith(str(pathlib.Path(self.project_root_path).resolve())):
            return "Access outside root directory is not allowed."
        
        if self.can_write_checker and not self.can_write_checker(relative_path):
            return f"Write permission denied for {path}."
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File {path} written successfully."
        except Exception as e:
            return f"Error writing file {path}: {e}"


class ApplyDiffInput(BaseModel):
    diff: str = Field(description="Simplified unified diff content")
    path: str = Field(description="Path to the file relative to project root")


class ApplyDiffTool(BaseTool):
    """
    Tool that applies a simplified unified diff to a file.
    """
    name: str = "apply_diff"
    args_schema: Optional[ArgsSchema] = ApplyDiffInput
    description: str = '''
    Apply a simplified unified diff to a file at the specified path.
    The diff should only contain the @@ hunk headers and changes, without file headers.

    Hunk Header Explanation:
      Each hunk header has the format @@ -a,b +c,d @@, where:
        - a: Starting line number in the original file (1-based)
        - b: Number of lines in the original file affected by the hunk
        - c: Starting line number in the new file (1-based)
        - d: Number of lines in the new file affected by the hunk

      The lines following the hunk header must match the counts specified:
        - The hunk must include exactly b lines from the original file (context or removed lines, marked with ' ' or '-')
        - The hunk must include exactly d lines for the new file (context or added lines, marked with ' ' or '+')
        - If the counts do not match, the diff will fail to parse.

    Example:
        @@ -2,3 +2,4 @@
            function calculateTotal(items) {
        -      return items.reduce((sum, item) => sum + item, 0);
        +      const total = items.reduce((sum, item) => sum + item * 1.1, 0);
        +      return Math.round(total * 100) / 100;
            }

        In this example, the hunk header means: start at line 2, 3 lines from the original file, and 4 lines in the new file. The lines after the header must match these counts.

    Another example with multiple hunks:
        @@ -1,1 +1,2 @@
        +   // Added header comment
            import React from 'react';
        @@ -10,2 +11,3 @@
              return (
        -        Hello World
        +        Hello World
        +        New paragraph
              );

    '''



    project_root_path: str
    can_write_checker: Optional[Callable[[pathlib.Path], bool]] = None

    def __init__(self, project_root_path: str, can_write_checker: Optional[Callable[[pathlib.Path], bool]] = None):
        super().__init__(project_root_path=project_root_path, can_write_checker=can_write_checker)

    def _run(self, diff: str, path: str) -> str:
        relative_path = pathlib.Path(path)
        full_path = (pathlib.Path(self.project_root_path) / relative_path).resolve()

        # Security check
        if not str(full_path).startswith(str(pathlib.Path(self.project_root_path).resolve())):
            return "Access outside root directory is not allowed."
        
        if self.can_write_checker and not self.can_write_checker(relative_path):
            return f"Write permission denied for {path}."
        
        if not os.path.exists(full_path):
            return f"File {path} not found relative to root directory."
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                original_lines = f.readlines()
        except Exception as e:
            return f"Error reading file {path}: {e}"

        # Wrap the simplified diff in proper unified diff format
        wrapped_diff = self._wrap_diff(diff, path)
        
        try:
            patch = PatchSet(wrapped_diff.splitlines(keepends=True))
        except Exception as e:
            return f"Error parsing diff: {e}"

        # Apply the patch
        new_lines = original_lines[:]
        
        try:
            for patched_file in patch:
                for hunk in patched_file:
                    # Convert 1-indexed to 0-indexed
                    start_index = hunk.source_start - 1
                    end_index = start_index + hunk.source_length
                    
                    # Build new content for this hunk
                    new_hunk_lines = []
                    for line in hunk:
                        if line.is_context or line.is_added:
                            new_hunk_lines.append(line.value)
                    
                    # Replace the block
                    new_lines[start_index:end_index] = new_hunk_lines

            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return f"Diff applied successfully to {path}."
        except Exception as e:
            return f"Error applying diff to {path}: {e}"

    def _wrap_diff(self, diff_content: str, file_path: str) -> str:
        """
        Wrap simplified diff content in proper unified diff format
        """
        # Add the file header that unidiff expects
        wrapped = f"--- {file_path}\n+++ {file_path}\n{diff_content}"
        return wrapped

class ListProjectContentTool(BaseTool):
    """
    Tool that recursively lists the directory structure of the target project path along with file contents.
    """
    name: str = "list_project_content"
    description: str = '''
    Recursively list the directory structure of the target project path along with file contents.

    For each directory, it shows the relative path from the project root. For each file, it displays the file name
    and the content indented. If a file cannot be read, an error message is displayed.

    Note that this tool will greatly increase the processing burden. Use this tool judiciously.
    '''

    project_root_path: str
    
    def __init__(self, project_root_path: str, **kwargs):
        super().__init__(project_root_path=project_root_path, **kwargs)

    def _run(self) -> str:
        output = []
        src_prefix = os.path.join('src', '')
        for root, _, files in os.walk(self.project_root_path):
            rel_root = os.path.relpath(root, self.project_root_path)
            if not (rel_root == 'src' or rel_root.startswith(src_prefix)):
                continue

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_root_path)
                # Corrected logic: only process .java or .cs files
                if not (rel_path.endswith(".java") or rel_path.endswith(".cs")):
                    continue

                if rel_path.startswith(src_prefix):
                    output.append(f"  File: {rel_path}")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        indented_content = "\n".join("    " + line for line in content.splitlines())
                        output.append(indented_content)
                    except Exception as e:
                        output.append(f"    Error reading file {rel_path}: {e}")
        return "\n".join(output)

def create_permission_checker(fileconfig: dict[str, str]) -> Callable:
    """
    Creates a permission checker to verify write permissions for specific paths.

    Args:
        root_dir (str): The root directory path
        fileconfig (dict[str, str]): File configuration dictionary, where keys are relative paths and values are permission strings ("r", "w", "rw")

    Returns:
        callable: Permission checking function that accepts a path and returns whether it has write permission

    Example:
        >>> checker = create_permission_checker({"src/": "rw", "docs/": "r"})
        >>> checker(pathlib.Path("/home/user/src/main.py"))  # Returns True
    """
    perm_map = {pathlib.Path(p): perm.lower() for p, perm in fileconfig.items()}

    def can_write(relative_path: pathlib.Path) -> bool:
        """
        Check if the specified path has write permission, distinguishing between directory and file permissions, prioritizing the most specific (longest path) permission configuration
        """
        best_match_len = -1
        best_perm = None
        for config_path, perm in perm_map.items():
            is_dir = str(config_path).endswith(os.sep)
            
            match_len = 0
            if is_dir:
                if config_path in relative_path.parents or config_path == relative_path:
                    match_len = len(str(config_path))
            elif config_path == relative_path:
                match_len = len(str(config_path))

            if match_len > best_match_len:
                best_match_len = match_len
                best_perm = perm
        
        return best_perm == "rw"

    return can_write


