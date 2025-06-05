from typing import List, Optional, Union
from pydantic import BaseModel, Field

class Output:
    """Unified output format definitions."""

    class String(BaseModel):
        """Single string result."""
        result: str

    class StringList(BaseModel):
        """List of strings result."""
        result: List[str]

    class Code(BaseModel):
        """Single code block."""
        code: str

    class CodeList(BaseModel):
        """Multiple code blocks."""
        multiple_codes_list: List[str]

    class Bool(BaseModel):
        """Boolean answer."""
        answer: bool

    class CodeWithDependencies(BaseModel):
        """Code with dependencies."""
        code: str
        dependencies: List[str] = Field(default_factory=list)

    class ReAct(BaseModel):
        """ReAct output format."""
        thought: str
        action: Optional[str] = None
        argument: Optional[Union[str, List[str]]] = None
        consistent: bool