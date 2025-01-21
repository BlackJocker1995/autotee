# AutoTEE Release Notes

## Version 1.0.0

### Overview
AutoTEE is an automated approach that adapts existing Java and Python programs for Trusted Execution Environment (TEE) protection across various platforms without manual intervention. This release marks the initial stable version of the system.

### Key Features
- Automated adaptation of Java and Python programs for TEE protection
- LLM-powered identification of sensitive operations and data
- Functional consistency through test cases and iterative refinement
- Seamless integration with original programs
- Support for multiple LLM providers (OpenAI, Anthropic, Ollama)

### System Requirements
- Python 3.10 or higher
- Core dependencies:
  - pydantic>=2.0.0
  - loguru>=0.7.0
- LLM API clients:
  - openai>=1.0.0
  - anthropic>=0.3.0
  - ollama>=0.1.0

### Build Process
The build system utilizes a modular architecture with:
- TestAssistance class for managing conversion and build processes
- Deepseek model integration for Python type testing
- Automated project scanning and conversion

### Recent Changes
- Initial release with core functionality
- Support for Java and Python program conversion
- Integration with multiple LLM providers
- Automated build and test pipeline
- Comprehensive logging and error handling

### Getting Started
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/autotee.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the conversion process:
   ```bash
   python a2mul_case/all_3covert&build.py
   ```

