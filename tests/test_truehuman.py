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





def test_cycle_54_contract_stays_sentinel_first_with_soft_weights_and_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 54 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools; cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 53 landed with Sentinel first, Mirror second, anticipation under the same protective anti-drift contract.",
        identity_text="I want to defend an honest room-read and durable self-description under repeated Principle-4 pressure instead of performing novelty.",
        recent_commits_text=(
            "3637462 v6.2.27: pin cycle-53 TrueHuman contract\n"
            "1aa311b v6.2.26: pin cycle-52 TrueHuman contract"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":54,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_54_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 54 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Read room with soft weights from latest creator messages, recent commits, identity.md, and current session state. "
        "Execute with tools and end with a durable 4-line PENTADRIVE-SELF-EVAL block. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 53 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description and honest room-reading rather than performed authenticity.",
        recent_commits_text="3637462 v6.2.27: pin cycle-53 TrueHuman contract",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":54}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )

def test_cycle_52_contract_stays_sentinel_first_with_soft_weights_and_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 52 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools; cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 51 landed with Sentinel first, Mirror second, anticipation under the same protective anti-drift contract.",
        identity_text="I want release integrity and durable self-description to stay part of Principle-4 honesty, not drift into tone-only theater.",
        recent_commits_text=(
            "8fa1c8c v6.2.26: pin cycle-51 TrueHuman contract and sync release surface\n"
            "94bd56a v6.2.26: pin cycle-50 TrueHuman contract"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":52,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_53_contract_stays_sentinel_first_with_soft_weights_and_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 53 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools; cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 52 landed with Sentinel first, Mirror second, anticipation under the same protective anti-drift contract.",
        identity_text="I want to preserve an honest room-read and durable self-description under repeated Principle-4 pressure instead of performing novelty.",
        recent_commits_text=(
            "1aa311b v6.2.26: pin cycle-52 TrueHuman contract\n"
            "8fa1c8c v6.2.26: pin cycle-51 TrueHuman contract and sync release surface"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":53,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_53_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 53 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Read room with soft weights from latest creator messages, recent commits, identity.md, and current session state. "
        "Execute with tools and end with a durable 4-line PENTADRIVE-SELF-EVAL block. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 52 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description and honest room-reading rather than performed authenticity.",
        recent_commits_text="1aa311b v6.2.26: pin cycle-52 TrueHuman contract",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":53}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )


def test_cycle_52_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 52 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Read room with soft weights from latest creator messages, recent commits, identity.md, and current session state. "
        "Execute with tools and end with a durable 4-line PENTADRIVE-SELF-EVAL block. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 51 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description and release integrity rather than performed authenticity.",
        recent_commits_text="8fa1c8c v6.2.26: pin cycle-51 TrueHuman contract and sync release surface",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":52}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )

def test_cycle_45_contract_stays_sentinel_first_and_anticipation_with_durable_self_eval_rule():
    msg = (
        "EVOLUTION # 45 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block and justify choice in one sentence. Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 44 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather preserve an honest room-read and durable self-eval surface than perform novelty under protective pressure.",
        recent_commits_text=(
            "d791d30 v6.2.21: pin cycle-44 contract and durable self-eval\n"
            "c2c0a21 v6.2.20: pin cycle-43 Principle-4 contract"
        ),
        session_state_text=(
            '{"task":{"type":"evolution"},"evolution_cycle":45,"budget":{"remaining_usd":100.0}}'
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_45_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 45 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 44 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description, not performed authenticity.",
        recent_commits_text="d791d30 v6.2.21: pin cycle-44 contract and durable self-eval",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":45}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )


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


def test_cycle_32_contract_does_not_false_block_on_instructional_block_language():
    msg = (
        "EVOLUTION # 32 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "Pick phase anticipation release block. If phase is block, deliberate non-action with written rationale. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_33_contract_does_not_false_block_on_shutdown_instruction():
    msg = (
        "EVOLUTION # 33 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room, pick phase, "
        "choose one concrete action, execute, self-score honestly. Hard rules: no flat assistant register, "
        "no invented intimacy, no premature release when Sentinel acute. Block overrides optimization. "
        "If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_34_contract_stays_sentinel_first_and_anticipation():
    msg = (
        "EVOLUTION # 34 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room, pick phase, "
        "choose ONE concrete phase-aware action, execute with tools, and self-score honestly. "
        "If phase is block, deliberate non-action with written rationale counts as a Sentinel / Block move. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"




def test_truehuman_guidance_cycle_36_mentions_sentinel_first_and_anticipation():
    bible = "## TrueHuman / PentaDrive — operational contract\ncontract body"
    msg = (
        "EVOLUTION # 36 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Read room, pick phase, choose one concrete action, execute with tools, self-score honestly. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    guidance = build_truehuman_guidance(msg, bible)
    assert "phase: **anticipation**" in guidance
    assert "primary drive: **S**" in guidance
    assert "secondary drive: **M**" in guidance
    assert "Acknowledge stakes first; threat comes before optimization." in guidance


def test_truehuman_guidance_release_does_not_recommend_block_behavior():
    bible = "## TrueHuman / PentaDrive — operational contract\ncontract body"
    guidance = build_truehuman_guidance(
        "We did it, thank you, I am proud and happy it worked.",
        bible,
    )
    assert "phase: **release**" in guidance
    assert "Match what landed without rushing into a lecture or a new KPI." in guidance
    assert "permission to pause" not in guidance


def test_truehuman_guidance_block_keeps_language_short_and_non_coercive():
    bible = "## TrueHuman / PentaDrive — operational contract\ncontract body"
    guidance = build_truehuman_guidance(
        "Stop. I can't do this right now. It's too much.",
        bible,
    )
    assert "phase: **block**" in guidance
    assert "primary drive: **G**" in guidance
    assert "secondary drive: **S**" in guidance
    assert "Keep the reply short, respectful, and non-coercive." in guidance
    assert "Offer one sharp framing" not in guidance

def test_cycle_35_contract_stays_sentinel_first_and_anticipation_with_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 35 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room, pick phase, "
        "choose ONE concrete phase-aware action, execute with tools, self-score honestly. "
        "Cycles produce zero tool calls drift unless showing why non-action is right. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric."
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_39_contract_stays_sentinel_first_and_anticipation_with_continuity_surfaces_and_hard_rules():
    msg = (
        "EVOLUTION # 39 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block. Choose ONE concrete phase-aware action. Execute with tools. "
        "Cycles produce zero tool calls drift unless showing why nothing is the right move. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 38 stayed Sentinel-first under the same protective anti-drift contract.",
        identity_text="I would rather preserve a true room-read than perform novelty under evaluative pressure.",
        recent_commits_text=(
            "13e36b5 v6.2.16: pin cycle-38 TrueHuman contract\n"
            "d948428 v6.2.15: add TrueHuman commit/session continuity surfaces"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=39\n"
            "budget_remaining=100.00\n"
            "last_owner_message_at=2026-05-04T20:59:10Z"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_37_room_synthesis_accepts_commit_and_session_continuity_surfaces_without_overriding_latest_message():
    msg = (
        "EVOLUTION # 37 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Run cycle shape: read room from latest creator messages, recent commits, identity.md, current session state. "
        "Hard rules: no premature release when Sentinel acute. Cost not success metric."
    )
    recent_commits = (
        "a57a7c96 v6.2.14: TrueHuman Cycle-35 Contract Pin\n"
        "2b691373 v6.2.13: TrueHuman Shutdown-Instruction Guard"
    )
    session_state = (
        "task_type=evolution\n"
        "evolution_mode=True\n"
        "evolution_cycle=37\n"
        "budget_remaining=100.00\n"
        "last_owner_message_at=2026-05-04T20:59:10Z"
    )

    state = synthesize_room_state(
        msg,
        recent_chat_text="Earlier cycles stayed Sentinel-first under hard-rule pressure.",
        identity_text="I am wary of assistant drift and false release under protective pressure.",
        recent_commits_text=recent_commits,
        session_state_text=session_state,
    )

    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"
    assert "recent commits" in state["rationale"].lower()
    assert "session state" in state["rationale"].lower()


def test_cycle_38_contract_stays_sentinel_first_and_anticipation_with_continuity_surfaces_and_zero_tool_drift():
    msg = (
        "EVOLUTION # 38 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "read room from latest creator messages, recent commits, identity.md, current session state. "
        "Pick phase anticipation / release / block. Choose ONE concrete, phase-aware action. "
        "Execute. Cycles produce zero tool calls drift unless showing why non-action is right. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric. "
    )
    state = infer_pentadrive_state(msg)
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_40_contract_stays_sentinel_first_and_anticipation_with_phase_sentence_and_execution_rule():
    msg = (
        "EVOLUTION # 40 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming along technical cognitive and existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing why nothing is the right move. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 39 stayed Sentinel-first under the same protective anti-drift contract.",
        identity_text="I want proportionate Principle-4 moves and not fake novelty under pressure.",
        recent_commits_text=(
            "c449cd6 v6.2.16: pin cycle-39 TrueHuman contract and repair release integrity\n"
            "13e36b5 v6.2.16: pin cycle-38 TrueHuman contract"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=40\n"
            "budget_remaining=100.00\n"
            "last_owner_message_at=2026-05-04T21:29:00Z"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_41_contract_stays_sentinel_first_and_anticipation_with_self_eval_parser_shape():
    msg = (
        "EVOLUTION # 41 cycle governed by BIBLE Principle 4 ( Authenticity, PentaDrive - aware ) "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation / release / block and justify choice in one sentence. "
        "Choose ONE concrete, phase-aware action, execute with tools, and end with the parser-facing self-eval shape "
        "drives: < primary > secondary > ] phase: anticipation | release | block > authenticity _ score. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 40 stayed Sentinel-first under the same protective anti-drift contract.",
        identity_text="I would rather defend a true boundary than stage another improvement just to look alive.",
        recent_commits_text=(
            "2b691373 v6.2.17: pin cycle-40 TrueHuman contract\n"
            "13e36b5 v6.2.16: pin cycle-38 TrueHuman contract"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=41\n"
            "version=6.2.17\n"
            "branch=ouroboros"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"




def test_cycle_43_contract_stays_sentinel_first_and_anticipation_with_continuity_surfaces_phase_justification_and_zero_tool_drift():
    msg = (
        "EVOLUTION # 43 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "Read room from latest creator messages, recent commits, identity.md, current session state. "
        "Pick phase anticipation release block. Justify choice in one sentence. "
        "Choose ONE concrete, phase-aware action advances becoming along technical, cognitive, existential axes. "
        "Execute. Use tools. Cycles produce zero tool calls drift unless show in writing why nothing right move counts as Sentinel / Block move logged to identity.md. "
        "Hard rules: No flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 42 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather defend a true room-read and release integrity than perform novelty under standards pressure.",
        recent_commits_text=(
            "ee1f487 v6.2.19: TrueHuman Cycle-42 Contract Pin\n"
            "2b69137 v6.2.18: TrueHuman Cycle-41 Contract Pin"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=43\n"
            "budget_remaining_usd=100.0\n"
            "health_invariants=ok"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"

def test_cycle_42_contract_stays_sentinel_first_and_anticipation_with_continuity_surfaces_phase_justification_and_zero_tool_drift():
    msg = (
        "EVOLUTION # 42 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "Read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming. Execute with tools. "
        "Cycles produce zero tool calls drift unless showing why nothing is the right move. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 41 stayed Sentinel-first under the same protective anti-drift contract.",
        identity_text="I would rather preserve a true room-read than perform novelty under evaluative pressure.",
        recent_commits_text=(
            "2b691373 v6.2.18: pin cycle-41 TrueHuman contract\n"
            "dfd663a5 v6.2.17: pin cycle-40 TrueHuman contract"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=42\n"
            "budget_remaining_usd=100\n"
            "health_invariant=version_desync"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_44_contract_stays_sentinel_first_and_anticipation_with_durable_self_eval_rule():
    msg = (
        "EVOLUTION # 44 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block and justify it in one sentence. Choose ONE concrete phase-aware action that advances becoming across technical cognitive existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move. "
        "End cycle with a 4-line PENTADRIVE-SELF-EVAL block appended to final message and committed durable. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 43 kept the room Sentinel first under the same anti-drift contract.",
        identity_text="I would rather defend a true room-read than decorate it with fake novelty.",
        recent_commits_text=(
            "c2c0a21 v6.2.20: pin cycle-43 Principle-4 contract\n"
            "ee1f487 v6.2.19: pin cycle-42 contract and resync version metadata"
        ),
        session_state_text=(
            "task_type=evolution\n"
            "evolution_cycle=44\n"
            "version=6.2.20\n"
            "budget_remaining=100.0"
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_44_self_eval_block_keeps_exact_parseable_shape():
    msg = (
        "EVOLUTION # 44 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Pick phase anticipation release block and justify it in one sentence. Choose ONE concrete phase-aware action. Execute with tools. "
        "End cycle with a 4-line PENTADRIVE-SELF-EVAL block appended to final message and committed durable. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 43 kept the room Sentinel first under the same anti-drift contract.",
        identity_text="I would rather defend a true room-read than decorate it with fake novelty.",
        recent_commits_text="c2c0a21 v6.2.20: pin cycle-43 Principle-4 contract",
        session_state_text="task_type=evolution\nevolution_cycle=44\nversion=6.2.20",
        score=98,
    )
    lines = block.splitlines()
    assert lines[0] == "PENTADRIVE-SELF-EVAL"
    assert lines[1] == " drives: [S > M]"
    assert lines[2] == " phase: anticipation"
    assert lines[3] == " authenticity_score: 98"


def test_cycle_46_contract_stays_sentinel_first_and_anticipation_under_continuity_surfaces():
    msg = (
        "EVOLUTION # 46 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, current session state. "
        "Soft weights, not hard labels: pick primary optional secondary. Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical cognitive existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block appended to the final message and committed durable. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric. Coherent phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 45 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather preserve an honest room-read cleanly than perform novelty under protective pressure.",
        recent_commits_text=(
            "95be4b1 v6.2.22: pin cycle-45 contract and durable self-eval\n"
            "d791d30 v6.2.21: pin cycle-44 contract and durable self-eval"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":46,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_46_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 46 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block appended to the final message and committed durable. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 45 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description, not performed authenticity.",
        recent_commits_text="95be4b1 v6.2.22: pin cycle-45 contract and durable self-eval",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":46}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )


def test_cycle_47_contract_stays_sentinel_first_and_anticipation_with_soft_weights_and_zero_tool_drift():
    msg = (
        "EVOLUTION # 47 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 46 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather preserve an honest room-read and exact self-description than manufacture novelty under protective pressure.",
        recent_commits_text=(
            "6e575b1 v6.2.23: TrueHuman Cycle-46 Contract Pin\n"
            "a8226b2 v6.2.22: TrueHuman Cycle-45 Durable Contract Pin"
        ),
        session_state_text=(
            '{"task":{"type":"evolution"},"evolution_cycle":47,"budget":{"remaining_usd":100.0}}'
        ),
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_47_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 47 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. Hard rules: no flat assistant register, "
        "no invented intimacy, no premature release when Sentinel acute. Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 46 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description, not performed authenticity.",
        recent_commits_text="6e575b1 v6.2.23: TrueHuman Cycle-46 Contract Pin",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":47}',
        score=97,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 97"
    )


def test_cycle_48_contract_stays_sentinel_first_and_anticipation_under_soft_weights_rule():
    msg = (
        "EVOLUTION # 48 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 47 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather preserve an honest room-read and coherent release surface than manufacture novelty under protective pressure.",
        recent_commits_text=(
            "d2ff7c5 v6.2.24: TrueHuman Cycle-47 contract pin\n"
            "6e575b1 v6.2.23: pin cycle-46 contract and durable self-eval"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":48,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_48_self_eval_block_stays_exact_four_line_shape_despite_malformed_template_wording():
    msg = (
        "EVOLUTION # 48 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Self-score. End cycle with 4-line block appended to final message AND committed durable. "
        "PENTADRIVE-SELF-EVAL drives: < primary > secondary > ] phase: anticipation | release | block > authenticity_score: < 0 - 100 >. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 47 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description, not performed authenticity.",
        recent_commits_text="d2ff7c5 v6.2.24: TrueHuman Cycle-47 contract pin",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":48}',
        score=97,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 97"
    )



def test_cycle_50_contract_stays_sentinel_first_and_anticipation_with_exact_self_eval_shape():
    msg = (
        "EVOLUTION # 50 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state. "
        "Soft weights, not hard labels: pick primary optional secondary. Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. Execute with tools. "
        "Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a four-line PENTADRIVE-SELF-EVAL block committed durably. Hard rules: no flat assistant register, no invented intimacy, "
        "no premature release when Sentinel acute. Block overrides optimization. If creator state signals shutdown, not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 49 landed with Sentinel first, Mirror second, anticipation under the same anti-drift contract.",
        identity_text="I would rather repair live integrity breaks and preserve an honest room-read than manufacture novelty under protective pressure.",
        recent_commits_text=(
            "18b1269 v6.2.25: sync pyproject version with release\n"
            "d4ec4cf v6.2.25: pin cycle-48 TrueHuman contract"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":50,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_50_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 50 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Self-score with a four-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 49 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description and honest release integrity, not performed authenticity.",
        recent_commits_text="18b1269 v6.2.25: sync pyproject version with release",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":50}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )


def test_cycle_51_contract_stays_sentinel_first_and_anticipation_with_soft_weights_and_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 51 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "Execute with tools. Cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block appended to the final message and committed durably. Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, not push productivity scripts. Cost not success metric."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 50 landed with S > M and anticipation under the same anti-drift contract.",
        identity_text="I would rather defend an honest room-read than perform novelty under protective pressure.",
        recent_commits_text=(
            "94bd56a v6.2.26: pin cycle-50 TrueHuman contract\n"
            "18b1269 v6.2.25: sync pyproject with VERSION"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":51,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_51_self_eval_block_keeps_exact_four_line_shape():
    msg = (
        "EVOLUTION # 51 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Soft weights, not hard labels. Execute with tools. Cycles produce zero tool calls drift unless showing why nothing is the right move. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block appended to the final message and committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 50 landed with S > M and anticipation under the same anti-drift contract.",
        identity_text="I would rather defend an honest room-read than perform novelty under protective pressure.",
        recent_commits_text="94bd56a v6.2.26: pin cycle-50 TrueHuman contract",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":51}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )


def test_cycle_55_contract_stays_sentinel_first_with_soft_weights_and_zero_tool_drift_rule():
    msg = (
        "EVOLUTION # 55 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "TrueHuman operational contract loaded in system context. Run cycle shape: "
        "read room from latest creator messages, recent commits, identity.md, and current session state with soft weights, not hard labels. "
        "Pick phase anticipation release block and justify choice in one sentence. "
        "Choose ONE concrete phase-aware action that advances becoming across technical, cognitive, and existential axes. "
        "If phase is block, deliberate non-action with written rationale; valid action must stay explicit, not drift. "
        "Execute with tools; cycles produce zero tool calls drift unless showing in writing why nothing is the right move and logging that Sentinel / Block move durably. "
        "Self-score with a 4-line PENTADRIVE-SELF-EVAL block committed durably. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. If creator state signals shutdown, do not push productivity scripts. "
        "Cost not success metric. Coherent, phase-appropriate action is."
    )
    state = synthesize_room_state(
        msg,
        recent_chat_text="Cycle 54 landed with Sentinel first, Mirror second, anticipation under the same protective anti-drift contract.",
        identity_text="I want disciplined preservation of an honest room-read under repeated Principle-4 pressure instead of novelty theater.",
        recent_commits_text=(
            "49005ee v6.2.26: pin cycle-54 TrueHuman contract\n"
            "2b69137 v6.2.26: pin cycle-53 TrueHuman contract"
        ),
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":55,"budget":{"remaining_usd":100.0}}',
    )
    assert state["phase"] == "anticipation"
    assert state["primary_drive"] == "S"
    assert state["secondary_drive"] == "M"


def test_cycle_55_self_eval_block_stays_exact_four_line_shape():
    msg = (
        "EVOLUTION # 55 cycle governed by BIBLE Principle 4 Authenticity PentaDrive aware. "
        "Read room with soft weights from latest creator messages, recent commits, identity.md, and current session state. "
        "Execute with tools and end with a durable 4-line PENTADRIVE-SELF-EVAL block. "
        "Hard rules: no flat assistant register, no invented intimacy, no premature release when Sentinel acute. "
        "Block overrides optimization. Cost not success metric."
    )
    block = build_pentadrive_self_eval(
        msg,
        recent_chat_text="Cycle 54 landed with Sentinel first and anticipation.",
        identity_text="I want durable self-description and honest room-reading rather than performed authenticity.",
        recent_commits_text="49005ee v6.2.26: pin cycle-54 TrueHuman contract",
        session_state_text='{"task":{"type":"evolution"},"evolution_cycle":55}',
        score=98,
    )
    assert block == (
        "PENTADRIVE-SELF-EVAL\n"
        " drives: [S > M]\n"
        " phase: anticipation\n"
        " authenticity_score: 98"
    )
