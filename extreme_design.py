"""Historical coincident-load screening and largest-unit-out capacity checks."""
import json
from urllib.request import urlopen
from urllib.parse import urlencode
import numpy as np
import pandas as pd


def fetch_history(latitude, longitude, start_year, end_year):
    if not 1940 <= start_year <= end_year:
        raise ValueError('Invalid historical years')
    frames=[]; urls=[]
    for first in range(start_year,end_year+1,5):
        last=min(first+4,end_year)
        params=dict(latitude=latitude,longitude=longitude,start_date=f'{first}-01-01',
                    end_date=f'{last}-12-31',models='era5',timezone='Asia/Kolkata',
                    hourly='temperature_2m,relative_humidity_2m,shortwave_radiation')
        url='https://archive-api.open-meteo.com/v1/archive?'+urlencode(params)
        with urlopen(url,timeout=90) as response: data=json.load(response)
        frames.append(pd.DataFrame(data['hourly'])); urls.append(url)
    frame=pd.concat(frames,ignore_index=True)
    frame['time']=pd.to_datetime(frame['time'])
    expected=pd.date_range(f'{start_year}-01-01',f'{end_year+1}-01-01',freq='h',inclusive='left')
    if frame.time.duplicated().any() or not frame.time.equals(pd.Series(expected)):
        raise ValueError('Historical timestamps incomplete or duplicated; sizing blocked')
    values=frame[['temperature_2m','relative_humidity_2m','shortwave_radiation']]
    if values.isna().any().any() or not np.isfinite(values).all().all():
        raise ValueError('Historical data contain missing/nonfinite hours; sizing blocked')
    if not frame.relative_humidity_2m.between(0,100).all() or (frame.shortwave_radiation<0).any():
        raise ValueError('Invalid historical humidity or radiation')
    return frame,urls


def design_analysis(frame, load, indoor, margin, uplift, leakage_factor):
    # Keep T, RH and radiation from the same hour. Stress uplift is explicit.
    t=frame.temperature_2m.to_numpy(dtype=float)+uplift
    rh=frame.relative_humidity_2m.to_numpy(dtype=float)/100
    ghi=frame.shortwave_radiation.to_numpy(dtype=float)
    terms=load(t,rh,ghi,setpoint=indoor,air=leakage_factor)
    components=pd.DataFrame({k:np.broadcast_to(v,len(frame)) for k,v in terms.items()})
    total=components.sum(axis=1)
    idx=int(np.argmax(total.to_numpy()))
    annual=pd.DataFrame({'Year':frame.time.dt.year,'Heat load kW':total,'Dry bulb C':t}).groupby('Year').max().reset_index()
    return dict(required_kw=float(total.iloc[idx])*(1+margin/100),raw_peak_kw=float(total.iloc[idx]),
                governing_hour=str(frame.time.iloc[idx]),governing_temperature=float(t[idx]),
                governing_rh=float(rh[idx]*100),governing_ghi=float(ghi[idx]),
                components=components.iloc[idx],annual=annual,
                percentiles=pd.DataFrame({'Exceedance %':[0.4,1.,2.],
                'Dry bulb C':np.quantile(t,[.996,.99,.98]),
                'Coincident total load percentile kW':np.quantile(total,[.996,.99,.98])}))


def redundancy(required_kw, capacities_tr, derating):
    capacities=np.asarray(capacities_tr,dtype=float)*3.517*derating
    if required_kw<=0 or not 0<derating<=1 or len(capacities)<2 or (capacities<=0).any():
        raise ValueError('Invalid capacity or derating')
    surviving=float(capacities.sum()-capacities.max())
    return dict(surviving_kw=surviving,pass_n_plus_one=bool(surviving>=required_kw),
                reserve_kw=surviving-required_kw,installed_tr=float(np.sum(capacities_tr)))
