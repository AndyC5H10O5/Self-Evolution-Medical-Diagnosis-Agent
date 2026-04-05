from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from evolve_core.schemas import EvolutionCandidate

# 项目根目录: .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME_DIR = PROJECT_ROOT / "runtime" / "evolution"
QUEUE_FILE = RUNTIME_DIR / "candidates.jsonl"
STATE_FILE = RUNTIME_DIR / "consumer_state.json"


def _ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def enqueue_candidate(candidate: EvolutionCandidate) -> str:
    candidate.validate()
    _ensure_runtime_dir()
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(candidate.to_dict(), ensure_ascii=False) + "\n")
    return f"queued:{candidate.event_id}"


class FileQueueConsumer:
    def __init__(self, poll_seconds: float = 1.0) -> None:
        self.poll_seconds = poll_seconds
        self._last_line = self._load_state_line()

    def _load_state_line(self) -> int:
        _ensure_runtime_dir()
        if not STATE_FILE.exists():
            return 0
        try:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            line = int(raw.get("last_line", 0))
            return max(0, line)
        except Exception:
            return 0

    def _save_state_line(self, line_no: int) -> None:
        _ensure_runtime_dir()
        payload = {"last_line": max(0, line_no)}
        STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _iter_unconsumed(self) -> list[tuple[int, EvolutionCandidate]]:
        if not QUEUE_FILE.exists():
            return []

        rows: list[tuple[int, EvolutionCandidate]] = []
        with QUEUE_FILE.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if line_no <= self._last_line:
                    continue
                text = line.strip()
                if not text:
                    self._last_line = line_no
                    self._save_state_line(self._last_line)
                    continue
                try:
                    raw = json.loads(text)
                    candidate = EvolutionCandidate.from_dict(raw)
                except Exception:
                    self._last_line = line_no
                    self._save_state_line(self._last_line)
                    continue
                rows.append((line_no, candidate))
        return rows

    def run_forever(self, handler: Callable[[EvolutionCandidate], None]) -> None:
        while True:
            pending = self._iter_unconsumed()
            if not pending:
                time.sleep(self.poll_seconds)
                continue

            for line_no, candidate in pending:
                try:
                    handler(candidate)
                finally:
                    self._last_line = line_no
                    self._save_state_line(self._last_line)
