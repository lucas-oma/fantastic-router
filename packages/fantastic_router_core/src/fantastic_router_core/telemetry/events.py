from dataclasses import dataclass
from typing import Any

@dataclass
class PlannedActionEvent:
    query: str
    actions: list[dict]
    user_id: str | None

def emit(event: Any) -> None:
    # OSS: no-op (can log); ENT overrides to send to queue/db
    pass


# TODO add to readme: Document /api/plan, action schema, and explicitly state: “Feedback ranking & personalization are available in the Enterprise edition.”

