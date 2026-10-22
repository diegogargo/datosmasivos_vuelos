"""Bronze BTS en Spark/Delta; conserva campos originales como cadenas y procedencia.

Importar este módulo no requiere Spark ni accede al workspace. run_bronze sí exige
una sesión real de Databricks y archivos completos en un Volume verificado.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from src.ingestion.acquire_range import months
from src.processing.contracts import COLUMNS
from src.utils.common import digest, now, read_json, write_json

METADATA = {'_source_period', '_source_zip_sha256', '_source_csv_sha256', '_source_url',
            '_source_file', '_source_downloaded_at', '_ingested_at', '_run_id'}


def identifier(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        raise ValueError('Identificador SQL inválido; usar letras, números y guion bajo')
    return f'`{value}`'


def table_identifier(value):
    parts = value.split('.')
    if len(parts) != 3:
        raise ValueError('La tabla debe indicar catalogo.esquema.tabla')
    return '.'.join(identifier(part) for part in parts)


def column_names(header):
    """Mapeo posicional explícito para encabezados vacíos, sin borrar columnas."""
    if not set(COLUMNS).issubset(header):
        raise ValueError('Faltan campos BTS para Bronze')
    names = []
    for index, name in enumerate(header):
        normalized = name if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) else f'_bts_column_{index}'
        if normalized in names or normalized in METADATA:
            raise ValueError(f'Campo duplicado o reservado: {normalized}')
        names.append(normalized)
    return names


def contained_file(root, relative):
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if Path(relative).is_absolute() or not candidate.is_relative_to(root):
        raise ValueError('Ruta del manifiesto fuera del Volume del proyecto')
    if not candidate.is_file():
        raise FileNotFoundError(f'Archivo de origen faltante: {relative}')
    return candidate


def verify_source(root, period, item):
    if item.get('period') != period or item.get('status') != 'complete':
        raise ValueError('Mes no completo o periodo incoherente')
    names = column_names(item.get('csv_header', []))
    if type(item.get('csv_rows')) is not int or item['csv_rows'] <= 0:
        raise ValueError('Conteo de origen inválido')
    if item.get('csv_columns') != len(names):
        raise ValueError('Cantidad de campos del manifiesto incoherente')
    for key, hash_key in [('path', 'sha256'), ('csv_path', 'csv_sha256')]:
        path = contained_file(root, item[key])
        if digest(path) != item.get(hash_key):
            raise ValueError(f'Hash de origen incorrecto: {key}')
        if key == 'csv_path' and path.stat().st_size != item.get('csv_bytes'):
            raise ValueError('Tamaño de CSV incoherente')
    return contained_file(root, item['csv_path']), names


def volume_root_path(value):
    path = Path(value)
    if not str(value).startswith('/Volumes/') or len(path.parts) < 5 or '..' in path.parts:
        raise ValueError('Usar la ruta real /Volumes/catalogo/esquema/volume/proyecto')
    return path


def run_bronze(spark, volume_root, table, start='2025-01', end='2025-01', run_id=None):
    """Reemplazo Delta atómico por mes. No altera otras particiones ni limpia filas."""
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType, StructField, StructType

    root = volume_root_path(volume_root)
    quoted = table_identifier(table)
    run_id = run_id or str(uuid.uuid4())
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
        raise ValueError('run_id inválido')
    requested = months(start, end)
    manifest = read_json(root / 'data/raw/manifest.json')
    report_path = root / 'reports/bronze' / f'{run_id}.json'
    report = dict(run_id=run_id, layer='bronze', started_at=now(), start=start, end=end,
                  spark_version=spark.version, complete=False, months=[])
    spark.conf.set('spark.sql.session.timeZone', 'UTC')
    schema_names = None
    try:
        for period in requested:
            item = manifest['files'].get(period)
            if item is None:
                raise ValueError(f'Mes no adquirido: {period}')
            path, names = verify_source(root, period, item)
            if schema_names is None:
                schema_names = names
            if names != schema_names:
                raise ValueError('Cambio de esquema entre meses; requiere decisión explícita')
            schema = StructType([StructField(name, StringType(), True) for name in names])
            frame = (spark.read.schema(schema).option('header', True).option('enforceSchema', True)
                     .option('mode', 'FAILFAST').option('encoding', 'UTF-8').csv(str(path)))
            rows = frame.count()
            if rows != item['csv_rows']:
                raise ValueError(f'Conteo Spark {rows} distinto del CSV {item["csv_rows"]}')
            metadata = dict(_source_period=period, _source_zip_sha256=item['sha256'],
                            _source_csv_sha256=item['csv_sha256'], _source_url=item['url'],
                            _source_file=item['csv_path'], _source_downloaded_at=item.get('downloaded_at'),
                            _run_id=run_id)
            for name, value in metadata.items():
                frame = frame.withColumn(name, F.lit(value).cast('string'))
            frame = frame.withColumn('_ingested_at', F.current_timestamp())
            if not spark.catalog.tableExists(table):
                (frame.limit(0).write.format('delta').mode('errorifexists')
                 .partitionBy('_source_period').saveAsTable(table))
                spark.sql(f"ALTER TABLE {quoted} SET TBLPROPERTIES "
                          "('vuelos.layer'='bronze', 'vuelos.source'='bts_reporting_carrier')")
            properties = {row['key']: row['value'] for row in spark.sql(f'SHOW TBLPROPERTIES {quoted}').collect()}
            if properties.get('vuelos.layer') != 'bronze' or properties.get('vuelos.source') != 'bts_reporting_carrier':
                raise ValueError('La tabla existente no pertenece a esta ingesta Bronze')
            if spark.table(table).schema != frame.schema:
                # Spark puede marcar nullable metadatos literales de forma distinta tras guardar.
                expected = [(field.name, field.dataType.simpleString()) for field in frame.schema]
                actual = [(field.name, field.dataType.simpleString()) for field in spark.table(table).schema]
                if expected != actual:
                    raise ValueError('Esquema Delta incompatible; no sobrescribir automáticamente')
            (frame.write.format('delta').mode('overwrite')
             .option('replaceWhere', f"_source_period = '{period}'").saveAsTable(table))
            actual_rows = spark.table(table).where(F.col('_source_period') == period).count()
            if actual_rows != rows:
                raise ValueError('Conteo Delta posterior distinto; inspeccionar la ejecución')
            history = spark.sql(f'DESCRIBE HISTORY {quoted} LIMIT 1').first()
            report['months'].append(dict(period=period, source_rows=rows, bronze_rows=actual_rows,
                delta_version=history['version'], csv_sha256=item['csv_sha256'],
                original_columns=len(names), header_mapping=dict(zip(names, item['csv_header']))))
            write_json(report_path, report)
        report.update(complete=True, finished_at=now(), rows=sum(x['bronze_rows'] for x in report['months']))
    except Exception as exc:
        report.update(finished_at=now(), error=f'{type(exc).__name__}: {exc}')
        write_json(report_path, report)
        raise
    write_json(report_path, report)
    return report
