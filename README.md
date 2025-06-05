# AutoTEE

## Overview

Trusted Execution Environments (TEEs) provide a hardware-supported secure environment for programs, safeguarding sensitive data and operations (e.g., fingerprint verification and remote attestation) to ensure security and integrity of the running program. Despite widespread hardware support, programs that utilize TEEs to safeguard sensitive operations and data remain scarce due to the complexity of adaptation.

In this project, we introduce AutoTEE, an automated approach that adapts existing Java and Python programs for TEE protection across various platforms without manual intervention.

## Features

- **Automated Adaptation**: AutoTEE employs a Large Language Model (LLM) to identify code related to sensitive operations and data, converting them into TEE-executable versions.
- **Functional Consistency**: Ensures functional consistency through test cases and iterative refinement.
- **Seamless Integration**: Further code alteration and merging to integrate the transformed code with the original program, achieving automatic TEE protection.

## Evaluation

AutoTEE has been evaluated on practical TEEs, with the support of advanced LLMs, achieving success rates exceeding 80%.

## Getting Started

To get started with AutoTEE, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/autotee.git
    ```
2. Navigate to the project directory:
    ```bash
    cd autotee
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
