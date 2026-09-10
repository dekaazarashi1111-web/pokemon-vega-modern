/* Exact V4 preservation: only Happiny needs the Stage73 collision adapter.
 * All other species/modes delegate to the unchanged Stage84 consumer chain.
 * This code never changes a party, box, save, gate, item, or existing move slot.
 */
#include "bindings.h"
typedef unsigned char U8;
typedef unsigned short U16;
typedef unsigned int U32;
typedef U32 (*GetData)(const void *, int, void *);
typedef U8 (*EggFn)(void *, U16 *, U8);
typedef U8 (*MemoryFn)(void *, U16 *);
#define DATA ((GetData)0x0803F355u)
#define MODE (*(volatile U8 *)0x0203EC00u)
#define SHARED_INDEX ((const U16 *)0x09534C9Eu)
#define SHARED_MOVES ((const U16 *)0x0953594Au)
static const U16 preservation[] = P07_HAPPINY_EGG;
static U8 known(void *mon, U16 move) {
    U8 i; for (i=0; i<4; ++i) if ((U16)DATA(mon,13+i,0)==move) return 1;
    return 0;
}
static U8 append(void *mon,U16 *moves,U8 count,U16 move,U8 ignore) {
    U8 i;
    if (!move || count>=40 || (ignore && known(mon,move))) return count;
    for (i=0; i<count; ++i) if (moves[i]==move) return count;
    moves[count]=move;return count+1;
}
U8 P07_GetAllEggMoves(void *mon,U16 *moves,U8 ignore) {
    U8 count=((EggFn)P07_PARENT_EGG)(mon,moves,ignore),i;
    if ((U16)DATA(mon,11,0)!=364) return count;
    for (i=0;i<sizeof(preservation)/sizeof(*preservation);++i)
        count=append(mon,moves,count,preservation[i],ignore);
    return count;
}
U8 P07_GetMoveRelearnerMoves(void *mon,U16 *moves) {
    U16 egg[50],cursor,end;U8 count=0,n,i;
    if ((U16)DATA(mon,11,0)!=364 || MODE!=1)
        return ((MemoryFn)P07_PARENT_MEMORY)(mon,moves);
    n=P07_GetAllEggMoves(mon,egg,1);
    for (i=0;i<n && i<50;++i) count=append(mon,moves,count,egg[i],1);
    cursor=SHARED_INDEX[364];end=SHARED_INDEX[365];
    for (;cursor<end;++cursor) count=append(mon,moves,count,SHARED_MOVES[cursor],1);
    return count;
}
