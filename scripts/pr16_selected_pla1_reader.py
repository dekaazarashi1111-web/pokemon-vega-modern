"""選定PLA1の全4byteを既存ARM consumerへ結ぶ。容量/自然入口は証明しない。"""
from __future__ import annotations

import hashlib
import json
import struct

BASE = 0x08000000
IMAGE_BASE = 0x095FA4F8
TARGET = 0x095FE848
OWNER = 530
FAMILY = 0
ENTRY = 0x09FFF05E
CODE_START = 0x09FFF044
CODE_SIZE = 2788
CANDIDATE = {"size": 33554432, "sha256": "0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583"}
IMAGE = {"size": 21383, "sha256": "499714cc04fd43ecb59ac45d8d23dad6badbc0137189c4fbcb8facbe13c46d13"}
ARM = {"size": CODE_SIZE, "sha256": "14b2e916522ce3cda1e624676edf5f73e95e1da045bcaa14ed1a24be78ba95aa"}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(data: bytes) -> dict:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def encode(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def take(data: bytes, offset: int, width: int) -> bytes:
    need(type(offset) is int and type(width) is int and 0 <= offset and 0 < width
         and offset + width <= len(data), "有限byte範囲")
    return data[offset:offset + width]


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(take(data, offset, 2), "little")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(take(data, offset, 4), "little")


def decode(image: bytes, owner: int, family: int) -> tuple[list[int], list[dict]]:
    """固定C形式に対する独立参照。指定owner/familyの鎖だけを読む。"""
    size = len(image)
    need(6720 <= size < 65535 and type(owner) is int and 0 <= owner < 1671
         and type(family) is int and family in (0, 1), "PLA1入力ABI")
    need(image[:4] == b"PLA1" and u16(image, 4) == 1 and u16(image, 6) == 32
         and u16(image, 8) == 1671 and image[11] == 8 and u32(image, 12) == 32
         and u32(image, 16) == 6716 and u32(image, 24) == size
         and 0 < u32(image, 28) <= 3342, "PLA1 header")
    nt, records = image[10], u32(image, 20)
    need(0 < nt <= 16 and 6716 + nt * 4 <= records <= size, "template/record境界")
    at = u16(image, 32 + owner * 4 + family * 2)
    need(records <= at and at + 3 <= size, "ownerのrecord範囲")
    ti = image[at + 2]
    need(ti < nt, "template ID")
    template_at, count = u16(image, 6716 + ti * 4), u16(image, 6718 + ti * 4)
    need(0 < count <= 256 and 6716 + nt * 4 <= template_at
         and template_at + count * 2 <= records, "template全範囲")
    n = (count + 7) // 8
    ns = (n + 7) // 8
    mask = bytearray(n)
    chain = []
    depth = 0
    while True:
        need(records <= at and at + 3 <= size and image[at + 2] == ti, "同templateのrecord")
        base, pos = u16(image, at), at + 3
        fields = [{"offset": at, "width": 2, "role": "relative_base_u16"},
                  {"offset": at + 2, "width": 1, "role": "template_id_u8"}]
        if base == 65535:
            full = take(image, pos, n)
            for i, value in enumerate(full):
                mask[i] ^= value
                fields.append({"offset": pos + i, "width": 1, "role": "full_mask_u8", "mask_index": i})
            end = pos + n
        else:
            depth += 1
            need(depth <= 8 and records <= base < at, "後方base/有限depth")
            selectors = int.from_bytes(take(image, pos, ns), "little")
            need(selectors >> n == 0, "selector範囲外bit")
            fields.extend({"offset": pos + i, "width": 1, "role": "selector_u8", "selector_index": i}
                          for i in range(ns))
            pos += ns
            for i in range(n):
                if selectors & (1 << i):
                    value = take(image, pos, 1)[0]
                    need(value != 0, "非zero差分")
                    mask[i] ^= value
                    fields.append({"offset": pos, "width": 1, "role": "xor_mask_u8", "mask_index": i})
                    pos += 1
            end = pos
        chain.append({"offset": at, "end_exclusive": end, "base": base,
                      "template_id": ti, "template_offset": template_at, "template_count": count,
                      "record_identity": identity(take(image, at, end - at)), "fields": fields})
        if base == 65535:
            break
        at = base
    need(count % 8 == 0 or mask[-1] >> (count % 8) == 0, "末尾未使用bit")
    moves = [u16(image, template_at + i * 2) for i in range(count)]
    need(all(0 < move <= 1062 for move in moves), "template move範囲")
    result = [move for i, move in enumerate(moves) if mask[i // 8] & (1 << (i % 8))]
    need(len(result) <= (160 if family == 0 else 40) and len(set(result)) == len(result), "出力件数/重複")
    return result, chain


def cover(chain: list[dict], offset: int, width: int) -> list[dict]:
    need(type(offset) is int and type(width) is int and offset >= 0 and width > 0, "対象範囲")
    result = []
    for byte in range(offset, offset + width):
        matches = [(row, field) for row in chain for field in row["fields"]
                   if field["offset"] <= byte < field["offset"] + field["width"]]
        need(len(matches) == 1, "対象byteの一意なreader型")
        row, field = matches[0]
        result.append({"offset": byte, "record_offset": row["offset"],
                       "role": field["role"], "field_offset": field["offset"], "field_width": field["width"]})
    return result


def execute(raw: bytes, image: bytes, capacity: int, expected: list[int]) -> dict:
    """既存fail-closed Thumb解釈器で実配置のdecoder本体とmemsetを実行。"""
    import pr16_dex_hof_runtime_sprite as engine
    stack, output, countp, stop = 0x03007F00, 0x02010000, 0x02010400, 0x01000000
    code = ((0x09FFF048, 0x09FFF360), (0x09FFF890, 0x09FFF8A0))
    readable = ((CODE_START, CODE_START + CODE_SIZE), (IMAGE_BASE, IMAGE_BASE + len(image)))

    class Reader(engine.Machine):
        def __init__(self):
            super().__init__(raw, code, ((stack - 2048, stack + 12), (output, output + 320), (countp, countp + 2)))
            self.target_reads = []

        def read(self, address, width):
            if BASE <= address < BASE + len(self.raw):
                need(any(lo <= address and address + width <= hi for lo, hi in readable), "未宣言ROM read拒否")
            value = super().read(address, width)
            if address < TARGET + 4 and TARGET < address + width:
                need(self.trace and width == 1, "実byte読取命令")
                pc = self.trace[-1]["address"]
                expected_pc = 0x09FFF2EC if address == TARGET else 0x09FFF328
                need(pc == expected_pc, "selector/XORの具体的LDRB")
                self.target_reads.append({"address": address, "width": width, "instruction": pc,
                                          "instruction_identity": identity(take(raw, pc - BASE, 2))})
            return value

    machine = Reader()
    machine.r[:4] = [IMAGE_BASE, len(image), OWNER, FAMILY]
    machine.r[13], machine.r[14] = stack, stop | 1
    machine.r[12] = engine.UNDEFINED_R12
    preserved = machine.r[4:12] + [machine.r[13]]
    for at in range(output, output + 320):
        machine.seed(at, 1, 0xA5)
    machine.seed(countp, 2, 0xBEEF)
    for offset, value in enumerate((output, capacity, countp)):
        machine.seed(stack + offset * 4, 4, value)
    machine.run(ENTRY, stop, limit=100000)
    need(machine.r[4:12] + [machine.r[13]] == preserved, "callee-saved/SP帰還")
    need({row["address"] for row in machine.target_reads} == set(range(TARGET, TARGET + 4)), "全4byte消費")
    success = capacity >= len(expected)
    need(machine.r[0] == int(success), "decoder実帰値")
    actual = bytes(machine.mem[output + i] for i in range(320))
    expected_bytes = b"".join(struct.pack("<H", move) for move in expected)
    if success:
        need(actual[:len(expected_bytes)] == expected_bytes and actual[len(expected_bytes):] == b"\xA5" * (320 - len(expected_bytes))
             and machine.read(countp, 2) == len(expected), "独立decode/出力境界")
    else:
        need(actual == b"\xA5" * 320 and machine.read(countp, 2) == 0xBEEF, "容量不足は出力/count無変更")
        need(not any(output <= row["address"] < output + 320 or row["address"] == countp for row in machine.writes), "失敗側出力write禁止")
    return {"capacity": capacity, "returned": machine.r[0], "output_count": len(expected) if success else None,
            "instruction_count": len(machine.trace), "instruction_trace_identity": identity(encode({"trace": machine.trace})),
            "target_reads": machine.target_reads, "callee_saved_and_sp_preserved": True,
            "output_identity": identity(actual), "output_write_on_failure": False if not success else None,
            "external_hooks": 0, "natural_entry_claimed": False, "native_processes": 0}


def prove(raw: bytes, image: bytes, arm: bytes) -> dict:
    need(identity(raw) == CANDIDATE and identity(image) == IMAGE and identity(arm) == ARM, "固定候補/PLA1/ARM全hash")
    need(take(raw, IMAGE_BASE - BASE, len(image)) == image
         and take(raw, CODE_START - BASE, len(arm)) == arm, "実配置全byte一致")
    expected, chain = decode(image, OWNER, FAMILY)
    typed = cover(chain, TARGET - IMAGE_BASE, 4)
    need(chain[0]["offset"] == 17227 and chain[0]["end_exclusive"] == 17239
         and [r["role"] for r in typed] == ["selector_u8", "xor_mask_u8", "xor_mask_u8", "xor_mask_u8"], "選定4byte境界")
    profiles = [execute(raw, image, cap, expected) for cap in (160, len(expected) - 1)]
    return {"schema_version": 1, "scope": "ONE_PLA1_OWNER_FAMILY_ACTUAL_CONDITIONAL_DECODER",
            "candidate": CANDIDATE, "image": IMAGE, "arm": ARM, "target": TARGET,
            "owner": OWNER, "family": FAMILY, "entry": ENTRY, "chain": chain,
            "target_roles": typed, "profiles": profiles, "actual_conditional_reader_proven": True,
            "formal_classification_changes": 0, "formal_classified": 789, "formal_unclassified": 85,
            "selected_unknown_origins": 6, "donor_safe_bytes": 0,
            "limitations_ja": ["owner530/family0と明示した非alias RAM/ABIの有限decoder実行。自然hook入口・画面供給の新受入ではない。",
                               "他2地点・窓外跨り・間接参照・退役移管・保存controller/heap/局所Saveは未完。",
                               "正式型差分には別の完了Actions受領が必要。"]}
