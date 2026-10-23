"""Generic multi-room cooling and site electricity screening model (hourly)."""
from datetime import datetime, timezone
import json
from urllib.request import urlopen
from urllib.parse import urlencode
import numpy as np
import pandas as pd

ROOM_DEFAULT = dict(Room='Room 1',Length_m=8.,Width_m=5.,Height_m=3.,Window_m2=3.,Door_m2=2.,Equipment_kW=2.,People=0,Occupancy='Always',Target_C=21.,AC_units=3,AC_TR_each=4.)
CIRCUIT_DEFAULT = dict(Load='Room lights',Room='Room 1',Type='Light',Count=4,Watts_each=20.,Schedule='Night')
SCHEDULES=['Always','Daylight','Night','Occupied hours','Off']

def validate_rooms(rooms,circuits):
    if rooms.empty: raise ValueError('Add at least one room')
    if rooms.Room.isna().any() or rooms.Room.astype(str).str.strip().eq('').any() or rooms.Room.duplicated().any():
        raise ValueError('Room names must be nonempty and unique')
    numeric=[c for c in ROOM_DEFAULT if c not in ['Room','Occupancy']]
    vals=rooms[numeric].apply(pd.to_numeric,errors='coerce')
    if not np.isfinite(vals).all().all(): raise ValueError('Every room numeric input must be finite')
    for c in ['Length_m','Width_m','Height_m','AC_TR_each']:
        if (vals[c]<=0).any():raise ValueError(c+' must be positive')
    if (vals[['Window_m2','Door_m2','Equipment_kW','People']]<0).any().any():raise ValueError('Room loads and openings cannot be negative')
    if (vals.AC_units<2).any() or (vals.AC_units%1!=0).any() or (vals.People%1!=0).any():raise ValueError('Use integer people counts and at least two integer AC units for N+1')
    if not vals.Target_C.between(10,35).all():raise ValueError('Room target temperatures must be 10-35 C')
    if not rooms.Occupancy.isin(SCHEDULES).all():raise ValueError('Unknown occupancy schedule')
    walls=2*(vals.Length_m+vals.Width_m)*vals.Height_m
    if ((vals.Window_m2+vals.Door_m2)>walls).any():raise ValueError('Windows plus doors exceed gross wall area')
    if not circuits.empty:
        if not circuits.Room.isin(list(rooms.Room)+['Site exterior']).all():raise ValueError('Each load must reference a room or Site exterior')
        v=circuits[['Count','Watts_each']].apply(pd.to_numeric,errors='coerce')
        if not np.isfinite(v).all().all() or (v<0).any().any() or (v.Count%1!=0).any():raise ValueError('Use nonnegative integer counts and finite watts')
        if not circuits.Schedule.isin(SCHEDULES).all() or not circuits.Type.isin(['Light','Fan','Other']).all():raise ValueError('Unknown load type or schedule')

def weather(latitude,longitude,start_year=None,end_year=None):
    archive=start_year is not None
    if archive and not 1940<=start_year<=end_year<datetime.now(timezone.utc).year:raise ValueError('Choose complete historical years from 1940')
    periods=[(s,min(s+4,end_year)) for s in range(start_year,end_year+1,5)] if archive else [(None,None)]
    frames=[];urls=[]
    for first,last in periods:
        params=dict(latitude=latitude,longitude=longitude,timezone='Asia/Kolkata',hourly='temperature_2m,relative_humidity_2m,shortwave_radiation',daily='sunrise,sunset')
        if archive:params.update(start_date=f'{first}-01-01',end_date=f'{last}-12-31',models='era5')
        else:params['forecast_days']=1
        url=('https://archive-api.open-meteo.com/v1/archive?' if archive else 'https://api.open-meteo.com/v1/forecast?')+urlencode(params)
        with urlopen(url,timeout=90 if archive else 25) as response: data=json.load(response)
        f=pd.DataFrame(data['hourly']);f['time']=pd.to_datetime(f.time)
        d=pd.DataFrame(data['daily']);d['date']=pd.to_datetime(d.time).dt.normalize()
        for c in ['sunrise','sunset']:d[c]=pd.to_datetime(d[c],errors='coerce')
        f['date']=f.time.dt.normalize();f=f.merge(d[['date','sunrise','sunset']],on='date',how='left',validate='many_to_one').drop(columns='date')
        frames.append(f);urls.append(url)
    frame=pd.concat(frames,ignore_index=True)
    if archive:
        expected=pd.date_range(f'{start_year}-01-01',f'{end_year+1}-01-01',freq='h',inclusive='left')
    else:expected=pd.date_range(frame.time.iloc[0].normalize(),periods=24,freq='h')
    if not frame.time.equals(pd.Series(expected)):raise ValueError('Missing, duplicated or unordered weather hours; calculation blocked')
    cols=['temperature_2m','relative_humidity_2m','shortwave_radiation']
    if frame[cols].isna().any().any() or not np.isfinite(frame[cols]).all().all():raise ValueError('Incomplete/nonfinite weather; calculation blocked')
    if not frame.relative_humidity_2m.between(0,100).all() or (frame.shortwave_radiation<0).any():raise ValueError('Weather RH/radiation out of range')
    if frame[['sunrise','sunset']].isna().any().any() or (frame.sunset<=frame.sunrise).any():raise ValueError('Sunrise/sunset unavailable; choose a supported location/date')
    return frame,dict(source='ERA5 via Open-Meteo' if archive else 'Open-Meteo forecast',urls=urls,retrieved_utc=datetime.now(timezone.utc).isoformat(),timezone='Asia/Kolkata')

def schedule(frame,name,opening=8,closing=18):
    # Radiation is preceding-hour mean: all energy bins end at frame.time.
    end=frame.time;start=end-pd.Timedelta(hours=1)
    # At midnight use previous day's sunrise/sunset shifted by one day.
    sunrise=frame.sunrise.where(end.dt.hour!=0,frame.sunrise-pd.Timedelta(days=1))
    sunset=frame.sunset.where(end.dt.hour!=0,frame.sunset-pd.Timedelta(days=1))
    daylight=((pd.concat([end,sunset],axis=1).min(axis=1)-pd.concat([start,sunrise],axis=1).max(axis=1)).dt.total_seconds()/3600).clip(0,1).to_numpy()
    if name=='Always':return np.ones(len(frame))
    if name=='Off':return np.zeros(len(frame))
    if name=='Daylight':return daylight
    if name=='Night':return 1-daylight
    # Integer daily business-hour boundaries; overnight supported, equal = 24h.
    h=(end.dt.hour.to_numpy()-1)%24
    return ((h>=opening)&(h<closing) if opening<closing else ((h>=opening)|(h<closing))).astype(float)

def humidity_ratio(t,r):
    p=610.94*np.exp(17.625*t/(t+243.04))*r
    return .62198*p/(101325-p)

def calculate(frame,rooms,circuits,p):
    validate_rooms(rooms,circuits)
    n=len(frame);t=frame.temperature_2m.to_numpy(float)+p.get('uplift',0)
    rh=frame.relative_humidity_2m.to_numpy(float)/100;ghi=frame.shortwave_radiation.to_numpy(float)
    electrical={k:np.zeros(n) for k in ['Equipment kW','Lights kW','Fans kW','Other kW','AC kW']}
    room_loads={name:np.zeros(n) for name in rooms.Room};room_peak={name:0. for name in rooms.Room}
    for row in circuits.to_dict('records'):
        watts=float(row['Count'])*float(row['Watts_each'])/1000
        power=watts*schedule(frame,row['Schedule'],p['opening'],p['closing'])
        key={'Light':'Lights kW','Fan':'Fans kW','Other':'Other kW'}[row['Type']]
        electrical[key]+=power
        if row['Room'] in room_loads:
            room_loads[row['Room']]+=power;room_peak[row['Room']]+=watts
    summaries=[];component_peaks=[];thermal_total=np.zeros(n)
    for room in rooms.to_dict('records'):
        name=room['Room'];area=room['Length_m']*room['Width_m'];volume=area*room['Height_m']
        wall=2*(room['Length_m']+room['Width_m'])*room['Height_m']-room['Window_m2']-room['Door_m2']
        sp=room['Target_C'];dt=np.maximum(0,t-sp);mdot=1.18*volume*p['ach']/3600
        envelope=(p['roof_u']*area+p['wall_u']*wall+p['window_u']*room['Window_m2']+p['door_u']*room['Door_m2'])*dt/1000
        solar=ghi*(p['roof_solar']*area+.0192*wall+room['Window_m2']*p['shgc'])/1000
        sensible=mdot*1.006*dt
        latent=np.maximum(0,mdot*2501*(humidity_ratio(t,rh)-humidity_ratio(sp,p['indoor_rh']/100)))
        occupancy=schedule(frame,room['Occupancy'],p['opening'],p['closing'])
        people=room['People']*(p['person_sensible']+p['person_latent'])/1000
        equipment=np.full(n,room['Equipment_kW'])
        total=envelope+solar+sensible+latent+equipment+people*occupancy+room_loads[name]
        # Capacity selection assumes full stated occupancy and all connected in-room loads.
        design=envelope+solar+sensible+latent+equipment+people+room_peak[name]
        idx=int(np.argmax(design));required=float(design[idx])*(1+p['margin']/100)
        available=room['AC_TR_each']*3.517*p['derating']*(room['AC_units']-1)
        cop=np.maximum(1.,p['cop']-p['cop_slope']*np.maximum(0,t-35))
        electrical['Equipment kW']+=equipment;electrical['AC kW']+=total/cop
        thermal_total+=total
        summaries.append({'Room':name,'Design cooling kW':required,'Nominal TR needed/unit':required/((room['AC_units']-1)*3.517*p['derating']),
            'Largest-unit-out kW':available,'N+1': 'PASS' if available>=required else 'FAIL',
            'Governing hour IST':str(frame.time.iloc[idx]),'Dry bulb C':t[idx],'RH %':rh[idx]*100,'GHI W/m2':ghi[idx]})
        for source,value in [('Envelope',envelope[idx]),('Solar',solar[idx]),('Infiltration sensible',sensible[idx]),('Infiltration latent',latent[idx]),('Equipment',equipment[idx]),('People sensible',room['People']*p['person_sensible']/1000),('People latent',room['People']*p['person_latent']/1000),('Lights/fans/other',room_peak[name])]:
            component_peaks.append({'Room':name,'Source':source,'Governing heat kW':value})
    result=pd.DataFrame(electrical);result.insert(0,'Time IST',frame.time)
    result['Thermal cooling kW']=thermal_total;result['Total demand kW']=sum(electrical.values())
    result['GHI W/m2']=ghi;result['Ambient C']=t
    return pd.DataFrame(summaries),result,pd.DataFrame(component_peaks)

def economics(hourly,capacity,p,annual_years):
    demand=hourly['Total demand kW'].to_numpy();solar=capacity*hourly['GHI W/m2'].to_numpy()/1000*p['pv_pr']
    imports=np.maximum(0,demand-solar);exports=np.maximum(0,solar-demand)
    h=(pd.to_datetime(hourly['Time IST']).dt.hour.to_numpy()-1)%24
    mask=(h>=p['peak_start'])&(h<p['peak_end']) if p['peak_start']<p['peak_end'] else ((h>=p['peak_start'])|(h<p['peak_end']))
    tariff=np.where(mask,p['peak_tariff'],p['tariff'])
    baseline=float((demand*tariff).sum()/annual_years)
    bill=float((imports*tariff-exports*p['export_tariff']).sum()/annual_years)
    capex=capacity*p['pv_capex'];om=capex*p['om']/100
    # Constant-real tariffs, no degradation; explicitly a screening NPV.
    factor=sum((1+p['discount']/100)**(-y) for y in range(1,p['life']+1))
    return dict(capacity_kwp=capacity,annual_bill=bill,annual_saving=baseline-bill,
        grid_kwh=float(imports.sum()/annual_years),export_kwh=float(exports.sum()/annual_years),
        pv_kwh=float(solar.sum()/annual_years),npv=(baseline-bill-om)*factor-capex,
        life_cycle_cost=capex+(bill+om)*factor,capex=capex),solar,imports,exports

def optimize_pv(hourly,max_kwp,p,annual_years):
    candidates=np.unique(np.append(np.arange(0,max_kwp,.5),max_kwp))
    rows=[economics(hourly,float(k),p,annual_years)[0] for k in candidates]
    df=pd.DataFrame(rows)
    return df,df.loc[df.life_cycle_cost.idxmin()]
