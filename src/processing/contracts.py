"""Reglas de negocio compartidas; no equivalen a ejecución en Databricks."""
import math
from datetime import datetime,timedelta
import pandas as pd

COLUMNS=['FlightDate','Reporting_Airline','Flight_Number_Reporting_Airline','Tail_Number',
'Origin','Dest','Distance','CRSDepTime','CRSArrTime','CRSElapsedTime','DepTime','ArrTime',
'DepDelay','ArrDelay','Cancelled','Diverted','CarrierDelay','WeatherDelay','NASDelay',
'SecurityDelay','LateAircraftDelay']
KEY=['FlightDate','Reporting_Airline','Flight_Number_Reporting_Airline','Origin','Dest','CRSDepTime']
def label_delay15(cancelled,delay):
    if pd.isna(cancelled) or pd.isna(delay):return None
    try:
        cancelled,delay=float(cancelled),float(delay)
    except (ValueError,TypeError):return None
    if cancelled!=0 or not math.isfinite(delay):return None
    return int(delay>=15)
def hhmm_minutes(value):
    if pd.isna(value):return None
    try:x=float(value)
    except (ValueError,TypeError):return None
    if not math.isfinite(x) or not x.is_integer():return None
    n=int(x)
    if n==2400:return 1440
    if not 0<=n<=2359 or n%100>=60:return None
    return (n//100)*60+n%100
def scheduled_local(date,hhmm):
    minutes=hhmm_minutes(hhmm)
    if minutes is None or pd.isna(date):return None
    return datetime.fromisoformat(str(date)[:10])+timedelta(minutes=minutes)
