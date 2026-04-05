from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from statistics import mean
from typing import Dict, Optional

from openai import OpenAI

from env.environment import Action, OpenEnvCodeReviewEnvironment


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
# Optional variable for docker-based client flows.
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_client() -> tuple[Optional[OpenAI], str, bool, str]:
    mock_mode = os.getenv("MOCK_INFERENCE", "0").strip().lower() in {"1", "true", "yes"}

    if mock_mode:
        return None, MODEL_NAME, True, "explicit_mock_flag"

    if not HF_TOKEN:
        return None, MODEL_NAME, True, "missing_credentials"

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    return client, MODEL_NAME, False, "api_mode"


def llm_review(client: OpenAI, model_name: str, task_payload: Dict) -> str:
    system_prompt = (
        "You are an expert code reviewer. Return concise, deterministic feedback with corrected C++ code. "
        "Always include a code block and a 2-4 bullet rationale."
    )
    user_prompt = (
        "Task details:\n"
        f"task_id: {task_payload['task_id']}\n"
        f"difficulty: {task_payload['difficulty']}\n"
        f"instruction: {task_payload['task']}\n"
        f"code:\n{task_payload['code']}\n\n"
        "Output requirements:\n"
        "1) Provide corrected/refactored C++ code\n"
        "2) Mention complexity/security impact when relevant\n"
        "3) Keep response under 220 words"
    )

    response = client.chat.completions.create(
        model=model_name,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content or ""


def mock_review(task_id: str) -> str:
    if task_id == "easy_bug_fix":
        return (
            "```cpp\n"
            "int add(int a, int b){\n"
            "    return a + b;\n"
            "}\n"
            "```\n"
            "- Fixed subtraction bug by returning a + b.\n"
            "- Correctness is now consistent for positive, negative, and zero values."
        )

    if task_id == "medium_optimization":
        return (
            "```cpp\n"
            "int sum(vector<int> v){\n"
            "    int s = 0;\n"
            "    for(int i = 0; i < v.size(); i++){\n"
            "        s += v[i];\n"
            "    }\n"
            "    return s;\n"
            "}\n"
            "```\n"
            "- Removed the nested loop.\n"
            "- Time complexity improves from O(n^2) to O(n)."
        )

    return (
        "```cpp\n"
        "class User {\n"
        "private:\n"
        "    string name;\n"
        "    string passwordHash;\n"
        "public:\n"
        "    void setName(const string& n){ name = n; }\n"
        "    string getName() const { return name; }\n"
        "    void setPassword(const string& raw){ passwordHash = hash(raw); }\n"
        "    bool verifyPassword(const string& raw) const { return passwordHash == hash(raw); }\n"
        "};\n"
        "```\n"
        "- Uses encapsulation and avoids plaintext password storage.\n"
        "- Security and class design are improved."
    )


def log_line(tag: str, payload: Dict) -> None:
    print(f"[{tag}] {json.dumps(payload, separators=(',', ':'), sort_keys=False)}")


def run_baseline() -> Dict:
    client, model_name, mock_mode, mode_reason = resolve_client()
    env = OpenEnvCodeReviewEnvironment(max_steps=3)

    task_ids = ["easy_bug_fix", "medium_optimization", "hard_refactor_security"]
    task_scores: Dict[str, float] = {}
    run_id = str(uuid.uuid4())

    log_line(
        "START",
        {
            "run_id": run_id,
            "timestamp_utc": now_iso(),
            "model": model_name,
            "mock_mode": mock_mode,
            "mode_reason": mode_reason,
            "task_count": len(task_ids),
            "tasks": task_ids,
        },
    )

    for task_id in task_ids:
        observation = env.reset(task_id=task_id)
        review_text = mock_review(task_id) if mock_mode else llm_review(client, model_name, observation.model_dump())
        _, reward, done, info = env.step(Action(review=review_text))
        task_scores[task_id] = reward.total

        log_line(
            "STEP",
            {
                "run_id": run_id,
                "timestamp_utc": now_iso(),
                "task_id": task_id,
                "difficulty": observation.difficulty,
                "reward_total": round(reward.total, 4),
                "reward_breakdown": {
                    "correctness": round(reward.correctness, 4),
                    "optimization": round(reward.optimization, 4),
                    "readability": round(reward.readability, 4),
                    "formatting": round(reward.formatting, 4),
                    "penalty": round(reward.penalty, 4),
                },
                "passed_tests": info["passed_tests"],
                "total_tests": info["total_tests"],
                "done": done,
            },
        )

    avg_score = mean(task_scores.values()) if task_scores else 0.0
    result = {
        "run_id": run_id,
        "timestamp_utc": now_iso(),
        "average_score": round(avg_score, 4),
        "mock_mode": mock_mode,
        "mode_reason": mode_reason,
        "scores": {k: round(v, 4) for k, v in task_scores.items()},
    }
    log_line("END", result)
    return result


if __name__ == "__main__":
    run_baseline()
