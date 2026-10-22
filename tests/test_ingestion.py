import csv,io,zipfile
from pathlib import Path
import pytest
from src.ingestion.bts import fetch,validate_zip
from src.processing.contracts import COLUMNS

def payload(columns=COLUMNS):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('flights.csv',','.join(columns)+'\n')
    return stream.getvalue()
class Response(io.BytesIO):
    headers={'Last-Modified':'test'}

def test_download_retry_cache_and_tamper(tmp_path):
    dest=tmp_path/'month.zip';calls=[]
    def opener(*args,**kwargs):
        calls.append(1)
        if len(calls)==1:raise OSError('corte simulado')
        return Response(payload())
    proof=fetch('https://example.test/month.zip',dest,opener=opener,sleeper=lambda _:None)
    assert len(calls)==2 and validate_zip(dest)=='flights.csv'
    cached=fetch(proof['url'],dest,proof,opener=lambda *a,**k:pytest.fail('No debe descargar'))
    assert cached['cache_hit']
    dest.write_bytes(b'alterado')
    with pytest.raises(ValueError,match='trazabilidad'):fetch(proof['url'],dest,proof)

def test_non_zip_and_missing_schema_are_rejected(tmp_path):
    dest=tmp_path/'bad.zip'
    with pytest.raises(zipfile.BadZipFile):
        fetch('https://example.test/bad',dest,opener=lambda *a,**k:Response(b'<html>error</html>'),sleeper=lambda _:None)
    assert not dest.exists() and not dest.with_suffix('.zip.part').exists()
    dest.write_bytes(payload(['wrong']))
    with pytest.raises(ValueError,match='Faltan campos'):validate_zip(dest)
