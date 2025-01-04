import inspect
from typing import Type

from loguru import logger
from pydantic import BaseModel

from LLM.action import Scenario
from LLM.llmodel import LModel
from LLM.output import Output
from a4test.test_assistance import timing_decorator
from static.projectUtil import truncate_string


class LModelReAct():
    """
    ReAct policy
    """
    def __init__(self, env_class:Type[Scenario]):
        self.actions = None
        self.candidate = None
        self.env_class = env_class
        self.code_dynamic = None
        self.methods_name, self.methods_structure = env_class.get_class_method_info()

        methods_doc = "\n".join(self.methods_structure)
        methods_name = "\n".join(self.methods_name)

        self.react_prompt = (rf"""
        You run in a thought, action, observation loop.
        At the end of the loop you output an Answer.
        Use thought to describe your thoughts about the question you have been asked.
        
        The <action> you can only choose from:
        
        {methods_name}
        
        Their definition are:
        
        {methods_doc}

        Your output should be a string in json format. 
        The json format that the output needs to follow: 
        {Output.ReactOutputForm.model_json_schema()}
        
        where
        - thought: you should always think about what to do.
        - action: the function to take, should be one of the available actions, when you get an answer.
        - argument: the arguments you need to perform the function.
        - consistent: Unless verified through verify_output_consistency and evident is provided, it will always remain False.
        When you think you have found the answer, do not output actions, but output answer.
        Your output will be directly parsed as a json string, so make sure your output is a valid json string, it must be in str format.
        Your output will be used to create an LLMOutput object using LLMOutput.model_validate_json
        Using None instead of null or "null".
        Please note that your output will be parsed directly.
        If the format is incorrect, the parsing will fail and you will be severely criticized.
        Perform one operation at a time in each output, do not include multiple operations in one output.
        """.strip())
        # - observation: the result of action
        # self.model_agent.messages_memary.append({"role": "system", "content": self.react_prompt})


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
    def __init__(self, env_class:type[Scenario], client_model:str, **arguments):
        super().__init__(env_class)
        self.agent = LModel.class_generator(client_model)

        # action_object
        self.action_object = env_class.Actions(**arguments)

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

    def infer_react(self, question, max_turns=20) -> int:
        # Initialize attempt counter
        attempt = 0
        # Set the initial prompt to the question
        next_prompt = question
        # Get the current size of the messages memory
        top_index = len(self.agent.messages_memary)

        # Loop until the maximum number of turns is reached

        while attempt < max_turns:
            # Increment the attempt counter
            attempt += 1

            # If more than two attempts, remove the last two messages from memory
            if attempt > 2 and len(self.agent.messages_memary) > top_index:
                self.agent.messages_memary.pop(top_index)
                self.agent.messages_memary.pop(top_index)

            # Query the model with the current prompt
            llm_output = self.query_json_react(next_prompt)

            # If no output is received, continue to the next iteration
            if llm_output is None:
                continue

            # Log the attempt and received output
            logger.info("*" * 40 + f" {attempt} try " + "*" * 40)
            # logger.debug(f"Receive: {llm_output}")
            logger.info(f"Thought: {llm_output.thought}")
            logger.info(f"Action: {llm_output.action}")
            logger.info(f"Consistent: {llm_output.consistent}")

            # If the output is consistent, return the attempt count
            if llm_output.consistent and llm_output.action is None:
                return attempt

            # Check if the action is known
            if llm_output.action not in self.methods_name:
                logger.info("Unknown action: {}({})".format(
                    llm_output.action, llm_output.argument
                ))
                # Update the prompt with an error message
                next_prompt = (f"Action Error - Unknown action: {llm_output.action}. "
                               f"You can only choose from {self.env_class.get_class_method_info()[0]}")
                # attempt -= 1
                continue

            # Log the action being run
            logger.info(truncate_string("Running {}({})".format(llm_output.action, llm_output.argument)))
            try:
                # Retrieve the method corresponding to the action
                action_func = getattr(self.action_object, llm_output.action)
                # Execute the method with the provided argument
                if llm_output.argument is not None:
                    #if isinstance(llm_output.argument, str):
                    observation = action_func(llm_output.argument)
                    # else:
                    #     observation = action_func(eval(llm_output.argument))
                else:
                    observation = action_func()

            except Exception as e:
                # Log any exceptions that occur during method execution
                logger.warning(f"Some Error, fail to call the function as {e}. "
                               f"The signature of function is {inspect.signature(action_func)}.")
                # Update the prompt with the error observation
                next_prompt = (f"Observation: Some Error, fail to call the function as {e}. "
                               f"The signature of function is {inspect.signature(action_func)}.")
                # attempt -= 1
                continue

            # Log the observation and update the prompt
            logger.debug("Observation: {}...\n".format(observation))
            logger.info(truncate_string("Observation: {}...\n".format(observation)))
            next_prompt = "Observation: {}".format(observation)

        # Return -1 if the maximum number of turns is reached without a consistent output
        return -1