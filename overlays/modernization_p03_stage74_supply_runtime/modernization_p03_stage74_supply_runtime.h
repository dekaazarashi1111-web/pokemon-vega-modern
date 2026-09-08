#ifndef MODERNIZATION_P03_STAGE74_SUPPLY_RUNTIME_H
#define MODERNIZATION_P03_STAGE74_SUPPLY_RUNTIME_H

typedef unsigned char Stage74U8;
typedef signed char Stage74S8;
typedef unsigned short Stage74U16;
typedef signed short Stage74S16;
typedef unsigned int Stage74U32;

enum Stage74ArchiveMode {
    STAGE74_MODE_NORMAL = 0,
    STAGE74_MODE_EGG = 1,
    STAGE74_MODE_MACHINE_PROBE = 2,
    STAGE74_MODE_MACHINE_PAGE_0 = 3,
    STAGE74_MODE_MACHINE_PAGE_1 = 4,
    STAGE74_MODE_MACHINE_PAGE_2 = 5,
    STAGE74_MODE_MACHINE_PAGE_3 = 6,
    STAGE74_MODE_TUTOR = 7
};

Stage74U8 Stage74_GetMoveRelearnerMoves(void *mon, Stage74U16 *moves);
Stage74U16 Stage74_BuildLearnableMoveset(void *mon, Stage74U16 *moves);
void Stage74_OpenArchiveModeMenu(void);
void Stage74_SetMachineMode(void);
void Stage74_SetTutorMode(void);
void Stage74_ResetMode(void);
void Stage74_PrepareMachinePages(void);
void Stage74_OpenMachinePageMenu(void);
void Stage74_CommitMachinePage(void);
void Stage74_SelectedMachinePageHasMoves(void);

/* Lightweight exact-ROM / host-oracle entry points. */
Stage74U32 Stage74_RuntimeProbe(Stage74U32 query);
Stage74U16 Stage74_PageCountForRowCount(Stage74U16 row_count);
Stage74U16 Stage74_PageStart(Stage74U8 page);
Stage74U16 Stage74_PageEnd(Stage74U16 row_count, Stage74U8 page);

#endif
