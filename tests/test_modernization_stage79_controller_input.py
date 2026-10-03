"""ROM-free executable regressions for the actual C runner's input predicate.

The predicate is extracted from the production harness and compiled, not
reimplemented in Python. The dropped-input regression also executes unchanged
against the pre-repair runner and must fail there.
"""
from __future__ import annotations
import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/mgba_battle_policy_smoke.c"


class ControllerInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RUNNER.read_text()
        cls.body = cls.source.split("static void policy_run_raid_controller_round(", 1)[1].split(
            "static bool policy_normal_battle_after_raid(", 1)[0]
        matches = re.findall(
            r"if \((gate != 0.*?)\) \{\s+uint32_t pulse_start", cls.body, re.S)
        if len(matches) != 1:
            raise AssertionError("expected exactly one controller pulse predicate")
        predicate = matches[0].replace("evidence->frames", "frames")
        cls.directory = tempfile.TemporaryDirectory(prefix="stage79-controller-input-")
        cls.addClassCleanup(cls.directory.cleanup)
        directory = Path(cls.directory.name)
        source = directory / "predicate.c"
        source.write_text("#include <stdint.h>\n"
            "int pulse(uint8_t gate, uint8_t latched_gate, uint32_t frames, uint32_t next_selection_press) {\n"
            "  (void)frames; (void)next_selection_press;\n"
            f"  return {predicate};\n" + "}\n")
        library = directory / "predicate.so"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                        str(source), "-o", str(library)], check=True, capture_output=True, text=True)
        cls.library = ctypes.CDLL(str(library))
        cls.pulse = cls.library.pulse
        cls.pulse.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint32, ctypes.c_uint32]
        cls.pulse.restype = ctypes.c_int

    def test_latched_selection_retries_after_deadline(self):
        for gate in (1, 2, 3):
            with self.subTest(gate=gate):
                self.assertEqual(self.pulse(gate, gate, 1530, 1530), 1,
                                 "dropped input must be retried after the release interval")

    def test_latched_selection_does_not_repeat_before_deadline(self):
        for gate in (1, 2, 3):
            for frame in range(1501, 1530):
                self.assertEqual(self.pulse(gate, gate, frame, 1530), 0)

    def test_unrecognized_gate_never_generates_input(self):
        for frame in (0, 1530, 20000):
            self.assertEqual(self.pulse(0, 0, frame, 0), 0)
            self.assertEqual(self.pulse(0, 1, frame, 0), 0)

    def test_new_selection_can_be_acknowledged_immediately(self):
        self.assertEqual(self.pulse(2, 1, 1504, 1530), 1)
        self.assertEqual(self.pulse(3, 2, 1508, 1534), 1)
        self.assertEqual(self.pulse(1, 0, 1512, 1538), 1)

    def test_intro_and_message_keep_their_existing_timers(self):
        for gate in (4, 5):
            self.assertEqual(self.pulse(gate, gate, 1500, 1530), 1)

    def test_menu_that_ignores_first_press_is_not_permanently_latched(self):
        presses = []
        latched, deadline = 0, 0
        for frame in range(100):
            if self.pulse(1, latched, frame, deadline):
                presses.append(frame)
                latched, deadline = 1, frame + 30
        self.assertEqual(presses, [0, 30, 60, 90])

    def test_retry_deadline_is_updated_and_keys_are_released(self):
        self.assertIn("POLICY_RAID_SELECTION_RETRY_INTERVAL = 30", self.source)
        self.assertRegex(self.body, r"next_selection_press = pulse_start\s*\+ POLICY_RAID_SELECTION_RETRY_INTERVAL;")
        self.assertIn("policy_run_raid_frames(core, evidence, 1, 2);", self.body)
        self.assertIn("policy_run_raid_frames(core, evidence, 0, 2);", self.body)
        self.assertIn("frame < POLICY_RAID_STATE_INPUT_LIMIT", self.body)


if __name__ == "__main__":
    unittest.main()
