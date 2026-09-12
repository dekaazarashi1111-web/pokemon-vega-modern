#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one preimage, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "tools/mgba_pr16_generic_form_carry.c",
    """    /* Entry run 34662054112 proved the authored-host ordering. Runtime helper
     * mapping then showed FINAL_LEAGUE_CLEARED is ledger 20, while ledger 21
     * is the distinct League II condition. Set only the Shaymin row owner. */
""",
    """    /* Entry run 34662054112 proved the authored-host ordering. Collection
     * Supply unlock_satisfied() requires league_ii_cleared plus either the
     * vega_hall_of_fame save field or Hall of Fame flag for FINAL_LEAGUE.
     * Ledger byte 20 is not read by that predicate. Set its exact backings. */
""",
)
replace_once(
    "tools/mgba_pr16_generic_form_carry.c",
    "    write8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20,1U);\n",
    "    write8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II,1U);\n",
)
replace_once(
    "tools/mgba_pr16_generic_form_carry.c",
    """        && read8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20)==1U
        && read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==0U
""",
    """        && read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==1U
""",
)
replace_once(
    "tools/mgba_pr16_generic_form_carry.c",
    """    a_require(m_flag_value(c)==1U && read8(c,QOL_LEDGER+QOL_LEDGER_HALL_OF_FAME)==1U
        && read8(c,QOL_LEDGER+0x73FU)==1U && read8(c,QOL_LEDGER+0x745U)==1U,
""",
    """    a_require(m_flag_value(c)==1U && read8(c,QOL_LEDGER+QOL_LEDGER_HALL_OF_FAME)==1U
        && read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==1U
        && read8(c,QOL_LEDGER+0x73FU)==1U && read8(c,QOL_LEDGER+0x745U)==1U,
""",
)
replace_once(
    "tests/test_pr16_generic_form_carry.py",
    """        final_league = before_guard.index(
            "write8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20,1U)"
        )
""",
    """        league_ii = before_guard.index(
            "write8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II,1U)"
        )
""",
)
replace_once(
    "tests/test_pr16_generic_form_carry.py",
    """        self.assertLess(hof_mirror, final_league)
        self.assertLess(final_league, host_progress)
""",
    """        self.assertLess(hof_mirror, league_ii)
        self.assertLess(league_ii, host_progress)
""",
)
replace_once(
    "tests/test_pr16_generic_form_carry.py",
    """        self.assertIn("read8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20)==1U", before_guard)
        self.assertIn("read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==0U", before_guard)
        self.assertNotIn("write8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II,1U)", before_guard)
""",
    """        self.assertEqual(
            before_guard.count("read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==1U"),
            2,
        )
        self.assertNotIn("write8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20,1U)", before_guard)
""",
)
replace_once(
    ".github/workflows/pr16-generic-form-carry.yml",
    """# Runtime maps FINAL_LEAGUE_CLEARED to ledger 20 and League II to ledger 21;
# acceptance sets only final-league before the one pre-map finalize.
""",
    """# Runtime FINAL_LEAGUE requires league_ii_cleared plus Hall of Fame;
# ledger byte 20 is not read by this predicate. Acceptance sets the exact
# backing fields before the one pre-map finalize and verifies them post-load.
""",
)
