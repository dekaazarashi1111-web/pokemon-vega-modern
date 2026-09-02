#!/usr/bin/env python3
"""Stage 61 の Seafoam/Victory Road 物理 producer を安全に再構築する。

Stage60 の canonical map serializer は会話NPCを優先しており、落石object、coord
event、Route20/Route23 のreset writerを意図的に保留している。これらを単にsource
ROMからコピーすると、FireRed側のflag/var/script pointerとArticuno story stateまで
Vegaへ混入する。このmoduleは対象surfaceのclean/Stage60 preimageをbyte単位で固定し、
明示済みStage61 namespaceだけを使うproject-owned bytecode/object/coord payloadを生成する。

公開APIは二段階である。

``build_stage61_topology_producer_contract``
    入力ROM、対象map header/event/object/coord、source scriptをfail-closedに監査する。

``materialize_stage61_topology_producer_state``
    監査済みcontract、payload base、外部でrelocate済みのStrength rootを受け取り、
    payload、固定preimage付きstructural patch、旧object recordのrebase表、state owner表を
    返す。source script/coord/movement pointerをpayloadへ流用しない。
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000
CLEAN_ROM_SIZE = 0x01000000
STAGE60_ROM_SIZE = 0x02000000
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE60_ROM_SHA256 = "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"

MAP_GROUPS_POINTER_SITE = 0x08054B0C
OBJECT_EVENT_SIZE = 24
COORD_EVENT_SIZE = 16
MAP_HEADER_SIZE = 28
EVENT_HEADER_SIZE = 20
STRENGTH_SOURCE_ROOT = 0x081A48B8

FLAG_MAPPING: Mapping[int, int] = {
    **{source: 0x162D + source - 0x40 for source in range(0x40, 0x4E)},
    0x0058: 0x163B,
    0x0059: 0x163C,
    0x02D2: 0x163D,
    0x02D3: 0x163E,
}
VAR_MAPPING: Mapping[int, int] = {
    0x4063: 0x5167,
    0x4064: 0x5168,
    0x4065: 0x5169,
    0x4066: 0x516A,
    0x4067: 0x516B,
}
LAYOUT_MAPPING: Mapping[int, int] = {0x0116: 564, 0x0117: 565}

# Source/target structures which this adapter owns or structurally patches. Unrelated warp/bg
# arrays are retained by pointer; their pointer/count preimages are nevertheless pinned in the
# complete event header below.
MAP_PREIMAGES: Mapping[str, Mapping[str, Any]] = {
    "SEAFOAM_1F": {
        "source_map": (1, 83),
        "source_header_address": 0x08313BD8,
        "source_header_hex": "fc872d08945e37083bb01608000000001f019c008b00000401070000",
        "source_event_address": 0x08375E94,
        "source_event_hex": "03070000145e37085c5e37080000000000000000",
        "source_objects_address": 0x08375E14,
        "source_objects_hex": (
            "0161000016000c000308000042000000b8481a0840000000"
            "02610000200009000308000043000000b8481a0841000000"
            "035c00000b00080003081100000000002a521a08d4010000"
        ),
        "target_map": (97, 83),
        "target_header_address": 0x092C25CC,
        "target_header_hex": "18182b0938114009460d2209000000001f010b028b00000401070000",
        "target_event_address": 0x09401138,
        "target_event_hex": "010700002011400980252c090000000000000000",
        "target_objects_address": 0x09401120,
        "target_objects_hex": "015c00000b0008000308110000000000b01e3f097d140000",
    },
    "SEAFOAM_B1F": {
        "source_map": (1, 84),
        "source_header_address": 0x08313BF4,
        "source_header_hex": "f48e2d08605f370845b01608000000001f019d008b00000401070000",
        "source_event_address": 0x08375F60,
        "source_event_hex": "040b0000a85e3708085f37080000000000000000",
        "source_objects_address": 0x08375EA8,
        "source_objects_hex": (
            "01610000160008000308000044000000b8481a0842000000"
            "026100001e0008000308000045000000b8481a0843000000"
            "035c000013001200030811000000000037521a08d5010000"
            "045c000018000e00040811000000000044521a08d6010000"
        ),
        "target_map": (97, 84),
        "target_header_address": 0x092C2654,
        "target_header_hex": "101f2b097c114009460d2209000000001f010c028b00000401070000",
        "target_event_address": 0x0940117C,
        "target_event_hex": "020b00004c114009e8252c090000000000000000",
        "target_objects_address": 0x0940114C,
        "target_objects_hex": (
            "015c0000130012000308110000000000e01e3f097e140000"
            "025c000018000e000408110000000000101f3f097f140000"
        ),
    },
    "SEAFOAM_B2F": {
        "source_map": (1, 85),
        "source_header_address": 0x08313C10,
        "source_header_hex": "38962d081460370846b01608000000001f019e008b00000401070000",
        "source_event_address": 0x08376014,
        "source_event_hex": "030b0000745f3708bc5f37080000000000000000",
        "source_objects_address": 0x08375F74,
        "source_objects_hex": (
            "01610000160008000308000046000000b8481a0844000000"
            "026100001e0008000308000047000000b8481a0845000000"
            "035c000012000f00030811000000000051521a08d7010000"
        ),
        "target_map": (97, 85),
        "target_header_address": 0x092C26DC,
        "target_header_hex": "54262b09a8114009460d2209000000001f010d028b00000401070000",
        "target_event_address": 0x094011A8,
        "target_event_hex": "010b00009011400970262c090000000000000000",
        "target_objects_address": 0x09401190,
        "target_objects_hex": "015c000012000f000308110000000000401f3f0980140000",
    },
    "SEAFOAM_B3F": {
        "source_map": (1, 86),
        "source_header_address": 0x08313C2C,
        "source_header_hex": "7c9d2d080c61370847b01608000000001f019f008b00000401070000",
        "source_event_address": 0x0837610C,
        "source_event_hex": "0609000128603708b86037080000000000613708",
        "source_objects_address": 0x08376028,
        "source_objects_hex": (
            "016100001700080001081100000000000000000046000000"
            "026100001800080001081100000000000000000047000000"
            "036100000c001000030800004d000000b8481a084a000000"
            "046100000d0010000308000000000000b8481a084b000000"
            "05610000090010000308000000000000b8481a0849000000"
            "0661000006001100030800004c000000b8481a0848000000"
        ),
        "target_map": (97, 86),
        "target_header_address": 0x092C2754,
        "target_header_hex": "982d2b0928124009460d2209000000001f010e028b00000401070000",
        "target_event_address": 0x09401228,
        "target_event_hex": "04090001bc114009f8262c09000000001c124009",
        "target_objects_address": 0x094011BC,
        "target_objects_hex": (
            "01610000170008000108110000000000ace83e0900000000"
            "02610000180008000108110000000000ace83e0900000000"
            "036100000d0010000308000000000000b8481a0800000000"
            "04610000090010000308000000000000b8481a0800000000"
        ),
    },
    "SEAFOAM_B4F": {
        "source_map": (1, 87),
        "source_header_address": 0x08313C48,
        "source_header_hex": "c0a42d08f461370826b11608000000001f01a0008b00000401070000",
        "source_event_address": 0x083761F4,
        "source_event_hex": "040403032061370880613708a0613708d0613708",
        "source_objects_address": 0x08376120,
        "source_objects_hex": (
            "01610000080012000108110000000000000000004c000000"
            "02610000090012000108110000000000000000004d000000"
            "038a0000090002000408110000000000a4b2160882000000"
            "045c00001600130004081100000000005e521a08d8010000"
        ),
        "source_coords_address": 0x083761A0,
        "source_coords_hex": (
            "1a001300010063400000000095b21608"
            "1b001300010063400000000095b21608"
            "1c001300010063400000000095b21608"
        ),
        "target_map": (97, 87),
        "target_header_address": 0x092C27A4,
        "target_header_hex": "dc342b09c0124009460d2209000000001f010f028b00000401070000",
        "target_event_address": 0x094012C0,
        "target_event_hex": "040400033c12400970272c09000000009c124009",
        "target_objects_address": 0x0940123C,
        "target_objects_hex": (
            "0161000008001200010811000000000088e3380900000000"
            "038a000009000200040811000000000078bf2d0900000000"
            "025c0000160013000408110000000000b01f3f0981140000"
            "04610000090012000108110000000000ace83e0900000000"
        ),
        "target_coords_address": 0,
        "target_coords_hex": "",
    },
    "VICTORY_1F": {
        "source_map": (1, 39),
        "source_header_address": 0x08313708,
        "source_header_hex": "7c842c08f0353708be5816080000000020017d008400000401070000",
        "source_event_address": 0x083735F0,
        "source_event_hex": "0702010210353708b8353708c8353708d8353708",
        "source_coords_address": 0x083735C8,
        "source_coords_hex": "140010000300644063000000ec581608",
        "target_map": (97, 39),
        "target_header_address": 0x092C15FC,
        "target_header_hex": "6cb72b0974f33f09460d22090000000020012c028400000401070000",
        "target_event_address": 0x093FF374,
        "target_event_hex": "080200029cf23f09449c3609000000005cf33f09",
        "target_coords_address": 0,
        "target_coords_hex": "",
    },
    "VICTORY_2F": {
        "source_map": (1, 40),
        "source_header_address": 0x08313724,
        "source_header_hex": "648d2c08a4373708c85916080000000020017e008400000401070000",
        "source_event_address": 0x083737A4,
        "source_event_hex": "0d090200043637083c3737088437370800000000",
        "source_objects_address": 0x08373604,
        "source_objects_hex": (
            "013400000700040003081100010001006d5a160800000000"
            "0236000014000b000411110001000400845a160800000000"
            "031a00001f00100004091100010004009b5a160800000000"
            "041900001a0006000328440001000100c95a160800000000"
            "051a0000240005000307110001000300b25a160800000000"
            "065c00001100060003081100000000002f501a08ab010000"
            "075c00002800070003081100000000003c501a08ac010000"
            "085c000019000d00030811000000000049501a08ad010000"
            "095c00000e000d00030811000000000056501a08ae010000"
            "0a610000080007000308000000000000b8481a0800000000"
            "0b610000060011000308000000000000b8481a0800000000"
            "0c610000210013000308000000000000b8481a0858000000"
            "0d290000280009000308110000000000368f1a0800000000"
        ),
        "source_coords_address": 0x08373784,
        "source_coords_hex": (
            "0200130003006540630000000b5a1608"
            "0e00130003006640630000003c5a1608"
        ),
        "target_map": (97, 40),
        "target_header_address": 0x092C1674,
        "target_header_hex": "54c02b0990f43f09460d22090000000020012d028400000401070000",
        "target_event_address": 0x093FF490,
        "target_event_hex": "0b09000088f33f09989c36090000000000000000",
        "target_objects_address": 0x093FF388,
        "target_objects_hex": (
            "01340000070004000308110001000100205c360900000000"
            "0236000014000b000411110001000400585c360900000000"
            "031a00001f0010000409110001000400905c360900000000"
            "045c0000110006000308110000000000100c3f0933140000"
            "055c0000280007000308110000000000400c3f0934140000"
            "065c000019000d000308110000000000700c3f0935140000"
            "075c00000e000d000308110000000000a00c3f0936140000"
            "08610000080007000308000000000000b8481a0800000000"
            "09610000060011000308000000000000b8481a0800000000"
            "0a610000210013000308000000000000b8481a0800000000"
            "0b290000280009000308110000000000368f1a0800000000"
        ),
        "target_coords_address": 0,
        "target_coords_hex": "",
    },
    "VICTORY_3F": {
        "source_map": (1, 41),
        "source_header_address": 0x08313740,
        "source_header_hex": "44952c0810393708ca5c16080000000020017f008400000401070000",
        "source_event_address": 0x08373910,
        "source_event_hex": "0c050100b8373708d83837080039370800000000",
        "source_objects_address": 0x083737B8,
        "source_objects_hex": (
            "01290000280007000309110001000100235d160800000000"
            "022a000015000500040a110001000400685d160800000000"
            "032900000a00110003091100010005003a5d160800000000"
            "042a00000b001000030a110001000500515d160800000000"
            "055c000026000700030811000000000063501a08af010000"
            "065c00000c000900030811000000000070501a08b0010000"
            "0761000013000f000308000000000000b8481a0800000000"
            "08610000210012000008000058000000b8481a0859000000"
            "0961000023000d000308000000000000b8481a0800000000"
            "0a610000200005000308000000000000b8481a0800000000"
            "0b29000026000d0003081100010001007f5d160800000000"
            "0c2a000027000d0003081100010001009a5d160800000000"
        ),
        "source_coords_address": 0x08373900,
        "source_coords_hex": "070007000300674063000000ef5c1608",
        "target_map": (97, 41),
        "target_header_address": 0x092C16CC,
        "target_header_hex": "34c82b0994f53f09460d22090000000020012e028400000401070000",
        "target_event_address": 0x093FF594,
        "target_event_hex": "0a050000a4f43f093c9d36090000000000000000",
        "target_objects_address": 0x093FF4A4,
        "target_objects_hex": (
            "01290000280007000309110000000000c4bd2d0900000000"
            "02290000280006000309110001000100c85c360900000000"
            "032a000015000500040a110001000400005d360900000000"
            "042900000a00110003091100010004007874360900000000"
            "052a00000b001000030a1100010004007874360900000000"
            "065c0000260007000308110000000000d00c3f0937140000"
            "075c00000c0009000308110000000000000d3f0938140000"
            "0861000013000f000308000000000000b8481a0800000000"
            "0961000023000d000308000000000000b8481a0800000000"
            "0a610000200005000308000000000000b8481a0800000000"
        ),
        "target_coords_address": 0,
        "target_coords_hex": "",
    },
    "ROUTE20": {
        "source_map": (3, 38),
        "source_header_address": 0x08314AF0,
        "source_header_hex": "48962b084cbd370814861708106d310825016c007800020301060000",
        "source_event_address": 0x0837BD4C,
        "source_event_hex": "0b02000310bc370818bd37080000000028bd3708",
        "target_map": (96, 31),
        "target_header_address": 0x092C0910,
        "target_header_hex": "b4f52909b4df3f09460d220908092c092501ea017800020301060000",
        "target_event_address": 0x093FDFB4,
        "target_event_hex": "0a020003a0de3f09249236090000000090df3f09",
    },
    "ROUTE23": {
        "source_map": (3, 42),
        "source_header_address": 0x08314B60,
        "source_header_hex": "14c72b0818c337085d911708906d310827016f007b00020301060000",
        "source_event_address": 0x0837C318,
        "source_event_hex": "07042a0944bf3708ecbf37080cc03708acc23708",
        "target_map": (96, 35),
        "target_header_address": 0x092C0A80,
        "target_header_hex": "90312a0938e23f09460d2209780a2c092701ef017b00020301060000",
        "target_event_address": 0x093FE238,
        "target_event_hex": "0c040009ace03f09a893360900000000cce13f09",
    },
}


SOURCE_SCRIPT_PINS: Mapping[str, tuple[int, str, str]] = {
    "SEAFOAM_B3F_COMPLETE_SURFACE": (
        0x0816B047,
        (
            "0352b016080290b01608002bd202070065b016082bd20207018cb0160802"
            "16024000002b46000700e8b016082b47000700e8b0160821024002000701"
            "88b016080329d20203a7160103014001009ab0160800006916024000002b"
            "46000700e8b016082b47000700e8b016082102400200060104b116084208"
            "80098021088018000700eeb0160821088018000704f9b016081663400100"
            "390157ff1b001500276b021702400100034fff000bb11608510000034fff"
            "0019b116085100000316014000006b021d1d1d1d2020201d1d1d1d1d1d"
            "fe1d1d1d1d20201d1d1d1d1d1dfe"
        ),
        "1507c75ab5bce177c773e70317850d7c4a8db72667520b902ba1753212e75be1",
    ),
    "SEAFOAM_B4F_SOURCE_SURFACE_WITH_STORY_DENYLIST": (
        0x0816B126,
        (
            "035eb116080540b1160801a9b1160804dfb1160802f1b11608002b070807"
            "014ab1160802260d80b400210d8007000605534d1908530f80032bbe0207"
            "00a5b116082bd30207007ab116082bd3020701a1b116080216024000002b"
            "4c00070061b216082b4d00070061b21608210240020007019db116080329"
            "d30203a71701032a82000316024000002b4c00070061b216082b4d000700"
            "61b2160821024002000601ccb1160802a20c000e002b010000a20d000e00"
            "2b0100000263400100e9b1160800005bff0002256101026340010003b216"
            "080140010019b216080000694fff0015b2160851000016634000006b021e"
            "1e1efe6916024000002b4c00070061b216082b4d00070061b21608210240"
            "020006017db2160842088009802108800900070067b21608210880090007"
            "0472b21608255c0116014000006b021702400100034fff0084b216085100"
            "00034fff008db216085100000316014000006b021111111313131311fe11"
            "111113131311fe694fff00a2b216085100006b0211fe"
        ),
        "78de4ea2f19d41aa0cd5e265b6c70a34cc21d505b0c4d5300ee9e53f04857010",
    ),
    "ROUTE20_RESET": (
        0x08178614,
        (
            "031a861708002bd20207002d8617082bd302070046861708022a40002a4100"
            "294200294300294400294500294600294700032a48002a49002a4a002a4b00"
            "294c00294d0003"
        ),
        "df55a046d9b7f55d503cba78e417209d6b70a290940e7e9612f74db88dc5d244",
    ),
    "ROUTE23_RESET": (
        0x0817915D,
        "0363911708002a5900295800166440000016654000001666400000166740000002",
        "f4625b8b5c039a076ff2adbbb0a412140b8d3bb5533363fe0fc6256e2585ed61",
    ),
    "VICTORY_1F_SWITCH": (
        0x081658EC,
        (
            "69216440640006011b591608a20c000e00d1020000a20c000f00e1020000"
            "2f2300258e003064050016644064006b026b02"
        ),
        "892968767f6bc726f71e0098ed98c8df9938987401cb8f83febc751a1aecc45f",
    ),
    "VICTORY_2F_SWITCH_1": (
        0x08165A0B,
        (
            "69216540640006013a5a1608a20d000a00d1020000a20d000b00e1020000"
            "2f2300258e0030640b0016654064006b026b02"
        ),
        "387af9681be8278f406a9982b886fc0451c001001d33c74ab6cfee1bab973d48",
    ),
    "VICTORY_2F_SWITCH_2": (
        0x08165A3C,
        (
            "69216640640006016b5a1608a221001000d1020000a221001100e1020000"
            "2f2300258e0030640c0016664064006b026b02"
        ),
        "a864db77531a7ce650d0d0313124156862f1c6ca22df88e501a52bcc502d3826",
    ),
    "VICTORY_3F_SWITCH": (
        0x08165CEF,
        (
            "6921674064000601215d1608a20c000c00d1020000a20c000d00e1020000"
            "2f2300258e0030640700640a0016674064006b026b02"
        ),
        "f1046964854febef8785a9db0a18f91915b3d7319e124b49ee5247d5af83b91e",
    ),
}


class Stage61TopologyProducerError(RuntimeError):
    """監査済み物理producerを推測なしに生成できない。"""


def _fail(message: str) -> None:
    raise Stage61TopologyProducerError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _hex(value: int, width: int = 8) -> str:
    return f"0x{value:0{width}X}"


def _read(raw: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if address < ROM_BASE or size < 0 or offset < 0 or offset + size > len(raw):
        _fail(f"{label} is outside ROM: {_hex(address)}+{size:#x}")
    return raw[offset:offset + size]


def _u16(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def _read_u32(raw: bytes, address: int, label: str) -> int:
    return _u32(_read(raw, address, 4, label))


def _map_header_address(raw: bytes, pair: tuple[int, int]) -> int:
    group, number = pair
    groups = _read_u32(raw, MAP_GROUPS_POINTER_SITE, "gMapGroups")
    group_table = _read_u32(raw, groups + group * 4, f"map group {group}")
    return _read_u32(raw, group_table + number * 4, f"map header {group}/{number}")


def _records(raw: bytes) -> list[bytes]:
    if len(raw) % OBJECT_EVENT_SIZE:
        _fail("object array is not record-aligned")
    return [raw[index:index + OBJECT_EVENT_SIZE]
            for index in range(0, len(raw), OBJECT_EVENT_SIZE)]


def _record(
    source: bytes,
    *,
    local_id: int | None = None,
    trainer_type: int | None = None,
    script: int | None = None,
    flag: int | None = None,
) -> bytes:
    if len(source) != OBJECT_EVENT_SIZE:
        _fail("object template size drifted")
    result = bytearray(source)
    if local_id is not None:
        result[0] = local_id
    if trainer_type is not None:
        struct.pack_into("<H", result, 12, trainer_type)
    if script is not None:
        struct.pack_into("<I", result, 16, script)
    if flag is not None:
        struct.pack_into("<H", result, 20, flag)
    return bytes(result)


@dataclass(frozen=True)
class TopologyRuntimePatch:
    """Stage60への適用前にexpectedを照合するstructural patch。"""

    address: int
    expected: bytes
    replacement: bytes
    role: str

    def to_report(self) -> dict[str, Any]:
        return {
            "address": _hex(self.address),
            "expected_hex": self.expected.hex(),
            "replacement_hex": self.replacement.hex(),
            "role": self.role,
        }


@dataclass(frozen=True)
class Stage61TopologyProducerContract:
    """clean/Stage60 preimageとstate ownershipを固定した監査結果。"""

    clean_sha256: str
    stage60_sha256: str
    source_evidence: tuple[Mapping[str, Any], ...]
    target_evidence: tuple[Mapping[str, Any], ...]
    script_evidence: tuple[Mapping[str, Any], ...]
    owner_rows: tuple[Mapping[str, Any], ...]
    assertions: Mapping[str, bool]
    contract_sha256: str

    def to_report(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "READY" if all(self.assertions.values()) else "FAIL",
            "clean_sha256": self.clean_sha256,
            "stage60_sha256": self.stage60_sha256,
            "source_evidence": [dict(row) for row in self.source_evidence],
            "target_evidence": [dict(row) for row in self.target_evidence],
            "script_evidence": [dict(row) for row in self.script_evidence],
            "state_owners": [dict(row) for row in self.owner_rows],
            "assertions": dict(self.assertions),
            "contract_sha256": self.contract_sha256,
        }


@dataclass(frozen=True)
class Stage61TopologyProducerMaterialization:
    """project-owned物理producer payloadとintegration contract。"""

    payload_base: int
    payload: bytes
    patches: tuple[TopologyRuntimePatch, ...]
    record_address_mapping: Mapping[int, int]
    node_addresses: Mapping[str, int]
    object_rows: tuple[Mapping[str, Any], ...]
    coord_rows: tuple[Mapping[str, Any], ...]
    map_script_rows: tuple[Mapping[str, Any], ...]
    owner_rows: tuple[Mapping[str, Any], ...]
    source_pointer_literals: tuple[int, ...]
    verification_assertions: Mapping[str, bool]
    materialization_sha256: str

    def rebase_object_address(self, address: int) -> int | None:
        """旧object record内siteを新arrayの同じfieldへ写す。"""

        for old, new in self.record_address_mapping.items():
            delta = address - old
            if 0 <= delta < OBJECT_EVENT_SIZE:
                return new + delta
        return None

    def to_report(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": (
                "READY" if all(self.verification_assertions.values()) else "FAIL"
            ),
            "payload_base": _hex(self.payload_base),
            "payload_size": len(self.payload),
            "payload_raw_hex": self.payload.hex(),
            "payload_sha256": _sha(self.payload),
            "patches": [row.to_report() for row in self.patches],
            "record_address_mapping": {
                _hex(old): _hex(new)
                for old, new in sorted(self.record_address_mapping.items())
            },
            "node_addresses": {
                name: _hex(address)
                for name, address in sorted(self.node_addresses.items())
            },
            "objects": [dict(row) for row in self.object_rows],
            "coords": [dict(row) for row in self.coord_rows],
            "map_scripts": [dict(row) for row in self.map_script_rows],
            "state_owners": [dict(row) for row in self.owner_rows],
            "source_pointer_literals": [
                _hex(value) for value in self.source_pointer_literals
            ],
            "verification_assertions": dict(self.verification_assertions),
            "materialization_sha256": self.materialization_sha256,
            "integration_contract": {
                "rule": "REBASE_ALL_PENDING_OBJECT_RECORD_PATCHES",
                "details": (
                    "graphics/script/visibility patchの旧record siteを"
                    "rebase_object_addressでpayload側へ写し、topology-owned fieldは"
                    "state_ownersを正として重複patchを拒否する"
                ),
            },
        }


def _owner_rows() -> tuple[Mapping[str, Any], ...]:
    flag_owners: Mapping[int, tuple[Sequence[str], Sequence[str]]] = {
        0x0040: (("096/031:tag3:reset_b3",), ("097/083:object:2:visibility",)),
        0x0041: (("096/031:tag3:reset_b3",), ("097/083:object:3:visibility",)),
        0x0042: (("096/031:tag3:reset_b3", "097/083:object:2:fall_reveal"),
                 ("097/084:object:3:visibility",)),
        0x0043: (("096/031:tag3:reset_b3", "097/083:object:3:fall_reveal"),
                 ("097/084:object:4:visibility",)),
        0x0044: (("096/031:tag3:reset_b3", "097/084:object:3:fall_reveal"),
                 ("097/085:object:2:visibility",)),
        0x0045: (("096/031:tag3:reset_b3", "097/084:object:4:fall_reveal"),
                 ("097/085:object:3:visibility",)),
        0x0046: (("096/031:tag3:reset_b3", "097/085:object:2:fall_reveal"),
                 ("097/086:object:1:visibility", "097/086:tag2/read",
                  "097/086:tag3/read")),
        0x0047: (("096/031:tag3:reset_b3", "097/085:object:3:fall_reveal"),
                 ("097/086:object:2:visibility", "097/086:tag2/read",
                  "097/086:tag3/read")),
        0x0048: (("096/031:tag3:reset_b4",), ("097/086:object:6:visibility",)),
        0x0049: (("096/031:tag3:reset_b4",), ("097/086:object:4:visibility",)),
        0x004A: (("096/031:tag3:reset_b4",), ("097/086:object:5:visibility",)),
        0x004B: (("096/031:tag3:reset_b4",), ("097/086:object:3:visibility",)),
        0x004C: (("096/031:tag3:reset_b4", "097/086:object:6:fall_reveal"),
                 ("097/087:object:1:visibility", "097/087:tag1/read",
                  "097/087:tag2/read", "097/087:tag3/read")),
        0x004D: (("096/031:tag3:reset_b4", "097/086:object:5:fall_reveal"),
                 ("097/087:object:4:visibility", "097/087:tag1/read",
                  "097/087:tag2/read", "097/087:tag3/read")),
        0x0058: (("096/035:tag3:reset_victory", "097/041:object:11:fall_reveal"),
                 ("097/040:object:10:visibility",)),
        0x0059: (("096/035:tag3:reset_victory",),
                 ("097/041:object:11:visibility",)),
        0x02D2: (("097/086:tag3:latch",),
                 ("096/031:tag3:guard_b3", "097/086:tag3:layout_guard")),
        0x02D3: (("097/087:tag3:latch",),
                 ("096/031:tag3:guard_b4", "097/087:tag3:layout_guard")),
    }
    var_owners: Mapping[int, tuple[Sequence[str], Sequence[str]]] = {
        0x4063: (("097/086:tag2:set_entry", "097/087:tag2:clear_entry"),
                 ("097/087:tag2:entry_guard", "097/087:tag4:warp_guard")),
        0x4064: (("096/035:tag3:reset_victory", "097/039:coord:1:switch"),
                 ("097/039:coord:1:guard", "097/039:projected_on_load")),
        0x4065: (("096/035:tag3:reset_victory", "097/040:coord:1:switch"),
                 ("097/040:coord:1:guard", "097/040:projected_on_load")),
        0x4066: (("096/035:tag3:reset_victory", "097/040:coord:2:switch"),
                 ("097/040:coord:2:guard", "097/040:projected_on_load")),
        0x4067: (("096/035:tag3:reset_victory", "097/041:coord:1:switch"),
                 ("097/041:coord:1:guard", "097/041:projected_on_load")),
    }
    result: list[Mapping[str, Any]] = []
    for source, (producers, consumers) in sorted(flag_owners.items()):
        result.append({
            "namespace": "FLAG",
            "source_id": _hex(source, 4),
            "target_id": _hex(FLAG_MAPPING[source], 4),
            "producer_owners": list(producers),
            "consumer_owners": list(consumers),
            "mapping": "NON_IDENTITY",
        })
    for source, (producers, consumers) in sorted(var_owners.items()):
        result.append({
            "namespace": "VAR",
            "source_id": _hex(source, 4),
            "target_id": _hex(VAR_MAPPING[source], 4),
            "producer_owners": list(producers),
            "consumer_owners": list(consumers),
            "mapping": "NON_IDENTITY",
        })
    return tuple(result)


def _evidence_row(
    name: str,
    side: str,
    spec: Mapping[str, Any],
) -> Mapping[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "map": f"{spec[f'{side}_map'][0]:03d}/{spec[f'{side}_map'][1]:03d}",
        "header_address": _hex(int(spec[f"{side}_header_address"])),
        "header_sha256": _sha(bytes.fromhex(str(spec[f"{side}_header_hex"]))),
        "event_address": _hex(int(spec[f"{side}_event_address"])),
        "event_sha256": _sha(bytes.fromhex(str(spec[f"{side}_event_hex"]))),
    }
    for kind in ("objects", "coords"):
        raw_key = f"{side}_{kind}_hex"
        if raw_key in spec:
            data = bytes.fromhex(str(spec[raw_key]))
            row[f"{kind}_address"] = _hex(int(spec[f"{side}_{kind}_address"]))
            row[f"{kind}_size"] = len(data)
            row[f"{kind}_sha256"] = _sha(data)
    return row


def _validate_map_preimage(
    rom: bytes,
    name: str,
    side: str,
    spec: Mapping[str, Any],
) -> None:
    pair = tuple(int(value) for value in spec[f"{side}_map"])
    header_address = _map_header_address(rom, pair)
    expected_header_address = int(spec[f"{side}_header_address"])
    if header_address != expected_header_address:
        _fail(
            f"{name} {side} header address drifted: "
            f"{_hex(header_address)} != {_hex(expected_header_address)}"
        )
    header = bytes.fromhex(str(spec[f"{side}_header_hex"]))
    if _read(rom, header_address, MAP_HEADER_SIZE, f"{name} {side} header") != header:
        _fail(f"{name} {side} map header preimage mismatch")
    event_address = _u32(header, 4)
    expected_event_address = int(spec[f"{side}_event_address"])
    if event_address != expected_event_address:
        _fail(f"{name} {side} event pointer drifted")
    event = bytes.fromhex(str(spec[f"{side}_event_hex"]))
    if _read(rom, event_address, EVENT_HEADER_SIZE, f"{name} {side} event") != event:
        _fail(f"{name} {side} event header preimage mismatch")
    for index, kind in ((0, "objects"), (2, "coords")):
        raw_key = f"{side}_{kind}_hex"
        if raw_key not in spec:
            continue
        expected = bytes.fromhex(str(spec[raw_key]))
        count = event[index]
        width = OBJECT_EVENT_SIZE if kind == "objects" else COORD_EVENT_SIZE
        if len(expected) != count * width:
            _fail(f"{name} {side} {kind} pinned size/count mismatch")
        pointer = _u32(event, 4 + index * 4)
        expected_pointer = int(spec[f"{side}_{kind}_address"])
        if pointer != expected_pointer:
            _fail(f"{name} {side} {kind} pointer drifted")
        actual = b"" if not expected else _read(
            rom, pointer, len(expected), f"{name} {side} {kind}"
        )
        if actual != expected:
            _fail(f"{name} {side} {kind} preimage mismatch")


def build_stage61_topology_producer_contract(
    clean_rom: bytes,
    stage60_rom: bytes,
) -> Stage61TopologyProducerContract:
    """対象surfaceをbyte単位で監査してfail-closed contractを返す。"""

    clean_digest = _sha(clean_rom)
    stage60_digest = _sha(stage60_rom)
    if len(clean_rom) != CLEAN_ROM_SIZE or clean_digest != CLEAN_ROM_SHA256:
        _fail(
            "clean FireRed JPN Rev.0 identity mismatch: "
            f"size={len(clean_rom)} sha256={clean_digest}"
        )
    if len(stage60_rom) != STAGE60_ROM_SIZE or stage60_digest != STAGE60_ROM_SHA256:
        _fail(
            "Stage60 identity mismatch: "
            f"size={len(stage60_rom)} sha256={stage60_digest}"
        )

    source_evidence: list[Mapping[str, Any]] = []
    target_evidence: list[Mapping[str, Any]] = []
    for name, spec in MAP_PREIMAGES.items():
        _validate_map_preimage(clean_rom, name, "source", spec)
        _validate_map_preimage(stage60_rom, name, "target", spec)
        source_evidence.append(_evidence_row(name, "source", spec))
        target_evidence.append(_evidence_row(name, "target", spec))

    script_evidence: list[Mapping[str, Any]] = []
    for name, (address, raw_hex, expected_sha) in SOURCE_SCRIPT_PINS.items():
        expected = bytes.fromhex(raw_hex)
        if _sha(expected) != expected_sha:
            _fail(f"internal source script pin hash mismatch: {name}")
        if _read(clean_rom, address, len(expected), name) != expected:
            _fail(f"source script preimage mismatch: {name}")
        script_evidence.append({
            "name": name,
            "address": _hex(address),
            "size": len(expected),
            "sha256": expected_sha,
        })

    owners = _owner_rows()
    source_owner_ids = {
        (row["namespace"], int(str(row["source_id"]), 0)) for row in owners
    }
    target_owner_ids = {
        (row["namespace"], int(str(row["target_id"]), 0)) for row in owners
    }
    target_script_fields = [
        _u32(bytes.fromhex(str(MAP_PREIMAGES[name]["target_header_hex"])), 8)
        for name in ("SEAFOAM_B3F", "SEAFOAM_B4F", "ROUTE20", "ROUTE23")
    ]
    assertions = {
        "clean_identity_exact": clean_digest == CLEAN_ROM_SHA256,
        "stage60_identity_exact": stage60_digest == STAGE60_ROM_SHA256,
        "ten_map_preimages_exact": len(source_evidence) == len(target_evidence) == 10,
        "eight_source_script_pins_exact": len(script_evidence) == 8,
        "state_owner_set_exact": source_owner_ids
        == ({("FLAG", value) for value in FLAG_MAPPING}
            | {("VAR", value) for value in VAR_MAPPING}),
        "mapped_state_injective": len(target_owner_ids) == len(owners),
        "all_state_nonidentity": all(
            int(str(row["source_id"]), 0) != int(str(row["target_id"]), 0)
            for row in owners
        ),
        "articuno_story_state_excluded": not (
            {("FLAG", 0x0082), ("FLAG", 0x02BE)} & source_owner_ids
        ),
        "four_target_map_script_fields_share_empty_table": (
            len(set(target_script_fields)) == 1
            and target_script_fields[0] == 0x09220D46
            and _read(stage60_rom, target_script_fields[0], 1, "empty map table")
            == b"\x00"
        ),
    }
    if not all(assertions.values()):
        _fail(
            "topology producer contract assertion failed: "
            + ",".join(key for key, value in assertions.items() if not value)
        )
    digest_payload = {
        "clean": clean_digest,
        "stage60": stage60_digest,
        "source": source_evidence,
        "target": target_evidence,
        "scripts": script_evidence,
        "owners": owners,
        "assertions": assertions,
    }
    return Stage61TopologyProducerContract(
        clean_sha256=clean_digest,
        stage60_sha256=stage60_digest,
        source_evidence=tuple(source_evidence),
        target_evidence=tuple(target_evidence),
        script_evidence=tuple(script_evidence),
        owner_rows=owners,
        assertions=assertions,
        contract_sha256=_sha(_stable(digest_payload)),
    )


class _Node:
    def __init__(self, raw: bytes = b"", *, align: int = 4) -> None:
        self.raw = bytearray(raw)
        self.align = align
        self.fixups: list[tuple[int, str, int]] = []

    def u8(self, value: int) -> "_Node":
        self.raw.append(value)
        return self

    def u16(self, value: int) -> "_Node":
        self.raw.extend(struct.pack("<H", value))
        return self

    def pointer(self, target: str, delta: int = 0) -> "_Node":
        self.fixups.append((len(self.raw), target, delta))
        self.raw.extend(b"\x00\x00\x00\x00")
        return self


def _script() -> _Node:
    return _Node(align=4)


def _checkflag(node: _Node, flag: int) -> None:
    node.u8(0x2B).u16(flag)


def _call_if(node: _Node, condition: int, target: str) -> None:
    node.u8(0x07).u8(condition).pointer(target)


def _goto_if(node: _Node, condition: int, target: str) -> None:
    node.u8(0x06).u8(condition).pointer(target)


def _setvar(node: _Node, variable: int, value: int) -> None:
    node.u8(0x16).u16(variable).u16(value)


def _compare(node: _Node, variable: int, value: int) -> None:
    node.u8(0x21).u16(variable).u16(value)


def _flag_write(node: _Node, opcode: int, flag: int) -> None:
    node.u8(opcode).u16(flag)


def _applymovement(node: _Node, local_id: int, movement: str) -> None:
    node.u8(0x4F).u16(local_id).pointer(movement)


def _setmetatile(node: _Node, x: int, y: int, metatile: int, collision: int) -> None:
    node.u8(0xA2).u16(x).u16(y).u16(metatile).u16(collision)


def _map_table(entries: Sequence[tuple[int, str]]) -> _Node:
    node = _Node(align=4)
    for tag, target in entries:
        node.u8(tag).pointer(target)
    node.u8(0)
    return node


def _condition_table(entries: Sequence[tuple[int, int, str]]) -> _Node:
    node = _Node(align=4)
    for variable, value, target in entries:
        node.u16(variable).u16(value).pointer(target)
    node.u16(0)
    return node


def _coord(x: int, y: int, elevation: int, variable: int, value: int) -> _Node:
    node = _Node(struct.pack("<HHBxHH2x", x, y, elevation, variable, value), align=4)
    return node


def _build_script_nodes() -> "OrderedDict[str, _Node]":
    nodes: "OrderedDict[str, _Node]" = OrderedDict()

    # Seafoam B3F transition/latch and falling-current flow.
    n = _script(); _checkflag(n, FLAG_MAPPING[0x02D2]); _call_if(n, 0, "b3_check")
    _checkflag(n, FLAG_MAPPING[0x02D2]); _call_if(n, 1, "b3_layout"); n.u8(0x02)
    nodes["b3_transition"] = n
    n = _script(); _setvar(n, 0x4002, 0)
    _checkflag(n, FLAG_MAPPING[0x0046]); _call_if(n, 0, "b3_add")
    _checkflag(n, FLAG_MAPPING[0x0047]); _call_if(n, 0, "b3_add")
    _compare(n, 0x4002, 2); _call_if(n, 1, "b3_stopped"); n.u8(0x03)
    nodes["b3_check"] = n
    n = _script(); _flag_write(n, 0x29, FLAG_MAPPING[0x02D2]); n.u8(0x03)
    nodes["b3_stopped"] = n
    n = _script(); n.u8(0xA7).u16(LAYOUT_MAPPING[0x0116]).u8(0x03)
    nodes["b3_layout"] = n
    n = _script(); n.u8(0x17).u16(0x4002).u16(1).u8(0x03)
    nodes["b3_add"] = n
    n = _script(); n.u8(0x69); _setvar(n, 0x4002, 0)
    _checkflag(n, FLAG_MAPPING[0x0046]); _call_if(n, 0, "b3_add")
    _checkflag(n, FLAG_MAPPING[0x0047]); _call_if(n, 0, "b3_add")
    _compare(n, 0x4002, 2); _goto_if(n, 1, "b3_blocked")
    n.u8(0x42).u16(0x8008).u16(0x8009)
    _compare(n, 0x8008, 24); _call_if(n, 0, "b3_ride_far")
    _compare(n, 0x8008, 24); _call_if(n, 4, "b3_ride_close")
    _setvar(n, VAR_MAPPING[0x4063], 1)
    n.raw.extend(struct.pack("<BBBBHH", 0x39, 97, 87, 0xFF, 27, 21))
    n.u8(0x27).u8(0x6B).u8(0x02)
    nodes["b3_fall"] = n
    n = _script(); _applymovement(n, 0x00FF, "b3_movement_far")
    n.u8(0x51).u16(0).u8(0x03); nodes["b3_ride_far"] = n
    n = _script(); _applymovement(n, 0x00FF, "b3_movement_close")
    n.u8(0x51).u16(0).u8(0x03); nodes["b3_ride_close"] = n
    n = _script(); _setvar(n, 0x4001, 0); n.u8(0x6B).u8(0x02)
    nodes["b3_blocked"] = n
    nodes["b3_movement_far"] = _Node(
        bytes.fromhex("1d1d1d1d2020201d1d1d1d1d1dfe"), align=1
    )
    nodes["b3_movement_close"] = _Node(
        bytes.fromhex("1d1d1d1d20201d1d1d1d1d1d1dfe"), align=1
    )
    nodes["b3_condition"] = _condition_table(((0x4001, 1, "b3_fall"),))
    nodes["b3_table"] = _map_table(((3, "b3_transition"), (2, "b3_condition")))

    # Seafoam B4F: Articuno resume/show state is deliberately absent.
    n = _script(); _checkflag(n, FLAG_MAPPING[0x02D3]); _call_if(n, 0, "b4_check")
    _checkflag(n, FLAG_MAPPING[0x02D3]); _call_if(n, 1, "b4_layout"); n.u8(0x02)
    nodes["b4_transition"] = n
    n = _script(); _setvar(n, 0x4002, 0)
    _checkflag(n, FLAG_MAPPING[0x004C]); _call_if(n, 0, "b4_add")
    _checkflag(n, FLAG_MAPPING[0x004D]); _call_if(n, 0, "b4_add")
    _compare(n, 0x4002, 2); _call_if(n, 1, "b4_stopped"); n.u8(0x03)
    nodes["b4_check"] = n
    n = _script(); _flag_write(n, 0x29, FLAG_MAPPING[0x02D3]); n.u8(0x03)
    nodes["b4_stopped"] = n
    n = _script(); n.u8(0xA7).u16(LAYOUT_MAPPING[0x0117]).u8(0x03)
    nodes["b4_layout"] = n
    n = _script(); n.u8(0x17).u16(0x4002).u16(1).u8(0x03)
    nodes["b4_add"] = n
    n = _script(); _setvar(n, 0x4002, 0)
    _checkflag(n, FLAG_MAPPING[0x004C]); _call_if(n, 0, "b4_add")
    _checkflag(n, FLAG_MAPPING[0x004D]); _call_if(n, 0, "b4_add")
    _compare(n, 0x4002, 2); _goto_if(n, 1, "b4_calm"); n.u8(0x02)
    nodes["b4_load"] = n
    n = _script(); _setmetatile(n, 12, 14, 0x012B, 0)
    _setmetatile(n, 13, 14, 0x012B, 0); n.u8(0x02); nodes["b4_calm"] = n
    n = _script(); n.u8(0x5B).u16(0x00FF).u8(2).u8(0x25).u16(0x0161).u8(0x02)
    nodes["b4_warp"] = n
    n = _script(); n.u8(0x69); _applymovement(n, 0x00FF, "b4_movement_enter")
    n.u8(0x51).u16(0); _setvar(n, VAR_MAPPING[0x4063], 0)
    n.u8(0x6B).u8(0x02); nodes["b4_enter"] = n
    nodes["b4_movement_enter"] = _Node(bytes.fromhex("1e1e1efe"), align=1)
    n = _script(); n.u8(0x69); _setvar(n, 0x4002, 0)
    _checkflag(n, FLAG_MAPPING[0x004C]); _call_if(n, 0, "b4_add")
    _checkflag(n, FLAG_MAPPING[0x004D]); _call_if(n, 0, "b4_add")
    _compare(n, 0x4002, 2); _goto_if(n, 1, "b4_blocked")
    n.u8(0x42).u16(0x8008).u16(0x8009)
    _compare(n, 0x8008, 9); _call_if(n, 0, "b4_ride_far")
    _compare(n, 0x8008, 9); _call_if(n, 4, "b4_ride_close")
    n.u8(0x25).u16(0x015C); _setvar(n, 0x4001, 0)
    n.u8(0x6B).u8(0x02); nodes["b4_fall"] = n
    n = _script(); _applymovement(n, 0x00FF, "b4_movement_far")
    n.u8(0x51).u16(0).u8(0x03); nodes["b4_ride_far"] = n
    n = _script(); _applymovement(n, 0x00FF, "b4_movement_close")
    n.u8(0x51).u16(0).u8(0x03); nodes["b4_ride_close"] = n
    n = _script(); _setvar(n, 0x4001, 0); n.u8(0x6B).u8(0x02)
    nodes["b4_blocked"] = n
    nodes["b4_movement_far"] = _Node(bytes.fromhex("1111111313131311fe"), align=1)
    nodes["b4_movement_close"] = _Node(bytes.fromhex("11111113131311fe"), align=1)
    n = _script(); n.u8(0x69); _applymovement(n, 0x00FF, "b4_movement_up")
    n.u8(0x51).u16(0).u8(0x6B).u8(0x02); nodes["b4_upward"] = n
    nodes["b4_movement_up"] = _Node(bytes.fromhex("11fe"), align=1)
    nodes["b4_warp_condition"] = _condition_table(
        ((VAR_MAPPING[0x4063], 1, "b4_warp"),)
    )
    nodes["b4_frame_condition"] = _condition_table((
        (VAR_MAPPING[0x4063], 1, "b4_enter"),
        (0x4001, 1, "b4_fall"),
    ))
    nodes["b4_table"] = _map_table((
        (3, "b4_transition"),
        (1, "b4_load"),
        (4, "b4_warp_condition"),
        (2, "b4_frame_condition"),
    ))

    # Route20/Route23 are bounded state writers, not generic story imports.
    n = _script(); _checkflag(n, FLAG_MAPPING[0x02D2]); _call_if(n, 0, "route20_b3")
    _checkflag(n, FLAG_MAPPING[0x02D3]); _call_if(n, 0, "route20_b4"); n.u8(0x02)
    nodes["route20_transition"] = n
    n = _script()
    for source in (0x40, 0x41): _flag_write(n, 0x2A, FLAG_MAPPING[source])
    for source in range(0x42, 0x48): _flag_write(n, 0x29, FLAG_MAPPING[source])
    n.u8(0x03); nodes["route20_b3"] = n
    n = _script()
    for source in range(0x48, 0x4C): _flag_write(n, 0x2A, FLAG_MAPPING[source])
    for source in (0x4C, 0x4D): _flag_write(n, 0x29, FLAG_MAPPING[source])
    n.u8(0x03); nodes["route20_b4"] = n
    nodes["route20_table"] = _map_table(((3, "route20_transition"),))

    n = _script(); _flag_write(n, 0x2A, FLAG_MAPPING[0x59])
    _flag_write(n, 0x29, FLAG_MAPPING[0x58])
    for source in range(0x4064, 0x4068): _setvar(n, VAR_MAPPING[source], 0)
    n.u8(0x02); nodes["route23_transition"] = n
    nodes["route23_table"] = _map_table(((3, "route23_transition"),))

    # Victory Road coord scripts. Floor-open metatiles are target semantic IDs.
    switch_specs = (
        ("victory1", 0x4064, ((12, 14), (12, 15)), (6,)),
        ("victory2a", 0x4065, ((13, 10), (13, 11)), (9,)),
        ("victory2b", 0x4066, ((33, 16), (33, 17)), (10,)),
        ("victory3", 0x4067, ((12, 12), (12, 13)), (8, 10)),
    )
    for name, source_var, positions, locals_ in switch_specs:
        n = _script(); n.u8(0x69); _compare(n, VAR_MAPPING[source_var], 100)
        _goto_if(n, 1, f"{name}_already")
        _setmetatile(n, positions[0][0], positions[0][1], 0x0307, 0)
        _setmetatile(n, positions[1][0], positions[1][1], 0x0317, 0)
        n.u8(0x2F).u16(0x0023).u8(0x25).u16(0x008E).u8(0x30)
        for local_id in locals_: n.u8(0x64).u16(local_id)
        _setvar(n, VAR_MAPPING[source_var], 100); n.u8(0x6B).u8(0x02)
        nodes[f"{name}_switch"] = n
        n = _script(); n.u8(0x6B).u8(0x02); nodes[f"{name}_already"] = n

    return nodes


def _build_object_nodes(strength_target: int) -> tuple[Mapping[str, _Node], Mapping[str, list[int]]]:
    result: "OrderedDict[str, _Node]" = OrderedDict()
    old_indices: dict[str, list[int]] = {}

    def source(name: str) -> list[bytes]:
        return _records(bytes.fromhex(str(MAP_PREIMAGES[name]["source_objects_hex"])))

    def target(name: str) -> list[bytes]:
        return _records(bytes.fromhex(str(MAP_PREIMAGES[name]["target_objects_hex"])))

    source_rows = source("SEAFOAM_1F"); rows = target("SEAFOAM_1F")
    rows += [
        _record(source_rows[0], local_id=2, trainer_type=FLAG_MAPPING[0x42],
                script=strength_target, flag=FLAG_MAPPING[0x40]),
        _record(source_rows[1], local_id=3, trainer_type=FLAG_MAPPING[0x43],
                script=strength_target, flag=FLAG_MAPPING[0x41]),
    ]
    result["objects_seafoam_1f"] = _Node(b"".join(rows)); old_indices["SEAFOAM_1F"] = [0]

    source_rows = source("SEAFOAM_B1F"); rows = target("SEAFOAM_B1F")
    rows += [
        _record(source_rows[0], local_id=3, trainer_type=FLAG_MAPPING[0x44],
                script=strength_target, flag=FLAG_MAPPING[0x42]),
        _record(source_rows[1], local_id=4, trainer_type=FLAG_MAPPING[0x45],
                script=strength_target, flag=FLAG_MAPPING[0x43]),
    ]
    result["objects_seafoam_b1f"] = _Node(b"".join(rows)); old_indices["SEAFOAM_B1F"] = [0, 1]

    source_rows = source("SEAFOAM_B2F"); rows = target("SEAFOAM_B2F")
    rows += [
        _record(source_rows[0], local_id=2, trainer_type=FLAG_MAPPING[0x46],
                script=strength_target, flag=FLAG_MAPPING[0x44]),
        _record(source_rows[1], local_id=3, trainer_type=FLAG_MAPPING[0x47],
                script=strength_target, flag=FLAG_MAPPING[0x45]),
    ]
    result["objects_seafoam_b2f"] = _Node(b"".join(rows)); old_indices["SEAFOAM_B2F"] = [0]

    # B3F local1/2 are target-owned service hosts at the exact source boulder coordinates.
    # Preserve their live target roots instead of replacing them with source null scripts.
    # local3/4 are likewise existing target records; only the proven topology-owned
    # visibility/script fields are rebound. The two actually missing source boulders are
    # appended as collision-free local5/6.
    source_rows = source("SEAFOAM_B3F"); target_rows = target("SEAFOAM_B3F")
    rows = [
        _record(target_rows[0], flag=FLAG_MAPPING[0x46]),
        _record(target_rows[1], flag=FLAG_MAPPING[0x47]),
        _record(target_rows[2], script=strength_target, flag=FLAG_MAPPING[0x4B]),
        _record(target_rows[3], script=strength_target, flag=FLAG_MAPPING[0x49]),
        _record(source_rows[2], local_id=5, trainer_type=FLAG_MAPPING[0x4D],
                script=strength_target, flag=FLAG_MAPPING[0x4A]),
        _record(source_rows[5], local_id=6, trainer_type=FLAG_MAPPING[0x4C],
                script=strength_target, flag=FLAG_MAPPING[0x48]),
    ]
    result["objects_seafoam_b3f"] = _Node(b"".join(rows)); old_indices["SEAFOAM_B3F"] = list(range(4))

    # B4F local1 is HOST_ALOLA_LIGHT (0x0938E388) repointed onto the source boulder
    # coordinate. It is a shared acquisition/topology host, not a disposable import stub.
    # local4 has a target service root as well. Preserve both roots and every non-topology
    # target field; only their missing visibility binding is supplied here.
    target_rows = target("SEAFOAM_B4F")
    rows = [
        _record(target_rows[0], flag=FLAG_MAPPING[0x4C]),
        target_rows[1],  # Target-owned Articuno; source story record is never imported.
        target_rows[2],
        _record(target_rows[3], flag=FLAG_MAPPING[0x4D]),
    ]
    result["objects_seafoam_b4f"] = _Node(b"".join(rows)); old_indices["SEAFOAM_B4F"] = list(range(4))

    rows = target("VICTORY_2F")
    for index in (7, 8, 9):
        rows[index] = _record(rows[index], script=strength_target)
    rows[9] = _record(rows[9], flag=FLAG_MAPPING[0x58])
    result["objects_victory_2f"] = _Node(b"".join(rows)); old_indices["VICTORY_2F"] = list(range(11))

    rows = target("VICTORY_3F")
    for index in (7, 8, 9):
        rows[index] = _record(rows[index], script=strength_target)
    source_rows = source("VICTORY_3F")
    rows.append(_record(
        source_rows[7], local_id=11, trainer_type=FLAG_MAPPING[0x58],
        script=strength_target, flag=FLAG_MAPPING[0x59],
    ))
    result["objects_victory_3f"] = _Node(b"".join(rows)); old_indices["VICTORY_3F"] = list(range(10))
    return result, old_indices


def _build_coord_nodes() -> Mapping[str, _Node]:
    result: "OrderedDict[str, _Node]" = OrderedDict()
    rows = []
    for x in (26, 27, 28):
        row = _coord(x, 19, 1, VAR_MAPPING[0x4063], 0)
        row.pointer("b4_upward")
        rows.append(row)
    node = _Node(align=4)
    for row in rows:
        base = len(node.raw); node.raw.extend(row.raw)
        node.fixups.extend((base + offset, target, delta)
                           for offset, target, delta in row.fixups)
    result["coords_seafoam_b4f"] = node

    coord_specs = (
        ("coords_victory_1f", ((20, 16, 3, 0x4064, 99, "victory1_switch"),)),
        ("coords_victory_2f", (
            (2, 19, 3, 0x4065, 99, "victory2a_switch"),
            (14, 19, 3, 0x4066, 99, "victory2b_switch"),
        )),
        ("coords_victory_3f", ((7, 7, 3, 0x4067, 99, "victory3_switch"),)),
    )
    for name, specs in coord_specs:
        node = _Node(align=4)
        for x, y, elevation, source_var, value, script_name in specs:
            row = _coord(x, y, elevation, VAR_MAPPING[source_var], value)
            row.pointer(script_name)
            base = len(node.raw); node.raw.extend(row.raw)
            node.fixups.extend((base + offset, target, delta)
                               for offset, target, delta in row.fixups)
        result[name] = node
    return result


def _allocate_nodes(
    nodes: Mapping[str, _Node], payload_base: int
) -> tuple[bytes, Mapping[str, int], Mapping[str, bytes]]:
    addresses: dict[str, int] = {}
    offsets: dict[str, int] = {}
    cursor = 0
    for name, node in nodes.items():
        if node.align <= 0 or node.align & (node.align - 1):
            _fail(f"invalid node alignment: {name}")
        cursor = (cursor + node.align - 1) & ~(node.align - 1)
        offsets[name] = cursor
        addresses[name] = payload_base + cursor
        cursor += len(node.raw)
    if payload_base + cursor > ROM_LIMIT:
        _fail("topology producer payload exceeds 32MiB ROM")
    blob = bytearray(b"\xFF" * cursor)
    resolved: dict[str, bytes] = {}
    for name, node in nodes.items():
        raw = bytearray(node.raw)
        for offset, target, delta in node.fixups:
            if target not in addresses:
                _fail(f"unresolved project-owned pointer: {name}->{target}")
            struct.pack_into("<I", raw, offset, addresses[target] + delta)
        start = offsets[name]
        blob[start:start + len(raw)] = raw
        resolved[name] = bytes(raw)
    return bytes(blob), addresses, resolved


def _patches(
    stage60_rom: bytes,
    addresses: Mapping[str, int],
    resolved: Mapping[str, bytes],
) -> tuple[TopologyRuntimePatch, ...]:
    rows: list[TopologyRuntimePatch] = []
    object_specs = (
        ("SEAFOAM_1F", "objects_seafoam_1f"),
        ("SEAFOAM_B1F", "objects_seafoam_b1f"),
        ("SEAFOAM_B2F", "objects_seafoam_b2f"),
        ("SEAFOAM_B3F", "objects_seafoam_b3f"),
        ("SEAFOAM_B4F", "objects_seafoam_b4f"),
        ("VICTORY_2F", "objects_victory_2f"),
        ("VICTORY_3F", "objects_victory_3f"),
    )
    for map_name, node_name in object_specs:
        spec = MAP_PREIMAGES[map_name]
        event = int(spec["target_event_address"])
        old_count = len(bytes.fromhex(str(spec["target_objects_hex"]))) // OBJECT_EVENT_SIZE
        old_pointer = int(spec["target_objects_address"])
        new_count = len(resolved[node_name]) // OBJECT_EVENT_SIZE
        rows.extend((
            TopologyRuntimePatch(
                event, bytes((old_count,)), bytes((new_count,)),
                f"{map_name}_OBJECT_COUNT",
            ),
            TopologyRuntimePatch(
                event + 4, struct.pack("<I", old_pointer),
                struct.pack("<I", addresses[node_name]),
                f"{map_name}_OBJECT_POINTER",
            ),
        ))
    coord_specs = (
        ("SEAFOAM_B4F", "coords_seafoam_b4f"),
        ("VICTORY_1F", "coords_victory_1f"),
        ("VICTORY_2F", "coords_victory_2f"),
        ("VICTORY_3F", "coords_victory_3f"),
    )
    for map_name, node_name in coord_specs:
        spec = MAP_PREIMAGES[map_name]
        event = int(spec["target_event_address"])
        expected_event = bytes.fromhex(str(spec["target_event_hex"]))
        new_count = len(resolved[node_name]) // COORD_EVENT_SIZE
        rows.extend((
            TopologyRuntimePatch(
                event + 2, expected_event[2:3], bytes((new_count,)),
                f"{map_name}_COORD_COUNT",
            ),
            TopologyRuntimePatch(
                event + 12, expected_event[12:16],
                struct.pack("<I", addresses[node_name]),
                f"{map_name}_COORD_POINTER",
            ),
        ))
    script_specs = (
        ("SEAFOAM_B3F", "b3_table"),
        ("SEAFOAM_B4F", "b4_table"),
        ("ROUTE20", "route20_table"),
        ("ROUTE23", "route23_table"),
    )
    for map_name, node_name in script_specs:
        spec = MAP_PREIMAGES[map_name]
        header = int(spec["target_header_address"])
        expected = bytes.fromhex(str(spec["target_header_hex"]))[8:12]
        rows.append(TopologyRuntimePatch(
            header + 8,
            expected,
            struct.pack("<I", addresses[node_name]),
            f"{map_name}_MAP_SCRIPT_POINTER",
        ))
    for patch in rows:
        if _read(stage60_rom, patch.address, len(patch.expected), patch.role) \
                != patch.expected:
            _fail(f"structural patch preimage mismatch: {patch.role}")
    return tuple(rows)


def _object_rows(
    addresses: Mapping[str, int], resolved: Mapping[str, bytes]
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    pairs = (
        ("SEAFOAM_1F", "objects_seafoam_1f"),
        ("SEAFOAM_B1F", "objects_seafoam_b1f"),
        ("SEAFOAM_B2F", "objects_seafoam_b2f"),
        ("SEAFOAM_B3F", "objects_seafoam_b3f"),
        ("SEAFOAM_B4F", "objects_seafoam_b4f"),
        ("VICTORY_2F", "objects_victory_2f"),
        ("VICTORY_3F", "objects_victory_3f"),
    )
    for map_name, node_name in pairs:
        data = resolved[node_name]
        rows.append({
            "map": f"{MAP_PREIMAGES[map_name]['target_map'][0]:03d}/"
                   f"{MAP_PREIMAGES[map_name]['target_map'][1]:03d}",
            "map_name": map_name,
            "node": node_name,
            "pointer": _hex(addresses[node_name]),
            "count": len(data) // OBJECT_EVENT_SIZE,
            "raw_hex": data.hex(),
            "sha256": _sha(data),
        })
    return tuple(rows)


def _coord_rows(
    addresses: Mapping[str, int], resolved: Mapping[str, bytes]
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    pairs = (
        ("SEAFOAM_B4F", "coords_seafoam_b4f"),
        ("VICTORY_1F", "coords_victory_1f"),
        ("VICTORY_2F", "coords_victory_2f"),
        ("VICTORY_3F", "coords_victory_3f"),
    )
    for map_name, node_name in pairs:
        data = resolved[node_name]
        rows.append({
            "map": f"{MAP_PREIMAGES[map_name]['target_map'][0]:03d}/"
                   f"{MAP_PREIMAGES[map_name]['target_map'][1]:03d}",
            "map_name": map_name,
            "node": node_name,
            "pointer": _hex(addresses[node_name]),
            "count": len(data) // COORD_EVENT_SIZE,
            "raw_hex": data.hex(),
            "sha256": _sha(data),
        })
    return tuple(rows)


def _script_rows(
    addresses: Mapping[str, int], resolved: Mapping[str, bytes]
) -> tuple[Mapping[str, Any], ...]:
    pairs = (
        ("097/086", "b3_table"),
        ("097/087", "b4_table"),
        ("096/031", "route20_table"),
        ("096/035", "route23_table"),
    )
    return tuple({
        "map": map_name,
        "node": node_name,
        "pointer": _hex(addresses[node_name]),
        "raw_hex": resolved[node_name].hex(),
        "sha256": _sha(resolved[node_name]),
    } for map_name, node_name in pairs)


def _record_mapping(
    addresses: Mapping[str, int], old_indices: Mapping[str, list[int]]
) -> Mapping[int, int]:
    node_for_map = {
        "SEAFOAM_1F": "objects_seafoam_1f",
        "SEAFOAM_B1F": "objects_seafoam_b1f",
        "SEAFOAM_B2F": "objects_seafoam_b2f",
        "SEAFOAM_B3F": "objects_seafoam_b3f",
        "SEAFOAM_B4F": "objects_seafoam_b4f",
        "VICTORY_2F": "objects_victory_2f",
        "VICTORY_3F": "objects_victory_3f",
    }
    result = {}
    for map_name, indices in old_indices.items():
        old_base = int(MAP_PREIMAGES[map_name]["target_objects_address"])
        new_base = addresses[node_for_map[map_name]]
        for index in indices:
            result[old_base + index * OBJECT_EVENT_SIZE] = (
                new_base + index * OBJECT_EVENT_SIZE
            )
    return result


def _source_topology_pointers() -> set[int]:
    pointers = {
        STRENGTH_SOURCE_ROOT,
        0x0816B047, 0x0816B052, 0x0816B090, 0x0816B09A,
        0x0816B0EE, 0x0816B0F9, 0x0816B10B, 0x0816B119,
        0x0816B126, 0x0816B15E, 0x0816B1A9, 0x0816B1DF,
        0x0816B1E9, 0x0816B1F1, 0x0816B203, 0x0816B219,
        0x0816B267, 0x0816B272, 0x0816B284, 0x0816B28D,
        0x0816B295, 0x0816B2A2,
        0x081658EC, 0x08165A0B, 0x08165A3C, 0x08165CEF,
        0x08178614, 0x0817861A, 0x0817915D, 0x08179163,
    }
    for spec in MAP_PREIMAGES.values():
        for key in ("source_objects_address", "source_coords_address"):
            if key in spec and int(spec[key]):
                pointers.add(int(spec[key]))
    return pointers


def _boulder_fields(object_rows: Iterable[Mapping[str, Any]]) -> list[tuple[str, int, int, int]]:
    result = []
    for row in object_rows:
        for record in _records(bytes.fromhex(str(row["raw_hex"]))):
            if record[1] != 0x61:
                continue
            result.append((
                str(row["map"]),
                record[0],
                _u16(record, 12),
                _u16(record, 20),
            ))
    return result


def materialize_stage61_topology_producer_state(
    contract: Stage61TopologyProducerContract,
    clean_rom: bytes,
    stage60_rom: bytes,
    payload_base: int,
    *,
    root_targets: Mapping[int, int],
) -> Stage61TopologyProducerMaterialization:
    """監査済み物理producerをproject-owned payloadへmaterializeする。"""

    if not all(contract.assertions.values()):
        _fail("unverified topology producer contract")
    if _sha(clean_rom) != contract.clean_sha256 or _sha(stage60_rom) != contract.stage60_sha256:
        _fail("topology producer contract/input provenance mismatch")
    if payload_base & 3 or not 0x09000000 <= payload_base < ROM_LIMIT:
        _fail(f"payload base is invalid: {_hex(payload_base)}")
    if set(root_targets) != {STRENGTH_SOURCE_ROOT}:
        _fail("root_targets must contain exactly the audited Strength root")
    strength_target = int(root_targets[STRENGTH_SOURCE_ROOT])
    if not ROM_BASE <= strength_target < ROM_LIMIT \
            or strength_target == STRENGTH_SOURCE_ROOT:
        _fail(f"relocated Strength root is invalid: {_hex(strength_target)}")

    nodes = _build_script_nodes()
    object_nodes, old_indices = _build_object_nodes(strength_target)
    nodes.update(object_nodes)
    nodes.update(_build_coord_nodes())
    payload, addresses, resolved = _allocate_nodes(nodes, payload_base)
    if payload_base <= strength_target < payload_base + len(payload):
        _fail("external Strength root overlaps topology producer payload")

    patches = _patches(stage60_rom, addresses, resolved)
    object_rows = _object_rows(addresses, resolved)
    coord_rows = _coord_rows(addresses, resolved)
    map_script_rows = _script_rows(addresses, resolved)
    record_mapping = _record_mapping(addresses, old_indices)
    imported_source_pointers = tuple(sorted(
        value for value in _source_topology_pointers()
        if struct.pack("<I", value) in payload
    ))

    expected_boulder_state = {
        ("097/083", 2): (FLAG_MAPPING[0x42], FLAG_MAPPING[0x40]),
        ("097/083", 3): (FLAG_MAPPING[0x43], FLAG_MAPPING[0x41]),
        ("097/084", 3): (FLAG_MAPPING[0x44], FLAG_MAPPING[0x42]),
        ("097/084", 4): (FLAG_MAPPING[0x45], FLAG_MAPPING[0x43]),
        ("097/085", 2): (FLAG_MAPPING[0x46], FLAG_MAPPING[0x44]),
        ("097/085", 3): (FLAG_MAPPING[0x47], FLAG_MAPPING[0x45]),
        ("097/086", 1): (0, FLAG_MAPPING[0x46]),
        ("097/086", 2): (0, FLAG_MAPPING[0x47]),
        ("097/086", 3): (0, FLAG_MAPPING[0x4B]),
        ("097/086", 4): (0, FLAG_MAPPING[0x49]),
        ("097/086", 5): (FLAG_MAPPING[0x4D], FLAG_MAPPING[0x4A]),
        ("097/086", 6): (FLAG_MAPPING[0x4C], FLAG_MAPPING[0x48]),
        ("097/087", 1): (0, FLAG_MAPPING[0x4C]),
        ("097/087", 4): (0, FLAG_MAPPING[0x4D]),
        ("097/040", 8): (0, 0),
        ("097/040", 9): (0, 0),
        ("097/040", 10): (0, FLAG_MAPPING[0x58]),
        ("097/041", 8): (0, 0),
        ("097/041", 9): (0, 0),
        ("097/041", 10): (0, 0),
        ("097/041", 11): (FLAG_MAPPING[0x58], FLAG_MAPPING[0x59]),
    }
    actual_boulder_state = {
        (map_name, local_id): (trainer_type, flag)
        for map_name, local_id, trainer_type, flag in _boulder_fields(object_rows)
    }
    # Only topology-owned boulder fields participate; unrelated target boulders are included
    # above with the exact zero state expected by the source mechanic.
    selected_actual = {
        key: actual_boulder_state.get(key) for key in expected_boulder_state
    }

    all_project_pointers = set(addresses.values())
    coord_script_pointers = {
        _u32(bytes.fromhex(str(row["raw_hex"])), offset + 12)
        for row in coord_rows
        for offset in range(0, len(bytes.fromhex(str(row["raw_hex"]))), COORD_EVENT_SIZE)
    }
    target_story = _records(bytes.fromhex(
        str(MAP_PREIMAGES["SEAFOAM_B4F"]["target_objects_hex"])
    ))[1]
    target_b3 = _records(bytes.fromhex(
        str(MAP_PREIMAGES["SEAFOAM_B3F"]["target_objects_hex"])
    ))
    target_b4 = _records(bytes.fromhex(
        str(MAP_PREIMAGES["SEAFOAM_B4F"]["target_objects_hex"])
    ))
    b3_output = _records(resolved["objects_seafoam_b3f"])
    b4_output = _records(resolved["objects_seafoam_b4f"])
    boulder_scripts = {
        (str(row["map"]), record[0]): _u32(record, 16)
        for row in object_rows
        for record in _records(bytes.fromhex(str(row["raw_hex"])))
        if record[1] == 0x61
    }
    expected_service_scripts = {
        ("097/086", 1): 0x093EE8AC,
        ("097/086", 2): 0x093EE8AC,
        ("097/087", 1): 0x0938E388,
        ("097/087", 4): 0x093EE8AC,
    }
    assertions = {
        "contract_provenance_exact": (
            contract.clean_sha256 == CLEAN_ROM_SHA256
            and contract.stage60_sha256 == STAGE60_ROM_SHA256
        ),
        "payload_within_32mib": payload_base + len(payload) <= ROM_LIMIT,
        "all_structural_patch_preimages_match": all(
            _read(stage60_rom, row.address, len(row.expected), row.role) == row.expected
            for row in patches
        ),
        "seven_object_arrays_materialized": len(object_rows) == 7,
        "object_counts_exact": [row["count"] for row in object_rows]
        == [3, 4, 3, 6, 4, 11, 11],
        "four_coord_arrays_materialized": [row["count"] for row in coord_rows]
        == [3, 1, 2, 1],
        "four_map_script_tables_materialized": len(map_script_rows) == 4,
        "all_old_object_records_rebasable": len(record_mapping) == 33,
        "source_topology_pointer_literal_zero": not imported_source_pointers,
        "all_coord_scripts_project_owned": coord_script_pointers <= all_project_pointers,
        "mapped_boulder_producer_consumer_fields_exact": (
            selected_actual == expected_boulder_state
        ),
        "strength_root_relocated_without_clobbering_service_hosts": (
            all(boulder_scripts.get(key) == value
                for key, value in expected_service_scripts.items())
            and all(
                script in {strength_target, *expected_service_scripts.values()}
                for script in boulder_scripts.values()
            )
        ),
        "b3_target_service_records_merged_field_exact": (
            b3_output[0] == _record(target_b3[0], flag=FLAG_MAPPING[0x46])
            and b3_output[1] == _record(target_b3[1], flag=FLAG_MAPPING[0x47])
            and b3_output[2] == _record(
                target_b3[2], script=strength_target, flag=FLAG_MAPPING[0x4B]
            )
            and b3_output[3] == _record(
                target_b3[3], script=strength_target, flag=FLAG_MAPPING[0x49]
            )
        ),
        "b4_target_service_records_merged_field_exact": (
            b4_output[0] == _record(target_b4[0], flag=FLAG_MAPPING[0x4C])
            and b4_output[3] == _record(target_b4[3], flag=FLAG_MAPPING[0x4D])
        ),
        "alola_acquisition_host_root_preserved": (
            _u32(b4_output[0], 16) == 0x0938E388
        ),
        "articuno_target_record_preserved_without_source_story_import": (
            b4_output[1] == target_story
            and _u32(b4_output[1], 16) != 0x0816B2A4
            and _u16(b4_output[1], 20) not in {0x0082, 0x02BE}
        ),
        "project_state_owner_set_exact": len(contract.owner_rows) == 23,
        "seafoam_physical_warp_targets_canonical_map": bytes((0x39, 97, 87, 0xFF))
        in resolved["b3_fall"],
        "layout_targets_are_project_clones": (
            struct.pack("<BH", 0xA7, 564) in resolved["b3_layout"]
            and struct.pack("<BH", 0xA7, 565) in resolved["b4_layout"]
        ),
        "victory_floor_open_metatiles_target_exact": all(
            struct.pack("<H", 0x0307) in resolved[name]
            and struct.pack("<H", 0x0317) in resolved[name]
            for name in ("victory1_switch", "victory2a_switch",
                         "victory2b_switch", "victory3_switch")
        ),
        "no_source_articuno_state_owner": all(
            int(str(row["source_id"]), 0) not in {0x0082, 0x02BE}
            for row in contract.owner_rows
        ),
    }
    if not all(assertions.values()):
        _fail(
            "topology producer materialization assertion failed: "
            + ",".join(key for key, value in assertions.items() if not value)
        )
    digest_payload = {
        "contract_sha256": contract.contract_sha256,
        "payload_base": payload_base,
        "payload_sha256": _sha(payload),
        "patches": [row.to_report() for row in patches],
        "record_mapping": sorted(record_mapping.items()),
        "owners": contract.owner_rows,
        "assertions": assertions,
    }
    return Stage61TopologyProducerMaterialization(
        payload_base=payload_base,
        payload=payload,
        patches=patches,
        record_address_mapping=record_mapping,
        node_addresses=addresses,
        object_rows=object_rows,
        coord_rows=coord_rows,
        map_script_rows=map_script_rows,
        owner_rows=contract.owner_rows,
        source_pointer_literals=imported_source_pointers,
        verification_assertions=assertions,
        materialization_sha256=_sha(_stable(digest_payload)),
    )


__all__ = [
    "CLEAN_ROM_SHA256",
    "FLAG_MAPPING",
    "LAYOUT_MAPPING",
    "MAP_PREIMAGES",
    "SOURCE_SCRIPT_PINS",
    "STAGE60_ROM_SHA256",
    "STRENGTH_SOURCE_ROOT",
    "Stage61TopologyProducerContract",
    "Stage61TopologyProducerError",
    "Stage61TopologyProducerMaterialization",
    "TopologyRuntimePatch",
    "VAR_MAPPING",
    "build_stage61_topology_producer_contract",
    "materialize_stage61_topology_producer_state",
]
