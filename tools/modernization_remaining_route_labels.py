"""Resolve text pointers from the pinned candidate's authored forget script graph.

No deprecated generated Stage25 JSON or external vendor checkout is required.
This decodes data only; it neither executes the game nor generates a PASS oracle.
"""
import struct

ENTRY=0x092D08FC
WIDTH={0x05:5,0x06:6,0x09:2,0x0f:6,0x21:5,0x23:5,0x25:3,0x27:1,0x31:3,0x32:1,0x97:2}
SELECT=(0x0f,0x09,0x25,0x27,0x21,0x06,0x25,0x21,0x06,0x25,0x21,0x06,0x97,0x25,0x97,0x21,0x06,0x23,0x21,0x06,0x23,0x21,0x06,0x05)

def resolve(rom):
    def data(a,n):
        if type(a) is not int or not 0x08000000<=a<=0x08000000+len(rom)-n:raise ValueError('script pointer outside candidate')
        return rom[a-0x08000000:a-0x08000000+n]
    def word(raw,off):return struct.unpack_from('<I',raw,off)[0]
    def script(a,ops):
        result=[]
        for op in ops:
            b=data(a,WIDTH[op])
            if b[0]!=op:raise ValueError('forget script opcode differs')
            result.append(b);a+=len(b)
        return result
    def text(seq):
        loads=[b for b in seq if b[0]==0x0f]
        if len(loads)!=1 or loads[0][1]!=0:raise ValueError('ambiguous text pointer')
        a=word(loads[0],2)
        raw=data(a,min(180,0x08000000+len(rom)-a))
        if b'\xff' not in raw or raw[0]==0xff:raise ValueError('empty or unterminated text')
        return a
    entry=script(ENTRY,(0x23,0x0f,0x09,0x05))
    select=script(word(entry[-1],1),SELECT)
    branches=[word(b,2) for b in select if b[0]==0x06]
    confirm=script(word(select[-1],1),(0x25,0x0f,0x09,0x21,0x06,0x05))
    deleted=script(word(confirm[-2],2),(0x23,0x31,0x32,0x0f,0x09,0x05))
    warning=script(branches[5],(0x0f,0x09,0x21,0x06,0x05))
    if word(warning[-2],2)!=word(select[-1],1):raise ValueError('warning/confirm graph disconnected')
    return {'text_pp_up_warning':text(warning),'text_forget_confirm':text(confirm),'text_forgot':text(deleted),'text_last_move':text(script(branches[2],(0x0f,0x09,0x05))),'text_form_rejected':text(script(branches[4],(0x0f,0x09,0x05)))}
