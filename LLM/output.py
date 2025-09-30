from typing import List, Optional, Union, Literal, Dict
from pydantic import BaseModel, Field

class Output:
    """Unified output format definitions."""

    class SensitiveType(BaseModel):
        type_list: Optional[List[Literal["Encryption", "Decryption", "Signature", "Verification", "Hash", "Seed", "Random", "Serialization", "Deserialization"]]] = Field(
            default_factory=list,
            description="List of sensitive operation. None if no sensitive operation appear"
        )

    class SensitiveStatementItem(BaseModel):
        type: Literal["Encryption", "Decryption", "Signature", "Verification", "Hash", "Seed", "Random", "Serialization", "Deserialization"]
        statements: List[str] = Field(description="List of code statements for the given sensitive type.")

    class SensitiveStatement(BaseModel):
        """
        Used to answer 'List the code statements that involved in {query}'.
        """
        statements: Optional[List['Output.SensitiveStatementItem']] = Field(
            default_factory=list,
            description="A list of objects, where each object contains a sensitive operation type and a list of corresponding code statements."
        )

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
