# T26 — Codex対戦ブリッジをStage 43で実証する

- Lane: `platform/tooling/engine/qa`
- Depends on: `T25`

## 目的

T25完了済みStage 42へ、gameplayを変えないversioned Codex Battle mailboxを追加する。
iPad RetroArch/mGBAのNetwork Control Interfaceから実ROM EWRAMをread/writeし、PCの
`vega-codex-battle` CLIがwrong ROMやstale commandを拒否しながらPING/PONGできるStage 43を作る。

T26は対戦本体を実装しない。transport、memory ABI、CLI、実iPad証跡を先に固定し、
T27/T28が通信不具合を戦闘・save不具合と混同しない状態を作る。

## 固定入力

- ROM-producing commit: `279890f7bcf087649517d331a841b62b801f9c24`
- ROM: `build/stages/42_factory_high_modes_v2.gba`
- ROM SHA-256: `2e3c796b1deff84c83b68fde29c2eddf8672b1870f1ebe3e8308969fafde1068`
- ROM size: 33,554,432 bytes
- metadata: `build/stages/42_factory_high_modes_v2.json`
- metadata SHA-256: `8692768f22f1ef9c5f0562712c110d063fb743f46ef7e2ebafbc021d084bf5a0`
- 設計正本: `design/codex_battle_architecture.md`
- iPad診断command: `ipad-wifi-ssh`。credential、固定接続先、app container pathはGitへ記録しない。

## 開始時の実機事実

- RetroArch configにNetwork Commandsの設定と既定UDP portがあり、現在はOFF。
- mGBA frameworkとinfo/config/save/state領域が存在する。
- RetroArch binaryにcore-memory read/write command文字列が存在する。
- OFF状態の`VERSION` probeは無応答。RetroArch/mGBA versionと実memory mapは未固定。

## 固定仕様

- transportはRetroArch NCIの`VERSION`、`GET_STATUS`、`READ_CORE_MEMORY`、`WRITE_CORE_MEMORY`を使う。
- SSHは診断、設定、versioned test ROM転送だけに使い、turn command transportにしない。
- T26 commandはread-only statusとmailbox `PING`だけ。任意address書込commandをproduction CLIへ公開しない。
- mailboxはmagic/version/size/capability/Stage identity/session nonce/sequence/inverse/CRCを持つ。
- hostはmailboxの宣言済みrequest spanだけを書ける。ROMはpayload commit順と全validatorを通してから受理する。
- wrong ROM/core/protocol/nonce/CRC、stale/future sequence、範囲外payloadはEWRAM/save/game state無変更で拒否する。
- 接続先IP/portはGit管理外local configまたはCLI引数。IPやcredentialをreportへ書かない。
- CLI既定出力は小さなversioned JSON、安定exit/error codeを持ち、source directory外から実行可能にする。
- RetroArch NCIはplain UDPとしてtrusted LAN限定を明記する。
- NCI enable操作はUIを優先する。直接configを変える場合はRetroArch停止、hash、backup、変更後照合を必須にする。
- iPadの既存ROM/saveを上書きせず、Stage 43をversioned filenameで新規配置する。

## 実行

1. Stage 42、metadata、worktree、iPad SSH doctorのidentityを確認する。
2. RetroArch/mGBA version、Network Commands設定、mGBA memory descriptor、実行中processを安全にinventoryする。
3. RetroArch停止またはUI操作を確認してNetwork Commandsを有効化し、`VERSION` / `GET_STATUS`をPASSする。
4. Stage 42のRAM owner、EWRAM末尾、battle/UI/save scratchを再監査し、mailbox範囲を中央layoutへ追加する。
5. mailbox ABI、generator、ROM initializer/poller、PING validatorを実装し、expected-byte付きStage 43を生成する。
6. UDP client、owner-only local config、JSON schema、`doctor` / `device configure` / `device status` / `bridge ping`をCLIへ実装する。
7. host simulatorとlibmGBAでtorn read/write、CRC、nonce、sequence、timeout、wrong phaseを全検査する。
8. Stage 43をiPadへ新規配置してmGBAで起動し、NCIからmailbox readとPING/PONG writeを実証する。
9. Stage 42→43 BPS、clean→Stage 43 BPS、clean rebuildと既存回帰を検証する。

## 必須成果物

- `docs/CODEX_BATTLE_PROTOCOL.md`
- `config/codex_battle_bridge.json`
- `overlays/codex_battle_bridge/**`
- `scripts/build_codex_battle_bridge.py`
- `scripts/rebuild_codex_battle_bridge_from_clean.py`
- `scripts/install_vega_codex_battle_cli.sh`
- `tools/vega_codex_battle.py`
- `tools/mgba_codex_battle_bridge_smoke.c`
- `tests/test_codex_battle_bridge.py`
- `reports/generated/codex_battle_bridge_{audit,coverage,ipad}.json`
- `build/stages/43_codex_battle_bridge.gba`（Git管理外）
- Stage 42→43 BPS、clean→Stage 43 BPS、mGBA、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] Stage 42 ROM/metadata identityが固定値に一致し、原本ROM/saveを変更・追跡しない。
- [ ] iPad RetroArch/mGBA version、NCI enable状態、port、core memory mapを機械可読証跡へ固定する。
- [ ] `VERSION`、`GET_STATUS`、EWRAMの`READ_CORE_MEMORY`、宣言mailboxへの`WRITE_CORE_MEMORY`が実iPadでPASSする。
- [ ] `doctor --json`がtransport/core/ROM/protocol/capabilityを判定し、秘密情報や端末固有pathを出さない。
- [ ] `device configure`がhost/portをowner-only local configへ保存し、repo、report、CLI既定出力へhostを漏らさない。
- [ ] `device status --json`と`bridge ping --json`が別directoryから安定JSON/exit codeで成功する。
- [ ] magic/version/size/Stage/session nonce/CRC/sequence/inverseの全validatorをROMとCLIの双方が持つ。
- [ ] torn、duplicate、stale、future、wrong nonce、wrong CRC、wrong phase、oversize requestが全て無変更で拒否される。
- [ ] mailbox初期化とPINGでparty、battle、save、RNG、Factory、Mirage、Reward stateが変化しない。
- [ ] RAM/ROM/save/hook overlap、declared span外変更が0で、Stage 43 clean rebuild/BPS/mGBAがPASSする。
- [ ] iPadの既存ROM/saveを上書きせず、実機証跡からIP、credential、container UUIDを除外する。

## 禁止する完了判定

- SSH接続、binary string、config keyの存在だけでNCI利用可能と判定しない。
- host simulator、PC mGBA、fake UDPだけでDONEにしない。iPad実機read/writeが必須。
- save file polling、savestate編集、任意memory write、StrictHostKeyChecking無効化へfallbackしない。
- NCIが使えない場合にRetroArchを無断で置換しない。証跡を残してBLOCKEDにする。

## 完了

1. task固有build/check、focused test、mGBA、iPad NCI、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ、秘密情報を除いた証跡を追記する。
3. `python3 scripts/taskctl.py done T26 --summary "iPad NCIとCodex Battle mailboxをStage43で実証"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T26:`で始まるcommitを作る。pushしない。
