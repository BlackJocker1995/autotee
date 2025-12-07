# AutoTEE

**Version:** 2.0

## Overview

Trusted Execution Environments (TEEs) provide a hardware-supported secure environment for programs, safeguarding sensitive data and operations (e.g., fingerprint verification and remote attestation) to ensure security and integrity of the running program. Despite widespread hardware support, programs that utilize TEEs to safeguard sensitive operations and data remain scarce due to the complexity of adaptation.

In this project, we introduce AutoTEE, an automated approach that adapts existing Java and Python programs for TEE protection across various platforms without manual intervention.

## Features

- **Automated Adaptation**: AutoTEE employs a Large Language Model (LLM) to identify code related to sensitive operations and data, converting them into TEE-executable versions.
- **Functional Consistency**: Ensures functional consistency through test cases and iterative refinement.
- **Seamless Integration**: Further code alteration and merging to integrate the transformed code with the original program, achieving automatic TEE protection.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/autotee.git
    cd autotee
    ```

2.  **Install `uv`**:
    This project uses `uv` to run. If you don't have it installed, you can install it with:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    `uv` will automatically manage the virtual environment and dependencies from `pyproject.toml`.

## Configuration

### LLM API Token

To use LLM providers that require an API key (like OpenAI, Google, DeepSeek), you must create a file named `tokenfile` inside the `LLM/` directory.

1.  **Create the file**:
    ```bash
    touch LLM/tokenfile
    ```

2.  **Add your token**:
    The file must contain your API token in the following format, where the key is the uppercase name of the provider:
    ```
    PROVIDER=YOUR_API_KEY
    ```

    **Example for OpenAI**:
    ```
    OPENAI=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

### Local LLM Server Configuration (vLLM, SGLang, Ollama)

For local LLM servers like vLLM, SGLang, and Ollama, the base URLs are configured within the `LLM/llmodel.py` file. If your local server is running on a different address or port, you may need to modify the `_provider_base_urls` dictionary in `LLM/llmodel.py` to match your setup.

**Example for vLLM in `LLM/llmodel.py`:**

```python
_provider_base_urls = {
    # ... other providers
    "vllm": "http://your-vllm-server-address:port/v1",
    "sglang": "http://your-sglang-server-address:port/v1",
    "ollama": "http://your-ollama-server-address:port",
}
```

## Supported LLMs

This project supports the following LLM providers:

-   **OpenAI**: Models from OpenAI (e.g., GPT-3.5, GPT-4).
-   **Qwen**: Tongyi Qwen models from Alibaba Cloud.
-   **DeepSeek**: Models from DeepSeek.
-   **Google**: Generative models from Google (e.g., Gemini).
-   **Ollama**: Run local models using Ollama.
-   **vLLM**: Run local models with vLLM OpenAI-compatible server.
-   **SGLang**: Run local models with SGLang OpenAI-compatible server.

## Usage

The main entry point for the program is `main.py`. Use `uv run` to execute tasks. This command will automatically install the required dependencies into a managed virtual environment and run the script.

**Important:** Before running, you must manually edit the `main.py` file to set the `project_name` variable to the absolute path of the project you wish to analyze.

```python
# In main.py
project_name = "/path/to/your/project"
```

**Command format**:
```bash
uv run main.py <task>
```

**Available tasks**:
- `leaf`: Run the processing task.
- `sensitive`: Query for sensitive parts of the project.
- `write`: Write sensitive information to a file.
- `test`: Run the test creation workflow.
- `transform`: Run the code transformation workflow.

**Example**:
```bash
uv run  main.py transform
```

## Intel SGX Support

### Test Environment
- Ubuntu 22.04 - 5.15.0-117-generic, VM, Ali cloud Z8 (Support SGX HW);
- Ubuntu 22.04, Intel I7-9700 (SGX1.0);
