"""
Run tests without pytest:
    ../../reflex-venv/bin/python tests/run_tests.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import hashlib
import json
import uuid
import unittest
from datetime import datetime, timedelta

from experiment_app.group_assignment import (
    assign_group,
    get_group_counts,
    load_saved_group,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_metadata(directory, session_id, group, branch="main",
                    start_offset_hours=0.0, finished=False,
                    argument_groups=None):
    start_time = datetime.now() - timedelta(hours=start_offset_hours)
    if argument_groups is None:
        argument_groups = ["arguments_group_1", "arguments_group_2", "arguments_group_3"]
    data = {
        "session_id": session_id,
        "branch": branch,
        "experimental_group": group,
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat() if finished else None,
        "argument_groups": argument_groups,
    }
    path = os.path.join(directory, f"{session_id}_metadata.json")
    with open(path, "w") as fh:
        json.dump(data, fh)
    return path


import tempfile

def tmp():
    """Create a fresh temp directory for each test."""
    return tempfile.mkdtemp()


# ===========================================================================
# get_group_counts
# ===========================================================================

class TestGetGroupCounts(unittest.TestCase):

    def test_empty_directory_returns_zeros(self):
        d = tmp()
        self.assertEqual(get_group_counts(d, "main"), (0, 0))

    def test_nonexistent_directory_returns_zeros(self):
        self.assertEqual(get_group_counts("/nonexistent/path/xyz", "main"), (0, 0))

    def test_counts_finished_sessions(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(d, str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(d, str(uuid.uuid4()), "control", finished=True)
        self.assertEqual(get_group_counts(d, "main"), (2, 1))

    def test_counts_recent_unfinished_sessions(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental",
                        start_offset_hours=0.5, finished=False)
        self.assertEqual(get_group_counts(d, "main"), (1, 0))

    def test_ignores_old_unfinished_sessions(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental",
                        start_offset_hours=3.0, finished=False)
        self.assertEqual(get_group_counts(d, "main"), (0, 0))

    def test_skips_current_session(self):
        d = tmp()
        my_id = str(uuid.uuid4())
        _write_metadata(d, my_id, "experimental", finished=True)
        # Without skipping
        exp_no_skip, _ = get_group_counts(d, "main", current_session_id="")
        self.assertEqual(exp_no_skip, 1)
        # With skipping
        exp_skip, _ = get_group_counts(d, "main", current_session_id=my_id)
        self.assertEqual(exp_skip, 0)

    def test_branch_isolation_main_ignores_dev(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental", branch="dev", finished=True)
        _write_metadata(d, str(uuid.uuid4()), "control", branch="main", finished=True)
        exp, ctrl = get_group_counts(d, "main")
        self.assertEqual((exp, ctrl), (0, 1))

    def test_branch_isolation_dev_ignores_main(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental", branch="main", finished=True)
        _write_metadata(d, str(uuid.uuid4()), "control", branch="dev", finished=True)
        exp, ctrl = get_group_counts(d, "dev")
        self.assertEqual((exp, ctrl), (0, 1))

    def test_ignores_non_metadata_files(self):
        d = tmp()
        open(os.path.join(d, f"{uuid.uuid4()}_results.jsonl"), "w").close()
        self.assertEqual(get_group_counts(d, "main"), (0, 0))

    def test_handles_corrupt_metadata_gracefully(self):
        d = tmp()
        with open(os.path.join(d, f"{uuid.uuid4()}_metadata.json"), "w") as fh:
            fh.write("NOT VALID JSON {{{{")
        # Must not raise
        self.assertEqual(get_group_counts(d, "main"), (0, 0))

    def test_both_finished_and_recent_counted(self):
        d = tmp()
        _write_metadata(d, str(uuid.uuid4()), "experimental", finished=True)
        _write_metadata(d, str(uuid.uuid4()), "control",
                        start_offset_hours=0.5, finished=False)
        self.assertEqual(get_group_counts(d, "main"), (1, 1))


# ===========================================================================
# assign_group
# ===========================================================================

class TestAssignGroup(unittest.TestCase):

    def test_assigns_experimental_when_fewer(self):
        self.assertEqual(assign_group("sid", 2, 5), "experimental")

    def test_assigns_control_when_fewer(self):
        self.assertEqual(assign_group("sid", 7, 3), "control")

    def test_tie_is_deterministic(self):
        sid = "test-session-abc"
        self.assertEqual(assign_group(sid, 3, 3), assign_group(sid, 3, 3))

    def test_tie_returns_valid_group(self):
        for _ in range(50):
            result = assign_group(str(uuid.uuid4()), 0, 0)
            self.assertIn(result, ("experimental", "control"))

    def test_tie_distribution_roughly_balanced(self):
        results = [assign_group(str(uuid.uuid4()), 0, 0) for _ in range(1000)]
        exp_fraction = results.count("experimental") / 1000
        self.assertGreaterEqual(exp_fraction, 0.40)
        self.assertLessEqual(exp_fraction, 0.60)

    def test_hashes_are_decoupled(self):
        sid = str(uuid.uuid4())
        h_group = hashlib.md5((sid + ":group").encode()).hexdigest()
        h_args = hashlib.md5((sid + ":args").encode()).hexdigest()
        self.assertNotEqual(h_group, h_args)


# ===========================================================================
# load_saved_group
# ===========================================================================

class TestLoadSavedGroup(unittest.TestCase):

    def test_returns_none_for_empty_session_id(self):
        self.assertIsNone(load_saved_group(tmp(), ""))

    def test_returns_none_when_file_missing(self):
        self.assertIsNone(load_saved_group(tmp(), "nonexistent-id"))

    def test_returns_saved_group(self):
        d = tmp()
        sid = str(uuid.uuid4())
        _write_metadata(d, sid, "control", finished=True)
        self.assertEqual(load_saved_group(d, sid), "control")

    def test_returns_none_when_argument_groups_empty(self):
        """Metadata written by submit_demographics (before init_if_needed finishes)
        has argument_groups=[]. Must NOT be treated as a completed init."""
        d = tmp()
        sid = str(uuid.uuid4())
        # Simulate metadata written mid-session (e.g. from submit_demographics)
        data = {
            "session_id": sid,
            "branch": "dev",
            "experimental_group": "experimental",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "argument_groups": []  # ← empty: init_if_needed not yet finished
        }
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            json.dump(data, fh)
        self.assertIsNone(load_saved_group(d, sid))

    def test_returns_group_when_argument_groups_populated(self):
        """Metadata with argument_groups set means init_if_needed completed."""
        d = tmp()
        sid = str(uuid.uuid4())
        data = {
            "session_id": sid,
            "branch": "dev",
            "experimental_group": "control",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "argument_groups": ["arguments_group_2", "arguments_group_3", "arguments_group_4"]
        }
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            json.dump(data, fh)
        self.assertEqual(load_saved_group(d, sid), "control")

    def test_returns_none_for_invalid_group_value(self):
        d = tmp()
        sid = str(uuid.uuid4())
        data = {"session_id": sid, "experimental_group": "invalid_value"}
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            json.dump(data, fh)
        self.assertIsNone(load_saved_group(d, sid))

    def test_handles_corrupt_file(self):
        d = tmp()
        sid = str(uuid.uuid4())
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            fh.write("CORRUPT {{")
        self.assertIsNone(load_saved_group(d, sid))

    def test_reconnection_scenario(self):
        """Simulate: session assigned 'experimental', WebSocket drops, state rebuilds.
        The metadata must have argument_groups populated to be valid."""
        d = tmp()
        sid = str(uuid.uuid4())
        # Simulate metadata written at the END of init_if_needed (argument_groups populated)
        data = {
            "session_id": sid,
            "branch": "main",
            "experimental_group": "experimental",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "argument_groups": ["arguments_group_1", "arguments_group_2", "arguments_group_3"]
        }
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            json.dump(data, fh)
        restored = load_saved_group(d, sid)
        self.assertEqual(restored, "experimental")

    def test_mid_session_metadata_not_detected_as_reconnection(self):
        """Exact reproduction of the submit_demographics false positive bug.
        Metadata exists but argument_groups is empty → must NOT restore group."""
        d = tmp()
        sid = str(uuid.uuid4())
        # This is what submit_demographics writes before init_if_needed finishes
        data = {
            "session_id": sid,
            "branch": "dev",
            "experimental_group": "experimental",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "argument_groups": []  # ← init_if_needed not finished yet
        }
        with open(os.path.join(d, f"{sid}_metadata.json"), "w") as fh:
            json.dump(data, fh)
        self.assertIsNone(load_saved_group(d, sid))


# ===========================================================================
# Integration
# ===========================================================================

class TestFullFlow(unittest.TestCase):

    def test_no_premature_counting(self):
        d = tmp()
        sid_1 = str(uuid.uuid4())
        # Before writing metadata, current session must not count
        exp, ctrl = get_group_counts(d, "main", current_session_id=sid_1)
        self.assertEqual((exp, ctrl), (0, 0))
        # After writing
        group_1 = assign_group(sid_1, exp, ctrl)
        _write_metadata(d, sid_1, group_1, finished=True)
        # Next session sees it
        sid_2 = str(uuid.uuid4())
        exp2, ctrl2 = get_group_counts(d, "main", current_session_id=sid_2)
        self.assertEqual(exp2 + ctrl2, 1)

    def test_balancing_over_20_sessions(self):
        d = tmp()
        groups = []
        for _ in range(20):
            sid = str(uuid.uuid4())
            exp, ctrl = get_group_counts(d, "main", current_session_id=sid)
            group = assign_group(sid, exp, ctrl)
            groups.append(group)
            _write_metadata(d, sid, group, finished=True)
        exp_total = groups.count("experimental")
        ctrl_total = groups.count("control")
        self.assertLessEqual(abs(exp_total - ctrl_total), 1,
            f"Expected balanced split, got exp={exp_total} ctrl={ctrl_total}")

    def test_dev_sessions_dont_affect_main(self):
        d = tmp()
        for _ in range(5):
            _write_metadata(d, str(uuid.uuid4()), "experimental",
                            branch="dev", finished=True)
        exp, ctrl = get_group_counts(d, "main")
        self.assertEqual((exp, ctrl), (0, 0))


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestGetGroupCounts, TestAssignGroup, TestLoadSavedGroup, TestFullFlow]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
