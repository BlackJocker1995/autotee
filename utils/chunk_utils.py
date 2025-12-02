from __future__ import annotations

from typing import Any, Dict, Tuple
from loguru import logger
from langchain_core.messages import BaseMessage # Added import for BaseMessage


def extract_token_usage(chunk: Dict[str, Any]) -> int:
    """Extracts total token usage from a LangGraph stream chunk.

    Args:
        chunk: A chunk returned by LangGraph during streaming.

    Returns:
        The total number of tokens used in the chunk.
    """
    total_tokens_for_chunk = 0
    # The token usage is in the 'agent' or '__end__' node of the graph
    for key in ('agent', '__end__'):
        if not (value := chunk.get(key)):
            continue

        if messages := value.get("messages"):
            # Ensure the message is of type BaseMessage to access response_metadata
            last_message: BaseMessage = messages[-1]
            current_total_tokens = 0

            # Prioritize usage_metadata if available and contains the relevant keys
            if hasattr(last_message, "usage_metadata") and last_message.usage_metadata:
                if "total_tokens" in last_message.usage_metadata:
                    current_total_tokens = last_message.usage_metadata.get("total_tokens", 0)

            # Fallback to response_metadata['token_usage'] if usage_metadata doesn't provide it
            if current_total_tokens == 0 and \
               hasattr(last_message, "response_metadata") and \
               (token_usage := last_message.response_metadata.get("token_usage")):
                current_total_tokens = token_usage.get("total_tokens", 0)

            total_tokens_for_chunk += current_total_tokens
    return total_tokens_for_chunk


def process_chunk(
    chunk: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Process a single LangGraph streaming chunk.

    The function walks through the chunk, extracts the most recent
    AI message, logs it and decides whether the task should terminate.

    Parameters
    ----------
    chunk : dict
        A chunk returned by LangGraph during streaming.
    message_queue : queue.Queue | None, optional
        Queue used to push UI updates back to the main process.
    task_id : str | None, optional
        Identifier of the task window that should receive the logs.

    Returns
    -------
    tuple[bool, str]
        * ``bool`` – ``True`` if the chunk contains a termination signal,
          ``False`` otherwise.
        * ``str`` – the raw AI message text (if not terminating) or an empty
          string when terminating.  In case of an exception, an error
          description is returned and the bool is ``False``.
    """
    try:
        # Iterate through each state update
        for _, state_update in chunk.items():
            # Only process updates that contain messages
            if "messages" in state_update and state_update["messages"]:
                # Get the last message
                last_message = state_update["messages"][-1]
                ai_msg_str = last_message.pretty_repr()

                # Log only the first 15 lines to avoid excessive output
                ai_msg_lines = ai_msg_str.splitlines()
                if len(ai_msg_lines) > 15:
                    truncated_msg = "\n".join(ai_msg_lines[:15]) + "\n...(truncated)"
                    logger.debug(truncated_msg)
                else:
                    logger.debug(ai_msg_str)

                # Check if it's a termination marker
                if "[Terminate]" in ai_msg_str:
                    # Terminate, return True + empty string
                    return True, ""

                # Non-termination message: return False + original message
                return False, str(ai_msg_str)

        # If the chunk contains no messages, treat as non-termination
        return False, ""

    except Exception as exc:
        # Log error
        logger.error(f"error: {exc}")
        # Another log entry (optional: send to lower level or console)
        # On error return False + empty string, caller can handle appropriately
        return False, ""
