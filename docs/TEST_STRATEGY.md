# テスト戦略

## 1. Static

毎コミットで実行します。

- private binary guard
- task DAG validation
- manifest header/uniqueness validation
- ID range overlap
- pointer範囲
- ROM allocation overlap
- table count一致
- symbol未解決

## 2. Build

- clean ROM hash
- stage input/output hash
- expected-byte assertion
- toolchain version
- source commit pin
- 32 MiB size
- GBA header checksum

## 3. Engine smoke

最低限の自動/半自動ケース:

1. title
2. new game
3. starter/初回party生成
4. wild battle
5. trainer battle
6. capture
7. level up
8. evolution
9. save
10. restart/load
11. party summary
12. Pokedex registration

初戦の行動順回帰では、アクタシ・ファマー・リープンの3分岐を実controllerで1ターン進める。
Item ID 0へ残留Quick Claw/Custap indicatorを命令境界で注入し、通知なしでPP/HPが更新される
ことを確認する。正規Quick Claw、Custap、Quick Drawは遅いbankを先頭へ移し、通知1回で
同じターンを完了することを別fixtureで検証する。

HM field能力回帰ではVega既存HM01〜08（Item 339〜346）を1個ずつ追加し、追加前は拒否値6、
追加直後とsnapshot復元後は許可値0になることをexact-ROMで確認する。各HMは手持ち0体、
技未習得、技習得済みを同じ結果にし、move書込みと新規story/save flagを0件にする。
Surfは非Surf中だけ許す入口とSurf中だけ許す入口を相互に反転して検査し、party callbackは
未所持を拒否し、所持時には元のmap/terrain callbackと同じ結果を返すことを確認する。

## 4. Vega regression

主要checkpoint saveを個人環境で作り、次を確認します。

- 序盤イベント
- ジム戦
- マップ接続
- 固定戦闘
- 殿堂入り
- 殿堂入り後シナリオ
- 図鑑関連
- カントー早期訪問を無視する経路と、訪問後にトーホクへ戻る経路の両方

セーブステートを互換性判定に使わず、ゲーム内セーブを使用します。

## 5. Kanto早期アクセスvertical slice

- 解禁直前の乗船不可
- シオウ3個目バッジ＋アーシアD・Hビル攻略直後・殿堂入り前の乗船可
- 全国図鑑なしでの乗船
- unlock flagの恒久latch。旧save対応時は既存殿堂入りsave移行、非対応時は安全な明示拒否
- 港NPC出現
- 地方間warp
- 推奨Lv.65以上の警告
- map name/music
- NPC会話
- 船上戦の拒否・敗北・辞退後も渡航可能
- 港からPC/帰還船まで強制戦闘・field move不要
- ジム仕掛け、trainer party、boss rewardは必要認定章fixtureで検証
- save/load in Kanto
- heal/whiteout/reset in Kanto
- return travel
- Kanto permit取得後もトーホク側の未解禁HMを使えない
- カントー訪問後のVega本編完走

## 6. 二地方生態・進行

- トーホク49論理地点で、未解禁・抽選外の元Vega encounterが変化しない。
- カントー47論理地点を全physical mapへcrosswalkし、全warp destinationを解決する。
- 541進化系統の両地方導線と全進化道具の入手可能性を検査する。
- 追加イベント34件の捕獲・撃破・逃走・敗北・満杯・再訪を検査する。
- 特殊個体125種は地方共有flagで重複捕獲できない。
- 港の往復を200回行い、save/load/heal/whiteout後も帰還できる。
- 往復200回はVega殿堂入り前と殿堂入り後の両方で行う。
- クチバ到着時の初期回廊と認定章gateにunreachable/circular prerequisiteがない。
- 全reachable Kanto stateから無条件帰還辺があることを逆到達性検査する。
- 早期は要求認定章数0〜4、Vega殿堂入り後は後半認定章・リーグ・共鳴だけが追加解禁される。
- Kanto scriptがVega badge/story/HM flagへ書き込まず、境界ノード以外がVega進行flagを参照しない。

## 7. 育成・操作QOL

- `tests/fixtures/qol_movement_courses.json` の100 tile直線、曲がり角、接触script、warp/段差courseで、ダッシュの所要frameがVega基準から25%以上、自転車は50%以上短縮されることを計測する。
- 全接触script、座標event、warp、段差、遭遇、歩数、毒、孵化判定を高速移動で各1回だけ処理する。
- 通常会話、看板、取得通知、店、PC、menu、battle messageを即時表示し、変数、色、改ページ、選択肢、明示wait、効果音、script同期順を保持する。
- 新規saveとQOL fieldを持たない移行saveの既定値、設定変更後のsave/load/resetを検査する。
- 固定RNG fixtureで、かわらずの石、あかいいと、power系、タマゴ技、共通level技、ball、通常/隠れ特性、おこう、メタモン、異親ID、リージョンフォームを網羅する。
- 経験アメ5種の100/800/3000/10000/30000、`x1/x5/x10/すべて`、途中level技・進化、Lv.100、EV非加算、選択個体限定を検査する。
- 共通複数使用UIを栄養drink、ハネ、ふしぎなアメ、テラピース、coin、単能力/全能力EV resetでも実行し、各上限、対象選択、cancel、効果なし時の非消費を検査する。
- IV判定境界0/1/15/16/25/26/29/30/31、EV各値/252/合計510、実IV31と「きたえた！」を手持ち/PC/タマゴで比較する。
- mint、特性カプセル/パッチ、銀/金王冠、努力値reset、全体学習装置ON/OFFをparty↔PC、進化、孵化、save/loadで検査する。
- 手持ち/box満杯、タマゴ5個queue、まとめ受取、孵化NORMAL/FAST/SKIPで個体、図鑑、nicknameの同一性を検査する。まるいおまもりは公式100種/quest境界と生成成功率2倍を固定RNGで比較する。
- PC検索、複数移動、一括逃がし、`field_pc_allowed`、relearn pool内技変更、技/持ち物操作、登録済み預かり親から256歩ごとに共有5個queueへ生成するタマゴバスケット、通常random野生限定の自動戦闘を、禁止個体/道具/map/戦闘、色違い、cancel、容量不足、save/load込みで検査する。
- 各badge、D・Hビル、Vega殿堂入り、Kanto Leagueの直前/直後でfirst-availabilityと反復供給を照合する。
- stage 23で麻痺速度1/2・行動不能1/4、眠り減少、凍り解凍1/5、毒1/8、固定CFRU猛毒counter、やけど1/16、急所stage分母と1.5倍、天候5/8 turn・雨晴れ補正・終了を固定RNGで検査する。
- end-turn状態damageはHPを直接更新せず1回分のbattle scriptだけを予約し、5 stock rootが単一CFRU command tableを指すことを検査する。wild/trainer/doubleは専用fixture、Factory/Raidは現行stageのpolicy scheduler回帰を使う。

## 8. Trainer AI・難易度

- 固定CFRU-JP AIの `AI_BASIC` / `AI_SEMI_SMART` / `AI_FULL_SMART` を固定global RNGで実行し、move、switch、hazard、setup、recovery、weather/field、item、gimmickを期待actionと比較する。
- Doubleはtarget、範囲技の味方巻込み、Protect/Wide Guard、Tailwind/Trick Room、Follow Me/Helping Handを検査する。
- 固定CFRUの既定knowledge model、分散cache/historyの無効化とT01で固定したworst-case性能閾値を検査する。
- 全体学習装置既定ONの連続saveで8 gym、初回league、Ginnoまで完走し、ace level、map/batch単位の一般trainer/野生調整、固有戦術、合法構成、一律level scaleなしを確認する。
- 3段階再戦/league、Sphere遺跡、NORMAL/RESEARCH/Safari、Mirageのitem/reward/state分離を各解禁境界で検査する。
- 高難度RaidはHOF＋認定章4の境界、partner/shield/end/capture/reward、reset/save-load、通常battleへのflag/state漏出を検査する。既存UI以外をrelease要件にしない。

## 9. Release

- clean inputから一発再生成
- 差分パッチをcleanへ適用してfinal hash一致
- ROMや元パッチがrelease archiveへ混入していない
- credits/changelog/readmeを含む
