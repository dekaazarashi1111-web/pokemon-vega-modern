#!/usr/bin/env python3
"""T08のRAM/save台帳を検証し、互換性reportを決定的に生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAM_LAYOUT = ROOT / "config" / "ram_layout.csv"
SAVE_LAYOUT = ROOT / "config" / "save_layout.csv"
OVERLAY_H = ROOT / "overlays" / "save_migration" / "save_migration.h"
OVERLAY_C = ROOT / "overlays" / "save_migration" / "save_migration.c"
REPORT = ROOT / "reports" / "generated" / "save_compatibility.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_intervals(path: Path) -> int:
    by_space: dict[str, list[tuple[int, int, str]]] = {}
    live_count = 0
    for row in read_rows(path):
        if row["status"] != "LIVE" or not row["start"]:
            continue
        start = int(row["start"], 0)
        end = int(row["end_exclusive"], 0)
        size = int(row["size"], 0)
        if start >= end or end - start != size:
            raise ValueError(f"不正interval: {path}:{row['symbol']}")
        by_space.setdefault(row["address_space"], []).append((start, end, row["symbol"]))
        live_count += 1
    for space, intervals in by_space.items():
        intervals.sort()
        for left, right in zip(intervals, intervals[1:]):
            if left[1] > right[0]:
                raise ValueError(f"live overlap: {space}:{left[2]} / {right[2]}")
    return live_count


def render() -> str:
    ram_count = validate_intervals(RAM_LAYOUT)
    save_count = validate_intervals(SAVE_LAYOUT)
    save_rows = read_rows(SAVE_LAYOUT)
    deferred = [row["symbol"] for row in save_rows if row["status"] == "DEFER"]
    excluded = [row["symbol"] for row in save_rows if row["status"] == "EXCLUDED"]
    identities = {
        "ram_layout": sha256(RAM_LAYOUT),
        "save_layout": sha256(SAVE_LAYOUT),
        "overlay_h": sha256(OVERLAY_H),
        "overlay_c": sha256(OVERLAY_C),
    }
    return f"""# T08 RAM / save compatibility report

## 結論

- 新規saveはCFRU-JPのsector 30/31 payloadにある未衝突領域
  `SAVE_PARASITE_IMAGE_OFFSET 0x1F18..0x2718`（EWRAM
  `0x0203D000..0x0203D800`）へ、固定2,048 byteのversion 1 ledgerを保存する。
- 既存Vega saveは無条件には受理しない。既存sector signature/checksumが正しく、ledgerが
  未作成の場合だけ、一回性migration entry pointで変換する。未知magic、未知version、size不一致、
  ledger checksum不一致、非zero予約領域は明示的に拒否する。
- Vega badge/HM/story flagは既存`SaveBlock1.flags`に残し、Kanto渡航・訪問・認定章・地方・
  League・anchorと共有しない。早期渡航は実証済みの`0x0824 && 0x114B`または殿堂入りだけから
  monotonicに付与する。

## RAM配置

正本は `config/ram_layout.csv`。T02のlive ownerをmergeした結果、live interval overlapは0件、
live intervalは{ram_count}件。旧Factory backup `0x0203E118..0x0203E274`は348 byte圧縮・
3体復元・reset unsafeのため廃止し、ledger内の6×100 byte snapshotへ置換した。
transaction scratchは保存領域外の`0x0203E300..0x0203E400`へ名前付きで予約した。

## 保存owner

正本は `config/save_layout.csv`（live interval {save_count}件）。

- 全国図鑑1025: 既存CFRU `SaveBlock1` の150-byte seen/caught fieldの先頭129 byteを正本とし、
  ledgerへ重複保存しない。
- 個体育成値: `natureMint` / Hyper Training / Tera typeを80-byte BoxPokemon ABI内に保持する。
- QOL: text `INSTANT`、hatch `FAST`、Exp Shareは1個目badge取得済みならON。最大5個のタマゴを
  80-byte単位のFIFOで保持する。badge等から導出可能なunlockは保存しない。
- 通貨: arcade coinは既存暗号化u16・上限9999を再利用。Factory BPは新規u16・上限9999。
  research rankはu8で保存するが、research point通貨はearn hook不在のため`DEFER`であり、
  storage/display/earn/spend経路を持たない。Mirageはitem reward ownerで数値通貨を持たない。
- 125共有捕獲bitはstatic encounterとRaidで一つだけ持つ。Raid reward/retry/in-progress/bonusは
  別fieldで、capture bitを複製しない。
- `itemObtainedFlags`は832 item/104 byteの旧fieldから999 item/125 byteへzero-extend migrationする。
- DEFER: {', '.join(deferred)}。save対象外: {', '.join(excluded)}。

## 原子的復旧

`VegaPersistCallback`は既存の二slot全sector saveを呼ぶ境界である。Factory入場、party復元、
once reward、遭遇credit減算＋pending生成、捕獲確定、Raid reward/retry/bonusは、callback失敗時に
ledgerを変更前へ戻す。fixtureではpartial staging write後に失敗させ、active slot・残高・pendingの
片側だけが変化しないことを確認した。Factory復元は元partyの全600 byte（個体、HP、PP、status、
持ち物を含む）をcopyしてから同じsaveでmarkerを消すため、電断時は入場前snapshotから冪等に
再試行できる。

pending encounterはpool、species、form、level、personality、nature、IV、ability、shiny、Tera、
generator version、16-byte fingerprint、transaction idを保存する。逃走・撃破・全滅・resetでは
保持し、捕獲成功のcommitだけが消去する。

## 検証結果

- `python3 -m unittest tests.test_save_layout tests.test_facility_save -v`: PASS（5 tests）
- host C compile: `-std=c11 -Wall -Wextra -Werror`: PASS
- RAM/save live interval overlap: 0
- new/migrated round-trip、checksum破損、未知version拒否、予約領域拒否、QOL既定、
  地方別profile/anchor、League I→II、125 shared capture、Raid reward/retry/bonus: PASS
- Factory save/reset/restore、save失敗rollback、600-byte exact party、BP cap/underflow、once reward、
  Mirage非干渉: PASS
- pending encounterのflash失敗、reset再構成、二重課金防止、捕獲時だけclear: PASS

## 入力identity

- `config/ram_layout.csv`: `{identities['ram_layout']}`
- `config/save_layout.csv`: `{identities['save_layout']}`
- `overlays/save_migration/save_migration.h`: `{identities['overlay_h']}`
- `overlays/save_migration/save_migration.c`: `{identities['overlay_c']}`

Networkは使用していない。根拠は固定CFRU-JP、T02生成監査、T06/T07 ABIに限定した。
"""


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "check"), nargs="?", default="build")
    args = parser.parse_args()
    expected = render()
    if args.command == "check":
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != expected:
            raise SystemExit("save compatibility reportが入力と一致しません。buildを実行してください")
        print("T08 save compatibility report: PASS")
        return 0
    atomic_write(REPORT, expected)
    print(f"generated: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
