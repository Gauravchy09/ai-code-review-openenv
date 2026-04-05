---
title: AI Code Review OpenEnv
emoji: "🤖"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - code-review
base_path: /web
---

# AI Code Review Environment (OpenEnv)

A real-world OpenEnv environment that simulates professional code review workflows.

The agent receives buggy or low-quality code, submits review feedback and fixed code, and gets a shaped reward from deterministic graders. This project is designed for OpenEnv Round 1 evaluation criteria: utility, grader quality, reward quality, reproducibility, and deployment readiness.

## Why this environment is useful

Code review is a daily engineering workflow with measurable quality outcomes:
- correctness of fixes
- optimization quality
- secure design choices
- explanation clarity

This environment can train/evaluate agentic reviewers instead of toy-game policies.

## Environment API

The environment follows the standard API:

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, done, info]`
- `state() -> dict`

### Typed Models

Pydantic models are used for full typed compliance:
- `Observation`
- `Action`
- `Reward`

## Observation / Action Spaces

### Observation

```json
{
  "code": "...",
  "task_id": "easy_bug_fix",
  "task": "Find and fix the logic bug...",
  "difficulty": "easy",
  "expected_outcomes": ["..."],
  "steps_taken": 0,
  "max_steps": 3,
  "review_history": []
}
```

### Action

```json
{
  "review": "Agent review + fixed code"
}
```

### Reward

```json
{
  "total": 0.0,
  "correctness": 0.0,
  "optimization": 0.0,
  "readability": 0.0,
  "formatting": 0.0,
  "penalty": 0.0
}
```

## Task Set (Easy -> Medium -> Hard)

1. **easy_bug_fix**
- Input has arithmetic bug (`a - b` instead of `a + b`)
- Grader checks bug identification + fixed code + mini test validation

2. **medium_optimization**
- Input has nested loop inefficiency
- Grader checks loop reduction, complexity rationale, and correctness signals

3. **hard_refactor_security**
- Input stores plaintext password publicly
- Grader checks encapsulation, password-handling improvements, and design quality

## Deterministic Graders + Test Case Validation

Each task has a deterministic grader returning a score in `[0.0, 1.0]`.

Shaped reward design:
- `+0.4` correctness
- `+0.3` optimization/security
- `+0.2` readability
- `+0.1` formatting
- `-0.3` wrong/destructive logic

The easy grader includes explicit hidden-style validation with arithmetic test cases.

## Baseline Inference Script

`inference.py` uses OpenAI client and evaluates all 3 tasks.

Required environment variables:
- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Optional environment variable:
- `LOCAL_IMAGE_NAME` (if you use docker-based local image flows)

If no credentials are present, `inference.py` automatically runs in deterministic mock mode to avoid runtime failure.

Optional local dry-run variable:
- `MOCK_INFERENCE=1` (runs deterministic mock reviews without external API calls)

### Structured stdout format

The script emits strict tagged logs:
- `[START] {...}`
- `[STEP] {...}`
- `[END] {...}`

## Local Setup

```bash
pip install -r requirements.txt
```

Run API server:

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

Round 1 local command (OpenEnv-style):

```bash
uv run server
```

Run baseline:

```bash
python inference.py
```

Run deterministic local baseline (no API call):

```bash
MOCK_INFERENCE=1 python inference.py
```

Run one-command pre-submission gate:

```bash
python scripts/pre_submit.py
```

## Docker

Build:

```bash
docker build -t code-review-openenv .
```

Run:

```bash
docker run --rm -p 7860:7860 code-review-openenv
```

## Hugging Face Space Deployment

- Create a **Docker Space**
- Add this repository
- Add environment variables: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
- Ensure Space has tag: `openenv`
- Health route: `/health`

Round 1 push command:

```bash
openenv push --repo-id your-username/my-env
```

## openenv.yaml

`openenv.yaml` is included with:
- metadata
- typed model paths
- task metadata
- API route map
- deterministic validation settings

## Suggested pre-submission checks

1. `python scripts/pre_submit.py` passes
2. `docker build` succeeds
3. container serves `/health`, `/reset`, `/step`, `/state`
4. baseline script runs end-to-end under 20 minutes
5. graders return bounded values in `[0.0, 1.0]`
6. all 3 tasks execute with reproducible scoring behavior
