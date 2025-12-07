import os
from abc import ABC, abstractmethod

from loguru import logger

from LLM.llmodel import LLMConfig, LLModel
from LLM.states.task_states import ConvertTaskState
from LLM.tasks_tool_creater import create_transform_tools
from utils.chunk_utils import process_chunk, extract_token_usage


class BaseTransformWorkflow(ABC):
    def __init__(
        self,
        project_path: str,
        code_hash: str,
        llm_config: LLMConfig,
        source_language: str,
        target_language: str,
    ):
        self.project_path = project_path
        self.code_hash = code_hash
        self.llm_config = llm_config
        self.source_language = source_language
        self.target_language = target_language
        self.hash_subdir = os.path.join(project_path, "project_code_files", code_hash)
        self.task_state = ConvertTaskState()

    def run(self) -> None:
        self._setup_project()
        source_code = self._get_source_code()
        if source_code is None:
            logger.error(f"Could not read source code for {self.code_hash}. Aborting transform.")
            return

        created_tools = create_transform_tools(
            project_root_path=self.hash_subdir,
            language=self.source_language,
            task_state=self.task_state,
        )

        system_prompt = self._get_system_prompt()
        llm = LLModel.from_config(self.llm_config)
        agent_executor = llm.create_tool_react(created_tools, system_prompt)

        initial_input = self._get_initial_input(source_code)

        total_all_tokens = 0
        token_usage_steps = 0
        try:
            for chunk in agent_executor.stream(initial_input, config={"recursion_limit": 150}):
                current_chunk_tokens = extract_token_usage(chunk)
                total_all_tokens += current_chunk_tokens
                if current_chunk_tokens > 0:
                    logger.info(f"Token usage for this step: {current_chunk_tokens}")
                    token_usage_steps += 1

                bool_result, _ = process_chunk(chunk)
                if bool_result:
                    break
            else:
                logger.error(f"The transformation task for {self.code_hash} failed because the agent stream ended prematurely without successful completion (possibly hit recursion limit).")

        except Exception as e:
            logger.error(f"The transformation task for {self.code_hash} failed due to an exception: {e}")

        logger.info(f"Total tokens for the workflow: {total_all_tokens}")
        if token_usage_steps > 0:
            average_tokens = total_all_tokens / token_usage_steps
            logger.info(f"Average tokens per step: {average_tokens:.2f}")
        else:
            logger.info("No token usage recorded for any step.")

    def _get_system_prompt(self) -> str:
        return (
            f"You are an expert polyglot software engineer specializing in high-fidelity, "
            f"idiomatic code migration from {self.source_language.capitalize()} to {self.target_language.capitalize()}. "
            "You can run tools to build, test, and modify the codebase."
            "Follow the user's constraints strictly and do not attempt to ask the user questions.\n"
            "{agent_scratchpad}"
        )

    @abstractmethod
    def _setup_project(self) -> None:
        pass

    @abstractmethod
    def _get_source_code(self) -> str | None:
        pass

    @abstractmethod
    def _get_initial_input(self, source_code: str) -> dict:
        pass
