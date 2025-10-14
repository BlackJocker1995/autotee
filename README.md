# AutoTEE

**Version:** 2.0

## Overview

Trusted Execution Environments (TEEs) provide a hardware-supported secure environment for programs, safeguarding sensitive data and operations (e.g., fingerprint verification and remote attestation) to ensure security and integrity of the running program. Despite widespread hardware support, programs that utilize TEEs to safeguard sensitive operations and data remain scarce due to the complexity of adaptation.

In this project, we introduce AutoTEE, an automated approach that adapts existing Java and Python programs for TEE protection across various platforms without manual intervention.

## Features

- **Automated Adaptation**: AutoTEE employs a Large Language Model (LLM) to identify code related to sensitive operations and data, converting them into TEE-executable versions.
- **Functional Consistency**: Ensures functional consistency through test cases and iterative refinement.
- **Seamless Integration**: Further code alteration and merging to integrate the transformed code with the original program, achieving automatic TEE protection.

## Deployment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/autotee.git
   cd autotee
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

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

## Usage

The main entry point for the program is `main.py`. You can execute different functions by specifying the task name in the command line.

**Important:** Before running, you must manually edit the `main.py` file to set the `project_name` variable to the absolute path of the project you wish to analyze.

```python
# In main.py
project_name = "/path/to/your/project"
```

**Command format**:
```bash
python main.py <task>
```

**Available tasks**:
- `leaf`: Run the processing task.
- `sensitive`: Query for sensitive parts of the project.
- `write`: Write sensitive information to a file.
- `test`: Run the test creation workflow.
- `transform`: Run the code transformation workflow.

**Example**:
```bash
python main.py transform
```

## Intel SGX Support

### Test Environment
- Ubuntu 22.04 - 5.15.0-117-generic, VM, Ali cloud Z8 (Support SGX HW);
- Ubuntu 22.04, Intel I7-9700 (SGX1.0);

