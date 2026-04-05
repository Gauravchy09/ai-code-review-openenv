from __future__ import annotations

from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from env.environment import Action, OpenEnvCodeReviewEnvironment

app = FastAPI(title="AI Code Review OpenEnv", version="1.0.0")
env = OpenEnvCodeReviewEnvironment(max_steps=3)


class ResetRequest(BaseModel):
    task_id: Optional[str] = Field(default=None, description="Optional task id")


class StepRequest(BaseModel):
    review: str = Field(..., min_length=1)


@app.get("/")
def home() -> Dict:
    return {
        "name": "AI Code Review OpenEnv",
        "status": "running",
        "routes": ["/health", "/tasks", "/reset", "/step", "/state"],
    }


@app.get("/web")
def web_home() -> Dict:
    return home()


@app.get("/health")
def health() -> Dict:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> Dict:
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "title": t.title,
                "difficulty": t.difficulty,
                "instruction": t.instruction,
                "expected_outcomes": t.expected_outcomes,
            }
            for t in env.tasks
        ]
    }


@app.post("/reset")
def reset(payload: ResetRequest) -> Dict:
    try:
        obs = env.reset(task_id=payload.task_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"observation": obs.model_dump()}


@app.post("/step")
def step(payload: StepRequest) -> Dict:
    try:
        obs, reward, done, info = env.step(Action(review=payload.review))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state() -> Dict:
    return env.state()


def main() -> None:
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)
