#include "dex_compact_map.h"
struct VegaDexRun { uint16_t end, value; };
_Static_assert(sizeof(struct VegaDexRun)==4u,"compact descriptor is two u16");
#include "dex_compact_tables.h"

/* immutable生成表だけを受け取る。generatorは全run境界とliteral範囲を検証する。 */
static uint16_t lookup(uint16_t key,const struct VegaDexRun *runs,
                       unsigned count,const uint16_t *literals)
{
    unsigned lo=0u,hi=count;
    uint16_t tag,value;
    if(key>runs[count-1u].end)return 0u;
    while(lo<hi){unsigned mid=(lo+hi)>>1;if(runs[mid].end<key)lo=mid+1u;else hi=mid;}
    tag=runs[lo].value;value=(uint16_t)(tag&0x3FFFu);
    if(!(tag&0x8000u))value-=(uint16_t)(runs[lo].end-key);
    return (tag&0x4000u)?literals[value]:value;
}
#define COUNT(a) ((unsigned)(sizeof(a)/sizeof((a)[0])))
uint16_t VegaDexCompactSpeciesOwner(uint16_t sid)
{return lookup(sid,sCompactSpecies,COUNT(sCompactSpecies),sCompactSpeciesLiterals);}
uint16_t VegaDexCompactOfficialOwner(uint16_t national)
{return lookup(national,sCompactOfficial,COUNT(sCompactOfficial),sCompactOfficialLiterals);}
uint16_t VegaDexCompactOwnerRepresentative(uint16_t owner)
{return lookup(owner,sCompactRepresentative,COUNT(sCompactRepresentative),NULL);}
