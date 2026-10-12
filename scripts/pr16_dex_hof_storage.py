#!/usr/bin/env python3
"""実32sector geometry用HOF scratch/journal scheduler。実ROMへ未接続。

main footer/rotation/14-sector authority、HOF2sector、CFRU30/QOL31を保つ。
新ownerはlogical4の256byteだけ。既存ROMが同形式を書けるとは主張しない。
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import struct
import zlib

SECTOR=4096; CAPACITY=32*SECTOR; HOF_SIZE=7936; TEAM=120; TEAMS=50
SIZES=(0xF24,0xF80,0xF80,0xF80,0xEC0,*([0xF80]*8),0x7D0)
SIGN=0x08012025; HOF_SIGN=0x08012025
JOURNAL_OFFSET=0xEC0; JOURNAL_SIZE=256; MAX_EPOCH=2**64-1
APPEND=1; SHIFT=2; INITIAL=3

def need(c,m):
 if not c:raise ValueError(m)
def sha(b):return hashlib.sha256(b).digest()
def checksum(b):
 need(len(b)%4==0,'word-aligned stock checksum')
 v=sum(struct.unpack('<'+'I'*(len(b)//4),b))&0xffffffff
 return (v+(v>>16))&65535

@dataclass(frozen=True)
class Token:
 epoch:int
 digest:bytes

@dataclass(frozen=True)
class Journal:
 source_counter:int
 target_counter:int
 old:Token
 new:Token
 kind:int
 slot:int
 undo:bytes
 source_sha:bytes
 def encode(self):
  need(0<=self.source_counter<=0xffffffff and self.target_counter==(self.source_counter+1)&0xffffffff,'exact successor counter')
  need(0<=self.old.epoch<MAX_EPOCH and self.new.epoch==self.old.epoch+1,'nonwrapping independent HOF epoch')
  need((self.kind==APPEND and 0<=self.slot<50)or(self.kind in(SHIFT,INITIAL)and self.slot==0),'bounded HOF transition')
  need(len(self.undo)==120 and all(len(x)==32 for x in(self.old.digest,self.new.digest,self.source_sha)),'complete tokens, undo and source identity')
  b=struct.pack('<4sHHIIQQ32s32sBBBB120s32s',b'HJ32',1,256,self.source_counter,self.target_counter,self.old.epoch,self.new.epoch,self.old.digest,self.new.digest,self.kind,self.slot,0,0,self.undo,self.source_sha)
  return b+struct.pack('<I',zlib.crc32(b))
 @classmethod
 def parse(cls,b):
  need(len(b)==256 and zlib.crc32(b[:252])==struct.unpack_from('<I',b,252)[0],'journal whole CRC')
  magic,version,size,old_count,new_count,old_epoch,new_epoch,old_hash,new_hash,kind,slot,r0,r1,undo,source_sha=struct.unpack('<4sHHIIQQ32s32sBBBB120s32s',b[:252])
  need((magic,version,size,r0,r1)==(b'HJ32',1,256,0,0),'exact journal schema')
  j=cls(old_count,new_count,Token(old_epoch,old_hash),Token(new_epoch,new_hash),kind,slot,undo,source_sha)
  need(j.encode()==b,'canonical journal');return j

def journal(old,next,source_counter,epoch,source_sha,kind,slot):
 need(len(old)==len(next)==HOF_SIZE,'whole HOF payload')
 need(kind in(APPEND,SHIFT,INITIAL),'supported bounded transition')
 if kind in(APPEND,INITIAL):
  need(0<=slot<TEAMS,'one team index');at=slot*TEAM
  need(old[:at]==next[:at] and old[at+TEAM:]==next[at+TEAM:],'append changes exactly one team and retains suffix')
  if kind==INITIAL:need(slot==0 and old==bytes(HOF_SIZE),'initial canonical absence only')
 else:
  need(slot==0 and old[TEAM:6000]==next[:5880] and old[6000:]==next[6000:],'full history shifts49teams, all1936 suffix retained');at=0
 return Journal(source_counter,(source_counter+1)&0xffffffff,Token(epoch,sha(old)),Token(epoch+1,sha(next)),kind,slot,old[at:at+TEAM],source_sha)

def undo(next,j):
 need(len(next)==HOF_SIZE and sha(next)==j.new.digest,'exact prepared HOF before inverse')
 if j.kind==SHIFT:old=j.undo+next[:5880]+next[6000:]
 else:
  at=j.slot*TEAM;old=next[:at]+j.undo+next[at+TEAM:]
 need(sha(old)==j.old.digest,'whole reconstructed old HOF SHA')
 return old

def make_hof(payload):
 need(len(payload)==HOF_SIZE,'whole legacy HOF')
 out=[]
 for i in range(2):
  b=bytearray(SECTOR);b[:3968]=payload[i*3968:(i+1)*3968]
  struct.pack_into('<H',b,0xFF4,checksum(b[:3968]));struct.pack_into('<I',b,0xFF8,HOF_SIGN);out.append(bytes(b))
 return out

def read_hof(images):
 need(len(images)==2 and all(len(b)==SECTOR for b in images),'two exact HOF sectors')
 for b in images:
  need(struct.unpack_from('<I',b,0xFF8)[0]==HOF_SIGN and struct.unpack_from('<H',b,0xFF4)[0]==checksum(b[:3968]),'valid legacy HOF footer')
 return b''.join(b[:3968]for b in images)

@dataclass
class Main:
 base:int
 counter:int
 first:int
 images:list[bytes]
 by_id:list[int]
 journal:Journal|None
 @property
 def token(self):return self.journal.new if self.journal else None
 @property
 def image_sha(self):return sha(b''.join(self.images))

def parse_main(images,base,validate_journal=True):
 need(len(images)==14,'complete main bank')
 by_id=[-1]*14;counter=None;first=None
 for p,b in enumerate(images):
  need(len(b)==SECTOR,'main physical sector size')
  sid,check,signature,count=struct.unpack_from('<HHII',b,0xFF4)
  need(sid<14 and by_id[sid]<0 and signature==SIGN and check==checksum(b[:SIZES[sid]]),'stock main sector validity')
  need(base==14*(count&1),'main parity authority')
  if counter is None:counter=count
  need(counter==count,'complete same generation');by_id[sid]=p
  if sid==0:first=p
 need(all(p==(first+i)%14 for i,p in enumerate(by_id)),'complete rotation')
 raw=images[by_id[4]][JOURNAL_OFFSET:0xFF0]
 if not validate_journal or raw==bytes(304):j=None
 else:
  need(raw[256:]==bytes(48),'retained remaining48byte zero owner');j=Journal.parse(raw[:256])
 return Main(base,counter,first,list(images),by_id,j)

def select(data):
 need(len(data)==CAPACITY,'exact128KiB; no implicit save extension')
 banks=[]
 for base in(0,14):
  try:banks.append(parse_main([bytes(data[(base+i)*SECTOR:(base+i+1)*SECTOR])for i in range(14)],base,False))
  except ValueError:pass
 need(banks,'at least one complete authority')
 if len(banks)==1:return parse_main(banks[0].images,banks[0].base)
 a,b=banks;d=(b.counter-a.counter)&0xffffffff
 need(d!=0x80000000,'no half-range ambiguity')
 if d==0:need(a.images==b.images,'no ambiguous equal counter')
 chosen=b if 0<d<0x80000000 else a
 return parse_main(chosen.images,chosen.base)

class PowerCut(BaseException):pass
class FlashError(IOError):pass
class Flash:
 def __init__(self,data):
  need(len(data)==CAPACITY,'exact32physical sectors');self.data=bytearray(data);self.observe=None;self.fault=None;self.operations=0;self.phase='idle';self.writes=[]
 def images(self,ids):return[bytes(self.data[i*SECTOR:(i+1)*SECTOR])for i in ids]
 def event(self,kind,sector,offset=-1):
  self.operations+=1
  if self.observe:self.observe(self,kind,sector,offset)
 def erase(self,sector):
  need(0<=sector<30,'existing30/31never borrowed');self.event('before_erase',sector)
  effect=self.fault(self,'erase',sector,-1)if self.fault else None
  if isinstance(effect,int):
   need(0<=effect<=SECTOR,'partial erase bound');self.data[sector*SECTOR:sector*SECTOR+effect]=b'\xff'*effect;self.event('partial_erase',sector,effect);raise PowerCut()
  if effect=='raise':raise FlashError('erase failed')
  if effect!='omit':self.data[sector*SECTOR:(sector+1)*SECTOR]=b'\xff'*SECTOR
  self.event('after_erase',sector)
 def write(self,sector,image):
  need(len(image)==SECTOR,'whole image');self.writes.append((self.phase,sector));self.erase(sector)
  order=(*range(0xFF8),*range(0xFF9,SECTOR),0xFF8)
  for n in order:
   effect=self.fault(self,'program',sector,n)if self.fault else None
   if effect=='raise':raise FlashError('program failed')
   if effect!='omit':self.data[sector*SECTOR+n]&=image[n]
   self.event('program',sector,n)
  need(self.images([sector])[0]==image,'entire readback, including tail and footer');self.event('verified',sector)

def intents(data,main):
 """非選択bankのlogical4だけ。完全CRCと旧main全byteへ結合。"""
 target=14-main.base
 for p in range(14):
  b=bytes(data[(target+p)*SECTOR:(target+p+1)*SECTOR])
  if struct.unpack_from('<H',b,0xFF4)[0]!=4:continue
  try:
   j=Journal.parse(b[JOURNAL_OFFSET:JOURNAL_OFFSET+256])
   need(j.source_counter==main.counter and j.source_sha==main.image_sha,'exact selected source, not just counter')
   need(main.token is None or main.token==j.old,'exact previous HOF token')
   need(struct.unpack_from('<I',b,0xFFC)[0]==j.target_counter and b[JOURNAL_OFFSET+256:0xFF0]==bytes(48),'journal final main image bound')
   yield j,(p-4)%14
  except ValueError:continue

def resolve(data):
 """cold read-only selector。main優先。再構成だけでFlash書込みをしない。"""
 main=select(data);fixed=[bytes(data[i*SECTOR:(i+1)*SECTOR])for i in(28,29)]
 pending=list(intents(data,main));need(len(pending)<=1,'at most one predecessor-bound intent')
 if pending:
  j,first=pending[0]
  if j.kind==INITIAL:return main,None,'initial-absence'
  try:
   p=read_hof(fixed)
   if sha(p)==j.old.digest:return main,p,'fixed-old'
   if sha(p)==j.new.digest:return main,undo(p,j),'inverse'
  except ValueError:pass
  # scratch stores complete old legacy sector images; journal supplies their payload hash.
  ids=[14-main.base+(first+i)%14 for i in(8,9)]
  p=read_hof([bytes(data[i*SECTOR:(i+1)*SECTOR])for i in ids]);need(sha(p)==j.old.digest,'scratch exact old HOF');return main,p,'scratch'
 try:p=read_hof(fixed)
 except ValueError:
  need(main.token is None,'missing exact committed HOF is not a fallback main');return main,None,'legacy-unclassified'
 if main.token:need(sha(p)==main.token.digest,'selected exact committed HOF token')
 return main,p,'fixed'

def next_main(source,j,change=False):
 counter=(source.counter+1)&0xffffffff;base=14*(counter&1);first=(source.first+1)%14;images=[None]*14
 for sid,p in enumerate(source.by_id):
  b=bytearray(source.images[p]);struct.pack_into('<I',b,0xFFC,counter)
  if sid==4:b[JOURNAL_OFFSET:0xFF0]=(j.encode()+bytes(48))if j else bytes(304)
  if change and sid==1:b[0]^=0x51
  struct.pack_into('<H',b,0xFF6,checksum(b[:SIZES[sid]]));images[(first+sid)%14]=bytes(b)
 return parse_main(images,base)

def commit(flash,next_payload,kind,slot=0,allow_initial=False):
 main,old,route=resolve(flash.data)
 need(not list(intents(flash.data,main)),'recover interrupted HOF before any new save')
 if old is None:
  need(allow_initial and kind==INITIAL and main.token is None,'explicit absence owner required, corruption is not migration permission');old=bytes(HOF_SIZE)
 else:need(kind!=INITIAL,'existing valid HOF cannot be silently cleared')
 epoch=main.token.epoch if main.token else 0
 j=journal(old,next_payload,main.counter,epoch,main.image_sha,kind,slot);j.encode()
 target=next_main(main,j,True);physical=lambda sid:target.base+target.by_id[sid]
 before=bytes(flash.data);old_images=flash.images([28,29])
 # First invalidate final id13. Neither scratch nor journal can make14complete.
 flash.phase='invalidate';flash.erase(physical(13));need(flash.images([physical(13)])[0]==b'\xff'*SECTOR,'final target invalidated before scratch')
 flash.phase='scratch'
 for sid,b in zip((8,9),old_images):flash.write(physical(sid),b)
 flash.phase='journal';flash.write(physical(4),target.images[target.by_id[4]])
 flash.phase='hof'
 for sid,b in zip((28,29),make_hof(next_payload)):flash.write(sid,b)
 need(read_hof(flash.images([28,29]))==next_payload,'whole new HOF durable before scratch reclaim')
 flash.phase='main'
 for sid in(*[x for x in range(14)if x not in(4,13)],13):flash.write(physical(sid),target.images[target.by_id[sid]])
 chosen,p,_=resolve(flash.data);need(chosen.counter==target.counter and chosen.token==j.new and p==next_payload,'exact new pair')
 need(flash.data[main.base*SECTOR:(main.base+14)*SECTOR]==before[main.base*SECTOR:(main.base+14)*SECTOR]and flash.data[30*SECTOR:]==before[30*SECTOR:],'all selectedmain andauxbytes protected')
 return chosen

def recover(flash):
 """旧mainを保護した物理rollback。通常Save/cloneの前に必要。"""
 main,old,route=resolve(flash.data);pending=list(intents(flash.data,main))
 if not pending:return
 j,first=pending[0];ids=[14-main.base+(first+i)%14 for i in(8,9)];flash.phase='recover-scratch'
 # new固定像からinverseするとき、旧完全像を先に別sectorへ再退避する。
 if old is not None:
  fixed=make_hof(old)
  if route!='scratch':
   for sid,b in zip(ids,fixed):flash.write(sid,b)
  flash.phase='recover-hof'
  for sid,b in zip((28,29),fixed):flash.write(sid,b)
  need(read_hof(flash.images([28,29]))==old,'physical old HOF restored')
 else:
  flash.phase='recover-absence'
  for sid in(28,29):flash.erase(sid)
  need(all(b==b'\xff'*SECTOR for b in flash.images([28,29])),'absence erase readback before journal retirement')
 # HOF復元後だけjournalを無効化。selected旧mainは一切書かない。
 flash.phase='recover-retire';retire=14-main.base+(first+4)%14;flash.erase(retire)
 need(flash.images([retire])[0]==b'\xff'*SECTOR,'journal retirement verified')
 selected,p,_=resolve(flash.data);need(selected.image_sha==main.image_sha and p==old,'recovery exact old pair')

def normal(flash):
 recover(flash);main,old,_=resolve(flash.data);target=next_main(main,main.journal)
 physical=lambda sid:target.base+target.by_id[sid];flash.phase='normal-invalidate';flash.erase(physical(13));need(flash.images([physical(13)])[0]==b'\xff'*SECTOR,'normal final target invalidated');flash.phase='normal'
 for sid in range(14):flash.write(physical(sid),target.images[target.by_id[sid]])
 chosen,p,_=resolve(flash.data);need(chosen.token==main.token and p==old,'normal inherits exact token, no orphan promotion');return chosen
