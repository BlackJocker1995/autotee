import os
from LLM.llmodel import LLMConfig, LLModel
from LLM.tasks_tool_creater import create_test_gen_tools
from static.projectUtil import read_code_block, save_code_block, short_hash
from loguru import logger

from utils.chunk_utils import process_chunk
from static.get_env import return_env # To get the project root for template
from utils.maven_utils import get_java_pom_template
# from build.language_tools import create_java_tools # No longer needed

def run_create_test_workflow(project_path: str, language: str, llm_config: LLMConfig) -> None:
    """
    Orchestrates the workflow for generating test files for sensitive code blocks.
    This function is currently designed to only handle Java projects.

    This is an abstract solution outlining the steps:
    1. Read sensitive code blocks from previously processed project data.
    2. For each code block (identified by its hash), create a new Test.py file.
    3. (Abstract) Use an LLM in a React-like loop to generate test inputs and ensure the sub-project runs.
    """
    logger.info("Starting the create test workflow.")

    # Define the directory where individual code files were saved
    project_code_files_dir = os.path.join(project_path, "project_code_files")
    
    # Iterate through the project_code_files directory to find code blocks
    # Each subdirectory in project_code_files_dir represents a code block identified by its hash
    
    if not os.path.exists(project_code_files_dir):
        logger.warning(f"Project code files directory not found: {project_code_files_dir}. Exiting test creation workflow.")
        return

    code_block_hashes = [d for d in os.listdir(project_code_files_dir) if os.path.isdir(os.path.join(project_code_files_dir, d))]
    
    if not code_block_hashes:
        logger.info("No code blocks found in project_code_files. Exiting test creation workflow.")
        return

    logger.info(f"Found {len(code_block_hashes)} code blocks for test generation.")

    for i, code_hash in enumerate(code_block_hashes):
        hash_subdir = os.path.join(project_code_files_dir, code_hash)
        
        # Define Maven standard directory structure
        java_main_dir = os.path.join(hash_subdir, "src", "main", "java", "com", "example", "project")
        java_test_dir = os.path.join(hash_subdir, "src", "test", "java", "com", "example", "project")

        # Ensure Maven directories exist
        os.makedirs(java_main_dir, exist_ok=True)
        os.makedirs(java_test_dir, exist_ok=True)

        source_code_file = "SensitiveFun.java"
        original_code_file_path = os.path.join(java_main_dir, source_code_file)
        
        # For Java, create a Test.java file
        test_file_name = "SensitiveFunTest.java"
        test_file_path = os.path.join(java_test_dir, test_file_name)
        
        # Create an empty Test.java file in the correct Maven test directory
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("") # Create an empty file
        logger.info(f"Created empty test file: {test_file_path}")

        # Get pom.xml template content and replace artifactId
        pom_content = get_java_pom_template()
        pom_content = pom_content.replace("REPLACE_ME_ARTIFACT_ID", code_hash)

        pom_file_path = os.path.join(hash_subdir, "pom.xml")
        with open(pom_file_path, "w", encoding="utf-8") as f:
            f.write(pom_content)
        logger.info(f"Created pom.xml for Maven project at: {pom_file_path}")
     
        created_tools = create_test_gen_tools(
            project_root_path=hash_subdir,
            language=language,
        )

        # Create LLM agent with the tools
        system_prompt = (
            "You are an autonomous Java build-and-test engineer. "
            "You can run tools to build, test, and modify the codebase."
            "Follow the user's constraints strictly and do not attempt to ask the user questions.\n"
            "{agent_scratchpad}"
        )
        llm = LLModel.from_config(llm_config) # Instantiate LLModel
        agent_executor = llm.create_tool_react(created_tools, system_prompt)

        initial_input = {"messages": [("user",f"""
        Generate a diverse set of test inputs for  {language} project located at `{hash_subdir}`, aiming to maximize both line and branch coverage. 
        Enhance the unit test coverage (line and branch) for the specified code unit.
        Ensure generated tests are syntactically correct, invoke relevant methods with appropriate inputs, and include assertions to validate expected behavior.
        
        **Completion Criteria:** You have successfully completed this task only when both of the following conditions are met:
        1. The task concludes after three consecutive attempts show no improvement in line and branch coverage.
        2. Test.java is not empty.
        3. All unit tests execute successfully, reporting 'Failures: 0, Errors: 0, Skipped: 0'
        
        """
        )]}
        
         # Run
        for chunk in agent_executor.stream(initial_input, config={"recursion_limit": 150}):
            bool_result, last_stream_message = process_chunk(chunk)
            if bool_result:
                break


    logger.info("Finished abstract test creation workflow.")
