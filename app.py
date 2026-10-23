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

st.set_page_config(page_title='Railway Facility Energy Design Studio',layout='wide')
st.title('Railway Facility Energy Design Studio')
st.caption('Generic rooms, historical extreme AC sizing with N+1, whole-site electricity and solar cost screening.')
mode=st.selectbox('Calculator',['Generic multi-room planner','Previous relay-room simulator'])
if mode=='Previous relay-room simulator':
 import runpy
 runpy.run_path('legacy_app.py',run_name='__main__')
 st.stop()

st.subheader('1. Station and weather basis')
a,b,c,d=st.columns(4)
station=a.text_input('Station / site name','Mancherial');code=b.text_input('Station code','MCI')
latitude=c.number_input('Latitude',-90.,90.,18.872,format='%.5f');longitude=d.number_input('Longitude',-180.,180.,79.444,format='%.5f')
st.caption('Changing name/code does not change coordinates. Current scheduling timezone is Asia/Kolkata (India).')
basis=st.radio('Analysis basis',['Historical extreme design + annual energy','Forecast day (operations only)'],horizontal=True)
last_year=datetime.now(timezone.utc).year-1
first,last=st.columns(2)
start_year=int(first.number_input('Historical start year',1940,last_year,last_year-29))
end_year=int(last.number_input('Historical end year',1940,last_year,last_year))
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
template=st.selectbox('Facility design template',list(TEMPLATES))
if st.button('Apply template - replace rooms and circuits'):
 st.session_state['active_template']=template
 st.session_state['template_version']=st.session_state.get('template_version',0)+1
 st.session_state.pop('saved_room_settings',None)
 st.rerun()
base,template_circuits=template_data(st.session_state.get('active_template','Custom / blank'))
st.caption('Templates are preliminary examples, not sanctioned equipment schedules. High mast template includes an artificial support kiosk with AC: remove its AC load before using results for a lights-only site.')
st.caption('All rooms have AC operating continuously. Equipment is continuous electrical input assumed to become room heat. People is the maximum simultaneous count. Add/delete rows as needed; window and door sizes are TOTAL areas in square metres.')
essential=['Room','Length_m','Width_m','Height_m','Window_m2','Door_m2','Equipment_kW','People']
rooms_basic=st.data_editor(base[essential],num_rows='dynamic',hide_index=True,key=f"rooms_{st.session_state.get('template_version',0)}",width='stretch',
 column_config={'People':st.column_config.NumberColumn(min_value=0,step=1),'Room':st.column_config.TextColumn(required=True)})
if rooms_basic.empty:
 st.info('Add at least one room to continue.');st.stop()
st.subheader('3. Room temperature, occupancy and AC configuration')
st.caption('Target_C is the room/critical-equipment upper temperature used for sizing. AC_units includes the standby unit. Set approved limits for each room; 21 C is only the relay-room starting example.')
saved_settings=st.session_state.get('saved_room_settings',{})
settings=pd.DataFrame([dict({'Room':r,'Target_C':21.,'Occupancy':'Always','AC_units':3,'AC_TR_each':4.},**saved_settings.get(r,{})) for r in rooms_basic.Room.dropna()])
settings=st.data_editor(settings,hide_index=True,disabled=['Room'],key='room_settings',width='stretch',
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
opening=int(a.number_input('Occupied hours start (IST, 0-23)',0,23,8));closing=int(b.number_input('Occupied hours end (IST, 0-23)',0,23,18))
st.caption('Night means sunset to sunrise. Daylight means sunrise to sunset. Occupied hours uses these daily clock hours; equal start/end means 24 hours. AC remains on outside occupancy hours.')

p=dict(opening=opening,closing=closing)
with st.expander('Engineering assumptions - review before equipment selection',expanded=False):
 st.caption('Shared envelope defaults apply to every room. No inter-room heat transfer, orientation-specific wall model or CFD. Room heat balance is a preliminary screening model.')
 for label,keyp,value in [('Roof U W/m2K','roof_u',2.5),('Wall U W/m2K','wall_u',1.8),('Window U W/m2K','window_u',5.7),('Door U W/m2K','door_u',3.),('Window solar heat gain coefficient','shgc',.75),('Effective roof solar gain factor','roof_solar',.15),('Air changes/hour','ach',.35),('Indoor RH %','indoor_rh',50.),('Sensible heat/person W','person_sensible',75.),('Latent heat/person W','person_latent',55.),('Design load allowance %','margin',15.),('AC available capacity fraction at extreme ambient','derating',.85),('AC COP at outdoor <=35 C','cop',3.5),('COP reduction per C above 35','cop_slope',.025),('Outdoor temperature stress uplift C','uplift',0.)]:
  p[keyp]=st.number_input(label,min_value=0.0,value=value,key=keyp)
 st.caption('0.85 derating and COP curve are editable assumptions, not manufacturer certification. Full people and all connected in-room circuits are assumed for capacity design, regardless of operating schedule. Historical weather variables remain coincident; optional stress uplift holds RH constant.')

st.subheader('5. Solar, transformer and optional BESS')
t1,t2,t3=st.columns(3)
power_factor=t1.number_input('Design power factor',0.5,1.0,0.90,step=0.01)
transformer_util=t2.number_input('Maximum transformer utilization',0.3,1.0,0.80,step=0.05)
transformer_reserve=t3.number_input('Future demand reserve fraction',0.,2.,0.20,step=0.05)
with st.expander('Optional BESS - surplus solar self-consumption only'):
 b1,b2,b3=st.columns(3)
 bess_kwh=b1.number_input('BESS energy capacity kWh (0=off)',min_value=0.,value=0.)
 bess_kw=b2.number_input('BESS inverter power kW',min_value=0.,value=0.)
 bess_eff=b3.number_input('Round-trip efficiency',0.5,1.,0.90,step=0.01)
 b4,b5=st.columns(2)
 bess_capex=b4.number_input('BESS installed cost Rs/kWh',min_value=0.,value=18000.)
 bess_om=b5.number_input('Annual BESS O&M %',min_value=0.,value=2.)
st.caption('Transformer and battery values are preliminary screening only; verify harmonics, protection, starting currents, fire safety, grid permissions and replacement costs.')
a,b,c=st.columns(3)
p['tariff']=a.number_input('Base import Rs/kWh',0.,100.,8.)
p['peak_tariff']=b.number_input('Peak import Rs/kWh',0.,100.,10.)
p['export_tariff']=c.number_input('Export credit Rs/kWh',0.,100.,2.)
a,b=st.columns(2)
p['peak_start']=int(a.number_input('Peak tariff start hour IST',0,23,18));p['peak_end']=int(b.number_input('Peak tariff end hour IST',0,23,22))
a,b,c=st.columns(3)
roof_area=a.number_input('Usable PV installation area m2',min_value=0.,value=24.)
m2kw=b.number_input('Area required per kWp m2',min_value=1.,value=5.)
installed=c.number_input('PV capacity to evaluate kWp',min_value=0.,value=4.)
with st.expander('Solar costing assumptions'):
 for label,k,val in [('PV installed cost Rs/kWp','pv_capex',50000.),('Annual PV O&M % of capex','om',1.),('Real discount rate %','discount',8.),('PV performance ratio','pv_pr',.78)]:
  p[k]=st.number_input(label,min_value=0.,value=val)
 p['life']=int(st.number_input('Economic horizon years',1,40,20))
st.caption('Optimization selects PV capacity minimizing discounted grid cost + PV capex + O&M within available area, in 0.5 kWp steps plus the exact area limit. No battery, demand charges, tariff escalation or PV degradation. GHI is a horizontal PV proxy; verify tilt, shade and equipment performance before procurement.')

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
historical=basis.startswith('Historical')
years=end_year-start_year+1 if historical else 1.
max_pv=roof_area/m2kw
if max_pv>500:
 st.error('Use a PV area limit of at most 500 kWp for this interactive screening tool.');st.stop()
if historical:
 candidates,best=optimize_pv(hourly,max_pv,p,years);chosen=float(best.capacity_kwp)
else:
 chosen=installed;candidates=None;best=None
cost,solar,imports,exports=economics(hourly,chosen,p,years)
hourly['PV generation kW']=solar;hourly['Grid import kW']=imports;hourly['Grid export kW']=exports
transformer=transformer_design(float(hourly['Total demand kW'].max()),chosen,power_factor,transformer_util,transformer_reserve)
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
 cost['annual_bill']=battery_bill
 cost['battery_capex']=investment
 cost['battery_incremental_lcc']=incremental
 cost['life_cycle_cost']+=incremental
else:
 cost['battery_capex']=0.

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
c.metric('Lowest-cost PV' if historical else 'Evaluated PV',f'{chosen:.2f} kWp')
d.metric('Mean annual net energy bill' if historical else 'Forecast-day net energy bill',f"Rs {cost['annual_bill']:,.0f}")
if historical:
 evaluated,*_=economics(hourly,installed,p,years)
 st.write(f"PV capex Rs {cost['capex']:,.0f}; annual gross bill saving Rs {cost['annual_saving']:,.0f}; incremental NPV Rs {cost['npv']:,.0f}; {p['life']}-year discounted life-cycle cost Rs {cost['life_cycle_cost']:,.0f}.")
 if installed>max_pv:st.warning('The separately evaluated PV exceeds the entered available area; it is excluded from the area-constrained optimum.')
 st.dataframe(pd.DataFrame([dict(Scenario='Selected PV evaluation',**evaluated),dict(Scenario='Area-constrained optimum',**cost)]),hide_index=True)
 st.plotly_chart(px.line(candidates,x='capacity_kwp',y='life_cycle_cost',title='Discounted total energy cost versus PV size'),width='stretch')
 st.caption('Economic optimum uses all historical years, with equal weight to each year. Energy demand assumes adequate cooling capacity; a failed N+1 check means the cooling requirement is not assured. Solar optimization changes PV size only, not approved room temperatures or occupancy.')

# Plot at most one week interactively, retain full data for energy and costing.
day=st.date_input('Plot start date',value=f.time.iloc[-1].date(),min_value=f.time.iloc[0].date(),max_value=f.time.iloc[-1].date())
plot=hourly[(hourly['Time IST']>=pd.Timestamp(day))&(hourly['Time IST']<pd.Timestamp(day)+pd.Timedelta(days=7))]
st.plotly_chart(px.area(plot,x='Time IST',y=['Equipment kW','Lights kW','Fans kW','Other kW','AC kW'],title='Electrical demand by source'),width='stretch')
st.plotly_chart(px.line(plot,x='Time IST',y=['Total demand kW','PV generation kW','Grid import kW'],title='Site demand, solar and grid electricity'),width='stretch')
st.dataframe(f[['time','sunrise','sunset']].drop_duplicates('sunrise').tail(7),hide_index=True)
st.dataframe(components,hide_index=True)
annual=hourly.assign(Year=hourly['Time IST'].dt.year).groupby('Year')[['Total demand kW','PV generation kW','Grid import kW','Grid export kW']].sum().rename(columns=lambda c:c.replace(' kW',' kWh')).reset_index()
st.dataframe(annual,hide_index=True)
st.download_button('Download hourly site demand CSV',hourly.to_csv(index=False),'site_hourly_demand.csv','text/csv')
config=dict(station=station,code=code,latitude=latitude,longitude=longitude,basis=basis,start_year=start_year,end_year=end_year,rooms=rooms.to_dict('records'),circuits=circuits.to_dict('records'),assumptions=p,solar_area_m2=roof_area,area_per_kwp=m2kw,evaluated_pv_kwp=installed,chosen_pv_kwp=chosen,transformer=transformer,bess_kwh=bess_kwh,bess_kw=bess_kw,bess_eff=bess_eff,bess_capex=bess_capex,provenance=provenance)
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
 text('All energy bins end at timestamp; sunrise/sunset overlaps use preceding-hour bins to align with mean radiation. Temperature and RH at the ending timestamp approximate bin conditions. PV uses GHI x kWp x performance ratio. No battery, demand charges, thermal storage, PV degradation, inter-room transfer, dynamic wall lag or CFD. Equipment derating and COP must be verified. Historical extreme capacity and forecast-day operations are separate. Polar sun cases are rejected.')
 text('Inputs and shared assumptions','Heading1')
 for k,v in p.items():text(f'{k}: {v}')
 for k,v in dict(usable_pv_area_m2=roof_area,area_per_kwp=m2kw,evaluated_pv_kwp=installed,chosen_pv_kwp=chosen).items():text(f'{k}: {v}')
 text('Results','Heading1');text('Transformer: '+json.dumps(transformer));text(f'BESS {bess_kwh} kWh, {bess_kw} kW, efficiency {bess_eff}');text(json.dumps(cost));text(f"Peak total site demand {hourly['Total demand kW'].max():.3f} kW. All capacity results are preliminary screening, not procurement certification.")
 table('Room inputs',rooms);table('Fan, light and other circuits',circuits);table('AC design results and N+1 checks',summary);table('Governing-hour heat contributions',components);table('Annual site electricity',annual)
 table('Sunrise and sunset: first and last seven days',pd.concat([f[['time','sunrise','sunset']].drop_duplicates('sunrise').head(7),f[['time','sunrise','sunset']].drop_duplicates('sunrise').tail(7)]).drop_duplicates())
 table('Plotted hourly demand and supply (up to seven days)',plot)
 if candidates is not None:table('PV cost alternatives',candidates)
 text('Full hourly results are downloadable as the companion CSV; this report contains summaries and the plotted interval to keep multi-decade reports readable.')
 SimpleDocTemplate(buffer,leftMargin=40,rightMargin=40).build(story);return buffer.getvalue()
st.download_button('Download complete design report PDF',report_pdf(),'site_energy_design_report.pdf','application/pdf')
