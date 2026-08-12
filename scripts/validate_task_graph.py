from __future__ import annotations

try:  # script実行とpackage importの両方を支える。
    from .common import repo_root
    from .taskctl import collect_consistency_errors
except ImportError:  # pragma: no cover - 実行方法で分岐するだけ
    from common import repo_root
    from taskctl import collect_consistency_errors


def main() -> int:
    errors = collect_consistency_errors(repo_root(), check_task_files=True)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("タスクグラフ・キュー・タスク仕様・互換ミラー検証: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
