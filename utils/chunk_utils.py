from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import queue
from loguru import logger

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
        error_msg = f"[red]Error in process_chunk:[/] {exc}"
        logger.error("error")
        # Another log entry (optional: send to lower level or console)
        # On error return False + empty string, caller can handle appropriately
        return False, ""
