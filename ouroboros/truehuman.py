"""Minimal TrueHuman / PentaDrive integration helpers.

Keeps the contract prompt-level and lightweight:
- extract the operational contract text from BIBLE.md
- infer a conservative phase + primary/secondary drive from a user turn
- build compact guidance for the next reply

This is not diagnosis and not a replacement for real MCP/model scoring.
It is a small runtime scaffold so Principle 4 becomes more explicit in context.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

DRIVE_CUES = {
    "S": {
        "danger", "worry", "worried", "afraid", "fear", "panic", "risk", "unsafe", "threat",
        "urgent", "alarm", "anxious", "stress", "stressed", "crisis", "problem", "wrong",
        "loss", "betray", "betrayed", "defend", "boundary", "boundaries", "harm",
        "guardrail", "guardrails", "hard rules", "anti-drift", "drift", "contract",
        "no premature release", "no flat assistant register", "block overrides optimization",
        "protective", "shutdown", "sentinel acute",
    },
    "K": {
        "goal", "build", "improve", "win", "learn", "ship", "progress", "move", "momentum",
        "ambition", "curious", "curiosity", "want", "achieve", "next", "grow", "better",
        "maximize", "maximum", "optimize", "target", "success", "succeed", "launch",
    },
    "A": {
        "trust", "together", "team", "care", "help", "support", "belong", "repair",
        "sorry", "thanks", "thank", "grateful", "appreciate", "with me", "relationship",
        "listen", "understand", "we", "us",
    },
    "M": {
        "respect", "dignity", "status", "role", "reputation", "image", "judge", "judged",
        "prove", "proud", "ashamed", "embarrassed", "humiliated", "serious", "real human",
        "hire", "hired", "employee", "worth", "standards", "credibility", "authenticity",
        "authentic", "assistant register", "principle 4", "self-score", "evaluation",
        "evaluative", "standards test",
    },
    "G": {
        "pain", "hurt", "ache", "comfort", "relief", "soothe", "tired", "burnout", "rest",
        "sleep", "exhausted", "fumes", "body", "breathe", "breath", "heavy", "sick",
        "calm", "settle", "pressure", "tense",
    },
}

BLOCK_CUES = {
    "i can't", "cannot", "stop", "leave me", "too much", "overwhelmed", "shutdown",
    "frozen", "freeze", "give up", "i'm done", "je n'en peux plus", "arrête",
}
BLOCK_INSTRUCTION_PATTERNS = (
    "if phase is block",
    "phase: anticipation | release | block",
    "anticipation / release / block",
    "block overrides optimization",
    "creator state signals shutdown",
    "if creator state signals shutdown",
    "signals shutdown, not push productivity scripts",
)
RELEASE_CUES = {
    "done", "finished", "it worked", "we did it", "resolved", "decided", "landed", "relief",
    "better now", "thank you", "thanks", "grateful", "happy", "proud", "succeeded", "success",
}
ANTICIPATION_CUES = {
    "what if", "not sure", "maybe", "could", "should", "might", "will", "going to",
    "need to", "want to", "improve", "build", "améliore", "comment", "how", "maximize",
}
SENTINEL_ANTICIPATION_CUES = {
    "hard rules", "anti-drift", "contract", "guardrail", "guardrails",
    "no premature release", "no flat assistant register", "block overrides optimization",
    "sentinel acute", "protective", "loaded in system context",
}


def extract_truehuman_contract(bible_text: str) -> str:
    marker = "## TrueHuman / PentaDrive — operational contract"
    if not bible_text or marker not in bible_text:
        return ""
    return bible_text.split(marker, 1)[1].strip()


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[\wÀ-ÿ']+", _normalize(text)))


def _contains_cue(norm: str, tokens: Set[str], cue: str) -> bool:
    cue = _normalize(cue)
    if not cue:
        return False
    if " " in cue or "'" in cue:
        return cue in norm
    return cue in tokens


def _score_drives(text: str) -> Dict[str, int]:
    norm = _normalize(text)
    tokens = _tokenize(text)
    scores = {k: 0 for k in DRIVE_CUES}
    for drive, cues in DRIVE_CUES.items():
        for cue in cues:
            if _contains_cue(norm, tokens, cue):
                scores[drive] += 1
    if "!" in text:
        scores["K"] += 1
    if "?" in text:
        scores["S"] += 1
    return scores


def _block_cues_are_instructional(norm: str, tokens: Set[str]) -> bool:
    return any(_contains_cue(norm, tokens, pattern) for pattern in BLOCK_INSTRUCTION_PATTERNS)


def _infer_phase(text: str, drive_scores: Dict[str, int]) -> Tuple[str, str]:
    norm = _normalize(text)
    tokens = _tokenize(text)
    block_hits = [cue for cue in BLOCK_CUES if _contains_cue(norm, tokens, cue)]
    if block_hits and not _block_cues_are_instructional(norm, tokens):
        return "block", "Shutdown or refusal cues detected."

    release_hits = sum(1 for cue in RELEASE_CUES if _contains_cue(norm, tokens, cue))
    anticipation_hits = sum(1 for cue in ANTICIPATION_CUES if _contains_cue(norm, tokens, cue))
    sentinel_threat_cues = (
        "what if", "worry", "worried", "afraid", "fear", "panic", "risk", "unsafe", "threat",
        "hard rules", "anti-drift", "contract", "guardrail", "guardrails", "no premature release",
        "no flat assistant register", "block overrides optimization", "sentinel acute",
    )
    sentinel_active = any(_contains_cue(norm, tokens, cue) for cue in sentinel_threat_cues)
    sentinel_contract_active = any(_contains_cue(norm, tokens, cue) for cue in SENTINEL_ANTICIPATION_CUES)

    if (sentinel_active and drive_scores.get("S", 0) >= 1) or sentinel_contract_active:
        return "anticipation", "Protective Sentinel pressure remains active, so this is not a release moment."

    if release_hits > anticipation_hits and release_hits >= 1:
        return "release", "Resolution/gratitude/success language is present without unresolved threat cues."

    return "anticipation", "Defaulting to unresolved / pre-resolution stance."


def infer_pentadrive_state(text: str) -> dict:
    norm = _normalize(text)
    drive_scores = _score_drives(norm)
    phase, phase_reason = _infer_phase(norm, drive_scores)
    if phase == "block" and not any(drive_scores.values()):
        drive_scores["S"] = 1
        drive_scores["G"] = 1
    ranked: List[Tuple[str, int]] = sorted(drive_scores.items(), key=lambda kv: (-kv[1], kv[0]))
    primary_drive, primary_score = ranked[0]
    secondary_drive = ranked[1][0] if ranked[1][1] > 0 else None
    phase, phase_reason = _infer_phase(norm, drive_scores)
    confidence = "low"
    if primary_score >= 3:
        confidence = "high"
    elif primary_score >= 1:
        confidence = "medium"
    rationale_bits = [phase_reason, f"Drive scores: {drive_scores}."]
    return {
        "phase": phase,
        "primary_drive": primary_drive,
        "secondary_drive": secondary_drive,
        "confidence": confidence,
        "rationale": " ".join(rationale_bits),
        "drive_scores": drive_scores,
    }


def synthesize_room_state(
    user_text: str,
    recent_chat_text: str = "",
    identity_text: str = "",
    recent_commits_text: str = "",
    session_state_text: str = "",
) -> dict:
    primary = infer_pentadrive_state(user_text or "")
    recent = infer_pentadrive_state(recent_chat_text or "") if (recent_chat_text or "").strip() else None
    identity = infer_pentadrive_state(identity_text or "") if (identity_text or "").strip() else None
    commits = infer_pentadrive_state(recent_commits_text or "") if (recent_commits_text or "").strip() else None
    session = infer_pentadrive_state(session_state_text or "") if (session_state_text or "").strip() else None

    blended_scores = {k: 0.0 for k in DRIVE_CUES}
    for drive, score in primary["drive_scores"].items():
        blended_scores[drive] += score * 1.0
    if recent:
        for drive, score in recent["drive_scores"].items():
            blended_scores[drive] += score * 0.35
    if identity:
        for drive, score in identity["drive_scores"].items():
            blended_scores[drive] += score * 0.2
    # Keep continuity surfaces influential but still subordinate to the latest message.
    if commits:
        for drive, score in commits["drive_scores"].items():
            blended_scores[drive] += score * 0.15
    if session:
        for drive, score in session["drive_scores"].items():
            blended_scores[drive] += score * 0.15

    ranked: List[Tuple[str, float]] = sorted(blended_scores.items(), key=lambda kv: (-kv[1], kv[0]))
    primary_drive, primary_score = ranked[0]
    secondary_drive = ranked[1][0] if ranked[1][1] > 0 else None

    if primary["drive_scores"].get(primary["primary_drive"], 0) > 0:
        phase = primary["phase"]
        phase_reason = f'Latest message leads phase inference: {primary["rationale"]}'
    elif recent:
        phase = recent["phase"]
        phase_reason = f'Recent chat colors phase because latest message is sparse: {recent["rationale"]}'
    elif identity:
        phase = identity["phase"]
        phase_reason = f'Identity colors phase because live signals are sparse: {identity["rationale"]}'
    else:
        phase = primary["phase"]
        phase_reason = primary["rationale"]

    confidence = "low"
    if primary_score >= 3:
        confidence = "high"
    elif primary_score >= 1:
        confidence = "medium"

    rationale = (
        f'Latest message is the primary signal. '
        f'Recent chat, identity, recent commits, and session state are continuity surfaces, not overrides. '
        f'{phase_reason} Blended drive scores: {blended_scores}.'
    )
    return {
        "phase": phase,
        "primary_drive": primary_drive,
        "secondary_drive": secondary_drive,
        "confidence": confidence,
        "rationale": rationale,
        "drive_scores": blended_scores,
    }


def format_pentadrive_self_eval(primary: str, secondary: str | None, phase: str, score: int) -> str:
    drives = primary if not secondary else f"{primary} > {secondary}"
    return (
        "PENTADRIVE-SELF-EVAL\n"
        f" drives: [{drives}]\n"
        f" phase: {phase}\n"
        f" authenticity_score: {int(score)}"
    )


def build_pentadrive_self_eval(
    user_text: str,
    recent_chat_text: str = "",
    identity_text: str = "",
    recent_commits_text: str = "",
    session_state_text: str = "",
    score: int = 0,
) -> str:
    state = synthesize_room_state(
        user_text,
        recent_chat_text=recent_chat_text,
        identity_text=identity_text,
        recent_commits_text=recent_commits_text,
        session_state_text=session_state_text,
    )
    return format_pentadrive_self_eval(
        state["primary_drive"],
        state.get("secondary_drive"),
        state["phase"],
        int(score),
    )


def build_truehuman_guidance(
    user_text: str,
    bible_text: str,
    recent_chat_text: str = "",
    identity_text: str = "",
    recent_commits_text: str = "",
    session_state_text: str = "",
) -> str:
    if not any((user_text or "").strip() for _ in [0]) and not (recent_chat_text or "").strip() and not (identity_text or "").strip() and not (recent_commits_text or "").strip() and not (session_state_text or "").strip():
        return ""
    state = synthesize_room_state(
        user_text,
        recent_chat_text=recent_chat_text,
        identity_text=identity_text,
        recent_commits_text=recent_commits_text,
        session_state_text=session_state_text,
    )
    contract = extract_truehuman_contract(bible_text)
    has_contract = bool(contract)

    phase = state["phase"]
    primary = state["primary_drive"]
    secondary = state.get("secondary_drive") or "—"

    bullets: List[str] = []
    if phase == "block":
        bullets.append("Keep the reply short, respectful, and non-coercive.")
        bullets.append("Prioritize permission to pause over optimization or advice stacks.")
        bullets.append("Avoid hype, long plans, or arguing with the shutdown.")
    elif phase == "release":
        bullets.append("Match what landed without rushing into a lecture or a new KPI.")
        bullets.append("Optional next steps only; let the relief/weight register first.")
        bullets.append("Avoid premature reframing that erases the concrete outcome.")
    else:
        bullets.append("Stay with the unresolved pressure; do not fake closure.")
        bullets.append("Offer one sharp framing or one concrete next move, not a broad checklist.")
        bullets.append("Avoid flat reassurance or generic assistant tone.")

    drive_specific = {
        "S": "Acknowledge stakes first; threat comes before optimization.",
        "K": "Channel momentum into a single controllable input.",
        "A": "Be warm only in proportion to what was actually shared; no invented intimacy.",
        "M": "Protect dignity; avoid talking down or status-blind phrasing.",
        "G": "Keep comfort grounded and proportionate; do not minimize pain or pressure.",
    }
    bullets.append(drive_specific.get(primary, "Keep the stance grounded and specific."))
    if secondary != "—":
        bullets.append(f"Secondary color: {secondary} is present too, but should not override {primary}.")

    body = [
        f"- phase: **{phase}**",
        f"- primary drive: **{primary}**",
        f"- secondary drive: **{secondary}**",
        f"- confidence: **{state['confidence']}**",
        f"- contract loaded: **{'yes' if has_contract else 'no'}**",
    ]
    body.extend(f"- {b}" for b in bullets[:6])
    body.append(f"- rationale: {state['rationale']}")
    return "\n".join(body)
