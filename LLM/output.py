from typing import List, Optional
from pydantic import BaseModel, Field

from LLM.action import Scenario

class BaseOutput(BaseModel):
    """Base class for all output types."""
    class Config:
        extra = "forbid"

class Output:
    """Collection of output format definitions."""
    
    class StructureAnswer(BaseOutput):
        """Basic string result output."""
        result: str = Field(..., description="The result string")

    class OutputCodeFormat(BaseModel):
        code: str

    class OutputStrListFormat(BaseModel):
        result: list[str]

    class OutputCodeListFormat(BaseModel):
        multiple_codes_list: list[str]

    class OutputBoolFormat(BaseModel):
        answer: bool

    class RustCodeWithDepend(BaseOutput):
        """Rust code output with dependencies."""
        code: str = Field(..., description="Rust source code")
        dependencies: List[str] = Field(default_factory=list, description="Required dependencies")

    class ReactOutputForm(BaseOutput):
        """ReAct framework output format."""
        thought: str = Field(..., description="Reasoning process")
        action: Optional[str] = Field(None, description="Action to take")
        argument: Optional[str | List[str]] = Field(None, description="Action arguments")
        consistent: bool = Field(..., description="Whether output is consistent")