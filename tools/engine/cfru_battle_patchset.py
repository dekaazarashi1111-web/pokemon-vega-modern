"""固定CFRU-JPのROM書換えをT06 battle coreだけへ縮退する。

上流の ``hooks`` / ``bytereplacement`` / ``repoints`` 等は、戦闘処理と
overworld・save・daycare・start menuの書換えを同じ制御ファイルに持つ。
このmoduleは固定sourceとT02 address auditを照合し、T06で許可したsection
（および明示したmixed section内のrecord）だけを選ぶ fail-closed boundaryで
ある。render APIは文字列を返すだけでfilesystemへ書き込まない。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
EXPECTED_CFRU_TREE = "f4424af017abd01afe2d2deb833fb67275f03804"
EXPECTED_PROFILE = "factory-like"
EXPECTED_AUDIT_SHA256 = "e6ac294cef03599ca33c13fb44472d03daefe2a84f8849f66e92621c21e01f10"

CONTROL_FILE_HASHES: Mapping[str, str] = {
    "hooks": "19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5",
    "bytereplacement": "98d0e13da0563c15f11435fd7f9f58f6d3220af47d4f12025730596932dfae00",
    "repoints": "b387e4239d00a59698407b1837b5573504bcb172fb41cae6afb7265c1008a12d",
    "repointall": "5aaac92950bb01fdf40ca8e16f0e097774afb8d892da760b804bb531c0482df3",
    "routinepointers": "dcc05504a939cb1876d1b569fb11a33021908bad4d9af7ed66ff74782b88ca24",
    "special_inserts.asm": "1a73b0f4cd18c3d366d2c9919e20f1708353a9f8fe901d30826f9aed58581ec6",
}

CONTROL_KINDS: Mapping[str, str] = {
    "hooks": "hook",
    "bytereplacement": "byte_replacement",
    "repoints": "repoint",
    "repointall": "repointall",
    "routinepointers": "routine_pointer",
    "special_inserts.asm": "special_insert",
}

ALLOWED_AUDIT_CLASSIFICATIONS = frozenset({"CFRU", "PORT", "SAME_TARGET"})
NON_CONTROL_SOURCES = frozenset({"scripts/make.py", "songs"})

# build_patchsetの結果を更新する時は、固定source/auditを再監査してから同時に
# 更新する。placeholderではなく、選択write IDとdomain countsのhard gateである。
EXPECTED_PATCHSET_WRITE_COUNT = 955
EXPECTED_WRITE_IDS_SHA256 = "fde2c57b7d57b3df4baeb0101d69ea33e9e9401d1bd09d5cb5ec9254d4ee01f0"
EXPECTED_DOMAIN_COUNTS: Mapping[str, int] = {
    "ability": 138,
    "ai": 12,
    "animation": 40,
    "battle_setup": 7,
    "battle_ui": 135,
    "capture": 55,
    "direct_dependency": 293,
    "facility": 28,
    "item": 76,
    "raid": 21,
    "turn_move": 150,
}


class BattlePatchsetError(ValueError):
    """固定入力またはT06 scope分類が契約から外れた。"""


@dataclass(frozen=True)
class SectionRule:
    disposition: str
    domain: str
    reason: str


@dataclass(frozen=True)
class ControlSection:
    filename: str
    title: str
    header_line: int
    start_line: int
    end_line_exclusive: int
    disposition: str
    domain: str
    reason: str

    @property
    def key(self) -> str:
        return f"{self.filename}:{self.header_line}:{self.title}"


@dataclass(frozen=True)
class PatchWrite:
    write_id: str
    sequence: int
    filename: str
    source_line: int
    source_kind: str
    symbol: str
    start: int
    end_exclusive: int
    classification: str
    section_key: str
    domain: str


@dataclass(frozen=True)
class BattlePatchset:
    profile: str
    input_hashes: tuple[tuple[str, str], ...]
    sections: tuple[ControlSection, ...]
    writes: tuple[PatchWrite, ...]
    audit_row_items: tuple[tuple[tuple[str, str], ...], ...]
    omitted_write_ids: tuple[str, ...]
    rendered_files: tuple[tuple[str, str], ...]
    fingerprint: str

    @property
    def write_ids(self) -> tuple[str, ...]:
        return tuple(row.write_id for row in self.writes)

    @property
    def domain_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(row.domain for row in self.writes).items()))

    @property
    def classification_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(row.classification for row in self.writes).items()))

    @property
    def kind_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(row.source_kind for row in self.writes).items()))

    def render(self) -> dict[str, str]:
        """sandboxへ渡せるfile名→内容を新しいdictで返す（書込みなし）。"""

        return dict(self.rendered_files)

    def selected_audit_rows(self) -> tuple[dict[str, str], ...]:
        """expected byte等を含む元audit全列を、選択順のcopyとして返す。"""

        return tuple(dict(items) for items in self.audit_row_items)

    def manifest(self) -> dict[str, object]:
        """report/metadataへ埋め込める決定的manifestを返す。"""

        return {
            "schema_version": 1,
            "profile": self.profile,
            "source": {
                "commit": EXPECTED_CFRU_COMMIT,
                "tree": EXPECTED_CFRU_TREE,
                "inputs": dict(self.input_hashes),
            },
            "write_count": len(self.writes),
            "write_ids_sha256": _stable_digest(list(self.write_ids)),
            "classification_counts": self.classification_counts,
            "kind_counts": self.kind_counts,
            "domain_counts": self.domain_counts,
            "omitted_write_count": len(self.omitted_write_ids),
            "rendered_sha256": {
                name: _sha256(text.encode("utf-8"))
                for name, text in self.rendered_files
            },
            "fingerprint": self.fingerprint,
        }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_digest(value: object) -> str:
    encoded = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return _sha256(encoded)


def _included(domain: str, reason: str) -> SectionRule:
    return SectionRule("INCLUDE", domain, reason)


def _mixed(domain: str, reason: str) -> SectionRule:
    return SectionRule("MIXED", domain, reason)


def _excluded(reason: str) -> SectionRule:
    return SectionRule("EXCLUDE", "excluded", reason)


def _rules() -> dict[str, dict[str, SectionRule]]:
    """固定sourceの全sectionを列挙する。未登録titleは必ず拒否する。"""

    hooks_include = {
        "Emit Functions": ("battle_ui", "battle controller emit ABI"),
        "Battle Terrain Functions": ("battle_setup", "battle terrain setup"),
        "Other Battle Stuff": ("turn_move", "normal battle turn/move core"),
        "Multi Hooks": ("turn_move", "double/NPC partner multi core"),
        "AI Hooks": ("ai", "fixed CFRU Battle_AI entrypoints"),
        "Mega Hooks": ("turn_move", "isolated mechanic entrypoints"),
        "Battle Animation Hooks": ("animation", "battle animation dispatch"),
        "Poke Ball Hooks": ("capture", "capture and ball battle path"),
        "Illusion Hooks": ("ability", "battle-local ability presentation"),
    }
    hooks_mixed = {
        "Dynamax Hooks": ("raid", "raid/Dynamax plus unrelated summary/field helpers"),
        "Overworld Hooks": ("battle_setup", "trainer battle setup mixed with map movement"),
        "Party Menu Hooks": ("battle_ui", "switch/facility selection mixed with field party UI"),
        "Other Hooks": ("direct_dependency", "stat/item/facility helpers mixed with Pokerus"),
        "Scrolling Multichoice": ("battle_ui", "critical capture/level UI mixed with field text"),
    }
    hooks_excluded = {
        "__preamble__", "Wild Encounter Hooks", "Roamer Hooks", "Save Expansion Hooks",
        "Main Menu Hooks", "DNS", "Shop", "Select-From-PC", "Keypad",
        "Character Customization", "Pre-Battle Mughots", "Dynamic Overworld Palettes",
        "Whiteout Hack", "Summary Screen", "Hall of Fame Fix", "Unhidden Power",
        "Evolution Methods", "Follow Me", "Learn Move", "Pokedex", "Daycare",
        "Shiny Charm", "TM/HM/Tutor Expansion", "Reusable TMs", "Start Menu",
        "Pokemon Storage System", "Updated Repel System", "Bag", "Move Reminder",
        "Triple Layer Blocks", "Expand Coins", "Safari Zone",
    }
    hooks: dict[str, SectionRule] = {
        title: _included(domain, reason)
        for title, (domain, reason) in hooks_include.items()
    }
    hooks.update(
        {title: _mixed(domain, reason) for title, (domain, reason) in hooks_mixed.items()}
    )
    hooks.update({title: _excluded("Vega field/story/menu/save ownership") for title in hooks_excluded})

    byte_include: dict[str, tuple[str, str]] = {
        "Nop Out End Turn 1,": ("turn_move", "CFRU end-turn dispatcher"),
        "Nop Out Incorrect Focus Punch Activation": ("turn_move", "move execution fix"),
        "Skip Encore Force Move - Allow Target Check": ("turn_move", "move target validation"),
        "Fix CMD49 References": ("turn_move", "battle script command ABI"),
        "Fix ThrashConfuses End2 -> Return": ("turn_move", "battle script return ABI"),
        "Remove Ditto Palette Fading": ("animation", "battle transform animation"),
        "Update ReloadHealthBar": ("battle_ui", "battle healthbar reload"),
        "Absorb Rebrancher Removal": ("turn_move", "battle script branch"),
        "Restore End Turn PerishSong_FutureSight Func Call (For Dynamax)": ("raid", "Dynamax end-turn dependency"),
        "Restore Old Cancel Multi Turn Moves": ("turn_move", "multi-turn cancellation"),
        "Shorter Confusion Hit String": ("battle_ui", "battle message encoding"),
        "Rain Dish Heal String": ("battle_ui", "battle message encoding"),
        "Another Heal String": ("battle_ui", "battle message encoding"),
        "Follow Me String": ("battle_ui", "move message; not follower system"),
        "Suction Cups String": ("battle_ui", "ability message"),
        "Lightning Rod String": ("battle_ui", "ability message"),
        "Safeguard Strings": ("battle_ui", "status message"),
        "Curse String": ("battle_ui", "move message"),
        "Grudge String": ("battle_ui", "move message"),
        "Capture Pokemon String": ("capture", "capture message"),
        "Crunch Description String": ("turn_move", "T04 move description bridge"),
        "Stat Raising Item String": ("battle_ui", "battle item message"),
        "Bind String": ("battle_ui", "volatile status message"),
        "Stas Name": ("battle_ui", "volatile status name"),
        "New Faint BS Command": ("turn_move", "faint command ABI"),
        "Poison Stuff": ("turn_move", "status execution"),
        "Baton Pass Helper": ("turn_move", "switch state transfer"),
        "Gained EXP Buffer Fix": ("battle_ui", "experience result text"),
        "Tag Team Fixes": ("turn_move", "NPC partner multi"),
        "Status Conditions Strings Table": ("battle_ui", "status strings"),
        "Old PokeBall Expansion Data Reset": ("capture", "ball data ABI"),
        "Poke Ball Limiter Removal": ("capture", "expanded ball IDs"),
        "Other Poke Ball Stuff": ("capture", "capture/raid ball behavior"),
        "atkF3_trygivecaughtmonnick Fixes": ("capture", "capture completion"),
        "Remove Old Mega Hooks": ("turn_move", "single mechanic hook ownership"),
        "Remove Old Illusion Hooks": ("ability", "single ability hook ownership"),
        "Animations": ("animation", "battle animation group"),
        "Hydro Pump Particle Update": ("animation", "move particle"),
        "Shiny Anim Fix": ("animation", "battle shiny animation"),
        "Needle Animation Fix": ("animation", "move/battle UI animation data"),
        "Physical Special Split Icon Loader": ("battle_ui", "battle move category icon"),
        "Move Selection Battle Windows": ("battle_ui", "battle move selection layout"),
        "Faster Battle Intro": ("battle_ui", "battle intro state timing"),
        "X-Items Gen 7 Update - +2 Stat Stage": ("item", "battle item semantics"),
        "Expand Type Name Length": ("direct_dependency", "canonical type name stride"),
        "Expand Move Name Length": ("direct_dependency", "canonical move name stride"),
        "Add Vu": ("battle_ui", "Japanese battle font glyph dependency"),
        "Fix Level String": ("battle_ui", "battle healthbox level rendering"),
        "Move Description Load": ("direct_dependency", "canonical move description table"),
        "Item icon Limit": ("item", "expanded item ID/icon boundary"),
        "Ability Expansion": ("ability", "16-bit ability ABI across battle routines"),
        "HP 4 Digits": ("battle_ui", "battle HP rendering"),
    }
    byte_known = {
        "__preamble__", "Optional Byte Changes", "Don't Count Eggs Healing PKMN Centre",
        "Extend Direct Sound Tracks", "Fix Movement Type 0xC (Hidden)",
        "Remove GF Evolution Limiters", "Disable Plot Related Trade Restrictions",
        "Fix Pokedex Species Issue", "Display Foreign Pokemon's ID even without National Dex",
        "PC Boxes Use More Wallpapers", "Increase Max Money to 9999999",
        "Really Tall Grass & Micro Grass Fix", "Snowflake Fix", "Faster Bike Speed",
        "End of Optional Byte Changes", "Remove Things", "Remove Help System",
        "Remove Deoxys Stat Changes", "Remove Deoxys Trade Limiter - b 0x4E590",
        "Remove Old Evolution Move Code", "Remove Old D/N Wild Switch Code",
        "Remove Danills Givepokemon hack", "Remove Randomizer Hook",
        "Remove Previous Quest And Free Up Space", "Remove Part of Old Auto-Run Code",
        "Remove Old Magma Armor + Flame Body ASM", "Remove DNS Palette Fade Disruptor",
        "Remove Old TM Expansion Stuff", "Remove Old Move Reminder Expansion Code",
        "Remove Shiny Quagsire's Bag Selection Hack", "Remove Old Item Picture Find Code",
        "Remove Old Whiteout screen fix", "Remove Old Overworld Form Change",
        "Remove Old End Battle Sky Battle Revert", "Remove Old JPAN Engine",
        "Remove Old End Turn Battle Scripts", "Remove Old Auto Run Code", "Remove Old RTC",
        "Remove Old DNS Seasons Code", "Remove Old Field Move Expansion",
        "Remove Old GetDaycareState code", "Remove Ghost Battles", "Save Expansion",
        "Remove Save Encryption", "Update Routines", "Restore Old Functions and Scripts",
        "Restore Old Sun Continues BS", "Remove Mr. DS Roost", "Remove Fixed Ability Prevention",
        "Black Flute String", "White Flute String", "Remove Old Flute Wild Code",
        "Mart Price Length Increase", "Breeding Ball Inheritance Fix",
        "Max Level HP Updates", "Lower EV Cap to 252",
        "Eggs Hatch at Level 1", "Friendship Event Updates", "Grow Level",
        "League Battle, TM/HM, Walking", "Dexnav", "Pokedex Screen Stats",
        "Expanded Boxes", "Expanded Bag", "Helpers For Sand Footstep Noise",
        "Expanded Pokedex RAM", "Seen Flags @0x202583C", "Caught Flags @0x20258B9",
        "Expand Coins", "Fix Ghost Battle String", "Increase Tutors to 72 (64 Regular + 8 Special)",
        "IsPokemonStorageFull special", "New Field Moves",
        "Help Fix Evolution Battle Terrain After Battle", "Remove Item Use Animation",
        "Footstep Noises", "Fix Slow Camera Update (OverworldBasic - see special_inserts.asm)",
        "LR Button Fixes", "Split Icons in Move Reminder UI", "Split Icons in TM Case",
        "No Giving TMs To Hold By Choosing Party Menu Give", "Ability Description Load",
        "MoveEventObjectToMapCoords",
        "Specific For Unbound, overrites a hook that shouldn't be there with vanilla data.",
        "Unbound Give All Pokes Guy", "Battle BG", "Box Pokemon Name Fix",
    }
    byte_rules = {
        title: _included(domain, reason)
        for title, (domain, reason) in byte_include.items()
    }
    byte_rules["Decryption"] = _mixed(
        "direct_dependency",
        "Pokemon payload decryption is required by linked battle code; save-key writes stay Vega-owned",
    )
    byte_rules["Max Level Updates"] = _mixed(
        "direct_dependency",
        "gExperienceTables repoints require the matching 256-row stride only; level-cap/UI bytes remain Vega-owned",
    )
    byte_rules.update({title: _excluded("non-battle global/field/save/content mutation") for title in byte_known})

    repoints = {
        "__preamble__": _excluded("include preamble"),
        "Tables": _mixed("direct_dependency", "battle tables mixed with save offsets"),
        "Scripts": _mixed("turn_move", "battle scripts mixed with field item scripts"),
        "Wild -> The Wild": _excluded("inactive localization candidates"),
        "The Foe -> The Opposing": _excluded("inactive localization candidates"),
        "Other Strings": _mixed("battle_ui", "battle strings mixed with field/loss strings"),
        "Gen 4 Player OW Running Fix": _excluded("overworld animation and trainer event"),
        "Battle Scripts": _included("turn_move", "battle script pointers"),
        "Battle Transitions": _included("battle_ui", "battle transition tables"),
        "Poke Ball Expansion": _included("capture", "capture tables"),
        "Graphics": _mixed("battle_ui", "battle graphics mixed with surf/trade graphics"),
        "PC Selection BRM": _excluded("PC/storage UI"),
        "Expanded Text Buffers": _excluded("field script/Pokedex helper"),
        "New Naming Screen": _excluded("naming UI"),
        "New Field Moves": _excluded("field party UI"),
        "Bag Sorter": _excluded("field bag UI"),
        "Grass Field Effects and Footstep Noises": _mixed(
            "animation", "critical-capture table mixed with field effects"
        ),
        "Start Menu": _excluded("start menu and UNBOUND content"),
    }

    repointall = {
        "__preamble__": _excluded("comment preamble"),
        "Repoints all pointers found at given location": _excluded("comment preamble"),
        (
            "(Eg. repoints pointer located at 0x8016364 which is 0x81D65A8 "
            "in vanilla, does not repoint 0x8016364)"
        ): _included(
            "direct_dependency", "canonical move/ability battle tables"
        ),
        "Poke Ball Stuff": _included("item", "ball/item canonical tables"),
    }

    routine = {
        "__preamble__": _excluded("include preamble"),
        "Tag Battle Fixes": _included("turn_move", "NPC partner multi completion"),
        "Script Commands": _excluded("field script command table"),
        "Specials": _mixed("facility", "facility/raid/stat specials mixed with field/story specials"),
        "Field Effects": _excluded("field effects"),
        "Expanded Text Buffers": _excluded("field script buffers"),
        "Character Customization": _excluded("overworld sprites"),
        "Dex Nav": _excluded("DexNav"),
        "Second Options Menu": _excluded("options menu"),
        "Item Functions": _excluded("field evolution item"),
        "Nicknaming": _excluded("naming UI"),
        "PSS Icons": _included("battle_ui", "physical/special/status icon routine"),
        "Expand Coins": _excluded("field currency scripts"),
        "Animations": _included("animation", "battle item-steal animation callback"),
        "Dive": _excluded("map movement"),
        "Muddy Slope Forced Movement": _excluded("map movement"),
        "Battle VBlank": _included("battle_ui", "battle VBlank callbacks"),
    }

    special_include = {
        "Ability Expansion Base Stats": ("ability", "expanded ability/base-stat ABI dependency"),
        "Ability Expansion gBattleMons Fix": ("ability", "16-bit battle ability field"),
        "Ability Expansion gLastUsedAbility Fix": ("ability", "16-bit last-used ability field"),
        "Hidden Abilities - Various Something": ("ability", "hidden ability battle access"),
        "Hidden Abilities - Player": ("ability", "player battle ability load"),
        "Hidden Abilities - Opponent": ("ability", "opponent battle ability load"),
        "AI Vanilla Item Use Bug Fix": ("ai", "fixed CFRU AI item choice"),
    }
    special_mixed = {
        "Max Level Limiter": ("turn_move", "transform personality fixes share a max-level block"),
    }
    special_excluded = {
        "__preamble__", "Game Speed Up", "Dynamic Overworld Palette - part of hook at 0x779c",
        "Pokedex Flags Banned Battle Types", "Vanilla Roamer Bug Fix", "Safari Zone Ball Count",
        "Max Level Limiters", "Roamer IVs Fix", "Hidden Abilities - Summary Screen",
        "Max Level - Limiter", "Max Level Hack - Limiter", "Remove Deoxys & Mew Trade Restrictions",
        "Fix Slow Camera Update", "Character Customization",
        "Dynamic Overworld Palettes & More OW Sprites", "Remove Add/Delete Item Limiter",
        "GetBagItemQuanity", "Triple Layer Blocks", "More OW Sprites",
        "Dynamic Overworld Palettes & More OW Sprites: Field Effects",
        "Remove Caught Mon Pokedex 151 Limiter", "Remove LR Change Bag Pockets",
        "Remove TM Animation", "Stay On Item Screen - Medicine", "Stay On Item Screen - PP Up",
        "Max Level Hack - Rare Candies", "Max Level Hack - Summary Screen",
        "Hidden Abilities - Ability Names", "Max Level Hack - Summary Screen Exp Display",
        "Losing Trainer Battle 9", "Dynamic Overworld Palettes", "Multichoice Pointers",
        "Multichoice Width",
    }
    special = {
        title: _included(domain, reason)
        for title, (domain, reason) in special_include.items()
    }
    special.update(
        {title: _mixed(domain, reason) for title, (domain, reason) in special_mixed.items()}
    )
    special.update({title: _excluded("non-battle field/UI/progression mutation") for title in special_excluded})

    return {
        "hooks": hooks,
        "bytereplacement": byte_rules,
        "repoints": repoints,
        "repointall": repointall,
        "routinepointers": routine,
        "special_inserts.asm": special,
    }


_PREPROCESSOR_WORDS = frozenset(
    {"include", "ifdef", "ifndef", "if", "elif", "else", "endif", "define", "undef", "pragma", "error"}
)


def _control_heading(raw: str) -> str | None:
    stripped = raw.strip()
    if not stripped.startswith("#"):
        return None
    title = stripped.lstrip("#").strip().strip("#").strip()
    if not title:
        return None
    if title.split(None, 1)[0].lower() in _PREPROCESSOR_WORDS:
        return None
    if re.match(r"^(?:0x)?[0-9A-Fa-f]{6,8}(?:\s|$)", title):
        return None
    tokens = title.split()
    if len(tokens) >= 2 and re.fullmatch(r"(?:0x)?[0-9A-Fa-f]{6,8}", tokens[1]):
        return None
    return title


def _special_headings(lines: Sequence[str]) -> list[tuple[int, str]]:
    headings = [(0, "__preamble__")]
    for index in range(len(lines) - 2):
        if not re.fullmatch(r"@{10,}", lines[index].strip()):
            continue
        if not re.fullmatch(r"@{10,}", lines[index + 2].strip()):
            continue
        match = re.fullmatch(r"@\s*(.*?)\s*", lines[index + 1].strip())
        if match:
            # 1-based title line. Section starts at the first separator, but all
            # active .org records occur after the title line.
            headings.append((index + 2, match.group(1)))
    return headings


def _headings(filename: str, text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    if filename == "special_inserts.asm":
        return _special_headings(lines)
    result = [(0, "__preamble__")]
    result.extend(
        (line_number, title)
        for line_number, raw in enumerate(lines, 1)
        if (title := _control_heading(raw)) is not None
    )
    return result


def classify_control_sections(control_texts: Mapping[str, str]) -> tuple[ControlSection, ...]:
    """全sectionを分類する。未知file/titleはfixed hash検査なしでも拒否する。"""

    rules = _rules()
    unknown_files = set(control_texts) - set(CONTROL_FILE_HASHES)
    missing_files = set(CONTROL_FILE_HASHES) - set(control_texts)
    if unknown_files or missing_files:
        raise BattlePatchsetError(
            f"control file集合が不正です: unknown={sorted(unknown_files)} missing={sorted(missing_files)}"
        )
    sections: list[ControlSection] = []
    for filename in CONTROL_FILE_HASHES:
        text = control_texts[filename]
        lines = text.splitlines()
        headings = _headings(filename, text)
        for index, (header_line, title) in enumerate(headings):
            try:
                rule = rules[filename][title]
            except KeyError as error:
                raise BattlePatchsetError(
                    f"未知sectionを拒否しました: {filename}:{header_line}:{title}"
                ) from error
            next_line = headings[index + 1][0] if index + 1 < len(headings) else len(lines) + 1
            sections.append(
                ControlSection(
                    filename=filename,
                    title=title,
                    header_line=header_line,
                    start_line=header_line + 1 if header_line else 1,
                    end_line_exclusive=next_line,
                    disposition=rule.disposition,
                    domain=rule.domain,
                    reason=rule.reason,
                )
            )
    return tuple(sections)


def _parse_hex(value: str, label: str) -> int:
    try:
        return int(value, 16)
    except ValueError as error:
        raise BattlePatchsetError(f"{label}がhexではありません: {value!r}") from error


def _mixed_domain(filename: str, section: ControlSection, row: Mapping[str, str], raw: str) -> str | None:
    symbol = row["symbol"]
    title = section.title
    token = raw.strip().split()[0] if raw.strip() else ""

    if filename == "bytereplacement" and title == "Decryption":
        return "direct_dependency" if token.upper() in {
            "0803F0B8", "0803F096", "0803F09C", "0803F072", "0803F078",
            "0803F500", "0803FC12", "080401DA",
        } else None

    if filename == "bytereplacement" and title == "Max Level Updates":
        return "direct_dependency" if token.upper() in {
            "0802F6B4", "0802F814", "0802F91C", "0803D364", "0803DF5E",
            "0803DFCA", "08040F50", "08043246", "080497B0", "080E8E38",
            "080E8F98", "080E90A0", "08136E92", "0813B1D2", "08159C70",
            "08159DD0", "08159ED8",
        } else None

    if filename == "hooks" and title == "Dynamax Hooks":
        excluded = {
            "CreateSummaryScreenGigantamaxIconHook", "SummaryScreen_ChangeCaughtBallSpriteVisibility",
            "SummaryScreen_DestroyCaughtBallSprite", "GiveMonToPlayer", "ScriptGiveMon",
        }
        if token in excluded:
            return None
        if token.startswith("ItemId_"):
            return "item"
        if token == "BatonPassEffects":
            return "turn_move"
        return "raid"
    if filename == "hooks" and title == "Overworld Hooks":
        return "battle_setup" if token in {
            "BattleSetup_ConfigureTrainerBattle", "BattleSetup_StartTrainerBattle"
        } else None
    if filename == "hooks" and title == "Party Menu Hooks":
        facility = {
            "DisplayPartyPokemonSelectForBattle", "CursorCb_NoEntry",
            "LoadMaxNumPokemonChooseBattleTowerStringHook", "CursorCb_Enter",
            "IsMonAllowedInBattleTower", "Task_ClosePartyMenuAfterText",
            "CanPokemonSelectedBeEnteredInBattleTower",
        }
        battle = {"ChooseFaintedMonHook", "ChooseFaintedMonCancelHook", "EmitChoosePokemon"}
        if token in facility:
            return "facility"
        if token in battle:
            return "battle_ui"
        return None
    if filename == "hooks" and title == "Other Hooks":
        domains = {
            "CalculateMonStatsNew": "direct_dependency",
            "SetMonHeldItemHook": "item",
            "GetMonAbility": "ability",
            "SetMonExpWithMaxLevelCheck": "direct_dependency",
            "GiveRandomFrontierMonByTier": "facility",
            "GetMegaSpecies": "turn_move",
            "SetMonPreventsSwitchingString": "turn_move",
        }
        return domains.get(token)
    if filename == "hooks" and title == "Scrolling Multichoice":
        if token.startswith("CriticalCapture") or token in {
            "SpriteCB_InitThrownBallBouncing", "PlayerHandleSuccessBallThrowAnim",
            "PlayerHandleBallThrowAnim",
        }:
            return "capture"
        if token.startswith("AutoScrollBattleLevelUpBoxHook"):
            return "battle_ui"
        return None

    if filename == "repoints" and title == "Tables":
        if token == "gSaveSectionOffsets":
            return None
        if token.startswith("gAbility"):
            return "ability"
        if token.startswith("gExperience"):
            return "direct_dependency"
        if token.startswith("gMove") or token.startswith("gBattle"):
            return "turn_move"
        return "battle_ui"
    if filename == "repoints" and title == "Scripts":
        return "turn_move" if token.startswith("BattleScript_") else None
    if filename == "repoints" and title == "Other Strings":
        excluded = {
            "gText_UnknownLocation", "sText_OutofUsablePokemon", "sText_LostAgaintWild",
            "sText_LostAgainstTrainer", "sText_BlackedOut", "gText_UsedVar2WildStronger",
            "gText_UsedVar2WildWeaker", "gText_PokemonAreNeeded",
        }
        return None if token in excluded else "battle_ui"
    if filename == "repoints" and title == "Graphics":
        if token in {"SurfPal", "TradeBallTiles", "TradeBallPal"}:
            return None
        return "battle_ui"
    if filename == "repoints" and title == "Grass Field Effects and Footstep Noises":
        return "capture" if token == "gBattleAnims_Special" else None

    if filename == "routinepointers" and title == "Specials":
        facility_names = {
            *(f"sp{value:03X}" for value in range(0x52, 0x58)),
            *(f"sp{value:03X}" for value in range(0x67, 0x74)),
            "sp0E7",
        }
        raid_names = {*(f"sp{value:03X}" for value in range(0x115, 0x11D))}
        prefix = token.split("_", 1)[0]
        if prefix in facility_names:
            return "facility"
        if prefix in raid_names:
            return "raid"
        if prefix in {"sp097", "sp098"}:
            return "battle_setup"
        if prefix == "sp12F":
            return "direct_dependency"
        if prefix == "sp131":
            return "turn_move"
        return None

    if filename == "special_inserts.asm" and title == "Max Level Limiter":
        # 0x326E2 is the max-level mutation; the following two sites only fix
        # Ditto transform personality and are part of battle state correctness.
        return "turn_move" if token.lower() in {".org"} and re.search(
            r"0x(?:33B48|33D08)\b", raw, re.IGNORECASE
        ) else None

    raise BattlePatchsetError(f"mixed section classifierがありません: {section.key} ({symbol})")


def _section_for_line(
    sections_by_file: Mapping[str, Sequence[ControlSection]], filename: str, line: int
) -> ControlSection:
    matches = [
        section
        for section in sections_by_file[filename]
        if section.start_line <= line < section.end_line_exclusive
    ]
    if len(matches) != 1:
        raise BattlePatchsetError(f"source lineのsectionが一意でありません: {filename}:{line}")
    return matches[0]


def _load_audit(data: bytes, profile: str) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as error:
        raise BattlePatchsetError(f"address auditがUTF-8ではありません: {error}") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    required = {
        "write_id", "sequence", "engine", "profile", "source_file", "source_line",
        "kind", "symbol", "start", "end_exclusive", "classification",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise BattlePatchsetError("address audit headerが不足しています")
    rows = [dict(row) for row in reader if row.get("engine") == "cfru" and row.get("profile") == profile]
    if not rows:
        raise BattlePatchsetError(f"address auditにprofileがありません: {profile}")
    ids = [row["write_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise BattlePatchsetError("address audit write_idが重複しています")
    return rows


def _render_line_control(
    filename: str, text: str, selected_lines: set[int], sections: Sequence[ControlSection]
) -> str:
    lines = text.splitlines()
    output = [
        "##Generated by tools/engine/cfru_battle_patchset.py; T06 battle-only fixed patchset",
    ]
    # Include files supply literal constants used by bytereplacement and are
    # harmless for other control files. Conditional directives are intentionally
    # flattened to the fixed audit profile by selecting only active audit rows.
    output.extend(raw for raw in lines if raw.startswith('#include "'))
    last_section = ""
    section_map = {
        line: _section_for_line({filename: sections}, filename, line)
        for line in sorted(selected_lines)
    }
    for line_number in sorted(selected_lines):
        section = section_map[line_number]
        if section.key != last_section:
            output.extend(("", f"##T06 {section.domain}: {section.title}"))
            last_section = section.key
        output.append(lines[line_number - 1])
    return "\n".join(output).rstrip() + "\n"


def _special_org_blocks(text: str) -> dict[int, list[str]]:
    lines = text.splitlines()
    # ``special_inserts.asm`` contains C-style block comments with otherwise
    # valid-looking ``.org`` records.  The upstream inserter scans raw text for
    # every .org while GNU as correctly ignores commented records; copying a
    # comment boundary into a filtered file therefore makes those two views
    # disagree and can read past special_inserts.bin.  Remove block comments
    # while preserving the original line count used by address_audit.csv.
    cleaned: list[str] = []
    in_comment = False
    for raw in lines:
        cursor = 0
        visible = ""
        while cursor < len(raw):
            if in_comment:
                end = raw.find("*/", cursor)
                if end < 0:
                    cursor = len(raw)
                    continue
                cursor = end + 2
                in_comment = False
                continue
            start = raw.find("/*", cursor)
            if start < 0:
                visible += raw[cursor:]
                cursor = len(raw)
                continue
            visible += raw[cursor:start]
            cursor = start + 2
            in_comment = True
        cleaned.append(visible)
    if in_comment:
        raise BattlePatchsetError("special_inserts.asm のblock commentが閉じていません")
    starts = [
        line_number
        for line_number, raw in enumerate(cleaned, 1)
        if re.match(r"^\s*\.org\s+", raw)
    ]
    blocks: dict[int, list[str]] = {}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(cleaned) + 1
        blocks[start] = cleaned[start - 1 : end - 1]
    return blocks


def _render_special(text: str, selected_lines: set[int], sections: Sequence[ControlSection]) -> str:
    lines = text.splitlines()
    blocks = _special_org_blocks(text)
    output = [
        ".text", ".align 2", ".thumb", "",
        '.include "../asm_defines.s"', '.include "../battle_script_macros.s"',
        "", "@ Generated battle-only fixed patchset; no field/save/menu .org sites.",
    ]
    last_section = ""
    for line_number in sorted(selected_lines):
        if line_number not in blocks:
            raise BattlePatchsetError(f"special insert audit lineが.orgではありません: {line_number}")
        section = _section_for_line({"special_inserts.asm": sections}, "special_inserts.asm", line_number)
        if section.key != last_section:
            output.extend(
                (
                    "",
                    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                    f"@ T06 {section.domain}: {section.title}",
                    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                )
            )
            last_section = section.key
        output.extend(blocks[line_number])
    return "\n".join(output).rstrip() + "\n"


def build_patchset(
    source_root: Path,
    audit_csv: Path,
    *,
    profile: str = EXPECTED_PROFILE,
    verify_fixed_hashes: bool = True,
    enforce_output_contract: bool = True,
) -> BattlePatchset:
    """固定入力からT06 battle-only patchsetを構築する（副作用なし）。"""

    source_root = Path(source_root)
    audit_csv = Path(audit_csv)
    if profile != EXPECTED_PROFILE:
        raise BattlePatchsetError(f"未監査profileを拒否しました: {profile}")
    if source_root.is_symlink() or not source_root.is_dir():
        raise BattlePatchsetError(f"CFRU source rootが不正です: {source_root}")
    if audit_csv.is_symlink() or not audit_csv.is_file():
        raise BattlePatchsetError(f"address auditが不正です: {audit_csv}")

    control_bytes: dict[str, bytes] = {}
    control_texts: dict[str, str] = {}
    input_hashes: list[tuple[str, str]] = []
    for filename, expected in CONTROL_FILE_HASHES.items():
        path = source_root / filename
        if path.is_symlink() or not path.is_file():
            raise BattlePatchsetError(f"control fileが欠落またはsymlinkです: {filename}")
        data = path.read_bytes()
        actual = _sha256(data)
        if verify_fixed_hashes and actual != expected:
            raise BattlePatchsetError(f"固定CFRU control hash不一致: {filename}: {actual}")
        try:
            text = data.decode("utf-8")
        except UnicodeError as error:
            raise BattlePatchsetError(f"control fileがUTF-8ではありません: {filename}") from error
        control_bytes[filename] = data
        control_texts[filename] = text
        input_hashes.append((filename, actual))

    audit_data = audit_csv.read_bytes()
    audit_hash = _sha256(audit_data)
    if verify_fixed_hashes and audit_hash != EXPECTED_AUDIT_SHA256:
        raise BattlePatchsetError(f"固定address audit hash不一致: {audit_hash}")
    input_hashes.append(("address_audit.csv", audit_hash))

    sections = classify_control_sections(control_texts)
    sections_by_file: dict[str, list[ControlSection]] = {
        filename: [] for filename in CONTROL_FILE_HASHES
    }
    for section in sections:
        sections_by_file[section.filename].append(section)

    rows = _load_audit(audit_data, profile)
    audit_by_id = {row["write_id"]: row for row in rows}
    selected: list[PatchWrite] = []
    omitted: list[str] = []
    selected_lines: dict[str, set[int]] = {filename: set() for filename in CONTROL_FILE_HASHES}
    for row in rows:
        source_file = row["source_file"].replace("\\", "/")
        filename = Path(source_file).name
        if filename not in CONTROL_FILE_HASHES:
            if any(source_file.endswith(suffix) for suffix in NON_CONTROL_SOURCES):
                omitted.append(row["write_id"])
                continue
            raise BattlePatchsetError(f"未知CFRU write sourceを拒否しました: {source_file}")
        if row["kind"] != CONTROL_KINDS[filename]:
            raise BattlePatchsetError(
                f"write kind不一致: {row['write_id']}: {row['kind']} != {CONTROL_KINDS[filename]}"
            )
        try:
            line = int(row["source_line"], 10)
            sequence = int(row["sequence"], 10)
        except ValueError as error:
            raise BattlePatchsetError(f"audit line/sequenceが整数ではありません: {row['write_id']}") from error
        source_lines = control_texts[filename].splitlines()
        if not 1 <= line <= len(source_lines):
            raise BattlePatchsetError(f"audit source_lineが範囲外です: {row['write_id']}")
        raw = source_lines[line - 1]
        if filename == "special_inserts.asm":
            if not re.match(r"^\s*\.org\s+", raw):
                raise BattlePatchsetError(f"special insert source_lineが.orgではありません: {row['write_id']}")
        elif not raw.strip() or raw.strip().startswith("#"):
            raise BattlePatchsetError(f"audit source_lineがactive recordではありません: {row['write_id']}")

        section = _section_for_line(sections_by_file, filename, line)
        if section.disposition == "INCLUDE":
            domain: str | None = section.domain
        elif section.disposition == "EXCLUDE":
            domain = None
        elif section.disposition == "MIXED":
            domain = _mixed_domain(filename, section, row, raw)
        else:
            raise BattlePatchsetError(f"未知section dispositionです: {section.disposition}")
        if domain is None:
            omitted.append(row["write_id"])
            continue
        classification = row["classification"]
        if classification not in ALLOWED_AUDIT_CLASSIFICATIONS:
            raise BattlePatchsetError(
                f"選択writeの分類を拒否しました: {row['write_id']}: {classification}"
            )
        start = _parse_hex(row["start"], f"{row['write_id']}.start")
        end = _parse_hex(row["end_exclusive"], f"{row['write_id']}.end_exclusive")
        if not 0x08000000 <= start < end <= 0x0A000000:
            raise BattlePatchsetError(f"選択write spanがROM範囲外です: {row['write_id']}")
        selected.append(
            PatchWrite(
                write_id=row["write_id"], sequence=sequence, filename=filename,
                source_line=line, source_kind=row["kind"], symbol=row["symbol"],
                start=start, end_exclusive=end, classification=classification,
                section_key=section.key, domain=domain,
            )
        )
        selected_lines[filename].add(line)

    selected.sort(key=lambda row: row.sequence)
    if [row.sequence for row in selected] != sorted(row.sequence for row in selected):
        raise BattlePatchsetError("selected write sequenceが不正です")
    if len({row.write_id for row in selected}) != len(selected):
        raise BattlePatchsetError("selected write_idが重複しています")

    rendered: list[tuple[str, str]] = []
    for filename in CONTROL_FILE_HASHES:
        if filename == "special_inserts.asm":
            text = _render_special(control_texts[filename], selected_lines[filename], sections_by_file[filename])
        else:
            text = _render_line_control(
                filename, control_texts[filename], selected_lines[filename], sections_by_file[filename]
            )
        rendered.append((filename, text))

    ids_digest = _stable_digest([row.write_id for row in selected])
    domains = dict(sorted(Counter(row.domain for row in selected).items()))
    if enforce_output_contract:
        if len(selected) != EXPECTED_PATCHSET_WRITE_COUNT:
            raise BattlePatchsetError(
                f"battle patchset write count drift: {len(selected)} != {EXPECTED_PATCHSET_WRITE_COUNT}"
            )
        if ids_digest != EXPECTED_WRITE_IDS_SHA256:
            raise BattlePatchsetError(f"battle patchset write ID drift: {ids_digest}")
        if domains != dict(EXPECTED_DOMAIN_COUNTS):
            raise BattlePatchsetError(f"battle patchset domain count drift: {domains}")

    fingerprint_payload = {
        "schema_version": 1,
        "profile": profile,
        "source_commit": EXPECTED_CFRU_COMMIT,
        "source_tree": EXPECTED_CFRU_TREE,
        "inputs": input_hashes,
        "write_ids": [row.write_id for row in selected],
        "write_domains": [row.domain for row in selected],
        "rendered": {name: _sha256(text.encode("utf-8")) for name, text in rendered},
    }
    return BattlePatchset(
        profile=profile,
        input_hashes=tuple(input_hashes),
        sections=sections,
        writes=tuple(selected),
        audit_row_items=tuple(
            tuple(audit_by_id[row.write_id].items()) for row in selected
        ),
        omitted_write_ids=tuple(omitted),
        rendered_files=tuple(rendered),
        fingerprint=_stable_digest(fingerprint_payload),
    )


def render_filtered_control_files(
    source_root: Path, audit_csv: Path, *, profile: str = EXPECTED_PROFILE
) -> dict[str, str]:
    """fixed hash/ID/count gateを通したsandbox用制御fileを返す。"""

    return build_patchset(source_root, audit_csv, profile=profile).render()


def select_battle_audit_rows(
    source_root: Path, audit_csv: Path, *, profile: str = EXPECTED_PROFILE
) -> tuple[dict[str, str], ...]:
    """fixed gate済みのT06 writeを、元address audit全列付きで返す。"""

    return build_patchset(
        source_root, audit_csv, profile=profile
    ).selected_audit_rows()
