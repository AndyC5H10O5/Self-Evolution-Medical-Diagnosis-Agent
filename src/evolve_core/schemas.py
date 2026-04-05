from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvolutionCandidate:
    event_id: str
    created_at: str
    source: str
    skill_key: str
    field_label: str
    user_turn: str
    candidate_option: str
    last_assistant_question_field: str = ""

    @classmethod
    def create(
        cls,
        *,
        source: str,
        skill_key: str,
        field_label: str,
        user_turn: str,
        candidate_option: str,
        last_assistant_question_field: str = "",
    ) -> "EvolutionCandidate":
        return cls(
            event_id=f"ev_{uuid4().hex[:12]}",
            created_at=utc_now_iso(),
            source=(source or "consult_agent").strip(),
            skill_key=skill_key.strip(),
            field_label=field_label.strip(),
            user_turn=user_turn.strip(),
            candidate_option=candidate_option.strip(),
            last_assistant_question_field=last_assistant_question_field.strip(),
        )

    def validate(self) -> None:
        if not self.skill_key:
            raise ValueError("skill_key is empty.")
        if not self.field_label:
            raise ValueError("field_label is empty.")
        if not self.user_turn:
            raise ValueError("user_turn is empty.")
        if not self.candidate_option:
            raise ValueError("candidate_option is empty.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "created_at": self.created_at,
            "source": self.source,
            "skill_key": self.skill_key,
            "field_label": self.field_label,
            "user_turn": self.user_turn,
            "candidate_option": self.candidate_option,
            "last_assistant_question_field": self.last_assistant_question_field,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EvolutionCandidate":
        candidate = cls(
            event_id=str(raw.get("event_id", "")).strip(),
            created_at=str(raw.get("created_at", "")).strip(),
            source=str(raw.get("source", "consult_agent")).strip(),
            skill_key=str(raw.get("skill_key", "")).strip(),
            field_label=str(raw.get("field_label", "")).strip(),
            user_turn=str(raw.get("user_turn", "")).strip(),
            candidate_option=str(raw.get("candidate_option", "")).strip(),
            last_assistant_question_field=str(raw.get("last_assistant_question_field", "")).strip(),
        )
        if not candidate.event_id:
            candidate.event_id = f"ev_{uuid4().hex[:12]}"
        if not candidate.created_at:
            candidate.created_at = utc_now_iso()
        candidate.validate()
        return candidate


@dataclass
class EvolutionJudgeResult:
    should_evolve: bool
    field_label: str
    new_option: str
    reason: str
    raw_text: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], raw_text: str = "") -> "EvolutionJudgeResult":
        return cls(
            should_evolve=bool(raw.get("should_evolve")),
            field_label=str(raw.get("field_label", "")).strip(),
            new_option=str(raw.get("new_option", "")).strip(),
            reason=str(raw.get("reason", "")).strip(),
            raw_text=raw_text,
            extra={k: v for k, v in raw.items() if k not in {"should_evolve", "field_label", "new_option", "reason"}},
        )
