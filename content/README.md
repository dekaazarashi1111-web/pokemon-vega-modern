# Content workspace

Content uses symbolic keys and may be authored before engine IDs are final. Place region-specific design files under `content/kanto/` and keep machine-consumed canonical rows in `manifests/`.

Kanto content must distinguish `KANTO_EARLY_ACCESS`, certification phases, `VEGA_HALL_OF_FAME`, and `KANTO_LEAGUE_CLEAR`; a single postgame boolean is insufficient. Early Kanto keeps the declared Lv.68–100 fixed high-level curve, carries an explicit recommended-level warning, and never makes its first ship battle mandatory. Imported V2 rows remain review inputs and are normalized before promotion.
