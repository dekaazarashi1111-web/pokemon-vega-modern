# P04 Species Runtime / Stage70

Stage69 ROMを親に、P04で予約済みのMega 49形態（Species ID 1621..1669）を
固定表・画像・名称・基礎データへmaterializeするbuild-time overlayです。

- `evolution` の新49行は全zero。Mega順方向・逆方向の意味付けはStage71だけが所有します。
- Ability ID 312..317の名称・説明はUI/OOB安全用の差替え可能な仮日本語です。
- Ability効果hook、rating、Mold Breaker判定の最終値はStage72で再審査します。
- Browt / Pombon / GecquaとSide Changeは対象外です。
- runtime C hookはこのoverlayに含めず、ROM table relocationは
  `tools/modernization_p04_species_runtime.py` が再現可能に生成します。
