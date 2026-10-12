#include "../../tools/mgba_pr16_circus_menu_identity.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    unsigned permutations[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
    uint32_t ids[3]={896754880U,2430179285U,3172108035U},ots[3]={7,7,7};
    uint16_t sp[3]={2,92,4};unsigned checks=0;
    for(unsigned p=0;p<6U;++p){uint32_t pid[3],ot[3];uint16_t species[3];
        for(unsigned i=0;i<3U;++i){pid[i]=ids[permutations[p][i]];ot[i]=ots[permutations[p][i]];species[i]=sp[permutations[p][i]];}
        for(unsigned i=0;i<3U;++i){assert(mi_find(3,pid,ot,species,pid[i],ot[i],species[i])==i);++checks;}
        assert(mi_find(3,pid,ot,species,pid[0],8,species[0])==3);++checks;
        assert(mi_find(3,pid,ot,species,pid[0],ot[0],99)==3);++checks;
        assert(mi_find(3,pid,ot,species,1,ot[0],species[0])==3);++checks;
    }
    for(unsigned n=0;n<7U;++n)if(n!=3U){assert(mi_find(n,ids,ots,sp,ids[0],7,2)==3);++checks;}
    assert(mi_find(3,ids,ots,sp,ids[0],7,0)==3);++checks;
    assert(mi_find(3,ids,ots,sp,ids[0],7,65536)==3);++checks;
    ids[1]=ids[0];sp[1]=sp[0];assert(mi_find(3,ids,ots,sp,ids[0],7,2)==3);++checks;
    printf("PASS_CIRCUS_MENU_IDENTITY checks=%u\n",checks);return 0;
}
