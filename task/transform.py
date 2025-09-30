import os
from LLM.llmodel import LLMConfig, LLModel
from LLM.tasks_tool_creater import create_test_gen_tools, create_transform_tools
from LLM.tools.cargo_tool import cargo_new
from static.projectUtil import read_code_block, save_code_block, short_hash
from loguru import logger

from utils.chunk_utils import process_chunk
from static.get_env import return_env # To get the project root for template
from utils.maven_utils import get_java_pom_template
# from build.language_tools import create_java_tools # No longer needed

def run_transform_workflow(project_path: str, language: str, llm_config: LLMConfig) -> None:
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
    
        cargo_new(hash_subdir)
        # TODO, change original SensitiveFun.java to a remote call.
        # 1. find SensitiveFun.java
        # 2. replace its function's body to a remote call pointing to a rust server. The remote call forward its argument as gson to the rust.
        
        
        created_tools = create_transform_tools(
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
