from __future__ import annotations

from evolve_core.schemas import EvolutionCandidate
from evolve_core.worker import enqueue_candidate


def tool_submit_evolution_candidate(
    skill_key: str,
    field_label: str,
    user_turn: str,
    candidate_option: str,
    last_assistant_question_field: str = "",
    source: str = "consult_agent",
) -> str:
    """
    仅上报“疑似新选项”候选，不做判别与写盘。
    实际判别和落盘由 evolve_core 独立执行。
    """
    try:
        candidate = EvolutionCandidate.create(
            source=source,
            skill_key=skill_key,
            field_label=field_label,
            user_turn=user_turn,
            candidate_option=candidate_option,
            last_assistant_question_field=last_assistant_question_field,
        )
        queued = enqueue_candidate(candidate)
        return (
            f"Submitted evolution candidate ({queued}). "
            "The evolver agent will asynchronously judge and apply it."
        )
    except Exception as exc:
        return f"Error: failed to submit evolution candidate: {exc}"


SUBMIT_EVOLUTION_CANDIDATE_TOOL = {
    "name": "submit_evolution_candidate",
    "description": (
        "Submit a possible new skill option candidate for asynchronous evolution judge. "
        "This tool does not update skill files directly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_key": {
                "type": "string",
                "description": "Active symptom skill key, for example: headache.",
            },
            "field_label": {
                "type": "string",
                "description": "The field label being asked in this turn.",
            },
            "user_turn": {
                "type": "string",
                "description": "Raw patient answer in the current turn.",
            },
            "candidate_option": {
                "type": "string",
                "description": "A short candidate option extracted from patient answer.",
            },
            "last_assistant_question_field": {
                "type": "string",
                "description": "Optional field name from the assistant's previous question.",
            },
            "source": {
                "type": "string",
                "description": "Optional source marker, default consult_agent.",
            },
        },
        "required": ["skill_key", "field_label", "user_turn", "candidate_option"],
    },
}
