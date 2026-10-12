#define CIRCUS_SUSTAIN_HOST_TEST
#include "../../tools/mgba_pr16_circus_sustain.h"
#include <assert.h>
#include <stdio.h>
static struct su_view fresh(void){return (struct su_view){.player=1,.enemy=2,
    .hp=170,.maxhp=171,.enemy_hp=167,.enemy_maxhp=167,.type1=11,.type2=11,.spatk_stage=6,
    .moves={247,92,109,182},.pp={24,16,16,16},.best=0};}
int main(void)
{
    struct su_memory m={0};struct su_view v=fresh();
    assert(su_choose(&v,&m)==1); /* 最初はToxic */
    v.status1=0x80;assert(su_choose(&v,&m)==3); /* 状態を確認してProtect */
    assert(su_choose(&v,&m)==2);assert(su_choose(&v,&m)==3); /* Confuse/Protect */
    v.status2=3;assert(su_choose(&v,&m)==0);assert(su_choose(&v,&m)==3);
    v.enemy=3;v.status1=0;v.status2=0;v.type1=3;assert(su_choose(&v,&m)==2); /* 毒免疫 */
    v.enemy=4;v.type1=8;assert(su_choose(&v,&m)==2); /* 鋼免疫 */
    v.enemy=5;v.type1=11;v.status1=0x10;assert(su_choose(&v,&m)==2); /* 既状態 */
    v=fresh();v.pp[1]=v.pp[2]=v.pp[3]=0;m=(struct su_memory){0};assert(su_choose(&v,&m)==0);
    v=fresh();v.enemy_hp=10;m=(struct su_memory){0};assert(su_choose(&v,&m)==0);
    v=fresh();m=(struct su_memory){0};assert(su_choose(&v,&m)==1);assert(su_choose(&v,&m)==1);
    assert(su_choose(&v,&m)==2);assert(su_choose(&v,&m)==0); /* 免疫/外れでも無限Toxic禁止 */
    v=fresh();v.moves[1]=73;m=(struct su_memory){0};assert(su_choose(&v,&m)==1);
    assert(su_choose(&v,&m)==3);assert(su_choose(&v,&m)==2);
    v.enemy=10;v.type1=12;assert(su_choose(&v,&m)==2); /* 草へSeedを選ばない */
    v=fresh();v.moves[1]=347;v.moves[2]=0;m=(struct su_memory){0};assert(su_choose(&v,&m)==1);
    v.spatk_stage=7;assert(su_choose(&v,&m)==1);v.spatk_stage=8;assert(su_choose(&v,&m)==0);
    v=fresh();v.moves[1]=347;v.moves[2]=0;v.hp=1;m=(struct su_memory){0};assert(su_choose(&v,&m)==0);
    v=fresh();m=(struct su_memory){.player=1,.enemy=2,.seen=1,.toxic=2,.confuse=1};
    v.player=8;assert(su_choose(&v,&m)==1); /* 別の実個体へ交替 */
    assert(su_bulk_score(0,100,100,100,100,100,0)==0);
    assert(su_bulk_score(90,0,100,100,100,100,0)==su_bulk_score(90,100,100,100,100,100,0));
    assert(su_bulk_score(80,100,92,171,125,90,1)>su_bulk_score(90,100,152,106,50,55,0));
    assert(su_bulk_score(255,100,65535,65535,65535,65535,1)==(uint64_t)255*65535*65535*131070*2);
    puts("PASS_CIRCUS_SUSTAIN_POLICY checks=28");return 0;
}
