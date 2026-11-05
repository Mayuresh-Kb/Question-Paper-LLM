from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class HeaderModel(StrictModel):
    institution: str = Field(default="My Institute", min_length=1, max_length=250)
    exam_name: str = Field(default="Examination", min_length=1, max_length=200)
    subject: str = Field(default="Subject", min_length=1, max_length=200)
    date: str = Field(default="", max_length=40)
    duration: str = Field(default="2 hours", min_length=1, max_length=80)
    instructions: str = Field(default="Figures to the right indicate marks.", max_length=3000)

class UnitPlan(StrictModel):
    unit_id: UUID
    marks: Annotated[int, Field(strict=True, ge=1, le=200)]
    questions_per_alternative: Annotated[int, Field(strict=True, ge=1, le=12)] = 2
    @model_validator(mode="after")
    def feasible(self):
        if self.marks < self.questions_per_alternative:
            raise ValueError("Each subquestion needs at least one mark; reduce the question count or increase marks.")
        return self

class GenerateRequest(StrictModel):
    upload_id: UUID
    units: list[UnitPlan] = Field(min_length=1, max_length=12)
    total_marks: Annotated[int, Field(strict=True, ge=1, le=2400)]
    paper_format: Literal["unit_test", "custom"] = "custom"
    mode: Literal["random", "balanced", "gemini"] = "balanced"
    difficulty: Literal["balanced", "easy", "medium", "hard"] = "balanced"
    header: HeaderModel = Field(default_factory=HeaderModel)
    @model_validator(mode="after")
    def consistent(self):
        if len({u.unit_id for u in self.units}) != len(self.units):
            raise ValueError("A unit may only be selected once.")
        if sum(u.marks for u in self.units) != self.total_marks:
            raise ValueError("Total paper marks must equal the sum of the selected unit marks.")
        if self.paper_format == "unit_test" and (len(self.units) != 2 or self.total_marks != 16 or any(u.marks != 8 for u in self.units)):
            raise ValueError("A unit test must contain exactly two units, 8 marks each, for a total of 16 marks.")
        return self

class QuestionEdit(StrictModel):
    id: UUID
    text: str = Field(min_length=3, max_length=12000)
    source_marks: Annotated[int, Field(strict=True, ge=1, le=200)]
    bloom: Annotated[int, Field(strict=True, ge=1, le=6)]
    topic: str = Field(default="", max_length=150)
    enabled: bool = True
    include_figures: bool = True
    render_mode: Literal["text"] | None = None

class BankEdit(StrictModel):
    unit_id: UUID
    name: str = Field(min_length=1, max_length=200)
    questions: list[QuestionEdit] = Field(min_length=1, max_length=500)

class ReplaceRequest(StrictModel):
    question_id: UUID
    replacement_id: UUID
