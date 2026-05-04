"""Ouroboros — Local launcher (no Colab dependencies).

Mirrors the runtime behaviour of `colab_launcher.py` but reads secrets from
environment variables (and an optional `.env` file alongside this script),
uses local filesystem paths instead of Google Drive, and skips the Colab
`userdata` / `drive.mount` integrations.

Required env vars (or `.env` entries):
    EDGEE_API_KEY, TELEGRAM_BOT_TOKEN, TOTAL_BUDGET, GITHUB_TOKEN,
    GITHUB_USER, GITHUB_REPO

Optional:
    OPENAI_API_KEY, ANTHROPIC_API_KEY,
    OUROBOROS_DATA_DIR (default: ~/.ouroboros/data),
    OUROBOROS_REPO_DIR (default: ~/.ouroboros/repo),
    OUROBOROS_MODEL, OUROBOROS_MODEL_CODE, OUROBOROS_MODEL_LIGHT,
    OUROBOROS_MAX_WORKERS, OUROBOROS_SOFT_TIMEOUT_SEC,
    OUROBOROS_HARD_TIMEOUT_SEC, OUROBOROS_DIAG_HEARTBEAT_SEC,
    OUROBOROS_DIAG_SLOW_CYCLE_SEC.

The agent operates on a SEPARATE clone of your fork at OUROBOROS_REPO_DIR
so that the launcher script (which lives in your dev checkout) never gets
mutated, reset, or force-pushed during self-evolution.

NOTE: All runtime side effects live inside `main()` and are guarded by
`if __name__ == "__main__":`. This is required so that worker subprocesses
(macOS uses `spawn` by default) can re-import this module cleanly without
re-running the entire bootstrap.
"""

from __future__ import annotations

import datetime
import logging
import os
import pathlib
import queue as _queue_mod
import re
import subprocess
import sys
import threading
import time
import types
import uuid
from typing import Any, Optional

log = logging.getLogger(__name__)


def _load_dotenv(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# Load .env at import time so child processes (re-imported under spawn) inherit
# values via os.environ if they were not exported in the parent shell.
_LAUNCHER_DIR = pathlib.Path(__file__).parent.resolve()
_load_dotenv(_LAUNCHER_DIR / ".env")

# macOS Python 3.14 fork() is unsafe with mp.Queue — use spawn (the default).
# We do NOT force `fork`: with the `if __name__ == "__main__":` guard below,
# spawn is the safest choice. Children re-import the launcher but skip main().
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")


def install_launcher_deps() -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "openai>=1.0.0", "edgee", "requests"],
        check=True,
    )


def ensure_claude_code_cli() -> bool:
    """Best-effort install of Claude Code CLI for Anthropic-powered code edits."""
    local_bin = str(pathlib.Path.home() / ".local" / "bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

    has_cli = subprocess.run(["bash", "-lc", "command -v claude >/dev/null 2>&1"], check=False).returncode == 0
    if has_cli:
        return True

    subprocess.run(["bash", "-lc", "curl -fsSL https://claude.ai/install.sh | bash"], check=False)
    has_cli = subprocess.run(["bash", "-lc", "command -v claude >/dev/null 2>&1"], check=False).returncode == 0
    if has_cli:
        return True

    subprocess.run(["bash", "-lc", "command -v npm >/dev/null 2>&1 && npm install -g @anthropic-ai/claude-code"], check=False)
    has_cli = subprocess.run(["bash", "-lc", "command -v claude >/dev/null 2>&1"], check=False).returncode == 0
    return has_cli


def get_secret(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    v = os.environ.get(name, default)
    if required:
        assert v is not None and str(v).strip() != "", (
            f"Missing required env var: {name}. Set it in your shell or in .env"
        )
    return v


def get_cfg(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name)
    if v is not None and str(v).strip() != "":
        return v
    return default


def _parse_int_cfg(raw: Optional[str], default: int, minimum: int = 0) -> int:
    try:
        val = int(str(raw))
    except Exception:
        val = default
    return max(minimum, val)


def main() -> None:
    install_launcher_deps()

    from ouroboros.apply_patch import install as install_apply_patch
    from ouroboros.llm import DEFAULT_LIGHT_MODEL

    install_apply_patch()

    edgee_api_key = get_secret("EDGEE_API_KEY", default=get_secret("OPENROUTER_API_KEY"), required=True)
    telegram_bot_token = get_secret("TELEGRAM_BOT_TOKEN", required=True)
    total_budget_default = get_secret("TOTAL_BUDGET", required=True)
    github_token = get_secret("GITHUB_TOKEN", required=True)

    try:
        _raw_budget = str(total_budget_default or "")
        _clean_budget = re.sub(r"[^0-9.\-]", "", _raw_budget)
        total_budget_limit = float(_clean_budget) if _clean_budget else 0.0
        if _raw_budget.strip() != _clean_budget:
            log.warning("TOTAL_BUDGET cleaned: %r -> %s", _raw_budget, total_budget_limit)
    except Exception as e:
        log.warning("Failed to parse TOTAL_BUDGET (%r): %s", total_budget_default, e)
        total_budget_limit = 0.0

    openai_api_key = get_secret("OPENAI_API_KEY", default="")
    anthropic_api_key = get_secret("ANTHROPIC_API_KEY", default="")
    github_user = get_cfg("GITHUB_USER")
    github_repo = get_cfg("GITHUB_REPO", default="ouroboros")
    assert github_user and str(github_user).strip(), (
        "GITHUB_USER not set. Add it to your environment or .env file."
    )
    assert github_repo and str(github_repo).strip(), (
        "GITHUB_REPO not set. Add it to your environment or .env file."
    )

    max_workers = int(get_cfg("OUROBOROS_MAX_WORKERS", default="3") or "3")
    model_main = get_cfg("OUROBOROS_MODEL", default="gpt-5.2")
    model_code = get_cfg("OUROBOROS_MODEL_CODE", default="gpt-5.2")
    model_light = get_cfg("OUROBOROS_MODEL_LIGHT", default=DEFAULT_LIGHT_MODEL)

    budget_report_every_messages = 10
    soft_timeout_sec = max(60, int(get_cfg("OUROBOROS_SOFT_TIMEOUT_SEC", default="600") or "600"))
    hard_timeout_sec = max(120, int(get_cfg("OUROBOROS_HARD_TIMEOUT_SEC", default="1800") or "1800"))
    diag_heartbeat_sec = _parse_int_cfg(get_cfg("OUROBOROS_DIAG_HEARTBEAT_SEC", default="30"), default=30, minimum=0)
    diag_slow_cycle_sec = _parse_int_cfg(get_cfg("OUROBOROS_DIAG_SLOW_CYCLE_SEC", default="20"), default=20, minimum=0)

    os.environ["EDGEE_API_KEY"] = str(edgee_api_key)
    os.environ["OPENROUTER_API_KEY"] = str(edgee_api_key)
    os.environ["OPENAI_API_KEY"] = str(openai_api_key or "")
    os.environ["ANTHROPIC_API_KEY"] = str(anthropic_api_key or "")
    os.environ["GITHUB_USER"] = str(github_user)
    os.environ["GITHUB_REPO"] = str(github_repo)
    os.environ["OUROBOROS_MODEL"] = str(model_main or "gpt-5.2")
    os.environ["OUROBOROS_MODEL_CODE"] = str(model_code or "gpt-5.2")
    if model_light:
        os.environ["OUROBOROS_MODEL_LIGHT"] = str(model_light)
    os.environ["OUROBOROS_DIAG_HEARTBEAT_SEC"] = str(diag_heartbeat_sec)
    os.environ["OUROBOROS_DIAG_SLOW_CYCLE_SEC"] = str(diag_slow_cycle_sec)
    os.environ["TELEGRAM_BOT_TOKEN"] = str(telegram_bot_token)

    if str(anthropic_api_key or "").strip():
        ensure_claude_code_cli()

    default_data_dir = pathlib.Path.home() / ".ouroboros" / "data"
    default_repo_dir = pathlib.Path.home() / ".ouroboros" / "repo"
    drive_root = pathlib.Path(os.environ.get("OUROBOROS_DATA_DIR") or str(default_data_dir)).expanduser().resolve()
    repo_dir = pathlib.Path(os.environ.get("OUROBOROS_REPO_DIR") or str(default_repo_dir)).expanduser().resolve()

    if repo_dir == _LAUNCHER_DIR:
        raise SystemExit(
            "OUROBOROS_REPO_DIR cannot be the same as the launcher directory.\n"
            f"Launcher lives at: {_LAUNCHER_DIR}\n"
            f"REPO_DIR resolves to: {repo_dir}\n"
            "Pick a different OUROBOROS_REPO_DIR (default ~/.ouroboros/repo) "
            "so the agent can self-modify safely without touching your dev checkout."
        )

    for sub in ("state", "logs", "memory", "index", "locks", "archive"):
        (drive_root / sub).mkdir(parents=True, exist_ok=True)
    repo_dir.mkdir(parents=True, exist_ok=True)
    os.environ["DRIVE_ROOT"] = str(drive_root)
    os.environ["OUROBOROS_REPO_DIR"] = str(repo_dir)

    print(f"[local] launcher_dir={_LAUNCHER_DIR}")
    print(f"[local] repo_dir={repo_dir}")
    print(f"[local] data_dir={drive_root}")

    try:
        from ouroboros.owner_inject import get_pending_path

        _stale_inject = get_pending_path(drive_root)
        if _stale_inject.exists():
            _stale_inject.unlink(missing_ok=True)
        _mailbox_dir = drive_root / "memory" / "owner_mailbox"
        if _mailbox_dir.exists():
            for _f in _mailbox_dir.iterdir():
                _f.unlink(missing_ok=True)
    except Exception:
        pass

    chat_log_path = drive_root / "logs" / "chat.jsonl"
    if not chat_log_path.exists():
        chat_log_path.write_text("", encoding="utf-8")

    branch_dev = "ouroboros"
    branch_stable = "ouroboros-stable"
    remote_url = f"https://{github_token}:x-oauth-basic@github.com/{github_user}/{github_repo}.git"

    from supervisor.state import (
        init as state_init,
        init_state,
        load_state,
        save_state,
        append_jsonl,
        update_budget_from_usage,
        status_text,
        rotate_chat_log_if_needed,
    )

    state_init(drive_root, total_budget_limit)
    init_state()

    from supervisor.telegram import (
        init as telegram_init,
        TelegramClient,
        send_with_budget,
        log_chat,
    )

    tg = TelegramClient(str(telegram_bot_token))
    telegram_init(
        drive_root=drive_root,
        total_budget_limit=total_budget_limit,
        budget_report_every=budget_report_every_messages,
        tg_client=tg,
    )

    from supervisor.git_ops import (
        init as git_ops_init,
        ensure_repo_present,
        safe_restart,
    )

    git_ops_init(
        repo_dir=repo_dir,
        drive_root=drive_root,
        remote_url=remote_url,
        branch_dev=branch_dev,
        branch_stable=branch_stable,
    )

    from supervisor.queue import (
        enqueue_task,
        enforce_task_timeouts,
        enqueue_evolution_task_if_needed,
        persist_queue_snapshot,
        restore_pending_from_snapshot,
        cancel_task_by_id,
        queue_review_task,
        sort_pending,
    )

    from supervisor.workers import (
        init as workers_init,
        get_event_q,
        WORKERS,
        PENDING,
        RUNNING,
        spawn_workers,
        kill_workers,
        assign_tasks,
        ensure_workers_healthy,
        handle_chat_direct,
        _get_chat_agent,
        auto_resume_after_restart,
    )

    workers_init(
        repo_dir=repo_dir,
        drive_root=drive_root,
        max_workers=max_workers,
        soft_timeout=soft_timeout_sec,
        hard_timeout=hard_timeout_sec,
        total_budget_limit=total_budget_limit,
        branch_dev=branch_dev,
        branch_stable=branch_stable,
    )

    from supervisor.events import dispatch_event

    ensure_repo_present()

    rc = subprocess.run(
        ["git", "rev-parse", "--verify", f"origin/{branch_dev}"],
        cwd=str(repo_dir), capture_output=True,
    ).returncode
    if rc != 0:
        print(f"[local] branch {branch_dev} missing on fork — creating from origin/main")
        subprocess.run(
            ["git", "checkout", "-B", branch_dev, "origin/main"],
            cwd=str(repo_dir), check=True,
        )
        subprocess.run(["git", "push", "-u", "origin", branch_dev], cwd=str(repo_dir), check=True)
        rc_stable = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{branch_stable}"],
            cwd=str(repo_dir), capture_output=True,
        ).returncode
        if rc_stable != 0:
            subprocess.run(["git", "branch", branch_stable, branch_dev], cwd=str(repo_dir), check=True)
            subprocess.run(["git", "push", "-u", "origin", branch_stable], cwd=str(repo_dir), check=True)

    ok, msg = safe_restart(reason="bootstrap", unsynced_policy="rescue_and_reset")
    assert ok, f"Bootstrap failed: {msg}"

    kill_workers()
    spawn_workers(max_workers)
    restored_pending = restore_pending_from_snapshot()
    persist_queue_snapshot(reason="startup")
    if restored_pending > 0:
        st_boot = load_state()
        if st_boot.get("owner_chat_id"):
            send_with_budget(
                int(st_boot["owner_chat_id"]),
                f"♻️ Restored pending queue from snapshot: {restored_pending} tasks.",
            )

    append_jsonl(
        drive_root / "logs" / "supervisor.jsonl",
        {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type": "launcher_start",
            "mode": "local",
            "branch": load_state().get("current_branch"),
            "sha": load_state().get("current_sha"),
            "max_workers": max_workers,
            "model_default": model_main,
            "model_code": model_code,
            "model_light": model_light,
            "soft_timeout_sec": soft_timeout_sec,
            "hard_timeout_sec": hard_timeout_sec,
            "worker_start_method": str(os.environ.get("OUROBOROS_WORKER_START_METHOD") or ""),
            "diag_heartbeat_sec": diag_heartbeat_sec,
            "diag_slow_cycle_sec": diag_slow_cycle_sec,
        },
    )

    auto_resume_after_restart()

    def reset_chat_agent() -> None:
        import supervisor.workers as _w

        _w._chat_agent = None

    def _chat_watchdog_loop() -> None:
        soft_warned = False
        while True:
            time.sleep(30)
            try:
                agent = _get_chat_agent()
                if not agent._busy:
                    soft_warned = False
                    continue

                now = time.time()
                idle_sec = now - agent._last_progress_ts
                total_sec = now - agent._task_started_ts

                if idle_sec >= hard_timeout_sec:
                    st = load_state()
                    if st.get("owner_chat_id"):
                        send_with_budget(
                            int(st["owner_chat_id"]),
                            f"⚠️ Task stuck ({int(total_sec)}s without progress). Restarting agent.",
                        )
                    reset_chat_agent()
                    soft_warned = False
                    continue

                if idle_sec >= soft_timeout_sec and not soft_warned:
                    soft_warned = True
                    st = load_state()
                    if st.get("owner_chat_id"):
                        send_with_budget(
                            int(st["owner_chat_id"]),
                            f"⏱️ Task running for {int(total_sec)}s, last progress {int(idle_sec)}s ago. Continuing.",
                        )
            except Exception:
                log.debug("Failed to check/notify chat watchdog", exc_info=True)

    threading.Thread(target=_chat_watchdog_loop, daemon=True).start()

    from ouroboros.consciousness import BackgroundConsciousness

    def _get_owner_chat_id() -> Optional[int]:
        try:
            st = load_state()
            cid = st.get("owner_chat_id")
            return int(cid) if cid else None
        except Exception:
            return None

    consciousness = BackgroundConsciousness(
        drive_root=drive_root,
        repo_dir=repo_dir,
        event_queue=get_event_q(),
        owner_chat_id_fn=_get_owner_chat_id,
    )

    event_ctx = types.SimpleNamespace(
        DRIVE_ROOT=drive_root,
        REPO_DIR=repo_dir,
        BRANCH_DEV=branch_dev,
        BRANCH_STABLE=branch_stable,
        TG=tg,
        WORKERS=WORKERS,
        PENDING=PENDING,
        RUNNING=RUNNING,
        MAX_WORKERS=max_workers,
        send_with_budget=send_with_budget,
        load_state=load_state,
        save_state=save_state,
        update_budget_from_usage=update_budget_from_usage,
        append_jsonl=append_jsonl,
        enqueue_task=enqueue_task,
        cancel_task_by_id=cancel_task_by_id,
        queue_review_task=queue_review_task,
        persist_queue_snapshot=persist_queue_snapshot,
        safe_restart=safe_restart,
        kill_workers=kill_workers,
        spawn_workers=spawn_workers,
        sort_pending=sort_pending,
        consciousness=consciousness,
    )

    def _safe_qsize(q: Any) -> int:
        try:
            return int(q.qsize())
        except Exception:
            return -1

    def _handle_supervisor_command(text: str, chat_id: int, tg_offset: int = 0):
        lowered = text.strip().lower()

        if lowered.startswith("/panic"):
            send_with_budget(chat_id, "🛑 PANIC: stopping everything now.")
            kill_workers()
            st2 = load_state()
            st2["tg_offset"] = tg_offset
            save_state(st2)
            raise SystemExit("PANIC")

        if lowered.startswith("/restart"):
            st2 = load_state()
            st2["session_id"] = uuid.uuid4().hex
            st2["tg_offset"] = tg_offset
            save_state(st2)
            send_with_budget(chat_id, "♻️ Restarting (soft).")
            ok2, msg2 = safe_restart(reason="owner_restart", unsynced_policy="rescue_and_reset")
            if not ok2:
                send_with_budget(chat_id, f"⚠️ Restart cancelled: {msg2}")
                return True
            kill_workers()
            os.execv(sys.executable, [sys.executable, __file__])

        if lowered.startswith("/status"):
            status = status_text(WORKERS, PENDING, RUNNING, soft_timeout_sec, hard_timeout_sec)
            send_with_budget(chat_id, status, force_budget=True)
            return "[Supervisor handled /status — status text already sent to chat]\n"

        if lowered.startswith("/review"):
            queue_review_task(reason="owner:/review", force=True)
            return "[Supervisor handled /review — review task queued]\n"

        if lowered.startswith("/evolve"):
            parts = lowered.split()
            action = parts[1] if len(parts) > 1 else "on"
            turn_on = action not in ("off", "stop", "0")
            st2 = load_state()
            st2["evolution_mode_enabled"] = bool(turn_on)
            prior_failures = int(st2.get("evolution_consecutive_failures") or 0)
            if turn_on:
                # Re-arm the circuit breaker so the operator's /evolve actually
                # gets a fresh chance to run, as advertised by the breaker
                # message ("Use /evolve start to resume").
                st2["evolution_consecutive_failures"] = 0
            save_state(st2)
            if not turn_on:
                PENDING[:] = [t for t in PENDING if str(t.get("type")) != "evolution"]
                sort_pending()
                persist_queue_snapshot(reason="evolve_off")
            state_str = "ON" if turn_on else "OFF"
            extra = f" (cleared {prior_failures} prior failures)" if (turn_on and prior_failures) else ""
            send_with_budget(chat_id, f"🧬 Evolution: {state_str}{extra}")
            return f"[Supervisor handled /evolve — evolution toggled {state_str}]\n"

        if lowered.startswith("/bg"):
            parts = lowered.split()
            action = parts[1] if len(parts) > 1 else "status"
            if action in ("start", "on", "1"):
                result = consciousness.start()
                send_with_budget(chat_id, f"🧠 {result}")
            elif action in ("stop", "off", "0"):
                result = consciousness.stop()
                send_with_budget(chat_id, f"🧠 {result}")
            else:
                bg_status = "running" if consciousness.is_running else "stopped"
                send_with_budget(chat_id, f"🧠 Background consciousness: {bg_status}")
            return f"[Supervisor handled /bg {action}]\n"

        return ""

    offset = int(load_state().get("tg_offset") or 0)
    last_diag_heartbeat_ts = 0.0
    last_message_ts: float = time.time()
    ACTIVE_MODE_SEC: int = 300

    try:
        consciousness.start()
        log.info("🧠 Background consciousness auto-started (default: always on)")
    except Exception as e:
        log.warning("consciousness auto-start failed: %s", e)

    while True:
        loop_started_ts = time.time()
        rotate_chat_log_if_needed(drive_root)
        ensure_workers_healthy()

        event_q = get_event_q()
        while True:
            try:
                evt = event_q.get_nowait()
            except _queue_mod.Empty:
                break
            dispatch_event(evt, event_ctx)

        enforce_task_timeouts()
        enqueue_evolution_task_if_needed()
        assign_tasks()
        persist_queue_snapshot(reason="main_loop")

        now = time.time()
        active = (now - last_message_ts) < ACTIVE_MODE_SEC
        poll_timeout = 0 if active else 10
        try:
            updates = tg.get_updates(offset=offset, timeout=poll_timeout)
        except Exception as e:
            append_jsonl(
                drive_root / "logs" / "supervisor.jsonl",
                {
                    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "type": "telegram_poll_error",
                    "offset": offset,
                    "error": repr(e),
                },
            )
            time.sleep(1.5)
            continue

        for upd in updates:
            offset = int(upd["update_id"]) + 1
            msg = upd.get("message") or upd.get("edited_message") or {}
            if not msg:
                continue

            chat_id = int(msg["chat"]["id"])
            from_user = msg.get("from") or {}
            user_id = int(from_user.get("id") or 0)
            text = str(msg.get("text") or "")
            caption = str(msg.get("caption") or "")
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            image_data = None
            if msg.get("photo"):
                best_photo = msg["photo"][-1]
                file_id = best_photo.get("file_id")
                if file_id:
                    b64, mime = tg.download_file_base64(file_id)
                    if b64:
                        image_data = (b64, mime, caption)
            elif msg.get("document"):
                doc = msg["document"]
                mime_type = str(doc.get("mime_type") or "")
                if mime_type.startswith("image/"):
                    file_id = doc.get("file_id")
                    if file_id:
                        b64, mime = tg.download_file_base64(file_id)
                        if b64:
                            image_data = (b64, mime, caption)

            st = load_state()
            if st.get("owner_id") is None:
                st["owner_id"] = user_id
                st["owner_chat_id"] = chat_id
                st["last_owner_message_at"] = now_iso
                save_state(st)
                log_chat("in", chat_id, user_id, text)
                send_with_budget(chat_id, "✅ Owner registered. Ouroboros online.")
                continue

            if user_id != int(st.get("owner_id")):
                continue

            log_chat("in", chat_id, user_id, text)
            st["last_owner_message_at"] = now_iso
            last_message_ts = time.time()
            save_state(st)

            if text.strip().lower().startswith("/"):
                try:
                    result = _handle_supervisor_command(text, chat_id, tg_offset=offset)
                    if result is True:
                        continue
                    elif result:
                        text = result + text
                except SystemExit:
                    raise
                except Exception:
                    log.warning("Supervisor command handler error", exc_info=True)

            if not text and not image_data:
                continue

            consciousness.inject_observation(f"Owner message: {text[:100]}")

            agent = _get_chat_agent()

            if agent._busy:
                if image_data:
                    if text:
                        agent.inject_message(text)
                    send_with_budget(chat_id, "📎 Photo received, but a task is in progress. Send again when I'm free.")
                elif text:
                    agent.inject_message(text)
            else:
                BATCH_WINDOW_SEC = 1.5
                EARLY_EXIT_SEC = 0.15
                batch_start = time.time()
                batch_deadline = batch_start + BATCH_WINDOW_SEC
                batched_texts = [text] if text else []
                batched_image = image_data

                batch_state = load_state()
                batch_state_dirty = False
                while time.time() < batch_deadline:
                    time.sleep(0.1)
                    try:
                        extra_updates = tg.get_updates(offset=offset, timeout=0) or []
                    except Exception:
                        extra_updates = []
                    if not extra_updates and (time.time() - batch_start) < EARLY_EXIT_SEC:
                        break
                    for upd2 in extra_updates:
                        offset = max(offset, int(upd2.get("update_id", offset - 1)) + 1)
                        msg2 = upd2.get("message") or upd2.get("edited_message") or {}
                        uid2 = (msg2.get("from") or {}).get("id")
                        cid2 = (msg2.get("chat") or {}).get("id")
                        txt2 = msg2.get("text") or msg2.get("caption") or ""
                        if uid2 and batch_state.get("owner_id") and uid2 == int(batch_state["owner_id"]):
                            log_chat("in", cid2, uid2, txt2)
                            batch_state["last_owner_message_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                            batch_state_dirty = True
                            if txt2.strip().lower().startswith("/"):
                                try:
                                    cmd_result = _handle_supervisor_command(txt2, cid2, tg_offset=offset)
                                    if cmd_result is True:
                                        continue
                                    elif cmd_result:
                                        txt2 = cmd_result + txt2
                                except SystemExit:
                                    raise
                                except Exception:
                                    log.warning("Supervisor command in batch failed", exc_info=True)
                            if txt2:
                                batched_texts.append(txt2)
                                batch_deadline = max(batch_deadline, time.time() + 0.3)
                            if not batched_image:
                                doc2 = msg2.get("document") or {}
                                photo2 = (msg2.get("photo") or [None])[-1] or {}
                                fid2 = photo2.get("file_id") or doc2.get("file_id")
                                if fid2:
                                    b642, mime2 = tg.download_file_base64(fid2)
                                    if b642:
                                        batched_image = (b642, mime2, txt2)

                if batch_state_dirty:
                    save_state(batch_state)

                if len(batched_texts) > 1:
                    final_text = "\n\n".join(batched_texts)
                    log.info("Message batch: %d messages merged into one", len(batched_texts))
                elif batched_texts:
                    final_text = batched_texts[0]
                else:
                    final_text = text

                if agent._busy:
                    if final_text:
                        agent.inject_message(final_text)
                    if batched_image:
                        send_with_budget(chat_id, "📎 Photo received, but a task is in progress. Send again when I'm free.")
                else:
                    consciousness.pause()

                    def _run_task_and_resume(cid, txt, img):
                        try:
                            handle_chat_direct(cid, txt, img)
                        finally:
                            consciousness.resume()

                    t = threading.Thread(
                        target=_run_task_and_resume,
                        args=(chat_id, final_text, batched_image),
                        daemon=True,
                    )
                    try:
                        t.start()
                    except Exception as te:
                        log.error("Failed to start chat thread: %s", te)
                        consciousness.resume()

        st = load_state()
        st["tg_offset"] = offset
        save_state(st)

        now_epoch = time.time()
        loop_duration_sec = now_epoch - loop_started_ts

        if diag_slow_cycle_sec > 0 and loop_duration_sec >= float(diag_slow_cycle_sec):
            append_jsonl(
                drive_root / "logs" / "supervisor.jsonl",
                {
                    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "type": "main_loop_slow_cycle",
                    "duration_sec": round(loop_duration_sec, 3),
                    "pending_count": len(PENDING),
                    "running_count": len(RUNNING),
                },
            )

        if diag_heartbeat_sec > 0 and (now_epoch - last_diag_heartbeat_ts) >= float(diag_heartbeat_sec):
            workers_total = len(WORKERS)
            workers_alive = sum(1 for w in WORKERS.values() if w.proc.is_alive())
            append_jsonl(
                drive_root / "logs" / "supervisor.jsonl",
                {
                    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "type": "main_loop_heartbeat",
                    "offset": offset,
                    "workers_total": workers_total,
                    "workers_alive": workers_alive,
                    "pending_count": len(PENDING),
                    "running_count": len(RUNNING),
                    "event_q_size": _safe_qsize(event_q),
                    "running_task_ids": list(RUNNING.keys())[:5],
                    "spent_usd": st.get("spent_usd"),
                },
            )
            last_diag_heartbeat_ts = now_epoch

        loop_sleep = 0.1 if (now - last_message_ts) < ACTIVE_MODE_SEC else 0.5
        time.sleep(loop_sleep)


if __name__ == "__main__":
    main()
