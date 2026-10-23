"""Aggregate daily EV charging windows, with explicit served/unserved energy."""
import numpy as np
import pandas as pd

EV_DEFAULTS=[dict(Group='AC destination',Points=0,Grid_kW_per_point=7.4,Efficiency=.90,Vehicles_per_day=0,Battery_kWh_per_vehicle=20.,Start_hour=8,End_hour=18),
             dict(Group='DC fast (~60 kW delivered)',Points=0,Grid_kW_per_point=64.,Efficiency=.94,Vehicles_per_day=0,Battery_kWh_per_vehicle=30.,Start_hour=0,End_hour=0)]

def charging_profile(hourly,groups,reference_pv_kwp,p,managed=False,site_import_ceiling_kw=100.):
    numeric=['Points','Grid_kW_per_point','Efficiency','Vehicles_per_day','Battery_kWh_per_vehicle','Start_hour','End_hour']
    if groups.empty:return np.zeros(len(hourly)),pd.DataFrame(),0.
    vals=groups[numeric].apply(pd.to_numeric,errors='coerce')
    if not np.isfinite(vals).all().all():raise ValueError('EV inputs must be finite numbers')
    if (vals[['Points','Vehicles_per_day','Battery_kWh_per_vehicle']]<0).any().any():raise ValueError('EV counts and energy must be nonnegative')
    if (vals.Grid_kW_per_point<=0).any() or not vals.Efficiency.between(.01,1).all():raise ValueError('EV output power must be positive and efficiency in 0-1')
    for col in ['Points','Vehicles_per_day','Start_hour','End_hour']:
        if (vals[col]%1!=0).any():raise ValueError('EV counts and window hours must be integers')
    if not vals[['Start_hour','End_hour']].apply(lambda c:c.between(0,23)).all().all():raise ValueError('EV hours must be 0-23')
    if site_import_ceiling_kw<0:raise ValueError('Import ceiling must be nonnegative')
    times=pd.to_datetime(hourly['Time IST']);hours=(times.dt.hour.to_numpy()-1)%24
    base=hourly['Total demand kW'].to_numpy(float);solar=reference_pv_kwp*hourly['GHI W/m2'].to_numpy(float)/1000*p['pv_pr']
    mask=(hours>=p['peak_start'])&(hours<p['peak_end']) if p['peak_start']<p['peak_end'] else ((hours>=p['peak_start'])|(hours<p['peak_end']))
    rates=np.where(mask,p['peak_tariff'],p['tariff'])
    grouped=pd.Series(np.arange(len(times))).groupby(times.dt.normalize().to_numpy()).apply(list)
    ev=np.zeros(len(base));summaries=[];connected=0.
    for row in groups.to_dict('records'):
        power=float(row['Points'])*float(row['Grid_kW_per_point']);connected+=power
        daily=float(row['Vehicles_per_day'])*float(row['Battery_kWh_per_vehicle'])/float(row['Efficiency'])
        start=int(row['Start_hour']);end=int(row['End_hour']);required=served=0.
        for indices in (grouped if daily>0 else []):
            ids=np.asarray(indices);h=hours[ids]
            allowed=((h>=start)&(h<end)) if start<end else (((h>=start)|(h<end)) if start>end else np.ones(len(h),bool))
            required+=daily;remaining=daily
            cells=ids[allowed]
            if not managed:
                cells=cells[np.argsort((hours[cells]-start)%24)]
                for i in cells:
                    take=min(remaining,power);ev[i]+=take;remaining-=take
                    if remaining<=1e-9:break
            else:
                segments=[]
                for i in cells:
                    current=base[i]+ev[i];spare=max(0.,solar[i]-current)
                    cap=min(power,max(0.,site_import_ceiling_kw+solar[i]-current))
                    solar_part=min(cap,spare)
                    if solar_part>0:segments.append((p['export_tariff'],(hours[i]-start)%24,i,solar_part))
                    if cap>solar_part:segments.append((rates[i],(hours[i]-start)%24,i,cap-solar_part))
                for price,order,i,capacity in sorted(segments):
                    take=min(remaining,capacity);ev[i]+=take;remaining-=take
                    if remaining<=1e-9:break
            served+=daily-max(0.,remaining)
        summaries.append({'Group':row['Group'],'Points':row['Points'],'Connected grid kW':power,'Requested battery kWh/day':daily*float(row['Efficiency']),
                          'Requested grid kWh (period)':required,'Served grid kWh (period)':served,'Unserved battery kWh (period)':max(0,required-served)*float(row['Efficiency'])})
    return ev,pd.DataFrame(summaries),connected
