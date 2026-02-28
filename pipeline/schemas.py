"""Output schemas matching the frontend JSON structure."""

from pydantic import BaseModel, Field


class FillInTheBlank(BaseModel):
    id: str = Field(description="Unique question ID, e.g. q_001")
    type: str = Field(default="fill_in_the_blank", description="Question type")
    content: str = Field(
        description="Sentence with [BLANK] replacing the key term. "
        "Must contain exactly one [BLANK] placeholder."
    )
    answer: str = Field(description="The word/phrase that fills the blank")
    explanation: str = Field(description="Brief explanation of why this is the answer")


class MultipleChoice(BaseModel):
    id: str = Field(description="Unique question ID, e.g. q_001")
    type: str = Field(default="multiple_choice", description="Question type")
    year: int = Field(description="Exam year")
    content: str = Field(description="The question text")
    options: list[str] = Field(
        description="List of answer choices (usually 5 for Korean exams)"
    )
    correctIndex: int = Field(
        description="0-based index of the correct answer in the options list"
    )
    explanation: str = Field(description="Explanation of the correct answer")


class QuizOutput(BaseModel):
    """Complete quiz output containing both question types."""

    multiple_choice: list[MultipleChoice] = Field(
        description="Multiple choice questions extracted from exam text"
    )
    fill_in_the_blank: list[FillInTheBlank] = Field(
        description="Fill-in-the-blank questions generated from key summary sentences"
    )
