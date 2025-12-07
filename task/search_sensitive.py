import os
import sys

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from loguru import logger
from tqdm import tqdm

from LLM.llmodel import LLMConfig, LLModel
from LLM.output import Bool, SensitiveStatement, SensitiveType
from static.projectUtil import read_code_block, save_code_block

BLOCK_SIZE_LIMIT = 10240
LLM_SYSTEM_PROMPT = """You are an expert in code security and TEE (Trusted Execution Environment).
Your task is to identify "leaf functions" that are suitable for porting to a TEE.

A "leaf function" has the following properties:
1.  **Lowest level of the program structure:** It does not depend on other user-defined functions within the project. It can, however, use standard library functions.
2.  **Basic Arguments:** Its argument types are primitive data types (e.g., integers, floating-point numbers) or basic composite structures (e.g., arrays and strings).
3.  **No instance context:** It should not rely on instance variables (e.g., using `this` or `self`).
"""
INPUT_NAME_PREFIX = "java_leaf"
OUTPUT_NAME_SUFFIX = "_sen"

# 配置 loguru：禁止它捕获 print/tqdm 的 stderr（避免重复或干扰）
logger.remove()  # 清除默认 handler
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


# 自定义一个适配器：让 tqdm.write() → logger.info()
class TqdmToLogger:
    def __init__(self, logger, level="INFO"):
        self.logger = logger
        self.level = level

    def write(self, buf):
        buf = buf.strip()
        if buf:
            self.logger.opt(depth=1).log(self.level, buf)

    def flush(self):
        pass  # logger 自动 flush


# 创建适配器实例
tqdm_logger = TqdmToLogger(logger, level="INFO")


class TokenUsageCallback(BaseCallbackHandler):
    def __init__(self, agent: LLModel):
        self.agent = agent

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        if response.llm_output and "token_usage" in response.llm_output:
            token_usage = response.llm_output["token_usage"]
            input_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            self.agent.total_input_tokens += input_tokens
            self.agent.total_completion_tokens += completion_tokens
            logger.debug(
                f"Token usage for current invoke: Input={input_tokens}, Completion={completion_tokens}. "
                f"Total: Input={self.agent.total_input_tokens}, Completion={self.agent.total_completion_tokens}"
            )


def _invoke_llm_chat(agent: LLModel, prompt: str, output_format=None):
    if output_format:
        chat = agent.create_stateless_chat(
            system_prompt=LLM_SYSTEM_PROMPT, output_format=output_format
        )
    else:
        chat = agent.create_stateless_chat(system_prompt=LLM_SYSTEM_PROMPT)

    # Instantiate and use the callback for this invocation
    token_callback = TokenUsageCallback(agent)
    result = chat.invoke({"input": prompt}, config={"callbacks": [token_callback]})

    print(result)
    return result


def query_sensitive_project(
    project_path: str, language: str, llm_config: LLMConfig
) -> None:
    agent = LLModel.from_config(llm_config)
    in_name = f"{language}_leaf"
    out_name = f"{llm_config.get_description()}{OUTPUT_NAME_SUFFIX}"

    logger.info(f"Switch to {project_path}.")
    input_dir = os.path.join(project_path, "ana_json")
    codes = read_code_block(input_dir, in_name)
    out = []
    processed_blocks = 0

    for code in tqdm(codes, desc="Processing", unit="item", mininterval=1):
        # Store token counts before processing this code block
        start_input_tokens = agent.total_input_tokens
        start_completion_tokens = agent.total_completion_tokens

        block = code["code"]

        if len(block) > BLOCK_SIZE_LIMIT:
            logger.debug("Over size, skip...")
            continue

        processed_blocks += 1
        # First question
        result1 = _invoke_llm_chat(
            agent,
            "Does this function utilize or implement any operations related to [cryptography, serialization]? Specifically, cryptography includes [Encryption, Decryption, Signature, Verification, Hash, Seed, Random]; serialization includes [Serialization, Deserialization]"
            + f"``` {block} ```",
            output_format=Bool,
        )
        if not result1 or not getattr(result1, "answer"):
            continue

        # Second question
        result2 = _invoke_llm_chat(
            agent,
            "Which specific subcategories type is it involve in?"
            + f"``` {block} ```  Specifically, cryptography includes [Encryption, Decryption, Signature, Verification, Hash, Seed, Random]; serialization includes [Serialization, Deserialization]",
            output_format=SensitiveType,
        )
        if not result2 or not result2.type_list:
            continue

        sensitive_types = list(set(result2.type_list))

        # Third question
        result3 = _invoke_llm_chat(
            agent,
            f"List the code statements that involved in {sensitive_types}:"
            + f"``` {block} ```  Specifically, cryptography includes [Encryption, Decryption, Signature, Verification, Hash, Seed, Random]; serialization includes [Serialization, Deserialization]",
            output_format=SensitiveStatement,
        )

        if not result3 or not result3.statements:
            continue

        # If all three questions pass, retain the item and add the new attributes

        code["sensitive_check"] = result1.answer
        code["sensitive_type"] = sensitive_types
        statements_dict = {item.type: item.statements for item in result3.statements}
        code["sensitive_statements"] = statements_dict
        logger.info(
            f"All sensitive checks passed and statements extracted for function. Sensitive check result: {code}"
        )
        out.append(code)

        # Calculate and log token usage for this session
        session_input_tokens = agent.total_input_tokens - start_input_tokens
        session_completion_tokens = (
            agent.total_completion_tokens - start_completion_tokens
        )
        logger.info(
            f"Session token usage for code block: Input={session_input_tokens}, "
            f"Completion={session_completion_tokens}, "
            f"Total={session_input_tokens + session_completion_tokens}"
        )

    if processed_blocks > 0:
        avg_input_tokens = agent.total_input_tokens / processed_blocks
        avg_completion_tokens = agent.total_completion_tokens / processed_blocks
        avg_total_tokens = (
            agent.total_input_tokens + agent.total_completion_tokens
        ) / processed_blocks
        logger.info(f"Average Input Tokens per block: {avg_input_tokens:.2f}")
        logger.info(f"Average Completion Tokens per block: {avg_completion_tokens:.2f}")
        logger.info(f"Average Total Tokens per block: {avg_total_tokens:.2f}")

    logger.info(f"Total Input Tokens: {agent.total_input_tokens}")
    logger.info(f"Total Completion Tokens: {agent.total_completion_tokens}")
    logger.info(
        f"Total Combined Tokens: {agent.total_input_tokens + agent.total_completion_tokens}"
    )

    output_dir = os.path.join(project_path, "ana_json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    save_code_block(output_dir, out, out_name)
