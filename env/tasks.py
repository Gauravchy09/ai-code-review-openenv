from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    title: str
    difficulty: str
    instruction: str
    starter_code: str
    expected_outcomes: List[str]


EASY_TASK = TaskDefinition(
    task_id="easy_bug_fix",
    title="Fix Arithmetic Bug",
    difficulty="easy",
    instruction=(
        "Find and fix the logic bug in the C++ function. Provide an improved code snippet "
        "and a short review summary."
    ),
    starter_code=(
        "int add(int a, int b){\n"
        "    return a - b;\n"
        "}\n"
    ),
    expected_outcomes=[
        "Identify subtraction bug",
        "Return a + b",
        "Maintain clean formatting",
    ],
)


MEDIUM_TASK = TaskDefinition(
    task_id="medium_optimization",
    title="Optimize Inefficient Summation",
    difficulty="medium",
    instruction=(
        "Optimize this function while preserving behavior. Provide revised code and explain "
        "time-complexity improvements."
    ),
    starter_code=(
        "int sum(vector<int> v){\n"
        "    int s=0;\n"
        "    for(int i=0;i<v.size();i++){\n"
        "        for(int j=0;j<v.size();j++){\n"
        "            s += v[i];\n"
        "        }\n"
        "    }\n"
        "    return s;\n"
        "}\n"
    ),
    expected_outcomes=[
        "Remove unnecessary nested loop",
        "Reduce time complexity to O(n)",
        "Preserve sum correctness",
    ],
)


HARD_TASK = TaskDefinition(
    task_id="hard_refactor_security",
    title="Refactor User Model for Security",
    difficulty="hard",
    instruction=(
        "Refactor for encapsulation and better security. Avoid storing plaintext password, "
        "and expose a cleaner class interface."
    ),
    starter_code=(
        "class User {\n"
        "public:\n"
        "    string name;\n"
        "    string password;\n"
        "};\n"
    ),
    expected_outcomes=[
        "Move sensitive fields to private",
        "Avoid plaintext password",
        "Provide setter/getter or verification method",
        "Improve class design",
    ],
)


TASKS: List[TaskDefinition] = [EASY_TASK, MEDIUM_TASK, HARD_TASK]
TASKS_BY_ID: Dict[str, TaskDefinition] = {task.task_id: task for task in TASKS}


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASKS_BY_ID:
        valid_ids = ", ".join(TASKS_BY_ID.keys())
        raise KeyError(f"Unknown task_id '{task_id}'. Valid values: {valid_ids}")
    return TASKS_BY_ID[task_id]
