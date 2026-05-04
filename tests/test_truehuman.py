from ouroboros.truehuman import (
    build_truehuman_guidance,
    extract_truehuman_contract,
    infer_pentadrive_state,
    synthesize_room_state,
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
