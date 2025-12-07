from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SensitiveType(BaseModel):
    type_list: Optional[
        List[
            Literal[
                "Encryption",
                "Decryption",
                "Signature",
                "Verification",
                "Hash",
                "Seed",
                "Random",
                "Serialization",
                "Deserialization",
            ]
        ]
    ] = Field(
        default_factory=list,
        description="List of sensitive operation. None if no sensitive operation appear",
    )


class SensitiveStatementItem(BaseModel):
    type: Literal[
        "Encryption",
        "Decryption",
        "Signature",
        "Verification",
        "Hash",
        "Seed",
        "Random",
        "Serialization",
        "Deserialization",
    ]
    statements: List[str] = Field(
        description="List of code statements for the given sensitive type."
    )


class SensitiveStatement(BaseModel):
    """
    Used to answer 'List the code statements that involved in {query}'.
    """

    statements: Optional[List["SensitiveStatementItem"]] = Field(
        default_factory=list,
        description="A list of objects, where each object contains a sensitive operation type and a list of corresponding code statements.",
    )


class Bool(BaseModel):
    """Boolean answer."""

    answer: bool
