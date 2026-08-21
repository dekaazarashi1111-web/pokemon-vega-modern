# Codex Battle Bridge protocol

状態: T26 / Stage 43 protocol 1.0

## 目的と境界

Stage 43は、RetroArch Network Control Interface（NCI）からmGBAのsystem memory mapにある
EWRAM mailboxだけを読み書きし、`PING` / `PONG`を交換する。対戦、party登録、行動選択、報酬、
save書込みはT26の範囲外である。

- transportはplain UDPであり暗号化・認証を持たない。信頼できる同一LAN（trusted LAN）だけで使う。
- SSHは設定診断とversioned ROM転送だけに使い、turn transportには使わない。
- production CLIは任意address read/writeを公開しない。host write可能範囲は
  `0x0203F880..0x0203F8C0`の64 byteだけである。
- NCIの`WRITE_CORE_MEMORY`はRetroAchievements hardcoreを無効化する可能性がある。
- ROM、save、savestateをPC側で直接編集しない。Stage 43は既存iPad ROM/saveとは別名で配置する。

一次仕様:

- RetroArch NCI: <https://docs.libretro.com/development/retroarch/network-control-interface/>
- mGBA libretro memory descriptors:
  <https://github.com/mgba-emu/mgba/blob/master/src/platform/libretro/libretro.c>

mGBAはGBA EWRAMをsystem address `0x02000000..0x02040000`としてdescriptorへ公開する。
NCIでは`READ_CORE_MEMORY <hex-address> <decimal-size>`と
`WRITE_CORE_MEMORY <hex-address> <hex-byte>...`を用いる。

## Stage 43 identity

| 項目 | 値 |
|---|---:|
| magic | `VCBX` / little-endian `0x58424356` |
| protocol | major 1 / minor 0 |
| Stage | 43 |
| Stage identity | `0x0DB5FBE5` |
| Stage 42 base CRC32 | `EECED58B` |
| capability | status、PING、NCI core memory (`0x00000007`) |
| mailbox | `0x0203F800..0x0203F900` (256 byte) |
| T26 reservation | `0x0203F800..0x0203FA00` (512 byte) |
| host request span | `0x0203F880..0x0203F8C0` (64 byte) |

残り256 byteはT27/T28のversioned拡張用に予約するが、protocol 1.0は読み書きしない。
mailboxはvolatileでありflashへ保存しない。

## Mailbox ABI

全multi-byte値はlittle-endian、structは256 byte固定である。

| offset | size | owner | field |
|---:|---:|---|---|
| `0x00` | 4 | ROM | magic |
| `0x04` | 2+2 | ROM | protocol major/minor |
| `0x08` | 2+2 | ROM | struct/header size |
| `0x0C` | 2+2 | ROM | request offset/size |
| `0x10` | 2+2 | ROM | snapshot offset/size |
| `0x14` | 4 | ROM | capability bits |
| `0x18` | 2+2 | ROM | Stage/phase |
| `0x1C` | 4 | ROM | Stage identity |
| `0x20` | 4 | ROM | Stage 42 base ROM CRC32 |
| `0x24` | 4 | ROM | bridge build identity |
| `0x28` | 4+4 | ROM | session nonce/inverse |
| `0x30` | 4+4 | ROM | RAM address/reserved size |
| `0x38` | 2+2+4 | ROM | max payload/command count/header flags |
| `0x40` | 4+4 | ROM | snapshot sequence/inverse |
| `0x48` | 2+2+4 | ROM | snapshot payload size/status/CRC32 |
| `0x50` | 4+4 | ROM | response sequence/inverse |
| `0x58` | 2+2 | ROM | response status/error |
| `0x5C` | 2+2 | ROM | response payload size/last command |
| `0x60` | 4+4+4 | ROM | PONG token/inverse/magic |
| `0x6C` | 4+4 | ROM | accepted request CRC/last accepted sequence |
| `0x74` | 4+4+4 | ROM | last rejected sequence/fingerprint/count |
| `0x80` | 4 | host | request session nonce |
| `0x84` | 2+2 | host | command/expected phase |
| `0x88` | 2+2+4 | host | payload size/flags/payload CRC32 |
| `0x90` | 32 | host | zero-padded payload |
| `0xB0` | 4+4 | host | request CRC32/reserved zero |
| `0xB8` | 4 | host | request sequence inverse |
| `0xBC` | 4 | host | request sequence commit |
| `0xC0` | 64 | ROM | future protocol area; protocol 1.0ではzero |

CRC32はIEEE polynomial `0xEDB88320`を使う。

- payload CRCは`request_payload[0:payload_size]`を覆う。
- request CRCはrequest span先頭48 byte（nonceから32-byte payload末尾まで）を覆う。
- snapshot CRCはmailbox `0x00..0x3F`と`0x50..0x7F`をこの順で覆う。

## Commit順とtorn防止

ROMはresponse payloadを書き、snapshot CRC、snapshot sequence inverse、snapshot sequenceの順で公開する。
hostはrequestの`0x80..0xB7`、sequence inverse、sequenceの順で3回に分けて書く。
sequenceが最後のcommit wordである。

ROMはpollごとにsequence/inverseを読み、requestをlocal copyし、sequence/inverseを再読する。
前後が一致しないtorn writeは応答も状態変更も行わない。受理済みsequenceの再送はbyte-stableな
duplicateとして無視する。次のsequence以外、nonce、CRC、phase、command、flags、payload幅の違反は
gameplay stateを変更せずerror responseだけを公開する。

## PING / PONG

`PING`はcommand `1`、expected phase `IDLE(1)`、payload 8 byteである。

```text
u32 token          # non-zero
u32 token_inverse  # ~token
```

成功時はresponse status `PONG(2)`、error `NONE(0)`、response payload size 12とし、
token、inverse、magic `PONG` (`0x474E4F50`)を返す。ROMが受理したrequest sequenceだけが
`last_accepted_sequence`を進める。

## Error code

| code | 意味 |
|---:|---|
| 0 | NONE |
| 1 | FUTURE_SEQUENCE |
| 2 | STALE_SEQUENCE |
| 3 | WRONG_NONCE |
| 4 | OVERSIZE |
| 5 | PAYLOAD_CRC |
| 6 | REQUEST_CRC |
| 7 | WRONG_PHASE |
| 8 | UNKNOWN_COMMAND |
| 9 | PAYLOAD_FORMAT |
| 10 | FLAGS |

magic/version/size/Stage identityが壊れたmailboxはROMが同じmailbox範囲だけを再初期化する。
CLIは書込み前に全header、nonce inverse、snapshot sequence/inverse、snapshot CRC、ROM CRCを検証し、
一致しない場合は一切書かない。

## CLIとexit code

`vega-codex-battle`は既定でもversioned JSONを出す。`--json`は明示契約として受理する。

| exit | error code | 意味 |
|---:|---|---|
| 0 | `OK` | 成功 |
| 2 | `USAGE` | 引数不正 |
| 10 | `CONFIG` | local device configなし/不正 |
| 20 | `TRANSPORT` | UDP timeout/接続不能 |
| 21 | `NCI_RESPONSE` | NCI response不正 |
| 22 | `CORE_OR_ROM` | system/core memory/ROM identity不一致 |
| 23 | `PROTOCOL` | mailbox ABI/capability/CRC不一致 |
| 24 | `REQUEST` | stale/illegal requestまたはROM error response |
| 25 | `CONFIG_WRITE` | owner-only config保存失敗 |

device configはXDG config配下にdirectory `0700`、file `0600`で保存する。通常JSON、report、
tracked sourceへhostを出さない。`doctor`はtransport、GBA system、Stage 43 ROM CRC、mailbox protocol、
capability、EWRAM descriptor readを判定する。`bridge ping`だけが宣言request spanへ書く。
