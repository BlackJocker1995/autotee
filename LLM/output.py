from typing import List, Optional, Union, Literal, Dict
from pydantic import BaseModel, Field

class Output:
    """Unified output format definitions."""

    class SensitiveType(BaseModel):
        type_list: Optional[List[Literal["Encryption", "Decryption", "Signature", "Verification", "Hash", "Seed", "Random", "Serialization", "Deserialization"]]] = Field(
            default_factory=list,
            description="List of sensitive operation types. Must be selected from: Encryption, Decryption, Signature, Verification, Hash, Seed, Random, Serialization, Deserialization."
        )

    class SensitiveStatementItem(BaseModel):
        type: Literal["Encryption", "Decryption", "Signature", "Verification", "Hash", "Seed", "Random", "Serialization", "Deserialization"]
        statement: str

    class SensitiveStatement(BaseModel):
        """
        Used to answer 'List the code statements that involved in {query}'.
        The dictionary key represents the sensitive operation type, and the value is the specific code statement.
        """
        statements: Optional[List['Output.SensitiveStatementItem']] = Field(default_factory=list)

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