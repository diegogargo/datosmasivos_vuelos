from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os

ROOT=Path(__file__).resolve().parents[2]
def now():return datetime.now(timezone.utc).isoformat()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(data,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    os.replace(t,p)
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
