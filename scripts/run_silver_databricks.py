"""Sube el módulo Silver y ejecuta un rango; reutiliza Bronze existente, sin descargar ZIP."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from run_databricks import Client,submit_and_wait
from src.ingestion.acquire_range import months
from src.ingestion.bronze import identifier
from src.processing.silver import load_airports
from src.utils.common import digest,write_json

def upload(client,base):
    files=sorted((ROOT/'src').rglob('*.py'))+sorted((ROOT/'data/reference').glob('*'))
    files+=[ROOT/'notebooks/databricks/02_silver.py']
    directories={base}
    for file in files:directories.add(base+'/'+file.relative_to(ROOT).parent.as_posix())
    for directory in sorted(directories,key=lambda p:p.count('/')):client.call('workspace','mkdirs',directory)
    for file in files:
        relative=file.relative_to(ROOT).as_posix();notebook=relative.startswith('notebooks/')
        destination=base+'/'+(relative.removesuffix('.py') if notebook else relative)
        arguments=['workspace','import',destination,'--file',str(file),'--overwrite','--format','SOURCE' if notebook else 'AUTO']
        if notebook:arguments+=['--language','PYTHON']
        client.call(*arguments)
    return {f.relative_to(ROOT).as_posix():digest(f) for f in files}

def execute(args):
    identifier(args.catalog);load_airports()
    expected=months(args.start,args.end)
    client=Client(args.cli,args.profile)
    username=client.call('current-user','me')['userName']
    if '/' in username or '\\' in username or username in {'','.','..'}:raise ValueError('Usuario incompatible con la ruta de workspace')
    base='/Users/'+username+'/datosmasivos_vuelos_jose'
    hashes=upload(client,base)
    params=dict(project_root='/Workspace'+base,catalog=args.catalog,
                output_root=f'/Volumes/{args.catalog}/bronze/vuelos_raw/vuelos',start=args.start,end=args.end)
    print('Código y dimensión transferidos. Ejecutando Silver sobre Bronze existente...',flush=True)
    run,output=submit_and_wait(client,base+'/notebooks/databricks/02_silver',params,'Vuelos Jose - Silver')
    report=json.loads(output.get('notebook_output',{}).get('result','{}'))
    if report.get('complete') is not True or report.get('quality_summary_passed') is not True or [m['period'] for m in report.get('months',[])]!=expected:
        raise ValueError('Silver no devolvió evidencia completa del rango solicitado')
    for month in report['months']:
        if month['source_rows']!=month['silver_rows']+month['quarantine_rows']+month['exact_duplicate_exclusions']:
            raise ValueError('No concilian los conteos de '+month['period'])
        if month.get('quality_summary',{}).get('quality_passed') is not True:
            raise ValueError('Falta comprobar tipos/etiquetas de '+month['period'])
    report['local_code_sha256']=hashes
    report['execution_role']='Código de Jose Miguel asistido por Codex; workspace de integración de Diego.'
    reference=ROOT/'reports/tables/bts_january_label_reference.json'
    if reference.exists():
        ref=json.loads(reference.read_text(encoding='utf-8'))
        for month in report['months']:
            if month['period']==ref['period']:
                actual=month['quality_summary']
                for field in ('eligible_departures','cancelled_rows','delayed_departures'):
                    if actual[field]!=ref[field]:raise ValueError('Difiere referencia CSV independiente de enero: '+field)
                report['january_reference_passed']=True
    write_json(ROOT/'reports/tables/databricks_silver_result.json',report)
    write_json(ROOT/'data/raw/databricks_silver_run_private.json',dict(run=run,workspace_path=base))
    print(f"SILVER CORRECTO: {report['rows']:,} aceptados; {report['quarantine_rows']:,} en cuarentena; {len(expected)} meses.",flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cli',required=True);p.add_argument('--profile',default='vuelos')
    p.add_argument('--catalog',default='workspace');p.add_argument('--start',default='2025-01');p.add_argument('--end',default='2025-01')
    p.add_argument('--execute',action='store_true');args=p.parse_args()
    print(f'Plan Silver: {len(months(args.start,args.end))} meses, {args.start} a {args.end}.',flush=True)
    if args.execute:execute(args)
    else:print('Añadir --execute para cargar código y ejecutar. No vuelve a descargar datos.')
if __name__=='__main__':main()
