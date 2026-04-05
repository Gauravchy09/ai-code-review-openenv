from __future__ import annotations

from typing import List

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class CodeReviewAction(Action):
    review: str = Field(..., description="Agent review suggestion and/or fixed code")


class CodeReviewObservation(Observation):
    code: str = Field(default="", description="Current code snippet for the task")
    task_id: str = Field(default="", description="Task identifier")
    task: str = Field(default="", description="Task instruction")
    difficulty: str = Field(default="", description="Task difficulty")
    expected_outcomes: List[str] = Field(default_factory=list)
    steps_taken: int = Field(default=0)
    max_steps: int = Field(default=0)
    review_history: List[str] = Field(default_factory=list)
