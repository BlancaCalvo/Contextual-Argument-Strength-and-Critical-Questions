"""
group_assignment.py
-------------------
Pure-Python helpers for experimental/control group counting and assignment.

Extracted from ExperimentState so the logic can be unit-tested without
importing Reflex, LangChain, or any other heavy dependency.

state.py should delegate to these functions instead of duplicating the logic.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def get_group_counts(
    output_dir: str,
    current_branch: str,
    current_session_id: str = "",
    recency_window_hours: float = 1.5,
) -> tuple[int, int]:
    """Return (experimental_count, control_count) for sessions in *output_dir*.

    Rules:
    - Only counts sessions whose ``branch`` field matches *current_branch*.
    - Skips the file belonging to *current_session_id* (the current participant).
    - A session is counted if it is **finished** (``end_time`` is set) OR
      **recent** (started within *recency_window_hours*).

    Returns (0, 0) if the directory does not exist or is empty.
    """
    exp_count = 0
    ctrl_count = 0

    if not os.path.exists(output_dir):
        return 0, 0

    now = datetime.now()
    cutoff = now - timedelta(hours=recency_window_hours)

    for filename in os.listdir(output_dir):
        if not filename.endswith("_metadata.json"):
            continue

        # Skip the current participant's own file
        if current_session_id and current_session_id in filename:
            continue

        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, "r") as fh:
                data = json.load(fh)

            # Branch isolation: dev sessions must not affect main counts
            file_branch = data.get("branch", "main")
            if file_branch != current_branch:
                continue

            group = data.get("experimental_group")
            if group not in ("experimental", "control"):
                continue

            is_finished = data.get("end_time") is not None

            is_recent = False
            start_time_str = data.get("start_time")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    if start_time > cutoff:
                        is_recent = True
                except (ValueError, TypeError):
                    pass

            if is_finished or is_recent:
                if group == "experimental":
                    exp_count += 1
                else:
                    ctrl_count += 1

        except Exception as exc:
            print(f"[group_assignment] Warning: could not read {filename}: {exc}")

    return exp_count, ctrl_count


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------

def assign_group(
    session_id: str,
    exp_count: int,
    ctrl_count: int,
) -> str:
    """Decide 'experimental' or 'control' for a new session.

    Priority:
    1. Assign to whichever group has fewer members (balance first).
    2. On a tie, use a deterministic but independent MD5 hash of the session_id
       (with a ':group' salt, decoupled from the argument-selection hash).
    """
    if exp_count < ctrl_count:
        return "experimental"
    if ctrl_count < exp_count:
        return "control"

    # Tie-break: hash-based 50/50
    h = hashlib.md5((session_id + ":group").encode()).hexdigest()
    return "experimental" if int(h, 16) % 2 == 0 else "control"


# ---------------------------------------------------------------------------
# Reconnection guard
# ---------------------------------------------------------------------------

def load_saved_group(output_dir: str, session_id: str) -> str | None:
    """Return the group saved on disk for *session_id*, or None if not found.

    Used to recover the group assignment after a WebSocket reconnection where
    Reflex rebuilds the state from scratch (resetting ``initialized`` to False).

    IMPORTANT: Only returns a group if ``argument_groups`` is populated in the
    metadata, which confirms that ``init_if_needed`` ran to completion. This
    prevents false positives caused by metadata written mid-session by other
    callers (e.g. ``submit_demographics``) before initialization is finished.
    """
    if not session_id:
        return None

    metadata_path = os.path.join(output_dir, f"{session_id}_metadata.json")
    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, "r") as fh:
            data = json.load(fh)
        group = data.get("experimental_group")
        # argument_groups is only populated at the end of init_if_needed.
        # An empty list means the metadata was written before init completed.
        argument_groups = data.get("argument_groups", [])
        if group in ("experimental", "control") and argument_groups:
            return group
    except Exception as exc:
        print(f"[group_assignment] Warning: could not restore group for {session_id}: {exc}")

    return None
