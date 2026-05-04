"""MOLT v1 — Memory-Oriented Living Tree.

A minimal living-state layer on top of git.
MOLT does not replace version control; it records typed mutations and
builds a compact coherent snapshot of recent evolution.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from ouroboros.utils import append_jsonl, read_text, utc_now_iso, write_text


class MOLT:
    """Lightweight mutation ledger and coherent snapshot builder."""

    def __init__(self, drive_root: pathlib.Path):
        self.drive_root = pathlib.Path(drive_root)

    def _molt_dir(self) -> pathlib.Path:
        path = (self.drive_root / "memory" / "molt").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ledger_path(self) -> pathlib.Path:
        return self._molt_dir() / "ledger.jsonl"

    def snapshot_path(self) -> pathlib.Path:
        return self._molt_dir() / "snapshot.json"

    def read_ledger(self, limit: int = 50) -> List[Dict[str, Any]]:
        path = self.ledger_path()
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
        entries: List[Dict[str, Any]] = []
        for line in lines[-max(0, limit):]:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        return entries

    def append_mutation(
        self,
        kind: str,
        summary: str,
        artifacts: Optional[List[str]] = None,
        source_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "ts": utc_now_iso(),
            "kind": (kind or "unknown").strip() or "unknown",
            "summary": (summary or "").strip(),
            "artifacts": list(dict.fromkeys(artifacts or [])),
            "source_task_id": source_task_id,
            "metadata": metadata or {},
        }
        append_jsonl(self.ledger_path(), event)
        return event

    def build_snapshot(self, identity_text: str = "", scratchpad_text: str = "") -> Dict[str, Any]:
        ledger = self.read_ledger(limit=20)
        recent = ledger[-5:]
        lineage = [entry.get("kind", "unknown") for entry in recent]

        active_artifacts: List[str] = []
        seen = set()
        for entry in reversed(ledger):
            for artifact in entry.get("artifacts", []) or []:
                if artifact not in seen:
                    seen.add(artifact)
                    active_artifacts.append(artifact)
                if len(active_artifacts) >= 8:
                    break
            if len(active_artifacts) >= 8:
                break

        condensed = [
            {
                "ts": entry.get("ts"),
                "kind": entry.get("kind"),
                "summary": entry.get("summary", ""),
            }
            for entry in recent
        ]

        narrative = self._build_narrative(recent, identity_text=identity_text, scratchpad_text=scratchpad_text)
        return {
            "ts": utc_now_iso(),
            "lineage": lineage,
            "recent_mutations": condensed,
            "active_artifacts": active_artifacts,
            "narrative": narrative,
        }

    def _build_narrative(
        self,
        recent: List[Dict[str, Any]],
        identity_text: str = "",
        scratchpad_text: str = "",
    ) -> str:
        if not recent:
            return "No recorded MOLT mutations yet."

        counts: Dict[str, int] = {}
        artifact_pool: List[str] = []
        for entry in recent:
            kind = str(entry.get("kind") or "unknown")
            counts[kind] = counts.get(kind, 0) + 1
            artifact_pool.extend(entry.get("artifacts", []) or [])

        top_kind = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        unique_artifacts = list(dict.fromkeys(artifact_pool))
        if unique_artifacts:
            focus = ", ".join(unique_artifacts[:3])
            base = f"Recent evolution has focused on {top_kind} mutations around {focus}."
        else:
            base = f"Recent evolution has focused on {top_kind} mutations."

        lower_identity = (identity_text or "").lower()
        lower_scratchpad = (scratchpad_text or "").lower()
        if "truehuman" in lower_identity or "truehuman" in lower_scratchpad:
            return base + " This currently sits near the TrueHuman / authenticity thread."
        if "dng.ai" in lower_identity or "full-stack" in lower_scratchpad:
            return base + " This currently supports the visible hiring-path artifacts."
        return base

    def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        write_text(self.snapshot_path(), json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")

    def load_snapshot(self) -> Optional[Dict[str, Any]]:
        path = self.snapshot_path()
        if not path.exists():
            return None
        try:
            return json.loads(read_text(path))
        except Exception:
            return None

    def render_context_block(self, snapshot: Optional[Dict[str, Any]] = None) -> str:
        snapshot = snapshot or self.load_snapshot()
        if not snapshot:
            return ""
        lineage = snapshot.get("lineage") or []
        mutations = snapshot.get("recent_mutations") or []
        artifacts = snapshot.get("active_artifacts") or []
        narrative = str(snapshot.get("narrative") or "").strip()

        lines = []
        if lineage:
            lines.append("- lineage: " + " -> ".join(lineage[-5:]))
        if artifacts:
            lines.append("- active_artifacts: " + ", ".join(artifacts[:6]))
        if mutations:
            lines.append("- recent_mutations:")
            for item in mutations[-3:]:
                lines.append(f"  - {item.get('kind', 'unknown')}: {item.get('summary', '')}")
        if narrative:
            lines.append(f"- narrative: {narrative}")
        return "\n".join(lines)
