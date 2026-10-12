#include "pr16_learnset_supply.h"
static uint16_t u16(const uint8_t *p) { return (uint16_t)(p[0] | (uint16_t)p[1]<<8); }
static uint32_t u32(const uint8_t *p) { return (uint32_t)u16(p) | (uint32_t)u16(p+2)<<16; }
uint8_t Pr16SupplyDecode(const uint8_t *p, uint32_t size, uint16_t owner,
    uint8_t family, uint16_t *out, uint16_t capacity, uint16_t *count)
{
    uint8_t mask[32] = {0}, ti, n, ns, depth = 0, nt;
    uint16_t at, base, template_at, template_count, result[160], used = 0, i, j;
    uint32_t records, pos, selectors;
    if (!p || !out || !count || size < 6720u || size >= 65535u || owner >= 1671u || family > 1u)
        return 0;
    if (p[0]!='P' || p[1]!='L' || p[2]!='A' || p[3]!='1' || u16(p+4)!=1u ||
        u16(p+6)!=32u || u16(p+8)!=1671u || p[11]!=8u || u32(p+12)!=32u ||
        u32(p+16)!=6716u || u32(p+24)!=size || !u32(p+28) || u32(p+28)>3342u)
        return 0;
    nt = p[10]; records = u32(p+20);
    if (!nt || nt>16u || records<6716u+(uint32_t)nt*4u || records>size) return 0;
    at = u16(p+32u+(uint32_t)owner*4u+(uint32_t)family*2u);
    if (at<records || (uint32_t)at+3u>size) return 0;
    ti = p[at+2u];
    if (ti>=nt) return 0;
    template_at = u16(p+6716u+(uint32_t)ti*4u);
    template_count = u16(p+6718u+(uint32_t)ti*4u);
    if (!template_count || template_count>256u || template_at<6716u+(uint32_t)nt*4u ||
        (uint32_t)template_at+(uint32_t)template_count*2u>records) return 0;
    n = (uint8_t)((template_count+7u)/8u); ns = (uint8_t)((n+7u)/8u);
    for (;;) {
        if (at<records || (uint32_t)at+3u>size || p[at+2u]!=ti) return 0;
        base = u16(p+at); pos = (uint32_t)at+3u;
        if (base==0xffffu) {
            if (pos+n>size) return 0;
            for (i=0;i<n;++i) mask[i]^=p[pos+i];
            break;
        }
        if (++depth>8u || base>=at || base<records || pos+ns>size) return 0;
        selectors=0;
        for (i=0;i<ns;++i) selectors|=(uint32_t)p[pos+i]<<(8u*i);
        pos+=ns;
        if (n<32u && (selectors>>n)) return 0;
        for (i=0;i<n;++i) if ((selectors>>i)&1u) {
            if (pos>=size || p[pos]==0u) return 0;
            mask[i]^=p[pos++];
        }
        at=base;
    }
    if (template_count%8u && (mask[n-1u]>>(template_count%8u))) return 0;
    for (i=0;i<template_count;++i) {
        uint16_t move=u16(p+template_at+(uint32_t)i*2u);
        if (!move || move>1062u) return 0;
        if ((mask[i/8u]>>(i%8u))&1u) {
            if (used>=160u || (family==1u && used>=40u)) return 0;
            for (j=0;j<used;++j) if (result[j]==move) return 0;
            result[used++]=move;
        }
    }
    if (used>capacity) return 0;
    for (i=0;i<used;++i) out[i]=result[i];
    *count=used;
    return 1;
}
uint8_t Pr16SupplyTutorBit(const struct Pr16RuntimeView *view, uint16_t owner, uint8_t slot)
{
    uint8_t i;
    if (!view || !view->bytes || view->owner!=owner || owner>=1671u || view->count!=64u || slot>=64u) return 0;
    for (i=8u;i<16u;++i) if (view->bytes[i]) return 0;
    return (uint8_t)((view->bytes[slot/8u]>>(slot%8u))&1u);
}
uint8_t Pr16SupplyPageCount(uint16_t count)
{
    return count && count<=160u ? (uint8_t)((count+39u)/40u) : 0u;
}
uint8_t Pr16SupplyPage(const uint16_t *archive, uint16_t count,
    const uint16_t known[4], uint8_t mode, uint8_t hall_of_fame,
    uint16_t *out, uint8_t capacity)
{
    uint16_t begin=0, end=count, i, j, selected[40];
    uint8_t used=0, is_known;
    if (!archive || !known || !out || !hall_of_fame || count>160u || mode<2u || mode>7u) return 0;
    if (mode==7u && count>40u) return 0;
    for (i=0;i<count;++i) {
        if (!archive[i] || archive[i]>1062u) return 0;
        for (j=0;j<i;++j) if (archive[j]==archive[i]) return 0;
    }
    if (mode>=3u && mode<=6u) {
        begin=(uint16_t)(mode-3u)*40u;
        end=begin+40u;
        if (end>count) end=count;
    }
    for (i=begin;i<end;++i) {
        is_known=0;
        for (j=0;j<4u;++j) if (known[j]==archive[i]) is_known=1;
        if (is_known) continue;
        if (used>=40u) return 0;
        selected[used++]=archive[i];
        if (mode==2u) break;
    }
    if (used>capacity) return 0;
    for (i=0;i<used;++i) out[i]=selected[i];
    return used;
}
