"""Running-room building layouts, portable immutable revisions and demand commitments."""
import hashlib,json,math,re
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from site_energy import ROOM_DEFAULT

SCHEMA=2

def running_room(rooms=10,beds_per_room=2,peak_guests=20,staff=4,kitchen_kw=12.,water_heating_kw=10.,laundry_kw=3.):
    if not 1<=rooms<=200 or not 1<=beds_per_room<=10 or not 0<=peak_guests<=rooms*beds_per_room or staff<0:
        raise ValueError('Peak guests must fit the bedroom/bed capacity; positive room and bed counts required')
    fraction=peak_guests/(rooms*beds_per_room)
    zones=[];loads=[]
    def zone(name,L,W,people,target=25.,ac=True,kind='Shared',equipment=.1,occupancy='Always',window=2.,fraction=1.):
        zones.append(dict(ROOM_DEFAULT,Room=name,Length_m=float(L),Width_m=float(W),Height_m=3.,Window_m2=window,Door_m2=2.,People=int(people),Target_C=target,Equipment_kW=equipment,Occupancy=occupancy,AC_units=2,AC_TR_each=2.,AC_enabled=ac,Zone_type=kind,Occupancy_fraction=fraction))
    def circuit(name,room,typ,count,watts,sched):loads.append(dict(Load=name,Room=room,Type=typ,Count=count,Watts_each=watts,Schedule=sched))
    for i in range(rooms):
        name=f'Bedroom {i+1:03d}';zone(name,4,4,beds_per_room,kind='Bedroom',fraction=fraction)
        circuit(name+' lights',name,'Light',2,15,'Night');circuit(name+' fans',name,'Fan',1,60,'Always')
    zone('Lobby / reception',6,4,max(1,math.ceil(peak_guests*.2))+staff,equipment=.5)
    zone('Dining hall',8,5,max(1,math.ceil(peak_guests*.5)),occupancy='Meal hours')
    zone('Kitchen',6,5,max(1,staff),ac=False,kind='Kitchen',equipment=1.,occupancy='Meal hours')
    zone('Baths / toilets',6,4,max(1,math.ceil(peak_guests*.2)),ac=False,kind='Utility',window=1.)
    zone('Laundry / services',4,3,max(1,staff//2),ac=False,kind='Utility')
    zone('Corridors',12,2,0,ac=False,kind='Circulation',equipment=0.,window=0.)
    for name in ['Lobby / reception','Dining hall','Kitchen','Baths / toilets','Laundry / services','Corridors']:
        circuit(name+' lights',name,'Light',6,18,'Always' if name in ['Lobby / reception','Corridors'] else 'Occupied hours')
    circuit('Cooking appliances','Kitchen','Other',1,kitchen_kw*1000,'Meal hours')
    circuit('Kitchen exhaust','Kitchen','Fan',2,250,'Meal hours')
    circuit('Dining fans','Dining hall','Fan',4,60,'Meal hours')
    circuit('Water heating','Baths / toilets','Other',1,water_heating_kw*1000,'Occupied hours')
    circuit('Laundry equipment','Laundry / services','Other',1,laundry_kw*1000,'Occupied hours')
    circuit('Water pump','Site exterior','Other',1,750,'Occupied hours')
    circuit('Exterior lights','Site exterior','Light',8,30,'Night')
    return pd.DataFrame(zones),pd.DataFrame(loads)


def revision(payload,station_code,label,previous=None,notes=''):
    code=station_code.strip().upper()
    if not re.fullmatch(r'[A-Z0-9_-]{1,20}',code):raise ValueError('Use a station code of letters, digits, underscore or hyphen')
    if previous and previous['station_code']!=code:raise ValueError('A new revision must retain the same station code')
    result=dict(schema_version=SCHEMA,station_code=code,design_label=label.strip(),revision=(previous['revision']+1 if previous else 1),
                parent_hash=previous['content_hash'] if previous else None,created_utc=datetime.now(timezone.utc).isoformat(),notes=notes,payload=payload)
    result['content_hash']=hashlib.sha256(json.dumps(result,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return result


def read_revision(raw):
    result=json.loads(raw)
    if result.get('schema_version')!=SCHEMA:raise ValueError('Unsupported station design schema')
    claimed=result.get('content_hash');body={k:v for k,v in result.items() if k!='content_hash'}
    if claimed!=hashlib.sha256(json.dumps(body,sort_keys=True,allow_nan=False).encode()).hexdigest():raise ValueError('Design hash mismatch: file was modified or corrupted')
    if not isinstance(result.get('revision'),int) or result['revision']<1:raise ValueError('Invalid revision number')
    return result


def monthly_demand(meter):
    """Read kVA or convert kW using per-interval PF; do not invent PF."""
    f=meter.copy();f['timestamp']=pd.to_datetime(f['timestamp'],errors='raise')
    if f.timestamp.duplicated().any():raise ValueError('Duplicate meter timestamps')
    if len(f)<2:raise ValueError('Upload at least two demand intervals')
    f=f.sort_values('timestamp')
    if 'kva' in f: demand=pd.to_numeric(f.kva,errors='raise')
    elif 'kw' in f and 'pf' in f:
        pf=pd.to_numeric(f.pf,errors='raise')
        if not pf.between(.01,1).all():raise ValueError('Meter PF must be positive and <=1')
        demand=pd.to_numeric(f.kw,errors='raise')/pf
    else:raise ValueError('Meter CSV needs timestamp,kva OR timestamp,kw,pf')
    if not np.isfinite(demand).all() or (demand<0).any():raise ValueError('Invalid measured demand')
    gaps=f.timestamp.diff().dropna().dt.total_seconds()/60
    if gaps.max()>60:raise ValueError('Meter data must be interval demand, not sparse monthly readings; gaps exceed one hour')
    f['kva']=demand
    out=f.groupby(f.timestamp.dt.to_period('M'))['kva'].max().rename('Measured peak kVA').reset_index().rename(columns={'timestamp':'Month'})
    out['Month']=out.Month.astype(str)
    coverage=f.groupby(f.timestamp.dt.to_period('M')).size()
    # End/start interval convention is utility-specific: conservative indicative completeness only.
    cadence=float(gaps.median());out['Coverage %']=[min(100.,100*coverage.loc[pd.Period(m)]/(pd.Period(m).days_in_month*1440/cadence)) for m in out.Month]
    out['Meter interval minutes']=cadence
    return out


def contract_options(monthly,current_kva,charge,minimum_fraction,excess_rate,reserve,step=5.,max_kva=1000.):
    """User-defined screening tariff. No claim to implement a specific utility order."""
    peaks=np.asarray(monthly['Measured peak kVA'],float)
    if not len(peaks) or (peaks<0).any() or not np.isfinite(peaks).all():raise ValueError('Invalid monthly demand')
    if current_kva<=0 or charge<0 or not 0<=minimum_fraction<=1 or excess_rate<0 or reserve<0 or step<=0:raise ValueError('Invalid contract/tariff inputs')
    floor=float(peaks.max()*(1+reserve));upper=max(current_kva,math.ceil(floor/step)*step)
    if upper>max_kva:raise ValueError('Contract search exceeds supported limit; increase the configured bound')
    candidates=np.unique(np.append(np.arange(step,upper+step*.1,step),[current_kva,math.ceil(floor/step)*step]))
    rows=[]
    for kva in candidates:
        billed=np.maximum(peaks,kva*minimum_fraction)
        monthly_charge=charge*billed+excess_rate*np.maximum(0,peaks-kva)
        rows.append({'Contract kVA':float(kva),'Observed-period demand charges Rs':float(monthly_charge.sum()),
            'Annualized demand charges Rs':float(monthly_charge.mean()*12),'Months exceeding contract':int((peaks>kva).sum()),'Meets peak plus reserve':bool(kva>=floor)})
    options=pd.DataFrame(rows);feasible=options[options['Meets peak plus reserve']]
    best=feasible.sort_values(['Annualized demand charges Rs','Contract kVA']).iloc[0]
    return options,best,floor
