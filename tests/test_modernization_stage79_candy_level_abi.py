"""Source regression for the native party-level ABI, not runtime PASS evidence.

The frozen Stage78 probe observes EXP 2034 before Rare Candy and 1059860
later. BoxMonData cannot supply the party-only MON_DATA_LEVEL field. Keep
this narrow regression separate from Stage79's actual mGBA acceptance gate.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "overlays/qol_production/qol_production.c"
BAD_LEVEL_READ = re.compile(
    r"\bFN_GET_BOX_MON_DATA\s*\(\s*mon\s*,\s*MON_DATA_LEVEL\s*\)"
)


def candy_body(source: str) -> str:
    """Find the callback definition rather than its forward declaration."""
    definition = re.search(
        r"\bcandy_continue_task\s*\([^;{}]*\)\s*\{", source
    )
    if definition is None:
        raise AssertionError("Rare Candy callback definition is missing")
    start = definition.end()
    depth = 1
    for offset in range(start, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start:offset]
    raise AssertionError("Rare Candy callback definition is not closed")


def reject_box_level_read(source: str) -> None:
    body = candy_body(source)
    if BAD_LEVEL_READ.search(body):
        raise AssertionError(
            "Rare Candy reads party MON_DATA_LEVEL through BoxMonData; "
            "use the native party GetMonData ABI instead"
        )


class CandyLevelABIRegressionTests(unittest.TestCase):
    def test_production_callback_does_not_use_box_level_reader(self):
        reject_box_level_read(SOURCE.read_text(encoding="utf-8"))

    def test_original_bad_reader_is_rejected(self):
        source = "void candy_continue_task(int task) {\n" \
                 " level = (u8)FN_GET_BOX_MON_DATA(mon, MON_DATA_LEVEL);\n}"
        with self.assertRaisesRegex(AssertionError, "BoxMonData"):
            reject_box_level_read(source)

    def test_whitespace_cannot_hide_the_bad_reader(self):
        source = "void candy_continue_task(int task) {\n" \
                 " level = FN_GET_BOX_MON_DATA ( mon,\n MON_DATA_LEVEL );\n}"
        with self.assertRaisesRegex(AssertionError, "BoxMonData"):
            reject_box_level_read(source)

    def test_party_reader_is_not_rejected(self):
        reject_box_level_read(
            "void candy_continue_task(int task) {\n"
            " level = FN_GET_MON_DATA(mon, MON_DATA_LEVEL);\n}"
        )

    def test_missing_callback_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "missing"):
            reject_box_level_read("void another_callback(void) {}")


if __name__ == "__main__":
    unittest.main()
