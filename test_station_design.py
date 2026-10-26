import json
import numpy as np
import pandas as pd
import pytest
from station_design import running_room,revision,read_revision,monthly_demand,contract_options
from site_energy import calculate
from test_site_energy import fixture,params

def test_running_room_building_and_peak_occupancy():
 r,c=running_room(10,2,16)
 beds=r[r.Zone_type=='Bedroom']
 assert len(beds)==10 and np.isclose((beds.People*beds.Occupancy_fraction).sum(),16)
 assert {'Kitchen','Dining hall','Lobby / reception','Baths / toilets','Laundry / services','Corridors'}.issubset(set(r.Room))
 s,h,_=calculate(fixture(),r,c,params())
 assert (s[s.Room=='Kitchen']['N+1']=='Not conditioned').all()
 assert np.isfinite(h['Total demand kW']).all()
 with pytest.raises(ValueError):running_room(2,2,5)

def test_revision_chain_and_integrity():
 r1=revision({'rooms':[]},'MCI','Running room')
 r2=revision({'rooms':[1]},'MCI','Running room',r1)
 assert r2['revision']==2 and r2['parent_hash']==r1['content_hash']
 assert read_revision(json.dumps(r2))==r2
 r2['payload']['rooms']=[2]
 with pytest.raises(ValueError):read_revision(json.dumps(r2))
 with pytest.raises(ValueError):revision({},'SC','Other',r1)

def test_meter_conversion_contract_reserve_and_charges():
 meter=pd.DataFrame({'timestamp':pd.date_range('2025-01-01',periods=96,freq='15min'),'kw':80.,'pf':.8})
 m=monthly_demand(meter);assert m['Measured peak kVA'].iloc[0]==100
 opts,best,floor=contract_options(m,200,300,.8,600,.1)
 assert np.isclose(floor,110) and best['Contract kVA']>=floor
 assert best['Annualized demand charges Rs']<opts[opts['Contract kVA']==200]['Annualized demand charges Rs'].iloc[0]
 assert m['Coverage %'].iloc[0]<100
 with pytest.raises(ValueError):monthly_demand(pd.concat([meter,meter.iloc[:1]]))

def test_running_program_updates_peak_allocation_in_ui():
 from streamlit.testing.v1 import AppTest
 from pathlib import Path
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 next(x for x in at.selectbox if x.label=='Facility design template').set_value('Running room')
 next(x for x in at.button if x.label=='Apply template - replace rooms and circuits').click().run()
 next(x for x in at.number_input if x.label=='Peak guests present').set_value(16).run()
 assert not at.exception
 settings=at.dataframe[1].value
 assert np.isclose(settings[settings.Zone_type=='Bedroom'].Occupancy_fraction.mean(),.8)
 next(x for x in at.button if x.label=='Create station design revision').click().run()
 assert not at.exception
 saved=at.session_state['download_revision']
 assert saved['revision']==1 and saved['payload']['running_room_program']['guests']==16

def test_battery_does_not_supply_free_initial_energy():
 from facility_design import battery_dispatch
 h=pd.DataFrame({'Total demand kW':[10.,10.],'GHI W/m2':[0.,0.]})
 d=battery_dispatch(h,0,20,10)
 assert np.allclose(d['Grid import kW'],10.)

def test_running_guest_pool_not_double_counted():
 r,c=running_room(10,2,16)
 p=params();p.update(running_peak_guests=16,sleeping_profile=[1.]*24)
 _,h,_=calculate(fixture(),r,c,p)
 assert np.allclose(h['Guests accounted for'],16)

def test_restored_tariff_replaces_unsaved_widget_value():
 from streamlit.testing.v1 import AppTest
 from pathlib import Path
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 next(x for x in at.number_input if x.label=='Base import Rs/kWh').set_value(17.).run()
 at.session_state['restored_payload']={'assumptions':{'tariff':8.},'code':'SC','station':'Secunderabad'}
 at.session_state['restore_epoch']=1
 at.run()
 assert not at.exception
 assert next(x for x in at.number_input if x.label=='Base import Rs/kWh').value==8.
 assert next(x for x in at.text_input if x.label=='Station code').value=='SC'


def test_missing_meter_timestamps_never_understate_monthly_peak():
 meter=pd.DataFrame({'timestamp':pd.date_range('2025-01-01',periods=3,freq='15min'),'kva':[80.,99.,90.]})
 assert monthly_demand(meter)['Measured peak kVA'].iloc[0]==99.
 for bad in [None,pd.NaT,'']:
  damaged=meter.copy()
  damaged.loc[1,'timestamp']=bad
  with pytest.raises(ValueError,match='timestamp'):
   monthly_demand(damaged)

def test_running_sleeping_profile_conserves_guests_and_exposes_overflow():
 rooms,circuits=running_room(10,2,16)
 for fraction in [0.,.5,1.]:
  p=params();p.update(running_peak_guests=16,sleeping_profile=[fraction]*24)
  _,hourly,_=calculate(fixture(),rooms,circuits,p)
  assert np.allclose(hourly['Guests accounted for'],16.)
  assert (hourly['Guests requiring bedroom overflow']>=0).all()
  if fraction==0.:
   assert hourly['Guests requiring bedroom overflow'].max()>0.
  if fraction==1.:
   assert np.allclose(hourly['Guests requiring bedroom overflow'],0.)
