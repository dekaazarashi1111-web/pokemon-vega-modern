# HOF容量: 根付きsong consumer分類

対象は現候補`0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583`の旧egg owner全874見かけ参照。numeric checkpointの455分類/419未知を継承し、旧全ROM走査を繰り返さず、新song由来の型付きsample領域だけを追加する。正式ROM/Save101、既存115owner、donor使用権限は変更しない。

## ソースと実engineの結合

- `pr16_dex_hof_song_sources.json`は固定CFRU-JP/pretの19原本（15text、MIDI2、WAV2）のsize/SHA-256/Git blob/commitを固定する。バイナリ原本はprivate作業dirだけへ取得する。
- `pr16_dex_hof_song_engine_review.json`は旧formalで独立比較したJP engineのsemantic証拠である。ROMのraw bytesやdisassembly本文を含めず、各windowのaddress/size/SHAと公開source対応、根付きliteral、effective dispatch、player容量を記録する。旧formalは現候補の代用にしない。Actionsで現候補全SHAと全windowを再照合して初めて分類に使う。
- boot entry→main初期化call→m4aSoundInit→SoundInit/MPlayExtender/MPlayOpenを結び、MPlayMain/ply_note、template上書き後の36slot、control/scalar handler、SoundMain RAM copy/PCM/DPCMを照合する。JP SoundModeのchannel数はpretのC defaultと異なるため、公開sourceをROM全体同一と扱わない。
- Song.msから4playerの実rowを選び、初期化済容量10/3/9/1とheader.trackCountの小さい方だけを読む。header/track配列、各command窓、実VOICE row、未shift keyで選ばれた1段SPL/RHYのchild/key-map、選択WaveDataを保存する。

## source ID集合と足音の反証

固定CFRU songs.hの無条件numeric定義からFEFE、条件付きUNBOUND、式/別名を除いた114個の明示IDを使う。これは全song tableの範囲証明でも、全IDが実ゲームから呼ばれた証明でもない。記号名が現曲名と一致するとは仮定しない。

songs250/251は固定CFRU MIDIでprogram14/13・key60、flagsのgroup084539B4、repointsのWave field08453A60/08453A54に対応する。一方、旧formalの実trackは両方program24であり、元MIDIと一致しない。現在候補でもこの比較を行い、差分はsource_midi_equivalence=falseとして保持する。一致していない曲を「現足音が原本どおり」と認定しない。source WAV全sampleのXOR128変換も独立確認し、一致したconsumerにだけsource-exactを付ける。

## fail-closed状態機械

- running status、VOICE rawu8（127へmaskしない）、保持key/velocity、repeat counter、pattern stack3、KEYSHを保持する。初期toneはtype1であり暗黙VOICE0はない。
- GOTOにはfallthroughなし。PATT4段目はFINE。REPT0/1/2/255、PEND深さ0、NOTE0〜3 optional operands、EOTの保持key更新を個別検証する。PC単独で閉路と判定しない。
- MEMACC/XCMD/PORT、共有TEMPO0、非yield閉路、budget超過、command解釈衝突はwhole-song拒否。未対応prefixを勝手に分類へ昇格しない。外部変更なしの型付きcommandモデルであり、実演奏・channel確保・優先度による開始受理の証明ではない。
- CGB1〜4をWaveDataにしない。5〜7とnested childを拒否。1段SPL/RHYはunshifted keyでlookupし、SPL優先、KEYSHによる再indexや再帰降下をしない。
- 全song横断でSong/Header/Player/VOICE/親child tone/key-map/Wave header/engine/commandの読取範囲を集約する。失敗trackの既読構造、VOICEのみでNOTEがない構造も保持し、payloadと競合するsample witnessは除外する。

## sampleと容量の境界

WaveData16byte headerと全sampleをbounded decodeする。DPCMはToneData CMP/REV経路とWaveData.typeを照合し、flagなしのtype1をDPCMとして分類しない。型付けされた最小encoded prefix内に4byte全体が収まる既存hitだけを除外する。header、padding、跨ぎ、未知域は除外しない。

最小encoded prefixは実engine read footprintと同義ではない。DPCM decoderは64sample/33byte block全体を読むうえ補間look-aheadもある。今回この完全footprintや間接参照不存在は主張せず、donor_eligible/donor_leasedは常にfalse。残件0でも別の退役/間接consumer完全性ゲートを閉じるまで容量を使わない。

## 実行と公開

`pr16-dex-hof-song.yml`は新source testと現candidateの新song readだけを行う。必要な現candidate再構成は既存固定ルートを1度使用し、旧全ROM inventory/heap/native/gameplayを再走しない。全候補SHAと最新owner afterSHAを照合する。新分類数を原本JSONに固定し、全旧accepted hitを逐byte維持する。

公開はsourceと最小address-size-SHA/text証跡のみ。ROM/rawhex/ROM断片、MIDI/WAV本体、入力save、runtime、runner、credentialは新規公開しない。producer/guard/upload/artifact名を機械照合し、guard成功専用dirだけをuploadする。hidden/symlink/未知拡張子/空reportは拒否する。終端記録ではActions全step成功と全snapshot bytes/末尾LF/Git blobを照合し、新nativeは0として記録する。
