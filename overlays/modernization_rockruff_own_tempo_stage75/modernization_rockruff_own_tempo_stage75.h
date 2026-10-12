#ifndef MODERNIZATION_ROCKRUFF_OWN_TEMPO_STAGE75_H
#define MODERNIZATION_ROCKRUFF_OWN_TEMPO_STAGE75_H

typedef unsigned char Stage75U8;
typedef signed char Stage75S8;
typedef unsigned short Stage75U16;
typedef signed short Stage75S16;
typedef unsigned int Stage75U32;

Stage75U16 Stage75_GetEggSpecies(Stage75U16 species);
Stage75U8 Stage75_GetEggMoves(void *mon, Stage75U16 *moves);
Stage75U8 Stage75_TryGenerateWildMonAdapter(const void *info, Stage75U8 area, Stage75U8 flags);
Stage75U8 Stage75_GetMoveRelearnerMoves(void *mon, Stage75U16 *moves);
Stage75U16 Stage75_BuildLearnableMoveset(void *mon, Stage75U16 *moves);
void Stage75_PrepareMachinePages(void);
void Stage75_SelectedMachinePageHasMoves(void);
void Stage75_OpenArchiveModeMenu(void);
void Stage75_OpenMachinePageMenu(void);
void Stage75_CommitMachinePage(void);
void Stage75_SetMachineMode(void);
void Stage75_SetTutorMode(void);
void Stage75_ResetMode(void);
Stage75U32 Stage75_RuntimeProbe(Stage75U32 query);

#endif
