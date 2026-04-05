from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.environment import Action, OpenEnvCodeReviewEnvironment


def main() -> None:
    env = OpenEnvCodeReviewEnvironment(max_steps=3)
    task_ids = ["easy_bug_fix", "medium_optimization", "hard_refactor_security"]

    for task_id in task_ids:
        obs = env.reset(task_id=task_id)
        assert obs.task_id == task_id

        sample_action = Action(
            review=(
                "```cpp\n"
                "// Sample candidate review output\n"
                "```\n"
                "- Fixed logic\n"
            )
        )
        _, reward, done, info = env.step(sample_action)

        assert 0.0 <= reward.total <= 1.0
        assert isinstance(done, bool)
        assert "task_passed" in info

    print("pre_validate: OK")


if __name__ == "__main__":
    main()
