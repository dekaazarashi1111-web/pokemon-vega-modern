#include <stdint.h>
#define PR16_CODE_START 0x95f97e4u
#define PR16_CODE_END 0x95f9a88u
#define PR16_INITIAL_DIRECT 0x91145f1u
#define PR16_NATURAL_DIRECT 0x9377729u
struct ProgressSample { uint16_t species; uint8_t level,policy,count,next_count; uint16_t moves[4],next[40]; };
static const struct ProgressSample progress_samples[]={
{1,50,1,4,0,{235,202,97,372},{0}},
{10,13,1,4,1,{64,116,98,17},{17}},
{649,9,1,3,1,{33,81,535},{535}},
{1029,50,1,4,1,{204,235,382,738},{738}},
{1670,48,1,4,1,{242,184,550,407},{407}},
{887,10,4,0,0,{0},{0}},
{1621,10,7,0,0,{0},{0}},
{1029,1,1,3,3,{22,33,543},{22,33,543}},
{649,1,1,2,2,{33,81},{33,81}},
};
