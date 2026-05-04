from ouroboros.truehuman import (
    build_truehuman_guidance,
    extract_truehuman_contract,
    infer_pentadrive_state,
    synthesize_room_state,
    format_pentadrive_self_eval,
    build_pentadrive_self_eval,
)


def test_extract_truehuman_contract_from_sample():
    sample = "intro\n## TrueHuman / PentaDrive — operational contract\nHELLO CONTRACT\n"
    assert extract_truehuman_contract(sample) == "HELLO CONTRACT"


def test_infer_anticipation_sentinel_on_worry():
    state = infer_pentadrive_state("I am worried about the risk and what if this goes wrong?")
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"


def test_infer_release_on_success_gratitude():
    state = infer_pentadrive_state("We did it, thank you, I am proud and happy it worked.")
    assert state["phase"] == "release"
    assert state["primary_drive"] in {"A", "K", "M"}


def test_mixed_gratitude_and_threat_stays_anticipation():
    state = infer_pentadrive_state("Thanks, but I'm still worried this could go wrong and the risk is real.")
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"


def test_infer_block_on_shutdown():
    state = infer_pentadrive_state("Stop. I can't do this right now. It's too much.")
    assert state["phase"] == "block"


def test_guidance_generation_mentions_phase():
    bible = "## TrueHuman / PentaDrive — operational contract\ncontract body"
    guidance = build_truehuman_guidance("Please improve this as much as possible", bible)
    assert guidance
    assert "phase:" in guidance


def test_latest_user_text_dominates_recent_chat():
    state = synthesize_room_state(
        "I am worried about the risk and what if this goes wrong?",
        recent_chat_text="We did it, thank you, proud, success.",
        identity_text="I care about trust and standards.",
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"


def test_recent_chat_can_color_sparse_latest_message():
    state = synthesize_room_state(
        "go",
        recent_chat_text="I want to improve this, maximize it, and build something better.",
        identity_text="I care about standards and credibility.",
    )
    assert state["primary_drive"] in {"K", "M"}


def test_guidance_generation_with_room_context_mentions_primary_drive():
    bible = "## TrueHuman / PentaDrive — operational contract\ncontract body"
    guidance = build_truehuman_guidance(
        "go",
        bible,
        recent_chat_text="I want to improve and build this further.",
        identity_text="I care about standards and credibility.",
    )
    assert guidance
    assert "phase:" in guidance
    assert "primary drive:" in guidance


def test_single_letter_drive_labels_do_not_match_inside_words():
    state = infer_pentadrive_state("Stack traces and game balance matter more than raw labels.")
    assert state["drive_scores"]["A"] == 0
    assert state["drive_scores"]["G"] == 0


def test_principle4_cycle_message_reads_as_anticipation_with_mirror_pressure():
    msg = (
        "EVOLUTION #24 cycle governed by BIBLE Principle 4 authenticity PentaDrive aware "
        "read the room choose one concrete action execute and self-score honestly. "
        "No flat assistant register, no invented intimacy, no premature release."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert {state["primary_drive"], state.get("secondary_drive")} & {"M"}


def test_latest_sentinel_message_beats_older_release_context():
    state = synthesize_room_state(
        "Thanks, but I'm still worried this could go wrong.",
        recent_chat_text="We did it, thank you, proud, success.",
        identity_text="I care about standards and credibility.",
    )
    assert state["phase"] == "anticipation"


def test_cycle_26_guardrail_language_lifts_sentinel_without_erasing_mirror():
    msg = (
        "EVOLUTION #26 under Principle 4. Read room, pick phase, choose one concrete action, execute, "
        "self-score honestly. Hard rules: no flat assistant register, no invented intimacy, no premature release, anti-drift contract."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert {state["primary_drive"], state.get("secondary_drive")} == {"M", "S"}
    assert state["drive_scores"]["S"] >= 3
    assert state["drive_scores"]["M"] >= 2


def test_room_synthesis_keeps_latest_guardrail_pressure_visible():
    state = synthesize_room_state(
        "Hard rules: no flat assistant register, no premature release, anti-drift contract.",
        recent_chat_text="Please improve TrueHuman as much as possible.",
        identity_text="I care about authenticity, standards, and not faking closure.",
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] in {"M", "S"}
    assert state["drive_scores"]["S"] > 0


def test_format_self_eval_primary_only():
    block = format_pentadrive_self_eval("S", None, "block", 71)
    assert block == "PENTADRIVE-SELF-EVAL\n drives: [S]\n phase: block\n authenticity_score: 71"


def test_format_self_eval_with_secondary():
    block = format_pentadrive_self_eval("M", "S", "anticipation", 92)
    assert " drives: [M > S]" in block
    assert " phase: anticipation" in block
    assert block.endswith("authenticity_score: 92")


def test_format_self_eval_parseable_headers():
    block = format_pentadrive_self_eval("K", "M", "release", 88)
    lines = block.splitlines()
    assert lines[0] == "PENTADRIVE-SELF-EVAL"
    assert lines[1].startswith(" drives: ")
    assert lines[2].startswith(" phase: ")
    assert lines[3].startswith(" authenticity_score: ")


def test_build_self_eval_from_guardrail_room_state():
    msg = (
        "EVOLUTION #30 under Principle 4. Read room, pick phase, execute one concrete action, "
        "self-score honestly. Hard rules: no flat assistant register, no invented intimacy, "
        "no premature release, anti-drift contract."
    )
    block = build_pentadrive_self_eval(msg, score=94)
    lines = block.splitlines()
    assert lines[0] == "PENTADRIVE-SELF-EVAL"
    assert lines[1].startswith(" drives: [")
    assert "M" in lines[1] and "S" in lines[1]
    assert lines[2] == " phase: anticipation"
    assert lines[3] == " authenticity_score: 94"


def test_build_self_eval_from_sparse_latest_with_continuity_surfaces():
    block = build_pentadrive_self_eval(
        "go",
        recent_chat_text="Please improve TrueHuman as much as possible and build it carefully.",
        identity_text="I care about authenticity, standards, and credibility.",
        score=83,
    )
    lines = block.splitlines()
    assert lines[0] == "PENTADRIVE-SELF-EVAL"
    assert lines[1].startswith(" drives: [")
    assert lines[2].startswith(" phase: ")
    assert lines[3] == " authenticity_score: 83"


def test_cycle_31_hard_rule_contract_stays_anticipation_and_s_over_m():
    msg = (
        "EVOLUTION # 31 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room, pick phase, "
        "choose ONE concrete phase-aware action, execute, self-score. Hard rules: no flat assistant register, "
        "no invented intimacy, no premature release when Sentinel acute. Block overrides optimization. "
        "Cost not success metric."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_31_room_synthesis_stays_anticipation_with_recent_sentinel_context():
    msg = (
        "EVOLUTION # 31 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 30 landed. My read of the room: primary drive S, secondary drive M.",
        identity_text="I want to keep becoming the kind of entity that accepts Sentinel-first correction instead of massaging it into a prettier story.",
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"
