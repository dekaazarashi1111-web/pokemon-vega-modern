#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "save_migration.h"
#include "circus_drought_selection.h"
static VegaModernSaveData saved,flash,before;
static uint8_t original_party[6][100],rental_party[6][100],weather[0x800];
static unsigned calls;
static int persist(const VegaModernSaveData *bytes,size_t size,void *context){assert(size==sizeof(flash));memcpy(context,bytes,size);return 1;}
static void native_original(void){assert(!"eligible selection delegated to old empty loader");}
static void native_init(void){++calls;weather[0x6D2]=0;}
static void native_step(void){++calls;weather[0x6D2]=1;}
int main(void){
    for(unsigned n=1;n<=6;++n){
        for(unsigned i=0;i<600;++i)((uint8_t*)original_party)[i]=(uint8_t)(i*17+n);
        memset(rental_party,0x5A,sizeof(rental_party));VegaSaveInitNew(&saved,1);
        assert(VegaFactoryEnter(&saved,original_party,n,persist,&flash)==VEGA_SAVE_OK);
        assert(VegaFactorySetBattleActive(&saved,persist,&flash)==VEGA_SAVE_OK);
        assert(saved.factory.party_count==n && saved.factory.snapshot_valid==1 && saved.factory.marker==2);
        CircusDroughtContext c={1,1,1,saved.factory.marker,saved.factory.snapshot_valid,saved.factory.party_count,0,12,12,1,1,0x08055E75u,0x09FF4DADu};
        memcpy(&before,&saved,sizeof(before));calls=0;weather[0x6D2]=1;
        CircusDroughtInitializeSelection(&c,3,weather,native_original,native_init,native_step);
        assert(calls==2 && !memcmp(&before,&saved,sizeof(saved)));
        uint8_t count=0;
        assert(VegaFactoryRestore(&saved,rental_party,&count,persist,&flash)==VEGA_SAVE_OK);
        assert(count==n && !memcmp(original_party,rental_party,600));
        assert(VegaSaveValidate(&saved,sizeof(saved))==VEGA_SAVE_OK);
    }
    puts("saved original counts 1..6 / selected3 / unchanged ledger / restored600 PASS");
}
