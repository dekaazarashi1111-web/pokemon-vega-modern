#!/usr/bin/env python3
"""公開するROM根拠はaddress/size/hashに限定する。ROM断片は送信しない。"""
import hashlib

def public_metadata(value):
    if isinstance(value,list):return [public_metadata(x)for x in value]
    if not isinstance(value,dict):return value
    out={}
    for key,item in value.items():
        if key=='address_hex':continue
        if key=='hex' or key.endswith('_hex'):
            raw=bytes.fromhex(item);prefix=''if key=='hex'else key[:-4]+'_'
            out[prefix+'size']=len(raw);out[prefix+'sha256']=hashlib.sha256(raw).hexdigest()
        else:out[key]=public_metadata(item)
    return out

def no_raw_rom_hex(value):
    if isinstance(value,list):return all(no_raw_rom_hex(x)for x in value)
    if not isinstance(value,dict):return True
    return all(k!='hex' and not k.endswith('_hex') and no_raw_rom_hex(v)for k,v in value.items())
