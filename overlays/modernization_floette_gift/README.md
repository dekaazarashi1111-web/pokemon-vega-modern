# フラエッテ（えいえんのはな）一回限りgift

Stage 68を親に、クチバFactory（map 96/5）の専用NPCから
`SPECIES_KEY_FLOETTE_ETERNAL`（canonical Species 1029）をLv.50で受け取る。

- `ITEM_KEY_MEGA_RING`（Item 580）所持時だけ解禁する。
- 一回限りのフォーム固有正本はexpanded flag `0x14CD`。
- 空きがあれば手持ち、満員ならPCへ送り、双方満員なら未取得のままにする。
- 配送後にflagを設定して通常セーブし、失敗時はflag・配送先・拡張台帳を補償rollbackする。
- 全国図鑑No.670は、52-byteの旧通常図鑑領域へ範囲外書込みせず、既存の拡張collection台帳bit 850（通常フラエッテのcanonical登録）をseen/caught共通正本として扱う。フォーム固有取得はbitを共有せず`0x14CD`で区別する。
- 旧`UNOBTAINABLE_EVENT_FORM_EXCLUDED`成果物は履歴として保持し、このStage 69契約だけで取得可能へoverrideする。

NPCはStage 68のlocal ID 14 / (24,19)を保持したうえで、local ID 15 /
(25,19)へ追加する。
