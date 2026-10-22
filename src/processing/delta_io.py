"""Escritura mensual limitada a tablas Delta pertenecientes a este proyecto."""
from src.ingestion.bronze import identifier,table_identifier
from src.ingestion.acquire_range import months

def write_month(spark,frame,table,period,layer):
    months(period,period);identifier(layer)
    quoted=table_identifier(table)
    if not spark.catalog.tableExists(table):
        fields=', '.join(identifier(f.name)+' '+f.dataType.simpleString() for f in frame.schema)
        spark.sql(f'CREATE TABLE {quoted} ({fields}) USING DELTA PARTITIONED BY (`_source_period`) '
                  f"TBLPROPERTIES ('vuelos.layer'='{layer}', 'vuelos.source'='bts_reporting_carrier')")
    properties={r['key']:r['value'] for r in spark.sql(f'SHOW TBLPROPERTIES {quoted}').collect()}
    if properties.get('vuelos.layer')!=layer or properties.get('vuelos.source')!='bts_reporting_carrier':
        raise ValueError('La tabla no pertenece a esta capa del proyecto: '+table)
    actual={f.name:f.dataType.simpleString() for f in spark.table(table).schema}
    expected={f.name:f.dataType.simpleString() for f in frame.schema}
    if actual!=expected:raise ValueError('Esquema incompatible; se conserva la tabla existente: '+table)
    # replaceWhere también verifica que las filas cumplan el predicado.
    frame.write.format('delta').mode('overwrite').option('replaceWhere',f"_source_period = '{period}'").saveAsTable(table)
    return spark.sql(f'DESCRIBE HISTORY {quoted} LIMIT 1').first()['version']

def drop_stage(spark,table):
    quoted=table_identifier(table)
    properties={r['key']:r['value'] for r in spark.sql(f'SHOW TBLPROPERTIES {quoted}').collect()}
    if properties.get('vuelos.layer')!='silver_stage' or properties.get('vuelos.source')!='bts_reporting_carrier':
        raise ValueError('Se conserva una tabla de staging ajena')
    spark.sql(f'DROP TABLE {quoted}')
