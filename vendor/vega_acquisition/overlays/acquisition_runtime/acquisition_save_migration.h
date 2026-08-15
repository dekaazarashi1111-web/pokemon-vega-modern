#ifndef VEGA_ACQUISITION_SAVE_MIGRATION_H
#define VEGA_ACQUISITION_SAVE_MIGRATION_H

#include <stddef.h>
#include <stdint.h>

#include "../../generated/acquisition_save_layout.h"

typedef uint8_t (*VegaAcqMigrationSpeciesRegistered)(uint16_t species_id,
                                                      void *context);

uint32_t VegaAcqSaveCrc32(const void *data, size_t size);
uint8_t VegaAcqSaveValidate(const VegaAcqSaveBlock *block);
void VegaAcqSaveInitialize(VegaAcqSaveBlock *block);
uint8_t VegaAcqSaveMigrate(VegaAcqSaveBlock *block,
                           VegaAcqMigrationSpeciesRegistered is_registered,
                           void *context);
void VegaAcqSaveFinalize(VegaAcqSaveBlock *block);

#endif /* VEGA_ACQUISITION_SAVE_MIGRATION_H */
