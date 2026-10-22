"""Ejecuta Silver, históricos y validación disponible; solo tras un piloto verificado."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import run_silver_databricks as silver_runner
from run_databricks import Client,submit_and_wait
from src.ingestion.acquire_range import months
from src.processing.historical_features import check_mode
from src.utils.common import digest,read_json,write_json


def execute(args):
    check_mode(args.availability_mode)
    requested=months(args.start,args.end)
    current=ROOT/'reports/tables/databricks_silver_result.json'
    pilot_path=ROOT/'reports/tables/databricks_silver_pilot.json'
    if not pilot_path.exists():
        pilot=read_json(current) if current.exists() else {}
        if not (pilot.get('complete') is True and pilot.get('start')=='2025-01'
                and pilot.get('end')=='2025-01' and pilot.get('months',[{}])[0].get('source_rows')==539747):
            raise ValueError('Primero debe terminar correctamente el piloto Silver de enero 2025. No lanzar duplicados.')
        write_json(pilot_path,pilot)
    if args.skip_silver:
        report=read_json(current)
        if not (report.get('complete') is True and report.get('quality_summary_passed') is True
                and [m['period'] for m in report.get('months',[])]==requested):
            raise ValueError('--skip-silver exige el reporte completo del mismo rango')
    else:
        silver_runner.execute(args)
    client=Client(args.cli,args.profile)
    username=client.call('current-user','me')['userName']
    if '/' in username or '\\' in username or username in {'','.','..'}:
        raise ValueError('Usuario incompatible con la ruta del workspace')
    base='/Users/'+username+'/datosmasivos_vuelos_jose'
    # Al reanudar históricos se vuelve a transferir el código, sin escribir Bronze/Silver.
    hashes=silver_runner.upload(client,base)
    notebook=ROOT/'notebooks/databricks/03_history_validation.py'
    destination=base+'/notebooks/databricks/03_history_validation'
    client.call('workspace','import',destination,'--file',str(notebook),'--overwrite',
                '--format','SOURCE','--language','PYTHON')
    hashes[notebook.relative_to(ROOT).as_posix()]=digest(notebook)
    params=dict(project_root='/Workspace'+base,catalog=args.catalog,start=args.start,end=args.end,
        output_root=f'/Volumes/{args.catalog}/bronze/vuelos_raw/vuelos',availability_mode=args.availability_mode)
    print('Ejecutando históricos y validación de capas disponibles. Modo: '+args.availability_mode,flush=True)
    run,output=submit_and_wait(client,destination,params,'Vuelos Jose - historicos y validacion')
    result=json.loads(output.get('notebook_output',{}).get('result','{}'))
    history,validation=result.get('history',{}),result.get('validation',{})
    if not history.get('complete') or not validation.get('passed'):
        raise ValueError('El job no devuelve históricos y validación correctos')
    if [m['period'] for m in history.get('months',[])]!=requested:
        raise ValueError('El rango de históricos devuelto no coincide con el solicitado')
    history['local_code_sha256']=hashes
    history['execution_role']='Código de Jose Miguel asistido por Codex; workspace de integración de Diego.'
    write_json(ROOT/'reports/tables/databricks_history_result.json',history)
    write_json(ROOT/'reports/tables/databricks_layer_validation.json',validation)
    write_json(ROOT/'data/raw/databricks_history_run_private.json',dict(run=run,workspace_path=base))
    print(f"HISTORICOS CORRECTOS: {history['rows']:,} filas; {len(requested)} meses.",flush=True)
    print('BRONZE/SILVER: '+str(validation.get('bronze_silver_passed'))+'; integración total: '+str(validation.get('complete')),flush=True)
    if validation.get('pending'):print('Pendiente: '+', '.join(validation['pending']),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cli',required=True);p.add_argument('--profile',default='vuelos')
    p.add_argument('--catalog',default='workspace');p.add_argument('--start',default='2024-01');p.add_argument('--end',default='2025-12')
    p.add_argument('--availability-mode',choices=['disabled','retrospective_ideal'],default='disabled')
    p.add_argument('--skip-silver',action='store_true');p.add_argument('--execute',action='store_true')
    args=p.parse_args()
    print(f'Plan José: {len(months(args.start,args.end))} meses, {args.start} a {args.end}; modo {args.availability_mode}.',flush=True)
    if args.execute:execute(args)
    else:print('Añadir --execute después del piloto verificado. No vuelve a descargar datos.')
if __name__=='__main__':main()
