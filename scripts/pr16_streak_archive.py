"""構築原本ZIPの厳密読取。追加許可はtrackedな割当CSV2本だけ。"""
import io
from pathlib import PurePosixPath
import re
import zipfile
from scripts.pr16_circus_identity import identity,need,strict
CSV={'source/config/ram_layout.csv','source/config/save_layout.csv'}
TEXT={'.json','.txt','.stdout','.stderr','.log','.c','.h','.py','.yml','.ld','.S'}
def unpack(raw,bound):
    need(identity(raw)==bound,'artifact ZIP identity differs')
    files={};total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(0<len(z.infolist())<500,'ZIP member count differs')
        for info in z.infolist():
            name=info.filename;p=PurePosixPath(name)
            need(name==p.as_posix() and not p.is_absolute() and '..' not in p.parts and '\\' not in name
                 and name not in files and not info.is_dir(),'unsafe/duplicate member path')
            need((info.external_attr>>16)&0o170000!=0o120000 and info.file_size<2000000,'unsafe member type/size')
            need(p.suffix in TEXT or name in CSV,'unapproved text suffix/path')
            data=z.read(info);total+=len(data);need(total<8000000,'expanded ZIP bound')
            data.decode('utf-8')
            need(b'\0' not in data and not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',data),'unsafe text')
            files[name]=data
    manifest=strict(files['members.json'])
    need(set(files)==set(manifest)|{'members.json'},'manifest coverage differs')
    for name,binding in manifest.items():need(identity(files[name])==binding,'member identity differs')
    return files,manifest
