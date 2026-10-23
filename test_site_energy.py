import numpy as np
import pandas as pd
from site_energy import ROOM_DEFAULT,calculate,schedule,economics,optimize_pv

def fixture():
 t=pd.date_range('2025-01-01',periods=48,freq='h')
 f=pd.DataFrame({'time':t,'temperature_2m':30.,'relative_humidity_2m':50.,'shortwave_radiation':np.tile([0]*7+[500]*11+[0]*6,2)})
 f['sunrise']=f.time.dt.normalize()+pd.Timedelta(hours=6,minutes=30)
 f['sunset']=f.time.dt.normalize()+pd.Timedelta(hours=18,minutes=30)
 return f

def params():
 return dict(opening=8,closing=18,roof_u=2.5,wall_u=1.8,window_u=5.7,door_u=3.,roof_solar=.15,shgc=.75,ach=.35,indoor_rh=50,person_sensible=75.,person_latent=55.,margin=15.,derating=.85,cop=3.5,cop_slope=.025,uplift=0,peak_start=18,peak_end=22,peak_tariff=10,tariff=8,export_tariff=2,pv_pr=.78,pv_capex=50000,om=1,discount=8,life=20)

def test_sunrise_schedule_fraction_and_night_complement():
 f=fixture();d=schedule(f,'Daylight');n=schedule(f,'Night')
 assert d[7]==.5 and d[19]==.5 and d.sum()==24
 assert np.allclose(d+n,1)

def test_people_and_circuit_heat_and_no_electric_double_count():
 f=fixture();r=pd.DataFrame([ROOM_DEFAULT]);cir=pd.DataFrame(columns=['Room','Count','Watts_each','Type','Schedule'])
 _,base,_=calculate(f,r,cir,params())
 r['People']=2
 c=pd.DataFrame([dict(Room='Room 1',Count=1,Watts_each=100.,Type='Light',Schedule='Always')])
 _,out,_=calculate(f,r,c,params())
 assert np.allclose(out['Thermal cooling kW']-base['Thermal cooling kW'],.36)
 assert np.allclose(out['Total demand kW']-base['Total demand kW'],.1+.36/3.5)
 c['Room']='Site exterior'
 _,outside,_=calculate(f,r,c,params())
 assert np.allclose(outside['Thermal cooling kW']-base['Thermal cooling kW'],.26)
 assert np.allclose(outside['Lights kW'],.1)

def test_rooms_add_and_energy_conservation_and_zero_pv():
 f=fixture();r=pd.DataFrame([ROOM_DEFAULT,dict(ROOM_DEFAULT,Room='Room 2')]);cir=pd.DataFrame(columns=['Room','Count','Watts_each','Type','Schedule'])
 _,h,_=calculate(f,r,cir,params());_,one,_=calculate(f,r.iloc[:1],cir,params())
 assert np.allclose(h['Total demand kW'],2*one['Total demand kW'])
 cost,pv,imp,exp=economics(h,8,params(),2)
 assert np.allclose(h['Total demand kW']+exp,pv+imp)
 costs,best=optimize_pv(h,0,params(),2)
 assert best.capacity_kwp==0 and best.npv==0

def test_geometry_rejected():
 import pytest
 r=pd.DataFrame([dict(ROOM_DEFAULT,Window_m2=10000)])
 with pytest.raises(ValueError,match='exceed'):calculate(fixture(),r,pd.DataFrame(),params())

def test_generic_ui_exports_with_cached_weather():
 from datetime import datetime
 from pathlib import Path
 from streamlit.testing.v1 import AppTest
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 assert not at.exception
 last=datetime.now().year-1
 at.session_state['site_weather']=((18.872,79.444,last-29,last,'Historical extreme design + annual energy'),fixture(),{'source':'controlled test fixture','urls':[],'retrieved_utc':'test'})
 at.run(timeout=60)
 assert not at.exception,list(at.exception)
 assert len(at.metric)==4
 assert len(at.get('download_button'))==3
