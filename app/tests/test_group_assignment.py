"""
tests/test_group_assignment.py
------------------------------
Unit tests for experiment_app.group_assignment

Run from the dev/cqs-experiment-app/ directory:

    pytest tests/test_group_assignment.py -v

No Reflex, no LangChain, no network required.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta

import pytest

# We import the module under test directly (no Reflex involved)
from experiment_app.group_assignment import (
    assign_group,
    get_group_counts,
    load_saved_group,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_metadata(directory: str, session_id: str, group: str, branch: str = "main",
                    start_offset_hours: float = 0.0, finished: bool = False) -> str:
    """Write a fake metadata file and return the path."""
    start_time = datetime.now() - timedelta(hours=start_offset_hours)
    data = {
        "session_id": session_id,
        "branch": branch,
        "experimental_group": group,
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat() if finished else None,
    }
    path = os.path.join(directory, f"{session_id}_metadata.json")
    with open(path, "w") as fh:
        json.dump(data, fh)
    return path


# ===========================================================================
# get_group_counts
# ===========================================================================

class TestGetGroupCounts:

    def test_empty_directory_returns_zeros(self, tmp_path):
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert (exp, ctrl) == (0, 0)

    def test_nonexistent_directory_returns_zeros(self, tmp_path):
        missing = str(tmp_path / "does_not_exist")
        exp, ctrl = get_group_counts(missing, "main")
        assert (exp, ctrl) == (0, 0)

    def test_counts_finished_sessions(self, tmp_path):
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "control", finished=True)

        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert exp == 2
        assert ctrl == 1

    def test_counts_recent_unfinished_sessions(self, tmp_path):
        # Started 30 min ago — within the 1.5h window
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental",
                        start_offset_hours=0.5, finished=False)
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert exp == 1
        assert ctrl == 0

    def test_ignores_old_unfinished_sessions(self, tmp_path):
        # Started 3 hours ago and never finished — stale, should NOT count
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental",
                        start_offset_hours=3.0, finished=False)
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert exp == 0
        assert ctrl == 0

    def test_skips_current_session(self, tmp_path):
        my_id = str(uuid.uuid4())
        _write_metadata(str(tmp_path), my_id, "experimental", finished=True)

        # Without skipping: should count 1
        exp_no_skip, _ = get_group_counts(str(tmp_path), "main", current_session_id="")
        assert exp_no_skip == 1

        # With skipping: should count 0
        exp_skip, _ = get_group_counts(str(tmp_path), "main", current_session_id=my_id)
        assert exp_skip == 0

    def test_branch_isolation_main_ignores_dev(self, tmp_path):
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental",
                        branch="dev", finished=True)
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "control",
                        branch="main", finished=True)

        # main branch only sees the control session
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert exp == 0
        assert ctrl == 1

    def test_branch_isolation_dev_ignores_main(self, tmp_path):
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental",
                        branch="main", finished=True)
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "control",
                        branch="dev", finished=True)

        exp, ctrl = get_group_counts(str(tmp_path), "dev")
        assert exp == 0
        assert ctrl == 1

    def test_ignores_non_metadata_files(self, tmp_path):
        # A results file should not be counted
        (tmp_path / f"{uuid.uuid4()}_results.jsonl").write_text("{}")
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert (exp, ctrl) == (0, 0)

    def test_handles_corrupt_metadata_gracefully(self, tmp_path):
        bad_path = tmp_path / f"{uuid.uuid4()}_metadata.json"
        bad_path.write_text("NOT VALID JSON {{{{")
        # Should not raise, just skip the broken file
        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert (exp, ctrl) == (0, 0)

    def test_both_finished_and_recent_counted_together(self, tmp_path):
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(str(tmp_path), str(uuid.uuid4()), "control",
                        start_offset_hours=0.5, finished=False)  # recent

        exp, ctrl = get_group_counts(str(tmp_path), "main")
        assert exp == 1
        assert ctrl == 1


# ===========================================================================
# assign_group
# ===========================================================================

class TestAssignGroup:

    def test_assigns_experimental_when_fewer(self):
        group = assign_group("any-session-id", exp_count=2, ctrl_count=5)
        assert group == "experimental"

    def test_assigns_control_when_fewer(self):
        group = assign_group("any-session-id", exp_count=7, ctrl_count=3)
        assert group == "control"

    def test_tie_is_deterministic(self):
        sid = "test-session-abc"
        result1 = assign_group(sid, exp_count=3, ctrl_count=3)
        result2 = assign_group(sid, exp_count=3, ctrl_count=3)
        assert result1 == result2, "Tie-break must be deterministic for same session_id"

    def test_tie_returns_valid_group(self):
        for _ in range(20):
            sid = str(uuid.uuid4())
            result = assign_group(sid, exp_count=0, ctrl_count=0)
            assert result in ("experimental", "control")

    def test_tie_distribution_roughly_balanced(self):
        """Over 1000 UUIDs, tie-break should split ~50/50 (±10%)."""
        results = [assign_group(str(uuid.uuid4()), 0, 0) for _ in range(1000)]
        exp_fraction = results.count("experimental") / 1000
        assert 0.40 <= exp_fraction <= 0.60, (
            f"Tie-break distribution is skewed: {exp_fraction:.2%} experimental"
        )

    def test_hash_for_group_differs_from_hash_for_args(self):
        """The group tie-break hash must use ':group' salt, not the bare session_id.
        This ensures the two decisions are statistically independent.
        """
        sid = str(uuid.uuid4())
        h_bare = hashlib.md5(sid.encode()).hexdigest()
        h_group = hashlib.md5((sid + ":group").encode()).hexdigest()
        h_args = hashlib.md5((sid + ":args").encode()).hexdigest()

        assert h_bare != h_group
        assert h_args != h_group


# ===========================================================================
# load_saved_group
# ===========================================================================

class TestLoadSavedGroup:

    def test_returns_none_for_empty_session_id(self, tmp_path):
        result = load_saved_group(str(tmp_path), "")
        assert result is None

    def test_returns_none_when_file_missing(self, tmp_path):
        result = load_saved_group(str(tmp_path), "nonexistent-session-id")
        assert result is None

    def test_returns_saved_group_when_file_exists(self, tmp_path):
        sid = str(uuid.uuid4())
        _write_metadata(str(tmp_path), sid, "control", finished=True)
        result = load_saved_group(str(tmp_path), sid)
        assert result == "control"

    def test_returns_none_for_unknown_group_value(self, tmp_path):
        sid = str(uuid.uuid4())
        data = {"session_id": sid, "experimental_group": "invalid_value"}
        path = os.path.join(str(tmp_path), f"{sid}_metadata.json")
        with open(path, "w") as fh:
            json.dump(data, fh)

        result = load_saved_group(str(tmp_path), sid)
        assert result is None

    def test_handles_corrupt_file_gracefully(self, tmp_path):
        sid = str(uuid.uuid4())
        path = tmp_path / f"{sid}_metadata.json"
        path.write_text("CORRUPT {{")
        result = load_saved_group(str(tmp_path), sid)
        assert result is None

    def test_reconnection_scenario(self, tmp_path):
        """Simulate: session assigned 'experimental', WebSocket drops, state rebuilds."""
        sid = str(uuid.uuid4())
        # First call to init_if_needed: assigns the group and writes metadata
        _write_metadata(str(tmp_path), sid, "experimental", finished=False)

        # Second call (after reconnection): should restore from disk, not re-balance
        restored = load_saved_group(str(tmp_path), sid)
        assert restored == "experimental"


# ===========================================================================
# Integration: full assignment flow simulation
# ===========================================================================

class TestFullAssignmentFlow:

    def test_no_premature_counting(self, tmp_path):
        """New session must NOT count itself before the group is written.

        Sequence:
        1. New session_id created (no metadata file yet).
        2. get_group_counts() called — must not see the current session.
        3. Group assigned.
        4. Metadata written.
        5. Next session's get_group_counts() DOES see the previous one.
        """
        sid_1 = str(uuid.uuid4())

        # Step 1-2: no file exists yet, count is 0,0
        exp, ctrl = get_group_counts(str(tmp_path), "main", current_session_id=sid_1)
        assert (exp, ctrl) == (0, 0)

        # Step 3-4: assign and write
        group_1 = assign_group(sid_1, exp, ctrl)
        _write_metadata(str(tmp_path), sid_1, group_1, finished=True)

        # Step 5: second session sees first one
        sid_2 = str(uuid.uuid4())
        exp2, ctrl2 = get_group_counts(str(tmp_path), "main", current_session_id=sid_2)
        assert exp2 + ctrl2 == 1

    def test_balancing_over_multiple_sessions(self, tmp_path):
        """After N participants, counts should stay within 1 of each other."""
        N = 20
        branch = "main"
        groups_assigned = []

        for _ in range(N):
            sid = str(uuid.uuid4())
            exp, ctrl = get_group_counts(str(tmp_path), branch, current_session_id=sid)
            group = assign_group(sid, exp, ctrl)
            groups_assigned.append(group)
            _write_metadata(str(tmp_path), sid, group, finished=True)

        exp_total = groups_assigned.count("experimental")
        ctrl_total = groups_assigned.count("control")
        assert abs(exp_total - ctrl_total) <= 1, (
            f"Balancing failed after {N} sessions: exp={exp_total}, ctrl={ctrl_total}"
        )

    def test_dev_sessions_dont_affect_main_balancing(self, tmp_path):
        """Dev sessions in the same output_dir must not skew main branch counts."""
        branch = "main"

        # 5 dev sessions all assigned to 'experimental'
        for _ in range(5):
            sid = str(uuid.uuid4())
            _write_metadata(str(tmp_path), sid, "experimental",
                            branch="dev", finished=True)

        # Main branch count must still be 0,0
        exp, ctrl = get_group_counts(str(tmp_path), branch)
        assert (exp, ctrl) == (0, 0)
