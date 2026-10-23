import numpy as np
import pandas as pd
import pytest
from ev_charging import charging_profile,EV_DEFAULTS
from test_site_energy import fixture,params

def inputs():
 f=fixture();return pd.DataFrame({'Time IST':f.time,'Total demand kW':10.,'GHI W/m2':f.shortwave_radiation})

def test_ev_energy_losses_points_and_unserved():
 g=pd.DataFrame([dict(EV_DEFAULTS[0],Points=2,Grid_kW_per_point=10.,Efficiency=.8,Vehicles_per_day=2,Battery_kWh_per_vehicle=20.,Start_hour=8,End_hour=11)])
 ev,s,k=charging_profile(inputs(),g,0,params())
 assert np.isclose(ev.sum(),100.) and ev.max()<=20. and k==20.
 assert s['Unserved battery kWh (period)'].sum()==0
 g.loc[0,'Points']=0
 ev,s,_=charging_profile(inputs(),g,0,params())
 assert ev.sum()==0 and s['Unserved battery kWh (period)'].sum()==80.

def test_managed_ceiling_and_conservation():
 g=pd.DataFrame([dict(EV_DEFAULTS[1],Points=1,Grid_kW_per_point=20.,Efficiency=1.,Vehicles_per_day=1,Battery_kWh_per_vehicle=20.)])
 ev,s,_=charging_profile(inputs(),g,0,params(),True,15.)
 assert ev.max()<=5. and np.isclose(ev.sum(),40.)
 assert s['Unserved battery kWh (period)'].sum()==0
 ev,s,_=charging_profile(inputs(),g,0,params(),True,10.)
 assert ev.sum()==0 and s['Unserved battery kWh (period)'].sum()==40.

def test_ev_zero_and_invalid():
 ev,s,k=charging_profile(inputs(),pd.DataFrame(EV_DEFAULTS),0,params())
 assert ev.sum()==0 and k==0
 bad=pd.DataFrame([dict(EV_DEFAULTS[0],Efficiency=0.)])
 with pytest.raises(ValueError):charging_profile(inputs(),bad,0,params())

def test_ev_ui_with_cached_weather_and_revision():
 from pathlib import Path
 from datetime import datetime
 from streamlit.testing.v1 import AppTest
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 g=dict(EV_DEFAULTS[1],Points=2,Vehicles_per_day=10)
 at.session_state['restored_payload']={'ev_settings':{'groups':[g]}}
 at.session_state['restore_epoch']=1
 last=datetime.now().year-1
 f=fixture();at.session_state['site_weather']=((18.872,79.444,last-29,last,'Historical extreme design + annual energy'),f,{'source':'controlled fixture','urls':[],'retrieved_utc':'test'})
 at.run(timeout=60)
 assert not at.exception,[e.value for e in at.exception]
 ev_table=next(df.value for df in at.dataframe if 'Unserved battery kWh (period)' in df.value.columns)
 assert ev_table['Connected grid kW'].sum()==128.
 assert ev_table['Unserved battery kWh (period)'].sum()==0
 next(x for x in at.button if x.label=='Create station design revision').click().run()
 assert at.session_state['download_revision']['payload']['ev_settings']['groups'][0]['Points']==2
