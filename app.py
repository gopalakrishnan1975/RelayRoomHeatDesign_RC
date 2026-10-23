import json
from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from site_energy import ROOM_DEFAULT,CIRCUIT_DEFAULT,SCHEDULES,weather,calculate,optimize_pv,economics
from facility_design import TEMPLATES,template_data,transformer_design,battery_dispatch
from station_design import running_room,revision,read_revision,monthly_demand,contract_options
from ev_charging import EV_DEFAULTS,charging_profile

st.set_page_config(page_title='Railway Facility Energy Design Studio',layout='wide')
st.title('Railway Facility Energy Design Studio')
st.caption('Generic rooms, historical extreme AC sizing with N+1, whole-site electricity and solar cost screening.')
mode=st.selectbox('Calculator',['Generic multi-room planner','Previous relay-room simulator'])
if mode=='Previous relay-room simulator':
 import runpy
 runpy.run_path('legacy_app.py',run_name='__main__')
 st.stop()

def number_input(label,*args,**kwargs):
 kwargs['key']=str(kwargs.get('key',label))+'_restore_'+str(st.session_state.get('restore_epoch',0))
 return st.number_input(label,*args,**kwargs)
def text_input(label,*args,**kwargs):
 kwargs['key']=str(kwargs.get('key',label))+'_restore_'+str(st.session_state.get('restore_epoch',0))
 return st.text_input(label,*args,**kwargs)

def col_input(column,label,*args,**kwargs):
 kwargs['key']=str(kwargs.get('key',label))+'_restore_'+str(st.session_state.get('restore_epoch',0))
 return column.number_input(label,*args,**kwargs)
def col_text(column,label,*args,**kwargs):
 kwargs['key']=str(kwargs.get('key',label))+'_restore_'+str(st.session_state.get('restore_epoch',0))
 return column.text_input(label,*args,**kwargs)

st.subheader('Station-specific design versions')
st.caption('Each revision has a station code, revision number, parent hash and all inputs. Download it to your station folder/OneDrive and upload it here to revise later. Streamlit session storage is temporary; files are not automatically written to a central registry.')
version_file=st.file_uploader('Load a saved station design revision JSON',type=['json'])
if st.button('Restore station design'):
 try:
  if version_file is None:raise ValueError('Select a saved revision file first')
  restored=read_revision(version_file.getvalue())
  if not isinstance(restored.get('payload'),dict) or not all(k in restored['payload'] for k in ['rooms','circuits','station','code','assumptions']):raise ValueError('Design payload is incomplete')
  st.session_state['restored_payload']=restored['payload'];st.session_state['parent_revision']=restored
  st.session_state['program_applied']=restored['payload'].get('running_room_program',{})
  st.session_state['restore_epoch']=st.session_state.get('restore_epoch',0)+1
  st.session_state['active_template']=restored['payload'].get('facility_template','Custom / blank')
  st.session_state['template_version']=st.session_state.get('template_version',0)+1
  st.session_state.pop('saved_room_settings',None)
  for k in restored['payload'].get('assumptions',{}):st.session_state.pop(k,None)
  st.rerun()
 except Exception as exc:st.error('Restore failed: '+str(exc))
loaded=st.session_state.get('restored_payload',{})

st.subheader('1. Station and weather basis')
a,b,c,d=st.columns(4)
station=col_text(a,'Station / site name',loaded.get('station','Mancherial'));code=col_text(b,'Station code',loaded.get('code','MCI'))
latitude=col_input(c,'Latitude',-90.,90.,loaded.get('latitude',18.872),format='%.5f');longitude=col_input(d,'Longitude',-180.,180.,loaded.get('longitude',79.444),format='%.5f')
st.caption('Changing name/code does not change coordinates. Current scheduling timezone is Asia/Kolkata (India).')
basis=st.radio('Analysis basis',['Historical extreme design + annual energy','Forecast day (operations only)'],horizontal=True,key='basis_'+str(st.session_state.get('restore_epoch',0)),index=0 if loaded.get('basis','Historical').startswith('Historical') else 1)
last_year=datetime.now(timezone.utc).year-1
first,last=st.columns(2)
start_year=int(col_input(first,'Historical start year',1940,last_year,loaded.get('start_year',last_year-29)))
end_year=int(col_input(last,'Historical end year',1940,last_year,loaded.get('end_year',last_year)))
key=(latitude,longitude,start_year,end_year,basis)
@st.cache_data(ttl=86400,show_spinner=False)
def cached_weather(lat,lon,first,last,basis):
 return weather(lat,lon,first,last) if basis.startswith('Historical') else weather(lat,lon)
if st.button('Load weather and sunrise/sunset'):
 try:
  with st.spinner('Loading complete hourly weather and daily sunrise/sunset...'):
   st.session_state['site_weather']=(key,*cached_weather(*key))
 except Exception as exc:
  st.session_state.pop('site_weather',None);st.error(str(exc))

st.subheader('2. Facility templates and room essentials')
template=st.selectbox('Facility design template',list(TEMPLATES),index=list(TEMPLATES).index(st.session_state.get('active_template','Custom / blank')))
if st.button('Apply template - replace rooms and circuits'):
 st.session_state['active_template']=template
 st.session_state.pop('restored_payload',None)
 st.session_state['template_version']=st.session_state.get('template_version',0)+1
 st.session_state.pop('saved_room_settings',None)
 st.rerun()
base,template_circuits=template_data(st.session_state.get('active_template','Custom / blank'))
program=loaded.get('running_room_program',{})
if st.session_state.get('active_template')=='Running room':
 st.subheader('Running-room building programme - bedrooms and common services')
 a,b,c=st.columns(3)
 bedrooms=int(col_input(a,'Number of bedrooms',1,200,int(program.get('bedrooms',10))))
 beds=int(col_input(b,'Beds per bedroom',1,10,int(program.get('beds',2))))
 guests=int(col_input(c,'Peak guests present',0,bedrooms*beds,min(int(program.get('guests',20)),bedrooms*beds)))
 a,b,c,d=st.columns(4)
 staff=int(col_input(a,'Peak staff',0,100,int(program.get('staff',4))))
 cooking=col_input(b,'Connected cooking appliances kW',min_value=0.,value=float(program.get('cooking',12.)))
 waterheat=col_input(c,'Connected water heating kW',min_value=0.,value=float(program.get('waterheat',10.)))
 laundry=col_input(d,'Connected laundry kW',min_value=0.,value=float(program.get('laundry',3.)))
 program=dict(bedrooms=bedrooms,beds=beds,guests=guests,staff=staff,cooking=cooking,waterheat=waterheat,laundry=laundry)
 if st.session_state.get('program_applied')!=program:
  st.session_state['program_applied']=program
  st.session_state.pop('saved_room_settings',None)
  st.session_state['template_version']=st.session_state.get('template_version',0)+1
  loaded.pop('rooms',None);loaded.pop('circuits',None)
 st.caption('Changing the building programme regenerates room and circuit rows; review any manual zone edits again.')
 base,template_circuits=running_room(bedrooms,beds,guests,staff,cooking,waterheat,laundry)
 st.caption(f'Bed capacity {bedrooms*beds}; peak guests {guests}. Bedrooms are sized at full permitted occupancy; energy uses {guests/(bedrooms*beds):.0%} of bed capacity at peak. For operating energy, guests assigned to dining/lobby/baths are removed from the bedroom pool; a person is not counted in two zones. Capacity design still checks full stated zone occupancy. Kitchen, baths, laundry and corridors start unconditioned; edit if required. Meal hours: 06-09, 12-15, 19-22 IST. Cooking and exhaust are scheduled; refrigeration is continuous.')
if loaded.get('rooms'):
 base=pd.DataFrame(loaded['rooms']);template_circuits=pd.DataFrame(loaded['circuits'])

st.caption('Templates are editable examples. A running room is a multi-zone accommodation building, not one large room. Non-conditioned zones contribute their equipment and circuit electricity without an artificial AC load.')
st.caption('Conditioned rooms have AC operating continuously. Equipment is continuous electrical input assumed to become room heat. People is the maximum simultaneous count. Add/delete rows as needed; window and door sizes are TOTAL areas in square metres.')
essential=['Room','Length_m','Width_m','Height_m','Window_m2','Door_m2','Equipment_kW','People']
rooms_basic=st.data_editor(base[essential],num_rows='dynamic',hide_index=True,key=f"rooms_{st.session_state.get('template_version',0)}",width='stretch',
 column_config={'People':st.column_config.NumberColumn(min_value=0,step=1),'Room':st.column_config.TextColumn(required=True)})
if rooms_basic.empty:
 st.info('Add at least one room to continue.');st.stop()
st.subheader('3. Room temperature, occupancy and AC configuration')
st.caption('Target_C is the room/critical-equipment upper temperature used for sizing. AC_units includes the standby unit. Set approved limits for each room; 21 C is only the relay-room starting example.')
saved_settings=st.session_state.get('saved_room_settings',{})
template_settings={row['Room']:row for row in base.to_dict('records')}
settings=pd.DataFrame([dict({'Room':r,'Target_C':21.,'Occupancy':'Always','AC_units':3,'AC_TR_each':4.,'AC_enabled':True,'Zone_type':'Generic','Occupancy_fraction':1.},**({k:v for k,v in template_settings.get(r,{}).items() if k not in essential or k=='Room'}|saved_settings.get(r,{}))) for r in rooms_basic.Room.dropna()])
settings=st.data_editor(settings,hide_index=True,disabled=['Room'],key=f"room_settings_{st.session_state.get('template_version',0)}",width='stretch',
 column_config={'Occupancy':st.column_config.SelectboxColumn(options=SCHEDULES,required=True),'AC_units':st.column_config.NumberColumn(min_value=2,step=1)})
st.session_state['saved_room_settings']={row['Room']:row for row in settings.to_dict('records')}
rooms=rooms_basic.merge(settings,on='Room',how='left')
st.subheader('4. Fans, lights and additional electrical loads')
st.caption('Assign each circuit to its room so its heat is included there. Use Site exterior for outdoor lighting or loads outside conditioned rooms. Enter each load only once; do not repeat it in Equipment_kW.')
circuits=st.data_editor((template_circuits if not template_circuits.empty else pd.DataFrame([CIRCUIT_DEFAULT,dict(Load='Room fans',Room='Room 1',Type='Fan',Count=2,Watts_each=60.,Schedule='Occupied hours')])),num_rows='dynamic',hide_index=True,key=f"circuits_{st.session_state.get('template_version',0)}",width='stretch',
 column_config={'Room':st.column_config.SelectboxColumn(options=list(rooms_basic.Room.dropna())+['Site exterior'],required=True),
 'Type':st.column_config.SelectboxColumn(options=['Light','Fan','Other'],required=True),
 'Schedule':st.column_config.SelectboxColumn(options=SCHEDULES,required=True),
 'Count':st.column_config.NumberColumn(min_value=0,step=1),'Watts_each':st.column_config.NumberColumn(min_value=0.)})
a,b=st.columns(2)
opening=int(col_input(a,'Occupied hours start (IST, 0-23)',0,23,int(loaded.get('assumptions',{}).get('opening',8))));closing=int(col_input(b,'Occupied hours end (IST, 0-23)',0,23,int(loaded.get('assumptions',{}).get('closing',18))))
st.caption('Night means sunset to sunrise. Daylight means sunrise to sunset. Occupied hours uses these daily clock hours; equal start/end means 24 hours. AC remains on outside occupancy hours.')

p=dict(opening=opening,closing=closing)
if st.session_state.get('active_template')=='Running room':
 p['running_peak_guests']=program['guests']
 with st.expander('Hourly sleeping occupancy as fraction of peak guests'):
  profile=st.data_editor(pd.DataFrame({'Hour start IST':range(24),'Fraction of peak':loaded.get('assumptions',{}).get('sleeping_profile',[1.]*24)}),hide_index=True,disabled=['Hour start IST'],key=f"sleep_profile_{st.session_state.get('template_version',0)}")
  p['sleeping_profile']=profile['Fraction of peak'].tolist()
with st.expander('Engineering assumptions - review before equipment selection',expanded=False):
 st.caption('Shared envelope defaults apply to every room. No inter-room heat transfer, orientation-specific wall model or CFD. Room heat balance is a preliminary screening model.')
 for label,keyp,value in [('Roof U W/m2K','roof_u',2.5),('Wall U W/m2K','wall_u',1.8),('Window U W/m2K','window_u',5.7),('Door U W/m2K','door_u',3.),('Window solar heat gain coefficient','shgc',.75),('Effective roof solar gain factor','roof_solar',.15),('Air changes/hour','ach',.35),('Indoor RH %','indoor_rh',50.),('Sensible heat/person W','person_sensible',75.),('Latent heat/person W','person_latent',55.),('Design load allowance %','margin',15.),('AC available capacity fraction at extreme ambient','derating',.85),('AC COP at outdoor <=35 C','cop',3.5),('COP reduction per C above 35','cop_slope',.025),('Outdoor temperature stress uplift C','uplift',0.)]:
  p[keyp]=number_input(label,min_value=0.0,value=float(loaded.get('assumptions',{}).get(keyp,value)),key=keyp)
 st.caption('0.85 derating and COP curve are editable assumptions, not manufacturer certification. Full people and all connected in-room circuits are assumed for capacity design, regardless of operating schedule. Historical weather variables remain coincident; optional stress uplift holds RH constant.')

st.subheader('5. Solar, transformer and optional BESS')
t1,t2,t3=st.columns(3)
power_factor=col_input(t1,'Design power factor',0.5,1.0,float(loaded.get('transformer_settings',{}).get('power_factor',.9)),step=0.01)
transformer_util=col_input(t2,'Maximum transformer utilization',0.3,1.0,float(loaded.get('transformer_settings',{}).get('utilization',.8)),step=0.05)
transformer_reserve=col_input(t3,'Future demand reserve fraction',0.,2.,float(loaded.get('transformer_settings',{}).get('reserve',.2)),step=0.05)
with st.expander('Optional BESS - surplus solar self-consumption only'):
 b1,b2,b3=st.columns(3)
 bess_kwh=col_input(b1,'BESS energy capacity kWh (0=off)',min_value=0.,value=float(loaded.get('bess_settings',{}).get('kwh',0.)))
 bess_kw=col_input(b2,'BESS inverter power kW',min_value=0.,value=float(loaded.get('bess_settings',{}).get('kw',0.)))
 bess_eff=col_input(b3,'Round-trip efficiency',0.5,1.,float(loaded.get('bess_settings',{}).get('eff',.9)),step=0.01)
 b4,b5=st.columns(2)
 bess_capex=col_input(b4,'BESS installed cost Rs/kWh',min_value=0.,value=float(loaded.get('bess_settings',{}).get('capex',18000.)))
 bess_om=col_input(b5,'Annual BESS O&M %',min_value=0.,value=float(loaded.get('bess_settings',{}).get('om',2.)))
st.caption('Transformer and battery values are preliminary screening only; verify harmonics, protection, starting currents, fire safety, grid permissions and replacement costs.')
a,b,c=st.columns(3)
p['tariff']=col_input(a,'Base import Rs/kWh',0.,100.,float(loaded.get('assumptions',{}).get('tariff',8.)))
p['peak_tariff']=col_input(b,'Peak import Rs/kWh',0.,100.,float(loaded.get('assumptions',{}).get('peak_tariff',10.)))
p['export_tariff']=col_input(c,'Export credit Rs/kWh',0.,100.,float(loaded.get('assumptions',{}).get('export_tariff',2.)))
a,b=st.columns(2)
p['peak_start']=int(col_input(a,'Peak tariff start hour IST',0,23,int(loaded.get('assumptions',{}).get('peak_start',18))));p['peak_end']=int(col_input(b,'Peak tariff end hour IST',0,23,int(loaded.get('assumptions',{}).get('peak_end',22))))
a,b,c=st.columns(3)
roof_area=col_input(a,'Usable PV installation area m2',min_value=0.,value=float(loaded.get('solar_area_m2',24.)))
m2kw=col_input(b,'Area required per kWp m2',min_value=1.,value=float(loaded.get('area_per_kwp',5.)))
installed=col_input(c,'PV capacity to evaluate kWp',min_value=0.,value=float(loaded.get('evaluated_pv_kwp',4.)))
with st.expander('Solar costing assumptions'):
 for label,k,val in [('PV installed cost Rs/kWp','pv_capex',50000.),('Annual PV O&M % of capex','om',1.),('Real discount rate %','discount',8.),('PV performance ratio','pv_pr',.78)]:
  p[k]=number_input(label,min_value=0.,value=float(loaded.get('assumptions',{}).get(k,val)))
 p['life']=int(number_input('Economic horizon years',1,40,int(loaded.get('assumptions',{}).get('life',20))))
st.caption('Optimization selects PV capacity minimizing discounted grid cost + PV capex + O&M within available area, in 0.5 kWp steps plus the exact area limit. PV capacity is optimized without BESS; the entered battery is evaluated separately. Grid demand charges are compared separately below. No tariff escalation or PV degradation. GHI is a horizontal PV proxy; verify tilt, shade and equipment performance before procurement.')

st.subheader('6. EV charging — two-wheelers and four-wheelers, AC and DC')
st.caption('Use separate rows for two-wheelers and four-wheelers, including AC/slow, destination and DC fast charging. Example ratings and battery energy are editable, not vehicle compatibility guarantees. Points is simultaneous connectors; Vehicles_per_day is the TOTAL daily sessions for that group, not per point. Grid_kW_per_point is the mains electrical input rating. Battery energy requested is converted to grid energy using Efficiency; losses are not counted twice. For a DC output rating, enter its corresponding manufacturer mains input rating. Ratings are illustrative and must match equipment/vehicles.')
ev_settings=loaded.get('ev_settings',{})
ev_groups=st.data_editor(pd.DataFrame(ev_settings.get('groups',EV_DEFAULTS)),num_rows='dynamic',hide_index=True,key='ev_groups_'+str(st.session_state.get('restore_epoch',0)),width='stretch',column_config={
 'Points':st.column_config.NumberColumn(min_value=0,step=1),
 'Vehicles_per_day':st.column_config.NumberColumn(min_value=0,step=1),
 'Grid_kW_per_point':st.column_config.NumberColumn(min_value=.1),
 'Efficiency':st.column_config.NumberColumn(min_value=.01,max_value=1.),
 'Start_hour':st.column_config.NumberColumn(min_value=0,max_value=23,step=1),
 'End_hour':st.column_config.NumberColumn(min_value=0,max_value=23,step=1)})
ev_managed=st.checkbox('Managed EV charging - prefer solar and cheaper hours',value=bool(ev_settings.get('managed',False)),key='ev_managed_'+str(st.session_state.get('restore_epoch',0)))
ev_ceiling=number_input('Managed charging site grid-import ceiling kW',min_value=0.,value=float(ev_settings.get('ceiling',100.)))
ev_firm=st.checkbox('Charging import ceiling is enforced by a verified external controller',value=bool(ev_settings.get('firm',False)),key='ev_firm_'+str(st.session_state.get('restore_epoch',0)))
ev_in_meter=st.checkbox('Uploaded meter data already includes all planned EV charging',value=bool(ev_settings.get('in_meter',False)),key='ev_meter_'+str(st.session_state.get('restore_epoch',0)))
st.caption('Equal start/end means 24 hours. All group vehicles are assumed available within the entered window; this is aggregate energy scheduling, not a queue or vehicle-level arrival/taper model. Unserved energy is shown, not hidden. Managed charging cannot curtail the existing building load. The app does not control chargers. PV sizing keeps the EV schedule fixed at the entered reference PV; it is not joint PV/charging optimization.')

st.subheader('7. Grid capacity commitment and actual maximum demand')
st.caption('Contract demand (kVA) is separate from transformer rating and energy (kWh). Upload utility interval maximum-demand data at the actual billing interval. Hourly simulation can understate 15/30-minute peaks; PV/BESS savings alone do not justify a contract reduction. This tool does not submit a utility contract change.')
meter_file=st.file_uploader('Meter demand CSV: timestamp,kva OR timestamp,kw,pf',type=['csv'])
grid_defaults=loaded.get('grid_contract',{})
a,b,c=st.columns(3)
current_contract=col_input(a,'Current grid contract kVA',min_value=1.,value=float(grid_defaults.get('current',100.)))
demand_rate=col_input(b,'Demand charge Rs/kVA/month - enter applicable tariff',min_value=0.,value=float(grid_defaults.get('rate',0.)))
min_fraction=col_input(c,'Minimum billed fraction of contract',0.,1.,float(grid_defaults.get('floor',.8)))
a,b,c=st.columns(3)
excess_rate=col_input(a,'Additional excess-demand charge Rs/kVA/month',min_value=0.,value=float(grid_defaults.get('excess',0.)))
contract_reserve=col_input(b,'Peak demand reserve fraction',0.,1.,float(grid_defaults.get('reserve',.15)))
contract_step=col_input(c,'Contract comparison step kVA',min_value=1.,value=float(grid_defaults.get('step',5.)))
restore_basis=st.checkbox('Model grid capacity without PV or BESS credit',value=bool(grid_defaults.get('no_generation_credit',True)),key='credit_'+str(st.session_state.get('restore_epoch',0)))
st.caption('Charges are user-defined screening rules, not a built-in utility tariff. Compare recorded demand, growth and seasonal peaks with the current contract; verify applicable category, billing minimum, ratchets, penalties and utility approval.')
measured_monthly=pd.DataFrame(loaded['measured_monthly']) if loaded.get('measured_monthly') else None
if meter_file is not None:
 try:
  measured_monthly=monthly_demand(pd.read_csv(meter_file))
  st.dataframe(measured_monthly,hide_index=True)
  st.caption('Meter demand includes whatever PV/BESS operated during measurement. Review generation outages, battery availability and future occupancy before proposing a reduced contract.')
  if len(measured_monthly)<12 or (measured_monthly['Coverage %']<95).any():st.warning('Less than 12 months or incomplete interval coverage: do not treat this sample as a proven annual peak. Annualized costs are indicative.')
 except Exception as exc:st.error('Meter data invalid: '+str(exc))
label=text_input('Station design label',loaded.get('design_label','Facility energy design'))
notes=st.text_area('Revision notes')
input_snapshot=dict(station=station,code=code,latitude=latitude,longitude=longitude,basis=basis,start_year=start_year,end_year=end_year,rooms=rooms.to_dict('records'),circuits=circuits.to_dict('records'),assumptions=p,solar_area_m2=roof_area,area_per_kwp=m2kw,evaluated_pv_kwp=installed,facility_template=st.session_state.get('active_template','Custom / blank'),running_room_program=program,design_label=label,ev_settings=dict(groups=ev_groups.to_dict('records'),managed=ev_managed,ceiling=ev_ceiling,firm=ev_firm,in_meter=ev_in_meter),measured_monthly=measured_monthly.to_dict('records') if measured_monthly is not None else None,
 transformer_settings=dict(power_factor=power_factor,utilization=transformer_util,reserve=transformer_reserve),bess_settings=dict(kwh=bess_kwh,kw=bess_kw,eff=bess_eff,capex=bess_capex,om=bess_om),grid_contract=dict(current=current_contract,rate=demand_rate,floor=min_fraction,excess=excess_rate,reserve=contract_reserve,step=contract_step,no_generation_credit=restore_basis))
if st.button('Create station design revision'):
 try:
  parent=st.session_state.get('parent_revision')
  if parent and parent['station_code']!=code.strip().upper():parent=None
  saved=revision(input_snapshot,code,label,parent,notes)
  st.session_state['parent_revision']=saved;st.session_state['download_revision']=saved
 except Exception as exc:st.error('Cannot create revision: '+str(exc))
if 'download_revision' in st.session_state:
 saved=st.session_state['download_revision']
 st.download_button(f"Download {saved['station_code']} design revision {saved['revision']}",json.dumps(saved,indent=2),f"{saved['station_code']}_design_r{saved['revision']:03d}_{saved['content_hash'][:8]}.json",'application/json')
 st.caption('Download this immutable file to retain it. Later edits require a new revision; exported inputs are a snapshot, not live synchronization. Parent hash links revisions but does not prove authorship or regulatory approval.')

record=st.session_state.get('site_weather')
if not record or record[0]!=key:
 st.info('Enter the room and circuit inputs, then click Load weather and sunrise/sunset. Historical data are required for extreme sizing and annual solar costing.');st.stop()
f,provenance=record[1:]
if not 0<p['derating']<=1 or not 0<p['pv_pr']<=1 or p['cop']<1 or not 0<=p['shgc']<=1 or p['indoor_rh']>100:
 st.error('Capacity fraction/PV ratio must be 0-1, COP >=1, SHGC 0-1 and indoor RH <=100.');st.stop()
try:
 summary,hourly,components=calculate(f,rooms,circuits,p)
except Exception as exc:
 st.error('Check inputs: '+str(exc));st.stop()
ev_base_hourly=hourly.copy()
base_site_peak=float(hourly['Total demand kW'].max())
try:
 ev_power,ev_summary,ev_connected=charging_profile(hourly,ev_groups,installed,p,ev_managed,ev_ceiling)
 hourly['EV charging kW']=ev_power
 hourly['Total demand kW']+=ev_power
except Exception as exc:st.error('EV charging inputs invalid: '+str(exc));st.stop()
historical=basis.startswith('Historical')
years=end_year-start_year+1 if historical else 1.
max_pv=roof_area/m2kw
if max_pv>500:
 st.error('Use a PV area limit of at most 500 kWp for this interactive screening tool.');st.stop()
if historical:
 candidates,best=optimize_pv(hourly,max_pv,p,years);chosen=float(best.capacity_kwp)
else:
 chosen=installed;candidates=None;best=None
if ev_managed and ev_connected>0:
 # Re-dispatch at the actually selected PV so the import ceiling is not based on a larger reference array.
 ev_power,ev_summary,ev_connected=charging_profile(ev_base_hourly,ev_groups,chosen,p,True,ev_ceiling)
 hourly['EV charging kW']=ev_power
 hourly['Total demand kW']=ev_base_hourly['Total demand kW']+ev_power
 if historical:candidates,_=optimize_pv(hourly,max_pv,p,years)
if not ev_summary.empty:
 st.subheader('EV charging energy and capacity check')
 st.dataframe(ev_summary,hide_index=True)
 st.write(f'Connected EV grid input: {ev_connected:.2f} kW; scheduled coincident EV peak: {ev_power.max():.2f} kW.')
 if ev_summary['Unserved battery kWh (period)'].sum()>1e-6:st.error('EV charging energy cannot be met within points, windows or import ceiling. Add capacity/time or reduce requested sessions.')
 if ev_managed and base_site_peak>ev_ceiling:st.warning('The building load itself exceeds the EV import ceiling in some hours; managed charging cannot correct that overload.')
ev_capacity_peak=max(base_site_peak,ev_ceiling) if ev_connected>0 and ev_managed and ev_firm else max(float(hourly['Total demand kW'].max()),base_site_peak+ev_connected)


cost,solar,imports,exports=economics(hourly,chosen,p,years)
hourly['PV generation kW']=solar;hourly['Grid import kW']=imports;hourly['Grid export kW']=exports
transformer=transformer_design(ev_capacity_peak,chosen,power_factor,transformer_util,transformer_reserve)
if bess_kwh>0:
 if bess_kw<=0:st.error('Nonzero BESS capacity requires inverter power.');st.stop()
 storage_hourly=hourly.copy()
 storage_hourly['GHI W/m2']*=p['pv_pr']
 dispatch=battery_dispatch(storage_hourly,chosen,bess_kwh,bess_kw,bess_eff)
 hourly['Grid import kW']=dispatch['Grid import kW'].to_numpy()
 hourly['Grid export kW']=dispatch['Grid export kW'].to_numpy()
 hourly['Battery SOC kWh']=dispatch['Battery SOC kWh'].to_numpy()
 hours=(hourly['Time IST'].dt.hour.to_numpy()-1)%24
 mask=((hours>=p['peak_start'])&(hours<p['peak_end'])) if p['peak_start']<p['peak_end'] else ((hours>=p['peak_start'])|(hours<p['peak_end']))
 rates=np.where(mask,p['peak_tariff'],p['tariff'])
 battery_bill=float((hourly['Grid import kW'].to_numpy()*rates-hourly['Grid export kW'].to_numpy()*p['export_tariff']).sum()/years)
 investment=bess_kwh*bess_capex
 factor=sum((1+p['discount']/100)**(-y) for y in range(1,p['life']+1))
 incremental=investment+(battery_bill-cost['annual_bill']+investment*bess_om/100)*factor
 baseline_bill=cost['annual_bill']+cost['annual_saving']
 cost['annual_bill']=battery_bill
 cost['annual_saving']=baseline_bill-battery_bill
 cost['grid_kwh']=float(hourly['Grid import kW'].sum()/years)
 cost['export_kwh']=float(hourly['Grid export kW'].sum()/years)
 cost['npv']-=incremental
 cost['battery_capex']=investment
 cost['battery_incremental_lcc']=incremental
 cost['life_cycle_cost']+=incremental
else:
 cost['battery_capex']=0.

contract_result=None
try:
 demand_basis=measured_monthly
 if demand_basis is None:
  model_kw=hourly['Total demand kW'] if restore_basis else hourly['Grid import kW']
  if restore_basis and ev_connected>0:
   building_kw=hourly['Total demand kW']-hourly['EV charging kW']
   model_kw=np.maximum(building_kw,ev_ceiling) if ev_managed and ev_firm else building_kw+ev_connected
  demand_basis=pd.DataFrame({'Month':hourly['Time IST'].dt.to_period('M').astype(str),'Measured peak kVA':np.asarray(model_kw)/power_factor}).groupby('Month',as_index=False)['Measured peak kVA'].max()
  demand_label='SIMULATED hourly demand; planning estimate only'
 else:
  demand_basis=demand_basis.copy()
  if ev_connected>0 and not ev_in_meter:
   demand_basis['Measured peak kVA']+=ev_connected/power_factor
   demand_label='Uploaded meter peak + conservative planned EV connected load (not an observed combined peak)'
  else:demand_label='Uploaded actual interval demand; measurement-period evidence'
 options,contract_result,required_contract=contract_options(demand_basis,current_contract,demand_rate,min_fraction,excess_rate,contract_reserve,contract_step,max_kva=100000.)
 st.subheader('Grid commitment comparison')
 st.write(demand_label)
 st.write(f"Peak plus reserve basis: {required_contract:.2f} kVA; lowest-charge feasible comparison: {contract_result['Contract kVA']:.2f} kVA. Current: {current_contract:.2f} kVA.")
 st.dataframe(options,hide_index=True)
 if demand_rate==0:st.info('Enter actual demand charges before interpreting cost savings.')
 if measured_monthly is None:st.warning('No actual meter data supplied. Do not lower a utility commitment based on this simulation alone.')
 st.download_button('Download grid contract comparison CSV',options.to_csv(index=False),'grid_contract_options.csv','text/csv')
except Exception as exc:st.error('Grid comparison unavailable: '+str(exc))

st.success(f"{len(f):,} complete hours loaded; {provenance['source']}; retrieved {provenance['retrieved_utc']}. Open-Meteo / ECMWF attribution: https://open-meteo.com/ (CC BY 4.0).")
st.subheader('Room AC capacity - historical extremes' if historical else 'Forecast-day cooling screening - NOT design sizing')
st.dataframe(summary,hide_index=True,width='stretch')
if (summary['N+1']=='FAIL').any():st.error('At least one room fails the largest-unit-out capacity check.')
st.caption('N+1 addresses steady-state cooling capacity only. Manufacturer total/sensible capacity, independent power, standby changeover, humidity control and transient hotspot protection require engineering verification. No capacity credit is taken for PV.')
st.subheader('Transformer and optional BESS screening')
st.dataframe(pd.DataFrame([transformer]),hide_index=True,width='stretch')
if transformer['oversize_warning']:st.error('Transformer requirement exceeds the available standard sizes.')
if bess_kwh>0:st.write(f"BESS {bess_kwh:.1f} kWh / {bess_kw:.1f} kW; incremental discounted battery cost Rs {cost['battery_incremental_lcc']:,.0f}.")
st.subheader('Overall site electricity and solar')
a,b,c,d=st.columns(4)
a.metric('Peak site electrical demand',f"{hourly['Total demand kW'].max():.2f} kW")
b.metric('Mean annual demand' if historical else 'Forecast-day demand',f"{hourly['Total demand kW'].sum()/years:,.0f} kWh")
c.metric(('PV candidate (managed EV)' if ev_managed and ev_connected>0 else 'Lowest-cost PV') if historical else 'Evaluated PV',f'{chosen:.2f} kWp')
d.metric('Mean annual net energy bill' if historical else 'Forecast-day net energy bill',f"Rs {cost['annual_bill']:,.0f}")
if historical:
 evaluated,*_=economics(hourly,installed,p,years)
 st.write(f"PV capex Rs {cost['capex']:,.0f}; annual gross bill saving Rs {cost['annual_saving']:,.0f}; incremental NPV Rs {cost['npv']:,.0f}; {p['life']}-year discounted life-cycle cost Rs {cost['life_cycle_cost']:,.0f}.")
 if installed>max_pv:st.warning('The separately evaluated PV exceeds the entered available area; it is excluded from the area-constrained optimum.')
 st.dataframe(pd.DataFrame([dict(Scenario='Selected PV evaluation',**evaluated),dict(Scenario='Area-constrained PV candidate',**cost)]),hide_index=True)
 st.plotly_chart(px.line(candidates,x='capacity_kwp',y='life_cycle_cost',title='Discounted total energy cost versus PV size'),width='stretch')
 if ev_managed and ev_connected>0:st.caption('Managed EV uses a two-pass heuristic: choose PV against reference charging, then re-dispatch EV at that PV. The candidate-cost curve holds the final EV schedule fixed. This is not a joint/global PV-charging optimum; an energy shortfall remains visible.')
 st.caption('Economic optimum uses all historical years, with equal weight to each year. Energy demand assumes adequate cooling capacity; a failed N+1 check means the cooling requirement is not assured. Solar optimization changes PV size only, not approved room temperatures or occupancy.')

# Plot at most one week interactively, retain full data for energy and costing.
day=st.date_input('Plot start date',value=f.time.iloc[-1].date(),min_value=f.time.iloc[0].date(),max_value=f.time.iloc[-1].date())
plot=hourly[(hourly['Time IST']>=pd.Timestamp(day))&(hourly['Time IST']<pd.Timestamp(day)+pd.Timedelta(days=7))]
st.plotly_chart(px.area(plot,x='Time IST',y=['Equipment kW','Lights kW','Fans kW','Other kW','AC kW','EV charging kW'],title='Electrical demand by source'),width='stretch')
st.plotly_chart(px.line(plot,x='Time IST',y=['Total demand kW','PV generation kW','Grid import kW'],title='Site demand, solar and grid electricity'),width='stretch')
st.dataframe(f[['time','sunrise','sunset']].drop_duplicates('sunrise').tail(7),hide_index=True)
st.dataframe(components,hide_index=True)
annual=hourly.assign(Year=hourly['Time IST'].dt.year).groupby('Year')[['Total demand kW','PV generation kW','Grid import kW','Grid export kW']].sum().rename(columns=lambda c:c.replace(' kW',' kWh')).reset_index()
st.dataframe(annual,hide_index=True)
st.download_button('Download hourly site demand CSV',hourly.to_csv(index=False),'site_hourly_demand.csv','text/csv')
config=dict(station=station,code=code,latitude=latitude,longitude=longitude,basis=basis,start_year=start_year,end_year=end_year,rooms=rooms.to_dict('records'),circuits=circuits.to_dict('records'),assumptions=p,solar_area_m2=roof_area,area_per_kwp=m2kw,evaluated_pv_kwp=installed,chosen_pv_kwp=chosen,transformer=transformer,bess_kwh=bess_kwh,bess_kw=bess_kw,bess_eff=bess_eff,bess_capex=bess_capex,provenance=provenance)
config.update(input_snapshot)
config['grid_comparison']=contract_result.to_dict() if contract_result is not None else None
st.download_button('Download design inputs JSON',json.dumps(config,indent=2),'site_design_inputs.json','application/json')

def report_pdf():
 buffer=BytesIO();styles=getSampleStyleSheet();story=[]
 def text(s,style='BodyText'):
  story.extend([Paragraph(escape(str(s)),styles[style]),Spacer(1,7)])
 def table(title,frame):
  story.append(PageBreak());text(title,'Heading1')
  frame=frame.copy()
  for offset in range(1,len(frame.columns),3):
   part=frame.iloc[:,[0]+list(range(offset,min(offset+3,len(frame.columns))))].copy()
   numeric=part.select_dtypes(include='number').columns
   part[numeric]=part[numeric].round(3)
   rows=[[Paragraph(escape(str(x)),styles['BodyText']) for x in part.columns]]+[[Paragraph(escape(str(x)),styles['BodyText']) for x in row] for row in part.values.tolist()]
   tb=LongTable(rows,repeatRows=1,colWidths=[125]*len(part.columns));tb.setStyle([('GRID',(0,0),(-1,-1),.3,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('VALIGN',(0,0),(-1,-1),'TOP')]);story.extend([tb,Spacer(1,10)])
 text('Generic Railway Facility Energy Design Studio Design','Title');text(f'{station} ({code}) | {latitude}, {longitude} | {basis}')
 text('Generated UTC '+datetime.now(timezone.utc).isoformat());text(f"Period: {f.time.iloc[0]} to {f.time.iloc[-1]}; {len(f):,} hourly records; Asia/Kolkata")
 text('Source and requests: '+json.dumps(provenance));text('Open-Meteo / ECMWF ERA5, CC BY 4.0. Reanalysis is modelled gridded history, not a local station extreme measurement.')
 text('Method and limitations','Heading1')
 text('Steady-state envelope conduction + solar surrogate + sensible/latent infiltration + equipment + people + assigned circuits. Cooling sizing assumes full people and all connected in-room circuits. Operating energy uses selected schedules; AC is continuous. Each circuit contributes once to electricity, and only assigned room circuits add room heat. Indoor RH is a cooling-load assumption, not an active humidity-control simulation.')
 text('All energy bins end at timestamp; sunrise/sunset overlaps use preceding-hour bins to align with mean radiation. Temperature and RH at the ending timestamp approximate bin conditions. PV uses GHI x kWp x performance ratio. BESS self-consumption and grid commitment charges are separate screening calculations; no joint PV/BESS/contract optimization, thermal storage, PV degradation, inter-room transfer, dynamic wall lag or CFD. Equipment derating and COP must be verified. Historical extreme capacity and forecast-day operations are separate. Polar sun cases are rejected.')
 text('Inputs and shared assumptions','Heading1')
 for k,v in p.items():text(f'{k}: {v}')
 for k,v in dict(usable_pv_area_m2=roof_area,area_per_kwp=m2kw,evaluated_pv_kwp=installed,chosen_pv_kwp=chosen).items():text(f'{k}: {v}')
 text('Station revision / running-room programme','Heading1');text(json.dumps(program));text('Latest created revision: '+str(st.session_state.get('parent_revision',{}).get('revision','Not saved')));text('Grid contract inputs: '+json.dumps(input_snapshot['grid_contract']));text('Grid comparison basis: '+demand_label);
 text('EV charger inputs: '+json.dumps(input_snapshot['ev_settings']));text(f'EV connected input {ev_connected:.3f} kW; electrical capacity design peak {ev_capacity_peak:.3f} kW. Unless externally enforced managed limits are confirmed, transformer screening includes full connected EV load plus building peak.');
 text('Results','Heading1');text('Transformer: '+json.dumps(transformer));text(f'BESS {bess_kwh} kWh, {bess_kw} kW, efficiency {bess_eff}');text(json.dumps(cost));text(f"Peak total site demand {hourly['Total demand kW'].max():.3f} kW. All capacity results are preliminary screening, not procurement certification.")
 if not ev_summary.empty:table('EV energy and capacity results',ev_summary)
 if contract_result is not None:table('Grid contract options (user-specified screening tariff)',options)
 table('Room inputs',rooms);table('Fan, light and other circuits',circuits);table('AC design results and N+1 checks',summary);table('Governing-hour heat contributions',components);table('Annual site electricity',annual)
 table('Sunrise and sunset: first and last seven days',pd.concat([f[['time','sunrise','sunset']].drop_duplicates('sunrise').head(7),f[['time','sunrise','sunset']].drop_duplicates('sunrise').tail(7)]).drop_duplicates())
 table('Plotted hourly demand and supply (up to seven days)',plot)
 if candidates is not None:table('PV cost alternatives',candidates)
 text('Full hourly results are downloadable as the companion CSV; this report contains summaries and the plotted interval to keep multi-decade reports readable.')
 SimpleDocTemplate(buffer,leftMargin=40,rightMargin=40).build(story);return buffer.getvalue()
st.download_button('Download complete design report PDF',report_pdf(),'site_energy_design_report.pdf','application/pdf')
