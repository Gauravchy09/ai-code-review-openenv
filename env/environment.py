from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .grader import GradeResult, grade_task
from .tasks import TASKS, TaskDefinition, get_task


class Observation(BaseModel):
    code: str
    task_id: str
    task: str
    difficulty: str
    expected_outcomes: List[str]
    steps_taken: int
    max_steps: int
    review_history: List[str] = Field(default_factory=list)


class Action(BaseModel):
    review: str = Field(..., min_length=1, description="Agent's code review suggestion and/or fixed code")


class Reward(BaseModel):
    total: float = Field(..., ge=0.0, le=1.0)
    correctness: float = Field(..., ge=0.0, le=1.0)
    optimization: float = Field(..., ge=0.0, le=1.0)
    readability: float = Field(..., ge=0.0, le=1.0)
    formatting: float = Field(..., ge=0.0, le=1.0)
    penalty: float = Field(..., ge=0.0, le=1.0)


class StepInfo(BaseModel):
    grade_feedback: str
    task_passed: bool
    passed_tests: int
    total_tests: int
    timestamp_utc: str


class OpenEnvCodeReviewEnvironment:
    def __init__(self, max_steps: int = 3) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self.max_steps = max_steps
        self._current_task: Optional[TaskDefinition] = None
        self._steps_taken: int = 0
        self._review_history: List[str] = []
        self._done: bool = False
        self._last_grade: Optional[GradeResult] = None

    @property
    def tasks(self) -> List[TaskDefinition]:
        return TASKS

    def _build_observation(self) -> Observation:
        if not self._current_task:
            raise RuntimeError("Environment is not initialized. Call reset() first.")
        return Observation(
            code=self._current_task.starter_code,
            task_id=self._current_task.task_id,
            task=self._current_task.instruction,
            difficulty=self._current_task.difficulty,
            expected_outcomes=self._current_task.expected_outcomes,
            steps_taken=self._steps_taken,
            max_steps=self.max_steps,
            review_history=self._review_history.copy(),
        )

    def reset(self, task_id: Optional[str] = None) -> Observation:
        if task_id is None:
            task_id = TASKS[0].task_id
        self._current_task = get_task(task_id)
        self._steps_taken = 0
        self._review_history = []
        self._done = False
        self._last_grade = None
        return self._build_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        if self._current_task is None:
            raise RuntimeError("Call reset() before step().")
        if self._done:
            raise RuntimeError("Episode is done. Call reset() for a new episode.")

        self._steps_taken += 1
        self._review_history.append(action.review)

        grade = grade_task(self._current_task, action.review)
        self._last_grade = grade

        reward = Reward(
            total=grade.total,
            correctness=grade.correctness,
            optimization=grade.optimization,
            readability=grade.readability,
            formatting=grade.formatting,
            penalty=grade.penalty,
        )

        self._done = grade.total >= 0.95 or self._steps_taken >= self.max_steps

        info = StepInfo(
            grade_feedback=grade.feedback,
            task_passed=grade.total >= 0.8,
            passed_tests=grade.passed_tests,
            total_tests=grade.total_tests,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        ).model_dump()

        return self._build_observation(), reward, self._done, info

    def state(self) -> Dict:
        if self._current_task is None:
            return {
                "initialized": False,
                "message": "Environment not reset yet.",
            }

        return {
            "initialized": True,
            "task_id": self._current_task.task_id,
            "difficulty": self._current_task.difficulty,
            "steps_taken": self._steps_taken,
            "max_steps": self.max_steps,
            "done": self._done,
            "last_reward": self._last_grade.total if self._last_grade else None,
            "history_length": len(self._review_history),
        }
