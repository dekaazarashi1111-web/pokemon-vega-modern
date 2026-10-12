#ifndef MODERNIZATION_P03_STAGE73_CONSUMER_RUNTIME_H
#define MODERNIZATION_P03_STAGE73_CONSUMER_RUNTIME_H

typedef unsigned char Stage73U8;
typedef unsigned short Stage73U16;
typedef unsigned int Stage73U32;

Stage73U8 Stage73_GetAllEggMoves(
    void *mon,
    Stage73U16 *moves,
    Stage73U8 ignore_already_known
);
Stage73U8 Stage73_GetMoveRelearnerMoves(void *mon, Stage73U16 *moves);
Stage73U16 Stage73_CollectionApplySelectedForm(void);

/* Lightweight exact-ROM / host-oracle entry points. */
Stage73U32 Stage73_RuntimeProbe(Stage73U32 query);
Stage73U16 Stage73_RotomSignatureMove(Stage73U16 species);
Stage73U8 Stage73_IsExactEggConflictSpecies(Stage73U16 species);

#endif
