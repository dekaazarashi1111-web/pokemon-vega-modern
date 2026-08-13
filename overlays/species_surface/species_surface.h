#ifndef VEGA_SPECIES_SURFACE_H
#define VEGA_SPECIES_SURFACE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define VEGA_BREED_STATS 6u
#define VEGA_EGG_MOVES 4u
#define VEGA_EGG_QUEUE_CAPACITY 5u
#define VEGA_PARTY_CAPACITY 6u

enum VegaHatchMode { VEGA_HATCH_NORMAL, VEGA_HATCH_SHORT, VEGA_HATCH_SKIP };
enum VegaEggDelivery { VEGA_EGG_TO_PARTY, VEGA_EGG_TO_PC, VEGA_EGG_RETAINED, VEGA_EGG_INVALID };

struct VegaBreedParent {
    uint16_t species;
    uint16_t form;
    uint16_t trainer_id;
    uint16_t held_effect;
    uint8_t nature;
    uint8_t ball;
    uint8_t ability_slot;
    uint8_t iv[VEGA_BREED_STATS];
    uint16_t egg_moves[VEGA_EGG_MOVES];
    uint16_t level_moves[VEGA_EGG_MOVES];
    bool is_ditto;
    bool hidden_ability;
};

struct VegaEgg {
    uint16_t species;
    uint16_t form;
    uint16_t moves[VEGA_EGG_MOVES];
    uint8_t nature;
    uint8_t ball;
    uint8_t ability_slot;
    uint8_t iv[VEGA_BREED_STATS];
    bool shiny;
};

struct VegaBreedRules {
    uint16_t incense_baby_species;
    uint8_t power_stat_a;
    uint8_t power_stat_b;
    bool everstone_a;
    bool everstone_b;
    bool destiny_knot;
    bool regional_form_from_a;
};

struct VegaEggQueue { struct VegaEgg eggs[VEGA_EGG_QUEUE_CAPACITY]; uint8_t count; };

uint32_t VegaBreedNext(uint32_t *state);
bool VegaBreed(const struct VegaBreedParent *a, const struct VegaBreedParent *b,
               const struct VegaBreedRules *rules, uint32_t *rng, struct VegaEgg *egg);
bool VegaEggQueuePush(struct VegaEggQueue *queue, const struct VegaEgg *egg);
enum VegaEggDelivery VegaEggQueueDeliver(struct VegaEggQueue *queue, uint8_t *party_count,
                                         uint16_t *pc_count, uint16_t pc_capacity);
bool VegaOvalCharmUnlocked(uint16_t distinct_official_caught, bool quest_complete);
uint8_t VegaEggSuccessPercent(uint8_t base_percent, bool oval_charm);
uint16_t VegaHatchAnimationFrames(enum VegaHatchMode mode);
bool VegaCompactIvEvPanel(bool pc_right_pane, bool egg, uint8_t stat_index,
                          uint8_t iv, uint16_t ev);

#endif
