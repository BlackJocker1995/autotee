import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import BaseTool
from langchain_community.agent_toolkits import FileManagementToolkit

from LLM.tools.cargo_tool import CargoCheckTool
from LLM.tools.file_tool import ApplyDiffTool, ListProjectStructureTool
from LLM.tools.language_tools import JacocCoverageTool, JavaCompileCheck, TemplateForTrans, MavenExecuteUnitTestTool

def create_transform_tools(project_root_path: str,  language:str) -> list[BaseTool]:
    """
    Factory function to create common project tools, including file management rooted at project_path.
    Custom tools will have project_path, rust_name, and test_number bound via closure.
    File management tools will operate relative to project_path.

    Args:
        project_path: The root path for the project, used by custom tools and file management.
        test_number: The expected number of passing tests for cargo_test.
        fileconfig: Optional dict specifying directory permissions, e.g. {".": "r", "rust": "rw"}

    Returns:
        A list of configured common and file management tool functions.
    """
    tools = [
        ListProjectStructureTool(project_root_path=project_root_path),
        ApplyDiffTool(project_root_path=project_root_path),
        MavenExecuteUnitTestTool(project_root_path=project_root_path, is_end_point=False),
        CargoCheckTool(project_root_path=project_root_path),
        TemplateForTrans(project_root_path=project_root_path)
    ]
    # Only modify the rust code
    rust_project_path = os.path.join(project_root_path)
    toolkit = FileManagementToolkit(
        root_dir=str(rust_project_path),
        selected_tools=["list_directory", "read_file", "write_file"]
    )
    root_tools = toolkit.get_tools()
    tools.extend(root_tools)
    return tools

def create_template_tools(project_root_path: str,  language:str) -> list[BaseTool]:
    """
    """
    tools = [
        TemplateForTrans(project_root_path=project_root_path),
    ]
    return tools # type: ignore


def create_test_gen_tools(project_root_path: str,  language:str) -> list[BaseTool]:
    """
    Factory function to create common project tools, including file management rooted at project_path.
    Custom tools will have project_path, rust_name, and test_number bound via closure.
    File management tools will operate relative to project_path.

    Args:
        project_path: The root path for the project, used by custom tools and file management.
        test_number: The expected number of passing tests for cargo_test.
        fileconfig: Optional dict specifying directory permissions, e.g. {".": "r", "rust": "rw"}

    Returns:
        A list of configured common and file management tool functions.
    """
    tools = [
        ListProjectStructureTool(project_root_path=project_root_path),
        ApplyDiffTool(project_root_path=project_root_path),
    ]

    toolkit = FileManagementToolkit(
        root_dir=str(project_root_path),
        selected_tools=["list_directory", "read_file", "write_file"]  # 选择需要的工具
    )
    root_tools = toolkit.get_tools()
    tools.extend(root_tools)
    
    if language == "java":
        tools.extend([
        JacocCoverageTool(project_root_path=project_root_path),
        JavaCompileCheck(project_root_path=project_root_path),
        MavenExecuteUnitTestTool(project_root_path=project_root_path, is_end_point=False)
        ])
    elif language == "python":
        pass
        
    return tools


