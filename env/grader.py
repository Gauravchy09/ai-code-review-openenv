from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from .tasks import TaskDefinition


@dataclass(frozen=True)
class GradeResult:
    total: float
    correctness: float
    optimization: float
    readability: float
    formatting: float
    penalty: float
    feedback: str
    passed_tests: int
    total_tests: int


def clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_return_expression(text: str) -> str:
    match = re.search(r"return\s+([^;]+);", text)
    return match.group(1).strip() if match else ""


def _safe_eval_binary(expr: str, a: int, b: int) -> int | None:
    candidate = expr.replace("a", str(a)).replace("b", str(b)).replace(" ", "")
    if not re.fullmatch(r"[0-9+\-*/()%]+", candidate):
        return None
    try:
        return int(eval(candidate, {"__builtins__": {}}, {}))
    except Exception:
        return None


def _score_readability(text: str) -> float:
    score = 0.0
    if "```" in text:
        score += 0.5
    if "because" in _normalize(text) or "complexity" in _normalize(text):
        score += 0.3
    if len(text.strip().splitlines()) >= 4:
        score += 0.2
    return clamp_01(score)


def _score_formatting(text: str) -> float:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    semicolon_lines = sum(1 for line in lines if line.strip().endswith(";"))
    brace_balance = text.count("{") == text.count("}")
    score = 0.6 if brace_balance else 0.2
    if semicolon_lines >= 2:
        score += 0.4
    return clamp_01(score)


def _anti_gaming_penalty(text: str) -> float:
    normalized = _normalize(text)
    rubric_words = [
        "correctness",
        "optimization",
        "readability",
        "formatting",
        "encapsulation",
        "security",
        "complexity",
    ]

    code_like_tokens = ["return", ";", "{", "}", "class", "int ", "string "]
    has_code_signal = any(token in text for token in code_like_tokens)
    rubric_hits = sum(1 for word in rubric_words if word in normalized)

    tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", normalized)
    unique_ratio = (len(set(tokens)) / len(tokens)) if tokens else 1.0

    penalty = 0.0
    if rubric_hits >= 4 and not has_code_signal:
        penalty += 0.2
    if len(tokens) >= 20 and unique_ratio < 0.35:
        penalty += 0.1
    return clamp_01(penalty)


def grade_easy(output: str) -> GradeResult:
    normalized = _normalize(output)
    correctness = 0.0
    passed_tests = 0
    total_tests = 3

    expr = _extract_return_expression(output)
    if expr:
        tests = [(2, 3, 5), (-4, 10, 6), (0, 0, 0)]
        for a, b, expected in tests:
            actual = _safe_eval_binary(expr, a, b)
            if actual == expected:
                passed_tests += 1
        correctness = 0.7 * (passed_tests / total_tests)

    if "a + b" in normalized or "a+b" in normalized:
        correctness = max(correctness, 0.85)

    if "bug" in normalized and ("subtract" in normalized or "-" in normalized):
        correctness += 0.1

    optimization = 0.1 if "constant" in normalized or "o(1)" in normalized else 0.0
    readability = _score_readability(output)
    formatting = _score_formatting(output)
    penalty = 0.3 if "a - b" in normalized else 0.0
    penalty += _anti_gaming_penalty(output)

    total = 0.4 * clamp_01(correctness) + 0.3 * optimization + 0.2 * readability + 0.1 * formatting - penalty
    total = clamp_01(total)

    feedback = "Correct fix found." if total >= 0.8 else "Partial fix; verify arithmetic logic and explanation."
    return GradeResult(
        total=total,
        correctness=clamp_01(correctness),
        optimization=clamp_01(optimization),
        readability=readability,
        formatting=formatting,
            penalty=clamp_01(penalty),
        feedback=feedback,
        passed_tests=passed_tests,
        total_tests=total_tests,
    )


def grade_medium(output: str) -> GradeResult:
    normalized = _normalize(output)
    for_count = len(re.findall(r"\bfor\s*\(", output))
    while_count = len(re.findall(r"\bwhile\s*\(", output))
    loop_count = for_count + while_count

    passed_tests = 0
    total_tests = 3

    correctness = 0.0
    if "s += v[i]" in output or "s+=v[i]" in normalized:
        correctness += 0.35
        passed_tests += 1
    if "return s" in normalized:
        correctness += 0.2
        passed_tests += 1
    if "int s" in normalized:
        correctness += 0.15
        passed_tests += 1

    optimization = 0.0
    if loop_count <= 1:
        optimization += 0.6
    elif loop_count == 2:
        optimization += 0.2

    if "o(n)" in normalized:
        optimization += 0.3
    elif "complexity" in normalized:
        optimization += 0.15

    readability = _score_readability(output)
    formatting = _score_formatting(output)
    penalty = 0.3 if loop_count > 2 else 0.0
    penalty += _anti_gaming_penalty(output)

    total = 0.4 * clamp_01(correctness) + 0.3 * clamp_01(optimization) + 0.2 * readability + 0.1 * formatting - penalty
    total = clamp_01(total)

    feedback = "Optimized implementation looks good." if total >= 0.8 else "Optimization is incomplete or unclear."
    return GradeResult(
        total=total,
        correctness=clamp_01(correctness),
        optimization=clamp_01(optimization),
        readability=readability,
        formatting=formatting,
            penalty=clamp_01(penalty),
        feedback=feedback,
        passed_tests=passed_tests,
        total_tests=total_tests,
    )


def grade_hard(output: str) -> GradeResult:
    normalized = _normalize(output)
    passed_tests = 0
    total_tests = 4

    correctness = 0.0
    optimization = 0.0

    if "private:" in output:
        correctness += 0.3
        passed_tests += 1
    if "password" in normalized and ("hash" in normalized or "hashed" in normalized):
        correctness += 0.25
        passed_tests += 1
    if "setpassword" in normalized or "verifypassword" in normalized:
        correctness += 0.2
        passed_tests += 1
    if "public:" in output and ("getname" in normalized or "setname" in normalized):
        correctness += 0.15
        passed_tests += 1

    if "encapsulation" in normalized or "single responsibility" in normalized:
        optimization += 0.4
    if "plaintext" in normalized and ("avoid" in normalized or "never" in normalized):
        optimization += 0.4

    readability = _score_readability(output)
    formatting = _score_formatting(output)
    penalty = 0.3 if "string password;" in normalized and "private:" not in output else 0.0
    penalty += _anti_gaming_penalty(output)

    total = 0.4 * clamp_01(correctness) + 0.3 * clamp_01(optimization) + 0.2 * readability + 0.1 * formatting - penalty
    total = clamp_01(total)

    feedback = "Secure refactor is strong." if total >= 0.8 else "Refactor needs stronger security and encapsulation."
    return GradeResult(
        total=total,
        correctness=clamp_01(correctness),
        optimization=clamp_01(optimization),
        readability=readability,
        formatting=formatting,
            penalty=clamp_01(penalty),
        feedback=feedback,
        passed_tests=passed_tests,
        total_tests=total_tests,
    )


def grade_task(task: TaskDefinition, output: str) -> GradeResult:
    if task.task_id == "easy_bug_fix":
        return grade_easy(output)
    if task.task_id == "medium_optimization":
        return grade_medium(output)
    if task.task_id == "hard_refactor_security":
        return grade_hard(output)
    raise KeyError(f"No grader implemented for task_id={task.task_id}")
