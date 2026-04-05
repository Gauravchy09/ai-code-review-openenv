from __future__ import annotations

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import CodeReviewAction, CodeReviewObservation


class AICodeReviewOpenEnv(
    EnvClient[CodeReviewAction, CodeReviewObservation, State]
):
    def _step_payload(self, action: CodeReviewAction) -> Dict:
        return {"review": action.review}

    def _parse_result(self, payload: Dict) -> StepResult[CodeReviewObservation]:
        obs_data = payload.get("observation", {})
        reward_payload = payload.get("reward")
        reward_value = reward_payload.get("total") if isinstance(reward_payload, dict) else reward_payload

        observation = CodeReviewObservation(
            code=obs_data.get("code", ""),
            task_id=obs_data.get("task_id", ""),
            task=obs_data.get("task", ""),
            difficulty=obs_data.get("difficulty", ""),
            expected_outcomes=obs_data.get("expected_outcomes", []),
            steps_taken=obs_data.get("steps_taken", 0),
            max_steps=obs_data.get("max_steps", 0),
            review_history=obs_data.get("review_history", []),
            done=payload.get("done", False),
            reward=reward_value,
            metadata=payload.get("info", {}),
        )

        return StepResult(
            observation=observation,
            reward=reward_value,
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("task_id"),
            step_count=payload.get("steps_taken", 0),
        )
