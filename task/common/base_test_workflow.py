import os
from abc import ABC, abstractmethod

from loguru import logger

from LLM.llmodel import LLMConfig, LLModel
from LLM.states.task_states import TestGenTaskState
from LLM.tasks_tool_creater import create_test_gen_tools
from utils.chunk_utils import extract_token_usage, process_chunk


class BaseTestWorkflow(ABC):
    """
    Abstract base class for a test generation workflow.
    """

    def __init__(
        self, project_path: str, language: str, llm_config: LLMConfig, code_hash: str
    ):
        self.project_path = project_path
        self.language = language
        self.llm_config = llm_config
        self.code_hash = code_hash
        self.hash_subdir = os.path.join(project_path, "project_code_files", code_hash)
        self.task_state = TestGenTaskState()

    def run(self) -> None:
        """
        Executes the entire test generation workflow.
        """
        self._setup_project_structure()
        self._run_llm_flow()

    @abstractmethod
    def _setup_project_structure(self) -> None:
        """
        Sets up the language-specific project structure, including build files and test directories.
        """
        pass

    def _get_system_prompt(self) -> str:
        """
        Returns a language-specific system prompt for the LLM agent.
        """
        return (
            f"You are an autonomous {self.language.capitalize()} build-and-test engineer. "
            "You can run tools to build, test, and modify the codebase."
            "Follow the user's constraints strictly and do not attempt to ask the user questions.\n"
            "{agent_scratchpad}"
        )

    @abstractmethod
    def _get_initial_input(self) -> dict:
        """
        Returns the language-specific initial input for the LLM agent.
        """
        pass

    def _run_llm_flow(self) -> None:
        """
        Initializes and runs the LLM agent to generate tests.
        """
        created_tools = create_test_gen_tools(
            project_root_path=self.hash_subdir,
            language=self.language,
            task_state=self.task_state,
        )

        system_prompt = self._get_system_prompt()
        llm = LLModel.from_config(self.llm_config)
        agent_executor = llm.create_tool_react(created_tools, system_prompt)

        initial_input = self._get_initial_input()

        total_all_tokens = 0
        token_usage_steps = 0
        for chunk in agent_executor.stream(
            initial_input, config={"recursion_limit": 150}
        ):
            current_chunk_tokens = extract_token_usage(chunk)
            total_all_tokens += current_chunk_tokens
            if current_chunk_tokens > 0:
                logger.info(f"Token usage for this step: {current_chunk_tokens}")
                token_usage_steps += 1

            process_chunk(chunk)

            if self.task_state.is_success():
                logger.success(
                    "All tasks passed (tests and coverage). Stopping execution."
                )
                break
