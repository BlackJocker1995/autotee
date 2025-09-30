from json import tool
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Any, Dict, Optional, List, Union, Type
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import SecretStr
from langchain_core.prompts import PromptTemplate
from abc import ABC, abstractmethod
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_ollama import ChatOllama
from langchain_community.llms.vllm import VLLMOpenAI


class LLMConfig(BaseSettings):
    """Configuration for LLM models. Only contains non-sensitive settings."""
    provider: str = "openai"  # Supported: "openai", "qwen", "deepseek", "google"
    model: str = ""
    base_url: str = ""
    token_file: str = "tokenfile"
    request_timeout: int = 300
    max_tokens: int = 4096
    max_retries: int = 4
    system_prompt: str = ""

    def get_description(self) -> str:
        """
        Returns a description of the LLM configuration.
        Returns:
            str: A description of the LLM configuration, suitable for use as a directory name.
        """
        # Replace characters potentially problematic in directory names (like '.') with underscores.
        safe_model_name = self.model.replace('.', '_').replace('/', '_').replace(':', '-')
        return f"{self.provider}_{safe_model_name}"

def read_token_from_file(token_file: str, provider: str) -> str:
    """Reads the token from the specified file based on the provider."""
    if provider == "ollama":
        return ""

    try:
        token_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), token_file)
        with open(token_file_path, "r") as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith(provider.upper() + "="):
                _, value = line.strip().split("=", 1)
                value = value.strip().strip('"')  # Remove quotes if present
                return value

        logger.error(f"Token not found for provider: {provider}")
        raise ValueError(f"Token not found for provider: {provider}")
    except FileNotFoundError:
        logger.error(f"Token file not found: {token_file}")
        raise FileNotFoundError(f"Token file not found: {token_file}")
    except Exception as e:
        logger.error(f"Error reading token file: {e}")
        raise RuntimeError(f"Error reading token file: {e}")


class LLModel(ABC):
    """
    Abstract base class for LLM models.
    """

    _chat_model_map = {
        "openai": ChatOpenAI,
        "qwen": ChatTongyi,  # Assuming Qwen is compatible with OpenAI's interface
        "deepseek": ChatDeepSeek,
        "google": ChatGoogleGenerativeAI,
        'vllm': ChatOpenAI,
        'ollama': ChatOllama
    }
    # Provider-specific configuration adjustments
    _provider_base_urls = {
        "ollama": "http://localhost:11434",
        "vllm": "http://localhost:30000/v1"
    }
    def __init__(self, config: "LLMConfig"):
        """
        Initializes the LLM model based on the provided configuration.

        Args:
            config (LLMConfig): Configuration object for LLM model.
        """
        logger.info(f"LLModel init called with config: {config}")
        self.config = config
        self.provider = config.provider
        self.system_prompt = config.system_prompt
        api_key = read_token_from_file(config.token_file, config.provider)

        # Adjust base URL based on provider
        config.base_url = self._provider_base_urls.get(self.provider, "")
        # Get the appropriate chat model class and initialize LLM
        chat_model_class = self._chat_model_map.get(self.provider)
        if not chat_model_class:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        self.llm = chat_model_class(
            model=config.model,
            request_timeout=config.request_timeout,
            max_retries=config.max_retries,
            max_tokens = config.max_tokens,
            api_key=api_key,
            base_url=config.base_url if config.base_url else None
        )
       

    def get_description(self) -> str:
        """
        Returns a description of the LLM model.

        Returns:
            str: A description of the LLM model, suitable for use as a directory name.
        """
        # Replace characters potentially problematic in directory names (like '.') with underscores.
        safe_model_name = self.config.model.replace('.', '_').replace('/', '_').replace(':', '-')
        return f"{self.provider}_{safe_model_name}"
    
    @classmethod
    def get_short_name(cls,model_client:str) -> str:
        """
        Get the short name of the model client.
        :param model_client: The name of the model client.
        :type model_client: str
        :return: The short name of the model client.
        :rtype: str
        """
        # Define a dictionary mapping model names to their short forms
        class_dict = {
            "gpt": "gpt",
            "qwen2.5": "qwen2.5",
            "qwen": "qwen",
            "llama": "llama",
            "deepseek-chat": "deepseek",
            "deepseek-r1": "deepseek-r1",
        }

        # Iterate over each key in the dictionary
        for key in class_dict:
            # Check if the current key is a substring of the model_client string
            if key in model_client:
                # If found, return the corresponding value from the dictionary
                return class_dict[key]

        # If no keys are found in model_client, raise an exception
        raise ValueError(f"Unknown model name: {model_client}")

    @classmethod
    def from_config(cls, config: "LLMConfig") -> "LLModel":
        """
        Factory method to create an LLModel instance from a configuration.

        Args:
            config (LLMConfig): Configuration object for LLM model.

        Returns:
            LLModel: An instance of LLModel.
        """
        return cls(config)


    def create_chat(self, system_prompt: str = "", output_format: Optional[Type[BaseModel]] = None):
        """
        Creates a chat runnable with the LLM, incorporating a system prompt if provided.

        Args:
            system_prompt (Optional[str]): The system prompt to guide the conversation.
            output_format (Optional[BaseModel]): The format for structured output, which can be a subclass of BaseModel.

        Returns:
            A runnable chat object.
        """
        if self.llm is None:
            raise ValueError("LLM model not initialized.")
        if system_prompt:
            self.system_prompt = system_prompt
            
        # Use the provided system prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            ("human", "{input}")
        ])
     
        if output_format:
            out = prompt | self.llm.with_structured_output(output_format)
        else:
            out = prompt | self.llm

        return out
    
    def create_stateless_chat(self, system_prompt: str = "", output_format: Optional[Type[BaseModel]] = None):
        """
        Creates a stateless chat runnable that does not modify the instance's system prompt.

        Args:
            system_prompt (str): The system prompt to use for this chat.
            output_format (Optional[Type[BaseModel]]): The Pydantic model for structured output.

        Returns:
            A runnable chat object.
        """
        if self.llm is None:
            raise ValueError("LLM model not initialized.")

        # Use the provided system prompt or the instance's default
        current_prompt = system_prompt if system_prompt else self.system_prompt
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=current_prompt),
            ("human", "{input}")
        ])
     
        if output_format:
            out = prompt | self.llm.with_structured_output(output_format)
        else:
            out = prompt | self.llm

        return out
    
    

    def create_tool_react(self, tools: list, system_prompt:str) -> Runnable:
        """
        Creates an agent using the LLM and provided tools.

        Args:
            tools (list): A list of tools to be used by the agent.

        Returns:
            CompiledGraph: The compiled graph representing the agent.
        """

        if self.llm is None:
            raise ValueError("LLM model not initialized.")
        return create_react_agent(self.llm, tools=tools, prompt=SystemMessage(content=system_prompt))