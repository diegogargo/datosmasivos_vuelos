"""Conversión estricta de hora local: no adivina una hora ambigua por DST."""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from src.processing.contracts import hhmm_minutes

def strict_scheduled_utc(date,hhmm,zone):
    minutes=hhmm_minutes(hhmm)
    if minutes is None:raise ValueError('HHMM inválido')
    local=datetime.fromisoformat(str(date)[:10])+timedelta(minutes=minutes)
    tz=ZoneInfo(zone)
    candidates=set()
    for fold in (0,1):
        utc=local.replace(tzinfo=tz,fold=fold).astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None)==local:candidates.add(utc)
    if not candidates:raise ValueError('Hora local inexistente por DST')
    if len(candidates)>1:raise ValueError('Hora local ambigua por DST')
    return candidates.pop()
