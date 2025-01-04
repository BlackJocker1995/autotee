from pydantic import BaseModel

from LLM.action import Scenario

class Output(Scenario):
    class StructureAnswer(BaseModel):
        result: str

    class OutputCodeFormat(BaseModel):
        code: str

    class OutputStrListFormat(BaseModel):
        result: list[str]

    class OutputCodeListFormat(BaseModel):
        multiple_codes_list: list[str]

    class OutputBoolFormat(BaseModel):
        answer: bool

    class RustCodeWithDepend(BaseModel):
        code: str
        dependencies: list[str]

    class ReactOutputForm(BaseModel):
        thought: str
        action: str | None
        argument: str | list[str] | None
        consistent: bool