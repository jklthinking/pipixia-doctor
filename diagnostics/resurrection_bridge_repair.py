"""Repair playbook selection for PipiXia resurrection handoff failures."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RepairHint:
    symptom: str
    cause: str
    action: str
    destructive: bool = False

class BridgeRepairAdvisor:
    RULES = {
        "stream-idle": RepairHint("stream-idle", "agent emitted no events before timeout", "stop run, annotate card, ask user to resume with /resume or start /new"),
        "workspace-missing": RepairHint("workspace-missing", "bound cwd no longer exists", "switch session to default workspace and require explicit /cd for writes"),
        "jsonl-drift": RepairHint("jsonl-drift", "Codex JSONL contains unknown event types", "keep raw event non-terminal, log protocol drift, update translator tests"),
        "profile-cross-talk": RepairHint("profile-cross-talk", "lark-cli config dir inherited from another profile", "restart bridge with profile-local LARKSUITE_CLI_CONFIG_DIR"),
    }

    def advise(self, symptom: str) -> RepairHint:
        return self.RULES.get(symptom, RepairHint(symptom, "unknown", "run bridge doctor and collect sanitized logs"))

    def can_auto_apply(self, hint: RepairHint) -> bool:
        return not hint.destructive and hint.symptom in {"stream-idle", "jsonl-drift"}
