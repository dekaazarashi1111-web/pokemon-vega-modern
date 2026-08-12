#!/usr/bin/env python3
"""固定CFRU-JPソースから、結合可能な技モデルを決定的に抽出する。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import unicodedata
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
EXPECTED_PRODUCTION_MOVE_COUNT = 0x3E0

# CFRUの356..766は世代順ではない。固定sourceに世代metadataがないため、PokeAPI
# moves.csv（2026-08-13取得）のgeneration_idをsymbol正規形で照合した決定表を埋め込む。
# 実行時network依存はなく、展開JSON SHA-256も検証する。
_GENERATION_MAP_SHA256 = "eb3bf94a8d4db8a250016ed42188f97031b0f9d175cc2c8bc7bcef22b83a30c1"
_GENERATION_MAP_B85 = """
c-mE1%a-IS4*Zv1&$6q#PVX>Q+H_*@<&iGeuiP{LKA{Ir&nhzn2oQRN{O=FvJw+<nKY#rB{U5+E*S)y&$Da>IB~PveUk&!XP
_4btk3T<wAC1bHyAFm@qpPcqB){fT*W6U=zDHu!KmL3I{nOoFYB~}BOGwKFnhQ}u$s2FIg^H=aAmELm*!HfixH!2|+(N3hHR
qqX%v5v+X4ieCaah1(C5k$^mt5S7cr!j=Z@J|ye3Rbg<sx4}S59s^=Nu!QROKX-OZ4b*>gmaQ{bos-?q`|EJttU0uRqaBTW;
$l=J~t{qMOHp=vP%vwdF&OF@**LZ!QLJvtY&N5z>q)WiwHyM|4FGKIQq8C(^MT8=vF?uvvJHnR%OfG22dT*mciO+lNgvg)-~
?3v}R(>Jj!a9+KIn^yVT)_zC%{eZi@14FCK0xBZWC&SqW))b^hIYJ(*~!C!JQ_j>9Uko8@3dbhXma;DXjtMJ%bX*OfC1LMRz
j;r|9m4$HaO{cGpjcEVF?hf;9zs3yj)<<G3p?I8XEoOWV4_Nrt-bH@*-zLJMUTf~^M_A%Y-ST2<awQMLI`wX!9rk3?@YKxC#
<OyIgxOA;_tRgq3sHLH;?1idD7l6gEv}l1)^b`9GP7ywrQwEYSfU^#&$<SRv#Q7Xy5~@H(k)7_>r%olXm;fZZ-e&)r=H4^y~
j$|_$!Cm!1s5=U6v@Oh4L9!RkMFGcu<<((FdG0s^{Rge7P*I3x#0HL)V4s$_BmI$dip%eMDWJJKTN^?S?|hNrQ>cTpUbJjk4
{GD9p)KPf49y1-ML8D=MZ$WjSwx)oq&@UIjNp2xi;epk}HMfr0(^8EPFHhV*vtxr7)?Pd2%4aLzWoV(t!+pLZPu;85ZTI(jC
zxi9Zh;unMj?$!{fhnbnMmS(dZG!T_QVY8$EGC|!bs=p#sJd%J%Nbn(bipn164I%AEy`ABMCWUbBvSi&{OsF#jHrBa`-FYgu
EyuVh9;hUzamny&cWK6;_`8T6C?RK*O7zPR=Q=~U5b}S4lkwGgI)$W8@xbjWTa-t5azI&{wN!i<Jm9ICd><jXxVUW!&4vp-o
RuI3ad;L36fVg#IuW~Ul3xQqhfG1VAtCU&RC{zASz`S#IJ{YLp(%!@Y4O2(jn@@Sy$sCi<EV}Jw>RWO+XR6ZSLDl)cOijG+#
>%GPmEbDV4QugmhD&_TYYzN8wh!zdK{Z<c8`0sO!+`s`lh+4e<(s}=XV;Tk{6^1@#&Cs8W#;VIM3*8F0MZ}_^w$Cm-4La0B2
d?;mA-)GaMr;0}Fu=B(JAf!s750&g*rsxexF|ee=&DXto20Kz*ica~a*9Rq(mQV5L~`JwPCN356Nsuh34_#i<y|%#{=#Znwe
oR0_o495Dr;sm7Jf(7vB5Qn_q~SDkMT!!RP}Yx4P2LEQ$?Vjq|^W(?sej&K`&r({N!7*sJ5VsqPmgX8Ex4aKCcW9)T;+--)w
^fxRklRUC)geO{aoF``i%mAfnu7;8%ePxnZmm-lj{fO%TueXDpNE;PT3yx(z_ZC5^dMFa!B;oKO|E~bX|63vls;e^|6MR6qe
qSpj4;oX3mxT1-3>9}*1}jrhzJ_70CXvqvNO0TkwQfQ<Q|ybK4dscSNp}6~4t*c!``hP5(<2Y`gj#w9F@}X?-C{Vh^(=7-tW
+e9Wlv5Wxoe%^xJC%)qN*eNYwVj=FBI&D5YylK-zu?<03<i-9b<UVOj?*Dp10*k=@tYr{L{m1_h(J{s0WdHPwf7AG7+);djc
V5k~Xd;lKEoqfOeqGEy2TsMphSGKu$$35M2E_FJPiJfneQW@Q>KP<cumP!OAxJhv}*(8%h4w0Rm~YB&`tS0a5RIRC}uADpue
pGc+A~^DTgJz<W>IC4i-sE6}-LIZ@p}1%uUW5#1BYmXQxN7aLj#b96u6A$O)1X>pcwwm!dajY9@)c69QIssxhC)k^i5z~U0i
!G_w26X^+)Lm@#4438To<diu{wSdmVj}OMDks;{a+$FGPbc{~(RYL7(We}DG!fz3ZS>Xi}C<73|h!{-FzU3<}(0L^kQLXmaA
(ya(^d>R+MFlMCrN-a@MKuY2q{&|*V*;SBAo$co1Z}&#b`0O&k_mW}JvDDeJw%Y1SkqZ8aiI9YAgJ!G4t%CTP#K^LSXM)QY$
QbcubT{^%fTfc57mJB2f9ST`i<f9zvM5EY_?1b`Qw_#sc%#mg(FQ1VmkNyKe*e5Kz%nJI<`4hBmbZVKJ1)Exe3)Iy(4s_>6T
QZS}NiiA%^@~?}E#nhX{E|-AR$%K(XeutNj(p;13MmZ7EKR;&tW7y(=%}O|Ak84gd6!#F3Qz^W6~vvaej+k2~^VX@yKVrLKH
3{N~6dqq^XMOm-0}wwT~#c+tfW-00#Ig<c?voDFR=91+%&MkcoL9e|@GKR_BaRq$sPAA<!lBY4Fq)(j6k%G1g<lAz_M0_SY#
A<SLidd7~b^Mz0%av2x}gB#N8^8k0RHYR<n#D~b?``nsVt<WqY`4Xd3cmYZ!wVQIHcM@V?6pqn~3UW+2sT~w*i+7D$uwA$&`
7$Ax`8(*B8;2IbHlA1@T8rJ3Q*4&k#L1W<+B~EpBa0Q}FxpoD9(u~B6zH^!Q=jKttm~=~Wtk55(wCJ<vm|>(<@#>Iij&**ET
003x=u}Dzgagsb?%xY7ee6^ym%Lys?EYr!R5*2pF41y!QGaN4H5Gg5;9IHC_L{CK5z*_w(VYmVPXG_W6#{AmK)+XZZP)EM;h
^lWw1!b8>fzo>xiUe^}r9o6tC(iXp9O*NS@L#%G$i`yeCpFdS5*Sk}bI}vgrWI#$|In;%uesL-F?hD#Ks>kf-H9wi?!4+FFN
!unB*onEGN1kbwP4^fWK;9ANL}y!IsLzdvy=^5I7$w(1BCN)VE|=)`i6yc~>7^S1yL$o&FWDQoUY!mUM5bLDapT%kOAj5%u^
Z~RqYBOCK;8Xu=vCAx61L#m+~F8Yl@DkLue735HM;39`6^C4o#9unlEre7O)!?klW?MJdQd{Jq`(DDoxHZ3DvgDt$2m$&?d1
i7o3ej3Iu!hLxME=?e%N)LXSK-t|-LHu3Vj{JEEzU(6{+QMD87F~VY{owLldtv;0Ip6!H(aX^DX8I~GN_m^%A65VvzYEU`N6
puF0&K^LTOV4+54>F8^;Lf|gwbzpqu`3x1-I8I;WJow0c{5kPQn@u&h#!*M?g8053(Z&S#oRp4sIyQ#e<KW=h4>iS#o*y-9}
0|IUDN$M|ZYD{8fFZ)xL^-le8pLZ#u{=`?ti*fBy%A(jfx
"""

_SOURCE_FILES = (
    "include/constants/moves.h",
    "include/constants/battle_move_effects.h",
    "include/constants/pokemon.h",
    "include/battle.h",
    "include/new/dynamax.h",
    "include/new/z_move_effects.h",
    "src/config.h",
    "src/Tables/battle_moves.c",
    "strings/attack_name_table.string",
    "strings/attack_descriptions.string",
    "assembly/data/attack_anim_table.s",
    "assembly/data/attack_description_table.s",
    "assembly/data/move_effect_table.s",
)

_BATTLE_FIELDS = (
    "effect",
    "power",
    "type",
    "accuracy",
    "pp",
    "secondaryEffectChance",
    "target",
    "priority",
    "flags",
    "z_move_power",
    "split",
    "z_move_effect",
)


class CFRUMoveInventoryError(ValueError):
    """CFRU技sourceが完全・一意に解決できない。"""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_sha256(value: object) -> str:
    return _sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _source_ref(path: str, line: int, symbol: str) -> dict[str, Any]:
    return {"path": path, "line": line, "symbol": symbol}


def _read_text(source_root: Path, relative: str) -> tuple[str, bytes]:
    path = source_root / relative
    if path.is_symlink() or not path.is_file():
        raise CFRUMoveInventoryError(f"required source is missing/non-regular: {relative}")
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8"), raw
    except UnicodeDecodeError as error:
        raise CFRUMoveInventoryError(f"required source is not UTF-8: {relative}") from error


def _parse_move_constants(text: str, path: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"^\s*#define\s+(MOVE_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\b",
        re.MULTILINE,
    )
    rows: list[dict[str, Any]] = []
    symbols: set[str] = set()
    ids: set[int] = set()
    for match in pattern.finditer(text):
        symbol = match.group(1)
        if symbol == "MOVE_NAME_LENGTH":
            continue
        move_id = int(match.group(2), 0)
        if symbol in symbols:
            raise CFRUMoveInventoryError(f"duplicate move symbol: {symbol}")
        if move_id in ids:
            raise CFRUMoveInventoryError(f"duplicate move id: {move_id}")
        symbols.add(symbol)
        ids.add(move_id)
        rows.append(
            {
                "symbol": symbol,
                "id": move_id,
                "source_ref": _source_ref(path, _line_number(text, match.start()), symbol),
            }
        )
    if not rows:
        raise CFRUMoveInventoryError("no MOVE_* numeric constants found")
    rows.sort(key=lambda row: row["id"])
    actual = [row["id"] for row in rows]
    expected = list(range(actual[-1] + 1))
    if actual != expected:
        raise CFRUMoveInventoryError("move ids are not a contiguous 0-based range")
    if rows[0]["symbol"] != "MOVE_NONE":
        raise CFRUMoveInventoryError("move id 0 must be MOVE_NONE")
    return rows


def _parse_numeric_defines(text: str) -> dict[str, int]:
    raw: dict[str, str] = {}
    for match in re.finditer(
        r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+([^/\n]+?)\s*(?://.*)?$",
        text,
        re.MULTILINE,
    ):
        value = match.group(2).strip()
        if "(" in match.group(1):
            continue
        raw[match.group(1)] = value
    resolved: dict[str, int] = {}
    progress = True
    while progress:
        progress = False
        for name, expression in raw.items():
            if name in resolved:
                continue
            try:
                resolved[name] = _evaluate_numeric(expression, resolved)
            except CFRUMoveInventoryError:
                continue
            progress = True
    return resolved


def _evaluate_numeric(expression: str, constants: Mapping[str, int]) -> int:
    expression = expression.strip()
    while expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()
    if not re.fullmatch(r"[A-Za-z0-9_xXa-fA-F()|+\-\s]+", expression):
        raise CFRUMoveInventoryError(f"unsupported numeric expression: {expression}")
    or_parts = [part.strip() for part in expression.split("|")]
    result = 0
    for part in or_parts:
        add_parts = re.split(r"(?=[+-])", part.replace(" ", ""))
        subtotal = 0
        for index, token in enumerate(add_parts):
            if not token:
                continue
            sign = 1
            if token[0] in "+-":
                sign = -1 if token[0] == "-" else 1
                token = token[1:]
            token = token.strip("()")
            try:
                value = int(token, 0)
            except ValueError:
                if token not in constants:
                    raise CFRUMoveInventoryError(f"unresolved numeric symbol: {token}")
                value = constants[token]
            subtotal += sign * value
        result |= subtotal
    return result


def _active_defines(config_text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(
            r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b", config_text, re.MULTILINE
        )
    }


def _preprocess_fragment(
    text: str, defines: set[str], *, preserve_lines: bool = False
) -> str:
    output: list[str] = []
    stack: list[tuple[bool, bool, bool]] = []
    active = True
    for line in text.splitlines():
        match = re.match(r"\s*#\s*(ifdef|ifndef)\s+([A-Za-z_]\w*)\s*$", line)
        if match:
            condition = match.group(2) in defines
            if match.group(1) == "ifndef":
                condition = not condition
            stack.append((active, condition, False))
            active = active and condition
            if preserve_lines:
                output.append("")
            continue
        if re.match(r"\s*#\s*else\s*(?://.*)?$", line):
            if not stack or stack[-1][2]:
                raise CFRUMoveInventoryError("unmatched/duplicate #else in battle move")
            parent, condition, _ = stack[-1]
            stack[-1] = (parent, condition, True)
            active = parent and not condition
            if preserve_lines:
                output.append("")
            continue
        if re.match(r"\s*#\s*endif\s*(?://.*)?$", line):
            if not stack:
                raise CFRUMoveInventoryError("unmatched #endif in battle move")
            parent, _, _ = stack.pop()
            active = parent
            if preserve_lines:
                output.append("")
            continue
        if re.match(r"\s*#\s*if\b", line):
            raise CFRUMoveInventoryError(f"unsupported preprocessor condition: {line.strip()}")
        if active:
            output.append(line)
        elif preserve_lines:
            output.append("")
    if stack:
        raise CFRUMoveInventoryError("unterminated preprocessor condition in battle move")
    return "\n".join(output)


def _matching_brace(text: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise CFRUMoveInventoryError("unterminated C initializer")


def _parse_battle_moves(
    text: str, path: str, expected_symbols: Sequence[str], defines: set[str]
) -> dict[str, dict[str, Any]]:
    active_text = _preprocess_fragment(text, defines, preserve_lines=True)
    declarations = list(
        re.finditer(
            r"\bconst\s+struct\s+BattleMove\s+gBattleMoves\s*\[\s*\]\s*=\s*\{",
            active_text,
        )
    )
    if len(declarations) != 1:
        raise CFRUMoveInventoryError("gBattleMoves declaration must be unique")
    table_open = active_text.find("{", declarations[0].start())
    table_close = _matching_brace(active_text, table_open)
    body = active_text[table_open + 1 : table_close]
    entry_pattern = re.compile(r"\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\{")
    result: dict[str, dict[str, Any]] = {}
    for match in entry_pattern.finditer(body):
        symbol = match.group(1)
        opening = table_open + 1 + body.find("{", match.start())
        closing = _matching_brace(active_text, opening)
        fragment = active_text[opening + 1 : closing]
        field_rows = re.findall(
            r"^\s*\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^,\n]+)\s*,?\s*(?://.*)?$",
            fragment,
            re.MULTILINE,
        )
        fields: dict[str, str] = {}
        for name, value in field_rows:
            if name in fields:
                raise CFRUMoveInventoryError(f"duplicate {symbol}.{name}")
            fields[name] = value.strip()
        if set(fields) != set(_BATTLE_FIELDS):
            missing = sorted(set(_BATTLE_FIELDS) - set(fields))
            extra = sorted(set(fields) - set(_BATTLE_FIELDS))
            raise CFRUMoveInventoryError(
                f"{symbol} battle fields differ: missing={missing}, extra={extra}"
            )
        if symbol in result:
            raise CFRUMoveInventoryError(f"duplicate gBattleMoves initializer: {symbol}")
        absolute_start = table_open + 1 + match.start()
        result[symbol] = {
            "fields": fields,
            "source_ref": _source_ref(
                path, _line_number(active_text, absolute_start), symbol
            ),
        }
    if set(result) != set(expected_symbols):
        missing = sorted(set(expected_symbols) - set(result))
        extra = sorted(set(result) - set(expected_symbols))
        raise CFRUMoveInventoryError(
            f"gBattleMoves symbols differ: missing={missing[:5]}, extra={extra[:5]}"
        )
    return result


def _parse_string_file(text: str, path: str) -> dict[str, dict[str, Any]]:
    lines = text.splitlines()
    result: dict[str, dict[str, Any]] = {}
    index = 0
    while index < len(lines):
        match = re.fullmatch(r"#org\s+@([^\s]+)\s*", lines[index])
        if not match:
            index += 1
            continue
        symbol = match.group(1)
        line_number = index + 1
        index += 1
        content: list[str] = []
        while index < len(lines) and not lines[index].startswith("#org "):
            if lines[index].strip():
                content.append(lines[index])
            index += 1
        if not content:  # gMoveNamesのtable anchorだけは本文を持たない。
            value: str | None = None
        elif len(content) == 1:
            value = content[0]
        else:
            raise CFRUMoveInventoryError(f"multi-line raw string body is unsupported: {symbol}")
        if symbol in result:
            raise CFRUMoveInventoryError(f"duplicate string symbol: {symbol}")
        result[symbol] = {
            "text": value,
            "source_ref": _source_ref(path, line_number, symbol),
        }
    return result


def _parse_name_sequence(text: str, path: str, count: int) -> list[dict[str, Any]]:
    symbols = _parse_string_file(text, path)
    anchor = symbols.pop("gMoveNames", None)
    if anchor is None or anchor["text"] is not None:
        raise CFRUMoveInventoryError("gMoveNames string anchor is missing/invalid")
    ordered: list[dict[str, Any]] = []
    for match in re.finditer(r"^#org\s+@([^\s]+)\s*$", text, re.MULTILINE):
        symbol = match.group(1)
        if symbol == "gMoveNames":
            continue
        ordered.append({"symbol": symbol, **symbols[symbol]})
    if len(ordered) != count:
        raise CFRUMoveInventoryError(
            f"gMoveNames entry count mismatch: expected {count}, got {len(ordered)}"
        )
    return ordered


def _parse_word_table(
    text: str, path: str, label: str, expected_count: int
) -> list[dict[str, Any]]:
    matches = list(re.finditer(rf"^{re.escape(label)}:\s*$", text, re.MULTILINE))
    if len(matches) != 1:
        raise CFRUMoveInventoryError(f"assembly table label must be unique: {label}")
    lines = text[matches[0].end() :].splitlines()
    base_line = _line_number(text, matches[0].end())
    rows: list[dict[str, Any]] = []
    for offset, line in enumerate(lines, 1):
        code = line.split("@", 1)[0].strip()
        if code.startswith(".word "):
            value = code[len(".word ") :].strip()
            if not re.fullmatch(r"(?:0x[0-9A-Fa-f]+|[0-9]+|[A-Za-z_]\w*)", value):
                raise CFRUMoveInventoryError(f"unsupported .word expression: {value}")
            rows.append(
                {
                    "symbol": value,
                    "source_ref": _source_ref(path, base_line + offset, value),
                }
            )
        elif rows and re.fullmatch(r"[A-Za-z_]\w*:\s*", code):
            break
    if len(rows) != expected_count:
        raise CFRUMoveInventoryError(
            f"{label} entry count mismatch: expected {expected_count}, got {len(rows)}"
        )
    return rows


def _assembly_labels(text: str) -> set[str]:
    return set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", text, re.MULTILINE))


def _battle_script_labels(source_root: Path) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    directory = source_root / "assembly/battle_scripts"
    if not directory.is_dir():
        raise CFRUMoveInventoryError("assembly/battle_scripts is missing")
    for path in sorted(directory.glob("*.s")):
        if path.is_symlink() or not path.is_file():
            raise CFRUMoveInventoryError(f"battle script is non-regular: {path.name}")
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(source_root).as_posix()
        for match in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*):", text, re.MULTILINE):
            symbol = match.group(1)
            result.setdefault(symbol, []).append(
                _source_ref(relative, _line_number(text, match.start()), symbol)
            )
    return result


def _parse_effect_constants(text: str, path: str) -> tuple[dict[str, int], dict[int, str]]:
    forward: dict[str, int] = {}
    reverse: dict[int, str] = {}
    for match in re.finditer(
        r"^\s*#define\s+(EFFECT_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\b",
        text,
        re.MULTILINE,
    ):
        symbol = match.group(1)
        value = int(match.group(2), 0)
        if symbol in forward or value in reverse:
            raise CFRUMoveInventoryError(f"duplicate move effect constant: {symbol}/{value}")
        forward[symbol] = value
        reverse[value] = symbol
    if not forward:
        raise CFRUMoveInventoryError("no EFFECT_* constants found")
    return forward, reverse


def _decode_generation_map() -> dict[str, int]:
    encoded = "".join(_GENERATION_MAP_B85.split()).encode("ascii")
    raw = zlib.decompress(base64.b85decode(encoded))
    if _sha256(raw) != _GENERATION_MAP_SHA256:
        raise RuntimeError("embedded generation map checksum mismatch")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("embedded generation map is not an object")
    return {str(key): int(generation) for key, generation in value.items()}


def _generation(move_id: int, suffix: str, count: int) -> int:
    if move_id == 0:
        return 0
    if move_id <= 165:
        return 1
    if move_id <= 251:
        return 2
    if move_id <= 354:
        return 3
    if move_id == 355:  # CFRU custom LEECFANG, Gen4追加blockの先頭。
        return 4
    if suffix == "STEELYHIT":  # CFRU custom "Metal Bash"。
        return 0
    generation_map = _decode_generation_map()
    if suffix in generation_map:
        return generation_map[suffix]
    if 0x2FF <= move_id <= 0x333:
        return 7
    if 0x334 <= move_id <= 0x39A:
        return 8
    if 0x39B <= move_id < count:
        return 9
    raise CFRUMoveInventoryError(f"unresolved generation: MOVE_{suffix}/{move_id}")


def _flags(expression: str, constants: Mapping[str, int]) -> tuple[list[str], int]:
    if expression == "0":
        return [], 0
    symbols = [part.strip() for part in expression.split("|")]
    if not all(re.fullmatch(r"FLAG_[A-Z0-9_]+", symbol) for symbol in symbols):
        raise CFRUMoveInventoryError(f"unsupported move flags expression: {expression}")
    if len(symbols) != len(set(symbols)):
        raise CFRUMoveInventoryError(f"duplicate flag in expression: {expression}")
    return symbols, _evaluate_numeric(expression, constants)


def _git_head(source_root: Path) -> str | None:
    git = source_root / ".git"
    if not git.is_dir():
        return None
    head = (git / "HEAD").read_text(encoding="ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", head):
        return head
    if not head.startswith("ref: "):
        raise CFRUMoveInventoryError("invalid CFRU .git/HEAD")
    ref = head[5:]
    loose = git / ref
    if loose.is_file():
        commit = loose.read_text(encoding="ascii").strip()
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    packed = git / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii").splitlines():
            if line.endswith(f" {ref}") and re.fullmatch(r"[0-9a-f]{40} .+", line):
                return line.split()[0]
    raise CFRUMoveInventoryError("cannot resolve CFRU git HEAD")


def _locked_commit(root: Path, source_root: Path) -> str | None:
    lock = root / "state/source-lock.json"
    if not lock.is_file():
        return None
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CFRUMoveInventoryError("state/source-lock.json is invalid") from error
    relative = source_root.relative_to(root).as_posix()
    matches = [
        row
        for row in data.get("sources", [])
        if isinstance(row, Mapping) and row.get("name") == "cfru" and row.get("path") == relative
    ]
    if len(matches) != 1:
        return None
    commit = matches[0].get("resolved_commit") or matches[0].get("actual_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise CFRUMoveInventoryError("source-lock CFRU commit is invalid")
    return commit


def _table_provenance(
    symbol: str, relative: str, text: str, raw: bytes, count: int
) -> dict[str, Any]:
    match = re.search(rf"\b{re.escape(symbol)}\s*:", text)
    if match is None:
        match = re.search(rf"\b{re.escape(symbol)}\s*\[", text)
    if match is None:
        match = re.search(rf"^\s*#define\s+{re.escape(symbol)}\b", text, re.MULTILINE)
    if match is None:
        match = re.search(rf"^#org\s+@{re.escape(symbol)}\s*$", text, re.MULTILINE)
    if match is None:
        raise CFRUMoveInventoryError(f"table symbol not found for provenance: {symbol}")
    return {
        "symbol": symbol,
        "path": relative,
        "line": _line_number(text, match.start()),
        "sha256": _sha256(raw),
        "entry_count": count,
    }


def build_cfru_move_inventory(root: Path, source_root: Path) -> dict[str, Any]:
    """固定CFRU-JP sourceから完全な技inventoryを返す。"""

    root = root.resolve()
    source_root = source_root.resolve()
    try:
        source_relative = source_root.relative_to(root).as_posix()
    except ValueError as error:
        raise CFRUMoveInventoryError("source_root must be inside root") from error
    if not source_root.is_dir():
        raise CFRUMoveInventoryError("source_root is not a directory")

    texts: dict[str, str] = {}
    raws: dict[str, bytes] = {}
    for relative in _SOURCE_FILES:
        texts[relative], raws[relative] = _read_text(source_root, relative)

    constants_path = "include/constants/moves.h"
    constants = _parse_move_constants(texts[constants_path], constants_path)
    count = len(constants)
    symbols = [row["symbol"] for row in constants]
    config_defines = _active_defines(texts["src/config.h"])
    battles = _parse_battle_moves(
        texts["src/Tables/battle_moves.c"],
        "src/Tables/battle_moves.c",
        symbols,
        config_defines,
    )
    names = _parse_name_sequence(
        texts["strings/attack_name_table.string"],
        "strings/attack_name_table.string",
        count,
    )
    descriptions = _parse_string_file(
        texts["strings/attack_descriptions.string"],
        "strings/attack_descriptions.string",
    )
    animations = _parse_word_table(
        texts["assembly/data/attack_anim_table.s"],
        "assembly/data/attack_anim_table.s",
        "gMoveAnimations",
        count,
    )
    description_table = _parse_word_table(
        texts["assembly/data/attack_description_table.s"],
        "assembly/data/attack_description_table.s",
        "gMoveDescriptions",
        count,
    )
    effect_scripts = _parse_word_table(
        texts["assembly/data/move_effect_table.s"],
        "assembly/data/move_effect_table.s",
        "gBattleScriptsForMoveEffects",
        256,
    )
    effect_forward, effect_reverse = _parse_effect_constants(
        texts["include/constants/battle_move_effects.h"],
        "include/constants/battle_move_effects.h",
    )

    numeric_constants: dict[str, int] = {}
    for relative in (
        "include/constants/pokemon.h",
        "include/battle.h",
        "include/constants/battle_move_effects.h",
        "include/new/z_move_effects.h",
    ):
        numeric_constants.update(_parse_numeric_defines(texts[relative]))
    numeric_constants.update(effect_forward)

    animation_labels = _assembly_labels(texts["assembly/data/attack_anim_table.s"])
    for row in animations:
        value = row["symbol"]
        if re.fullmatch(r"[A-Za-z_]\w*", value) and value not in animation_labels:
            raise CFRUMoveInventoryError(f"unresolved animation symbol: {value}")
    for row in description_table:
        value = row["symbol"]
        if re.fullmatch(r"[A-Za-z_]\w*", value) and value not in descriptions:
            raise CFRUMoveInventoryError(f"unresolved description symbol: {value}")
    script_labels = _battle_script_labels(source_root)
    for row in effect_scripts:
        value = row["symbol"]
        if re.fullmatch(r"[A-Za-z_]\w*", value):
            definitions = script_labels.get(value, [])
            if len(definitions) != 1:
                raise CFRUMoveInventoryError(
                    f"unresolved/ambiguous effect script symbol: {value} ({len(definitions)})"
                )

    split_names = {
        "SPLIT_PHYSICAL": "PHYSICAL",
        "SPLIT_SPECIAL": "SPECIAL",
        "SPLIT_STATUS": "STATUS",
    }
    moves: list[dict[str, Any]] = []
    for constant, name, description_pointer, animation in zip(
        constants, names, description_table, animations, strict=True
    ):
        symbol = constant["symbol"]
        suffix = symbol.removeprefix("MOVE_")
        move_id = constant["id"]
        fields = battles[symbol]["fields"]
        effect_symbol = fields["effect"]
        if effect_symbol not in effect_forward:
            raise CFRUMoveInventoryError(f"unresolved effect constant: {effect_symbol}")
        effect_id = effect_forward[effect_symbol]
        if effect_id >= len(effect_scripts) or effect_reverse.get(effect_id) != effect_symbol:
            raise CFRUMoveInventoryError(f"effect table mismatch: {effect_symbol}/{effect_id}")
        split_symbol = fields["split"]
        if split_symbol not in split_names:
            raise CFRUMoveInventoryError(f"unresolved split: {split_symbol}")
        type_symbol = fields["type"]
        target_symbol = fields["target"]
        if type_symbol not in numeric_constants or target_symbol not in numeric_constants:
            raise CFRUMoveInventoryError(
                f"unresolved type/target: {type_symbol}/{target_symbol}"
            )
        flag_symbols, flag_mask = _flags(fields["flags"], numeric_constants)
        description_symbol = description_pointer["symbol"]
        description_row = descriptions.get(description_symbol)
        effect_script = effect_scripts[effect_id]
        description_mapping_kind = (
            "SOURCE_SYMBOL" if description_row is not None else "EXTERNAL_ROM_POINTER"
        )
        animation_mapping_kind = (
            "SOURCE_SYMBOL"
            if re.fullmatch(r"[A-Za-z_]\w*", animation["symbol"])
            else "EXTERNAL_ROM_POINTER"
        )
        effect_script_mapping_kind = (
            "SOURCE_SYMBOL"
            if re.fullmatch(r"[A-Za-z_]\w*", effect_script["symbol"])
            else "EXTERNAL_ROM_POINTER"
        )
        priority_raw = _evaluate_numeric(fields["priority"], numeric_constants)
        if not 0 <= priority_raw <= 255:
            raise CFRUMoveInventoryError(f"priority outside s8 storage: {symbol}")
        japanese_name = name["text"]
        if not isinstance(japanese_name, str) or not japanese_name:
            raise CFRUMoveInventoryError(f"empty move name: {symbol}")
        moves.append(
            {
                "canonical_key": f"MOVE_KEY_{suffix}",
                "id": move_id,
                "cfru_symbol": symbol,
                "generation": _generation(move_id, suffix, count),
                "category": split_names[split_symbol],
                "category_symbol": split_symbol,
                "effect": effect_symbol,
                "effect_id": effect_id,
                "effect_script_symbol": effect_script["symbol"],
                "type": type_symbol.removeprefix("TYPE_"),
                "type_symbol": type_symbol,
                "type_id": numeric_constants[type_symbol],
                "power": _evaluate_numeric(fields["power"], numeric_constants),
                "accuracy": _evaluate_numeric(fields["accuracy"], numeric_constants),
                "pp": _evaluate_numeric(fields["pp"], numeric_constants),
                "secondary_effect_chance": _evaluate_numeric(
                    fields["secondaryEffectChance"], numeric_constants
                ),
                "target": target_symbol.removeprefix("MOVE_TARGET_"),
                "target_symbol": target_symbol,
                "target_id": numeric_constants[target_symbol],
                "priority": priority_raw - 256 if priority_raw >= 128 else priority_raw,
                "priority_raw": priority_raw,
                "flags": flag_symbols,
                "flags_mask": flag_mask,
                "z_move_power": _evaluate_numeric(fields["z_move_power"], numeric_constants),
                "z_move_effect_symbol": fields["z_move_effect"],
                "name": japanese_name,
                "name_ja": japanese_name,
                "name_symbol": name["symbol"],
                # V3 data/*.csv の move_name とexact joinするため原文を変更しない。
                "v3_exact_move_name": japanese_name,
                "name_nfc": unicodedata.normalize("NFC", japanese_name),
                "description": description_row["text"] if description_row else None,
                "description_ja": description_row["text"] if description_row else None,
                "description_symbol": description_symbol,
                "description_mapping_kind": description_mapping_kind,
                "animation": animation["symbol"],
                "animation_symbol": animation["symbol"],
                "animation_mapping_kind": animation_mapping_kind,
                "effect_script_mapping_kind": effect_script_mapping_kind,
                "vega_id_relation": (
                    "VEGA_FROZEN_RANGE_CANDIDATE"
                    if move_id <= 511
                    else "CFRU_APPEND_CANDIDATE"
                ),
                "source_refs": {
                    "constant": constant["source_ref"],
                    "battle_record": battles[symbol]["source_ref"],
                    "name": name["source_ref"],
                    "description_pointer": description_pointer["source_ref"],
                    "description_text": description_row["source_ref"] if description_row else None,
                    "animation": animation["source_ref"],
                    "effect_script_pointer": effect_script["source_ref"],
                    "effect_script": (
                        script_labels[effect_script["symbol"]][0]
                        if effect_script["symbol"] in script_labels
                        else None
                    ),
                },
            }
        )

    keys = [move["canonical_key"] for move in moves]
    if len(keys) != len(set(keys)):
        raise CFRUMoveInventoryError("duplicate canonical move keys")

    actual_commit = _git_head(source_root)
    locked_commit = _locked_commit(root, source_root)
    is_fixed_production_source = source_relative == "vendor/upstream/CFRU-JP"
    if is_fixed_production_source and (actual_commit is None or locked_commit is None):
        raise CFRUMoveInventoryError(
            "fixed CFRU source requires both source-lock identity and git HEAD"
        )
    if actual_commit and locked_commit and actual_commit != locked_commit:
        raise CFRUMoveInventoryError(
            f"CFRU source commit differs from source-lock: {actual_commit} != {locked_commit}"
        )
    source_commit = locked_commit or actual_commit or "UNVERSIONED_TEST_FIXTURE"
    table_rows = {
        "move_constants": _table_provenance(
            "MOVE_NONE", constants_path, texts[constants_path], raws[constants_path], count
        ),
        "battle_moves": _table_provenance(
            "gBattleMoves",
            "src/Tables/battle_moves.c",
            texts["src/Tables/battle_moves.c"],
            raws["src/Tables/battle_moves.c"],
            count,
        ),
        "move_names": _table_provenance(
            "gMoveNames",
            "strings/attack_name_table.string",
            texts["strings/attack_name_table.string"],
            raws["strings/attack_name_table.string"],
            count,
        ),
        "move_descriptions": _table_provenance(
            "gMoveDescriptions",
            "assembly/data/attack_description_table.s",
            texts["assembly/data/attack_description_table.s"],
            raws["assembly/data/attack_description_table.s"],
            count,
        ),
        "move_animations": _table_provenance(
            "gMoveAnimations",
            "assembly/data/attack_anim_table.s",
            texts["assembly/data/attack_anim_table.s"],
            raws["assembly/data/attack_anim_table.s"],
            count,
        ),
        "move_effect_scripts": _table_provenance(
            "gBattleScriptsForMoveEffects",
            "assembly/data/move_effect_table.s",
            texts["assembly/data/move_effect_table.s"],
            raws["assembly/data/move_effect_table.s"],
            len(effect_scripts),
        ),
    }
    file_hashes = {relative: _sha256(raws[relative]) for relative in sorted(raws)}
    for path in sorted((source_root / "assembly/battle_scripts").glob("*.s")):
        relative = path.relative_to(source_root).as_posix()
        file_hashes[relative] = _sha256(path.read_bytes())
    generation_counts = Counter(str(move["generation"]) for move in moves)
    summaries: dict[str, Any] = {
        "validation_scope": "CFRU_SOURCE_INTERNAL",
        "v3_name_join_contract": "EXACT_NAME_KEY_ONLY_NOT_RESOLUTION",
        "move_count": count,
        "min_id": 0,
        "max_id": count - 1,
        "vega_frozen_range_candidate_count": sum(move["id"] <= 511 for move in moves),
        "cfru_append_candidate_count": sum(move["id"] > 511 for move in moves),
        "generation_counts": dict(sorted(generation_counts.items(), key=lambda row: int(row[0]))),
        "external_rom_pointer_counts": {
            "description": sum(
                move["description_mapping_kind"] == "EXTERNAL_ROM_POINTER"
                for move in moves
            ),
            "animation": sum(
                move["animation_mapping_kind"] == "EXTERNAL_ROM_POINTER"
                for move in moves
            ),
            "effect_script": sum(
                move["effect_script_mapping_kind"] == "EXTERNAL_ROM_POINTER"
                for move in moves
            ),
        },
        "unresolved_count": 0,
        "duplicate_id_count": 0,
        "duplicate_key_count": 0,
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine": "CFRU-JP",
        "source_commit": source_commit,
        "provenance": {
            "source_root": source_relative,
            "source_commit": source_commit,
            "files": file_hashes,
            "generation_mapping": {
                "source": "PokeAPI data/v2/csv/moves.csv generation_id",
                "source_url": "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/moves.csv",
                "retrieved_date": "2026-08-13",
                "embedded_map_sha256": _GENERATION_MAP_SHA256,
                "runtime_network_required": False,
                "cfru_custom_generation_zero_symbols": ["MOVE_NONE", "MOVE_STEELYHIT"],
            },
        },
        "tables": table_rows,
        "moves": moves,
        "summaries": summaries,
    }
    summaries["inventory_sha256"] = _stable_sha256(
        {key: value for key, value in result.items() if key != "summaries"}
    )
    if is_fixed_production_source and count != EXPECTED_PRODUCTION_MOVE_COUNT:
        raise CFRUMoveInventoryError(
            f"fixed CFRU move count changed: {count} != {EXPECTED_PRODUCTION_MOVE_COUNT}"
        )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    source_root = (
        args.source_root.resolve()
        if args.source_root is not None
        else root / "vendor/upstream/CFRU-JP"
    )
    try:
        result = build_cfru_move_inventory(root, source_root)
    except (CFRUMoveInventoryError, OSError, TypeError, RuntimeError) as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
