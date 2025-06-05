from typing import Type, Optional, Dict, Any
from loguru import logger
from pydantic import BaseModel, Field

from LLM.action import Scenario
from LLM.llmodel import LModel
from LLM.output import Output
from a4test.test_assistance import timing_decorator
from static.projectUtil import truncate_string

class ReactConfig(BaseModel):
    """Configuration for ReAct model."""
    max_turns: int = Field(default=20, description="Maximum number of turns")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    logging_enabled: bool = Field(default=True, description="Enable detailed logging")

class LModelReAct:
    """ReAct (Reasoning + Acting) policy implementation."""

    REACT_PROMPT_TEMPLATE = """
    You run in a thought, action, observation loop.
    At the end of the loop you output an Answer.
    Use thought to describe your thoughts about the question you have been asked.
    
    Available actions:
    {methods_name}
    
    Action definitions:
    {methods_doc}

    Output format:
    {output_schema}
    """

    def __init__(self, env_class: Type[Scenario], config: Optional[ReactConfig] = None):
        """Initialize ReAct model with environment class and configuration.
        
        Args:
            env_class: Scenario class containing available actions
            config: Optional configuration settings
        """
        self.env_class = env_class
        self.config = config or ReactConfig()
        self.methods_name, self.methods_docs = env_class.get_class_method_info()
        self.react_prompt = self._build_prompt()
        
    def _build_prompt(self) -> str:
        """Build the formatted system prompt."""
        return self.REACT_PROMPT_TEMPLATE.format(
            methods_name="\n".join(f"- {name}" for name in self.methods_name),
            methods_doc="\n".join(self.methods_docs),
            output_schema=Output.ReactOutputForm.model_json_schema()
        ).strip()

    def candidate_dict(self, block):
        self.candidate = block

def extract_json(text: str):
    """
    Extract a JSON string from a given text.

    This function attempts to locate and extract a JSON object from the input text.
    It identifies the JSON content by searching for the first opening curly brace `{`
    and the last closing curly brace `}`. The extracted JSON string is then returned,
    with any escaped underscores (`\_`) replaced by regular underscores (`_`).

    :param text: The input text containing the JSON object.
    :type text: str

    :returns: The extracted JSON string if successful, or an error message if an exception occurs.
    :rtype: str

    :raises Exception: If an error occurs during the extraction process, an error message is returned instead.
    """
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        json_content = text[json_start:json_end].replace("\\_", "_")
        return json_content
    except Exception as e:
        return f"Error extracting JSON: {e}"

class ReActModel(LModelReAct):
    """Implementation of ReAct model with specific LLM backend."""
    
    def __init__(self, env_class: Type[Scenario], client_model: str, 
                 config: Optional[ReactConfig] = None, **kwargs: Dict[str, Any]):
        """Initialize ReAct model with specific configuration.
        
        Args:
            env_class: Scenario class containing available actions
            client_model: Name of the LLM client to use
            config: Optional ReAct configuration
            **kwargs: Additional arguments passed to action initialization
        """
        super().__init__(env_class, config)
        self.agent = LModel.class_generator(client_model)
        self.action_object = env_class.Actions(**kwargs)

    def get_short_name(self):
        return self.agent.get_short_name()

    @timing_decorator
    def query_json_react(self, message: str, remember=True) -> BaseModel:
        tmp_messages_memary = self.agent.messages_memary.copy()
        tmp_messages_memary.append({"role": "user", "content": message})
        tmp_messages_memary.insert(0, {"role": "system",
                                       "content": self.react_prompt})

        result = self.agent.execute(tmp_messages_memary, Output.ReactOutputForm)

        if remember:
            self.agent.messages_memary.append({"role": "user", "content": message})
            self.agent.messages_memary.append({"role": "assistant", "content": result.model_dump_json()})
        return result

    def infer_react(self, question: str) -> int:
        """Run the ReAct inference loop.
        
        Args:
            question: Initial question to process
            
        Returns:
            Number of turns taken or -1 if max_turns reached
        
        Raises:
            ValueError: If invalid action or argument received
        """
        attempt = 0
        next_prompt = question
        messages_start = len(self.agent.messages_memory)

        while attempt < self.config.max_turns:
            attempt += 1
            
            # Cleanup old messages if needed
            if attempt > 2:
                self._cleanup_messages(messages_start)
                
            # Get next action
            llm_output = self._get_next_action(next_prompt)
            if not llm_output:
                continue
                
            # Process output
            if self._is_final_answer(llm_output):
                return attempt
                
            # Execute action and get next prompt    
            try:
                next_prompt = self._execute_action(llm_output)
            except Exception as e:
                next_prompt = self._handle_action_error(e, llm_output)
                
        return -1

    def _get_next_action(self, prompt: str) -> Optional[Output.ReactOutputForm]:
        """Get next action from LLM."""
        try:
            return self.query_json_react(prompt)
        except Exception as e:
            logger.error(f"Failed to get next action: {e}")
            return None

    def _is_final_answer(self, output: Output.ReactOutputForm) -> bool:
        """Check if output represents final answer."""
        return output.consistent and output.action is None

    def _execute_action(self, output: Output.ReactOutputForm) -> str:
        """Execute action and return observation."""
        if output.action not in self.methods_name:
            return self._handle_unknown_action(output)
            
        action_func = getattr(self.action_object, output.action)
        observation = self._call_action(action_func, output.argument)
        
        return f"Observation: {observation}"

    def _call_action(self, func: Any, argument: Any) -> Any:
        """Call action function with argument."""
        if argument is not None:
            return func(argument)
        return func()

    def _cleanup_messages(self, start_index: int) -> None:
        """Clean up old messages."""
        while len(self.agent.messages_memory) > start_index:
            self.agent.messages_memory.pop(start_index)

    def _log_attempt(self, attempt: int, llm_output: Output.ReactOutputForm) -> None:
        """Log details of the current attempt.
        
        Args:
            attempt (int): Current attempt number
            llm_output (Output.ReactOutputForm): Output from LLM
        """
        logger.info("*" * 40 + f" {attempt} try " + "*" * 40)
        logger.info(f"Thought: {llm_output.thought}")
        logger.info(f"Action: {llm_output.action}")
        logger.info(f"Consistent: {llm_output.consistent}")

    def _handle_unknown_action(self, llm_output: Output.ReactOutputForm) -> str:
        """Handle unknown action error and return updated prompt.
        
        Args:
            llm_output (Output.ReactOutputForm): Output containing unknown action
            
        Returns:
            str: Updated prompt with error message
        """
        logger.info("Unknown action: {}({})".format(
            llm_output.action, llm_output.argument
        ))
        return (f"Action Error - Unknown action: {llm_output.action}. "
                f"You can only choose from {self.env_class.get_class_method_info()[0]}")

    def _handle_action_error(self, error: Exception, output: Output.ReactOutputForm) -> str:
        """Handle action execution error and return updated prompt.
        
        Args:
            error (Exception): Exception raised during action execution
            output (Output.ReactOutputForm): Output containing action details
            
        Returns:
            str: Updated prompt with error message
        """
        logger.warning(f"Error executing action {output.action}: {error}")
        return (f"Observation: Error executing action {output.action}: {error}. "
                f"The signature of function is {inspect.signature(getattr(self.action_object, output.action))}.")