# T01 toolchainとWSL converter運用

このdirectoryは、固定済みDPE-JP/CFRU-JPを再現するためのhost toolchain契約を管理します。`toolchain_manifest.json`がversion、path、SHA-256、source commit、sandbox制約のmachine-readable正本です。setupが受理するschemaは整数の`schema_version: 1`だけで、別版やJSON booleanはinstall前に拒否します。

## 最短手順

既定動作は読み取り専用です。

```bash
bash infra/setup_toolchain.sh
```

不足packageをmanifest固定版で導入する場合だけ、明示的に次を実行します。

```bash
bash infra/setup_toolchain.sh --install
```

`--install`だけが`apt-get update/install`を行います。無引数または`--check`はAPT、vendor、ROM、sandboxを変更しません。導入後も同じhash/version/source検査を行います。setupは呼出元の`PATH`を使用せず、起動直後に`/usr/bin:/bin`へ読み取り専用で固定します。Python、APT、sudo、dpkg、Gitなどのsecurity-sensitive commandは絶対pathで実行し、Pythonはisolated modeでmanifestを読みます。

実際に使用するbuild sandboxも検査できます。directoryは先に作成してください。

```bash
mkdir -p /mnt/c/pv/t01
bash infra/setup_toolchain.sh --sandbox-root /mnt/c/pv/t01
```

## 固定環境

- Ubuntu 24.04 `noble` / WSL2 / x86_64
- Python 3.12.3を先に使用する。固定sourceのimport probeはPASS済みであり、Python 3.7は導入しない。実測した非互換が出た場合だけ隔離runtimeを追加する。
- Ubuntu package `gcc-arm-none-eabi 13.2.1`、binutils 2.42、newlib 4.4.0を使用する。GCC driverだけでなく実際にCのcode generationを行う`cc1`もpackage/version/path/SHA-256で固定する。
- DPE `-Os`、CFRU `-O2`を含む固定ARM7TDMI compile flagsは現toolchainで受理済み。
- headless smokeのemulatorは`/usr/games/mgba` 0.10.2を使用する。Factory/AI実挙動fixtureは同じ版の`libmgba-dev`と固定host GCC 13.3.0でrunnerを構築する。runnerの実compile closureは`cc -###`とELFの`NEEDED`/interpreterから採取し、`cc1`、`as`、`collect2`、`ld`、LTO plugin/helper、PIE CRT、GCC support archive/linker script、glibc linker inputs、`libc.so.6`、ELF loader、link-time/runtime mGBA DSOをpath/package/version/SHA-256で固定する。固定済み`ldd`で`as`の6-file closureと`ld`の8-file closureを毎回再取得し、`libbfd`、`libsframe`、zlib、zstd、`libctf`、Jansson、glibc/loaderを含むmanifest集合との完全一致を要求する。
- converterは上流に同梱されたWindows PEをhash固定して使用し、Wineを導入しない。

package archive hashと実行ファイルhashはmanifestへ分けて記録しています。APTの署名検証に加えて、検査時は導入versionと実行ファイルのSHA-256を照合します。Windows更新でsystem bridgeまたはVC90 SxS runtimeが変わった場合も黙って許容せず、manifest更新専用の差分監査を要求します。

host runner headerは、実際の2 source（`factory_fixture_runner.c`と`mgba_ai_fixture_runner.c`）へbuild時と同じC flagsで`cc -M`を実行して依存unionを作ります。installed headerは122件で、内訳は個別SHA-256固定済みmGBA 16件と標準header 106件です。標準headerは`libc6-dev:amd64` 95件、`libgcc-13-dev:amd64` 6件、`linux-libc-dev:amd64` 5件だけを許可し、各pathの`dpkg-query -S`所有者、package version、package別件数を検査します。全122件と標準106件の双方について、absolute path順に`path<TAB>file_sha256<LF>`を連結したSHA-256をmanifestへ固定するため、dependency、内容、所有packageのどれが変わってもcheckは失敗します。

## Converter inventory

| Tool | Version | Executable SHA-256 | Fixture canonical assembly SHA-256 |
|---|---:|---|---|
| `grit.exe` | 0.8.6 | `3ef8b91d92e0f6e2977b1462683e9ac6ecf04c915cec623919553db02e143b31` | `453ab74e64d63d05524fb6b3e1b5ed303b9f24e28d71c18175bc61ad8ccb84e6` |
| `wav2agb.exe` | 1.1 | `fb167b599af88fb6f87a358b89181082bf5f4e7cd2ea90dac1309c2ca937fb48` | `b2e09c26377c45f7eaa6b2fc3c72315570b8667439dc667713867faf46d0a298` |
| `mid2agb.exe` | 1.05 | `e3b9f30251a2381c973debc65463a783e82e58f95815b544e1210f3ae1077e4e` | `7c858de79a5488db75aa66225c53cb6cbfc4794332eeb1336b6094d2289338d1` |

DPE/CFRUに重複する`grit.exe`、`wav2agb.exe`、`FreeImage.dll`、MinGW DLLはbyte一致します。`mid2agb.exe`はCFRUだけにあります。converter単体だけをコピーせず、固定source sandboxの`deps/`全体をstageします。`grit.exe`はembedded `Microsoft.VC90.CRT` x86 manifestを持つため、Windows WinSxS runtimeも検査対象です。

fixtureは各2回を独立directoryで実行し、2回の一致だけでなく上表のknown-good canonical hashとの一致も要求します。canonical化はconverterが出力する`Time-stamp:`行と改行表現だけを除外し、assembly dataの差異は許容しません。fixture入力とflags自体のSHA-256もmanifestに固定し、`setup_toolchain.sh --check`で照合します。

## WSL-safe sandbox

WSLのLinux filesystemから`cmd.exe`を起動するとcwdは`\\wsl.localhost\...`というUNC pathになります。`cmd.exe`はUNC cwdを受け付けず`C:\Windows`へ退避するため、converter出力先が壊れます。次を必須とします。

- build rootは`C:\pv\t01`のような短いWindows drive pathとし、WSL側では対応する`/mnt/c/pv/t01`を使用する。
- pathはASCIIのみ、空白なし、Windows表現がUNCでないことを事前検査する。
- `vendor/upstream/**`ではbuildしない。固定commitを`git archive`からvariantごとの使い捨てsandboxへ展開する。
- private ROM原本を変更しない。read-only原本からvariant専用working copyを作る。
- DPEにはLinux分岐でbare `grit` / `wav2agb` / `mid2agb`を要求するため、build driverがWindows PE launcher wrapperをPATHへ用意する。
- CFRUのWSL分岐は`deps/*.exe`を直接参照するため、source tree自体をNTFS sandboxへstageする。
- converterはWindows cwdを明示して実行し、終了code、command、入力hash、出力hashを記録する。
- Windows sandboxのACL設定にはhash/version固定した`C:\WINDOWS\System32\icacls.exe`をWSLから直接起動し、PowerShellは再帰allowlist検証だけに使用する。
- 同一入力/source/config/tool fingerprintについて独立sandboxで2回buildし、生成物のSHA-256一致を要求する。

上流treeにはcase-insensitive衝突、Windows予約名、非ASCII pathは監査時点でありません。とはいえwrapper側の検査は省略せず、Windows表現のsandbox rootはbuild driverとmanifestで共通の180文字以下に保ちます。

## 検査範囲

`setup_toolchain.sh`は次を一括検査します。

1. Ubuntu codename、architecture、WSL interop、Windows drive mount。
2. APT packageの導入状態と固定version。
3. Python、ARM tools、host GCCのcompile/link/runtime DSO closure、2 runnerの`cc -M` header closure、Make、Git、mGBAのversionとSHA-256。
4. converter、fixture入力/flags/expected canonical hash、重複copy、必要DLL、Windows VC90 SxS runtimeのSHA-256。
5. `cmd.exe`、Windows PowerShell、`icacls.exe`、`wslpath`のversion/hash。
6. DPE-JP、CFRU-JP、pokefireredのcommit pinとclean worktree。
7. 指定時はsandboxのNTFS mount、ASCII、空白、UNC、path長、workspace隔離条件。

これはfixture変換やfull upstream buildそのものではありません。build driverは別途、既存のPNG/WAV/MIDI fixtureを通したconverter出力の再現性、ARM compile/link、mGBA smoke、variantごとの2回build一致まで検証します。
