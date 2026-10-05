#!/usr/bin/env python3
"""新tail先頭384byteの見かけ参照を、型付きsource境界に束縛する。"""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='content/modernization/pr16_dex_union_tail_lease.json'
LO=0x09FFFB28;HI=LO+384

def need(x,m):
 if not x:raise ValueError(m)
def digest(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def lz(raw):
 need(len(raw)>=4 and raw[0]==16,'GBA LZ10 header');size=int.from_bytes(raw[1:4],'little');need(0<size<=100000,'bounded decoded asset');out=bytearray();at=4
 while len(out)<size:
  need(at<len(raw),'LZ flag in range');flags=raw[at];at+=1
  for bit in range(7,-1,-1):
   if len(out)==size:break
   if flags&(1<<bit):
    need(at+2<=len(raw),'LZ pair in range');a,b=raw[at:at+2];at+=2;n=(a>>4)+3;disp=((a&15)<<8|b)+1;need(disp<=len(out)and len(out)+n<=size,'valid LZ back reference')
    for _ in range(n):out.append(out[-disp])
   else:need(at<len(raw),'LZ literal in range');out.append(raw[at]);at+=1
 need(at==len(raw),'complete encoded LZ extent');return bytes(out)
def literals(raw):
 out=[]
 for high in(9,11,13):
  start=0
  while True:
   pos=raw.find(bytes([high]),start)
   if pos<0:break
   start=pos+1
   if pos<3:continue
   at=pos-3;v=struct.unpack_from('<I',raw,at)[0];normalized=v-(high-9)*0x1000000
   if LO<=normalized<HI:out.append(dict(address=0x08000000+at,target=v))
 return sorted(out,key=lambda r:r['address'])
def branches(raw):
 out=[]
 for i in range(0,len(raw)-3,2):
  h,l=struct.unpack_from('<HH',raw,i)
  if h&0xF800==0xF000 and l&0xF800==0xF800:
   off=((h&0x7FF)<<12)|((l&0x7FF)<<1)
   if off&(1<<22):off-=1<<23
   target=0x08000000+i+4+off
   if LO<=target<HI:out.append(dict(address=0x08000000+i,target=target))
 return out
def dpcm(raw,size):
 deltas=(0,1,4,9,16,25,36,49,-64,-49,-36,-25,-16,-9,-4,-1);out=bytearray();at=0
 while len(out)<size:
  need(at<len(raw),'DPCM block header');value=raw[at];at+=1;out.append(value);count=min(63,size-len(out))
  for i in range(count):
   need(at<len(raw),'DPCM nibble');nibble=(raw[at]>>(4*(i&1)))&15;value=(value+deltas[nibble])&255;out.append(value)
   if not(i&1):at+=1
  if count and not(count&1):at+=1
 need(at==len(raw),'exact minimal compressed sample prefix');return bytes(out)
def validate(raw):
 p=json.loads((ROOT/PROOF).read_bytes());need(p['scope']==dict(base=LO,size=384,literal_candidates=16,thumb_bl_candidates=0),'exact bounded tail scope')
 expected=sorted(({k:x[k]for k in('address','target')}for x in p['candidates']),key=lambda r:r['address'])
 need(literals(raw)==expected and branches(raw)==[],'entire ROM allbyte all3mirror literals and ThumbBL inventory')
 roots={r['address']:r for r in p['roots']};need(len(roots)==12 and len(expected)==16,'all12 typed roots and16 candidates');types={}
 for row in p['roots']:
  at=row['address']-0x08000000;b=raw[at:at+row['size']];need(digest(b)=={k:row[k]for k in('size','sha256')},'whole typed root binding')
  for site in row['refs']:need(struct.unpack_from('<I',raw,site-0x08000000)[0]==row['address'],'typed current root reference')
  kind=row['kind']
  if kind=='lz77':decoded=lz(b)
  elif kind.startswith('pcm8')or kind=='dpcm4':
   fields=struct.unpack_from('<HHIII',b);need(fields==tuple(row[k]for k in('wave_type','wave_status','wave_frequency','wave_loop_start','decoded_size')),'wave header and declared sample span');need(0<=fields[3]<=fields[4],'loop within declared samples');decoded=dpcm(b[16:],fields[4])if kind=='dpcm4'else b[16:]
   if kind=='pcm8_source_exact':need(row['source_sha256']=='592ad886eed8bc775a8c92d788f6526c1206867606f3020e9f3dbcc99d2094f9'and row['source_wav_rate']==16000 and row['source_pcm_transform']=='each byte xor 128; all4342 bytes exact','fixed independently matched source-WAV witness')
  elif kind=='text_eos_crossing':need(b[-1]==255 and row['eos_address']==row['address']+len(b)-1 and row['refs'],'rooted EOS-terminated text');decoded=None
  else:raise ValueError('unknown typed root')
  if decoded is not None:need(digest(decoded)==dict(size=row['decoded_size'],sha256=row['decoded_sha256']),'complete typed decoding')
 for row in p['candidates']:
  root=roots[row['root']];kind=root['kind'];types[kind]=types.get(kind,0)+1
  if kind=='text_eos_crossing':need(row['address']<=root['eos_address']<row['address']+4,'apparent pointer crosses typed EOS')
  else:need(root['address']+(4 if kind=='lz77'else 16)<=row['address']and row['address']+4<=root['address']+root['size'],'apparent pointer lies wholly in typed encoded payload')
 return dict(status='PASS_TYPED_TAIL_REFERENCE_CLASSIFICATION',address=LO,size=384,literal_candidates=16,thumb_bl_candidates=0,root_count=12,candidate_types=types,unclassified_candidates=0)
