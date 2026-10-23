import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime, timezone
from io import BytesIO
from extreme_design import fetch_history, design_analysis, redundancy
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

@st.cache_data(ttl=3600)
def weather_data(latitude, longitude):
    params = dict(latitude=latitude, longitude=longitude, timezone="Asia/Kolkata",
                  forecast_days=1, hourly="temperature_2m,relative_humidity_2m,shortwave_radiation")
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    with urlopen(url, timeout=20) as response:
        data = json.load(response)
    hourly = pd.DataFrame(data["hourly"])
    columns = ["temperature_2m", "relative_humidity_2m", "shortwave_radiation"]
    if len(hourly) != 24 or hourly[columns].isna().any().any() or not np.isfinite(hourly[columns]).all().all():
        raise ValueError("Expected 24 complete finite hourly weather records")
    if not hourly.relative_humidity_2m.between(0,100).all() or (hourly.shortwave_radiation < 0).any():
        raise ValueError("Weather values outside physical range")
    return hourly, url, datetime.now(timezone.utc).isoformat()


st.set_page_config(page_title="Relay Room Thermal + Solar",layout="wide")
st.title("Interlocking Room | Thermal and Solar Simulator")
st.caption("Preliminary heat-balance screening. Spatial heat map is an illustrative surrogate, NOT CFD.")
cname, ccode = st.columns(2)
station_name = cname.text_input("Station name", "Mancherial")
station_code = ccode.text_input("Station code", "MCI")
st.caption("Coordinates determine weather. Mancherial defaults are approximate; verify the relay-room location. Station code is a report identifier, not an automatic location lookup.")
clat, clon = st.columns(2)
latitude = clat.number_input("Station latitude", min_value=-90.0, max_value=90.0, value=18.872, format="%.5f")
longitude = clon.number_input("Station longitude", min_value=-180.0, max_value=180.0, value=79.444, format="%.5f")
weather_mode = st.radio("Weather source", ["Open-Meteo forecast", "Synthetic demonstration"], horizontal=True)
weather = None
weather_source = "Synthetic demonstration"
fetched_at = "Not applicable"
if weather_mode == "Open-Meteo forecast":
    try:
        weather, weather_source, fetched_at = weather_data(latitude, longitude)
        st.success("Open-Meteo forecast loaded: " + str(weather.time.iloc[0]) + " to " + str(weather.time.iloc[-1]) + " (Asia/Kolkata)")
        st.caption("Modelled weather, not a sensor measurement. Source: Open-Meteo, https://open-meteo.com/ (CC BY 4.0). Cached for one hour; retrieved UTC: " + fetched_at)
    except Exception as exc:
        st.error("Weather unavailable: " + str(exc) + ". Retry later or explicitly select Synthetic demonstration.")
        st.warning("Historical design sizing remains available below.")
with st.sidebar:
 L=st.slider("Length m",3.,20.,8.);W=st.slider("Width m",3.,15.,5.);H=st.slider("Height m",2.,6.,3.)
 T=st.slider("Outdoor peak temperature C",25.,50.,42.);target=st.slider("Manual relay-end air setpoint C",18.,30.,21.)
 min_target=st.slider("Minimum permitted relay-end temperature C",18.,30.,21.)
 max_target=st.slider("Maximum permitted relay-end temperature C",min_target,35.,min_target)
 pv_installed=st.slider("Installed solar PV kWp",0.,30.,8.)
 setpoint_step=st.select_slider("Optimization resolution C",options=[0.5,1.0],value=0.5)
 rh=st.slider("Outdoor RH %",10,95,55);rh_in=st.slider("Indoor RH %",35,65,50)
 Uroof=st.slider("Roof U value W/m2K",.2,5.,2.5);Uwall=st.slider("Wall U value",.2,4.,1.8)
 Aw=st.slider("Window m2",0.,15.,3.);Uw=st.slider("Window U value",.7,7.,5.7)
 shgc=st.slider("Window SHGC",.1,.9,.75);Ad=st.slider("Door m2",0.,6.,2.);Ud=st.slider("Door U value",.7,6.,3.)
 ach=st.slider("Air changes per hour",.05,3.,.35);equipment=st.slider("Equipment kW",.1,10.,2.)
 ghi=st.slider("Peak solar W/m2",0.0,1100.0,800.0)
 acx=st.slider("AC X m",0.,float(L),0.);acy=st.slider("AC Y m",0.,float(W),float(W/2))
 rx=st.slider("Relay X m",0.,float(L),float(L*.8));ry=st.slider("Relay Y m",0.,float(W),float(W/2))
 tariff=st.number_input("Import Rs/kWh",value=8.);export=st.number_input("Export Rs/kWh",value=2.)
 capex=st.number_input("PV Rs/kWp",value=50000.)

def sat(t):return 610.94*np.exp(17.625*t/(t+243.04))
def w(t,r):
 p=sat(t)*r
 return .62198*p/(101325-p)
def load(out,rhout,irr,roof=Uroof,window=Uw,solar=shgc,door=Ud,air=ach,setpoint=None):
 sp=target if setpoint is None else setpoint
 dt=np.maximum(0,out-sp)
 wall=max(0.0,2*(L+W)*H-Aw-Ad)
 mdot=1.18*L*W*H*air/3600
 latent=np.maximum(0,mdot*2501*(w(out,rhout)-w(sp,rh_in/100)))
 terms={"Roof":roof*L*W*dt/1000,"Walls":Uwall*wall*dt/1000,
 "Window":window*Aw*dt/1000,"Door":door*Ad*dt/1000,
 "Solar":irr*(.15*L*W+.0192*wall+Aw*solar)/1000,
 "Equipment":equipment,"Lighting":.2,
 "Infiltration sensible":mdot*1.006*dt,"Infiltration latent":latent}
 return terms
st.header("Extreme-condition AC sizing and N+1 redundancy")
st.caption("Primary equipment-selection workflow: historical coincident weather, not today's forecast. Operational forecast results below do not establish installed AC capacity.")
ys, ye = st.columns(2)
last_complete_year = datetime.now(timezone.utc).year - 1
history_start = int(ys.number_input("Historical start year",1940,last_complete_year,max(1940,last_complete_year-29)))
history_end = int(ye.number_input("Historical end year",1940,last_complete_year,last_complete_year))
design_indoor = st.number_input("Design relay-end upper temperature C",value=21.0,min_value=10.0,max_value=35.0)
design_margin = st.number_input("Explicit design load allowance %",value=15.0,min_value=0.0,max_value=100.0)
stress_uplift = st.number_input("Additional outdoor temperature stress uplift C",value=0.0,min_value=0.0,max_value=10.0)
st.caption("Stress uplift holds coincident RH constant; this is an intentionally conservative separate sensitivity, not a historical observation.")
peak_equipment = st.number_input("Maximum continuous equipment heat kW for sizing",value=float(equipment),min_value=0.1,max_value=100.0)
design_ach = st.number_input("Adverse infiltration air changes/hour",value=float(ach),min_value=0.01,max_value=10.0)
derating = st.number_input("Manufacturer-verified available capacity fraction at design conditions",value=0.85,min_value=0.1,max_value=1.0)
st.caption("0.85 is an illustrative assumption. Verify total and sensible capacities at the governing outdoor and indoor conditions from manufacturer data.")
unit_count = int(st.number_input("Installed equal AC units",value=3,min_value=2,max_value=10))
unit_tr = st.number_input("Nominal capacity of each AC unit TR",value=3.0,min_value=0.5,max_value=30.0,step=0.5)
activation_delay = st.number_input("Standby activation delay minutes",value=2.0,min_value=0.0,max_value=60.0)
resilience_mass = st.number_input("Effective room thermal capacitance for failure check kWh/C",value=4.0,min_value=0.1,max_value=100.0)
failure_initial = st.number_input("Room temperature immediately before failure C",value=20.0,min_value=10.0,max_value=35.0)
@st.cache_data(ttl=86400,show_spinner=False)
def cached_history(lat,lon,first,last):
 return fetch_history(lat,lon,first,last)
history_key=(latitude,longitude,history_start,history_end)
if st.button("Retrieve historical weather and size AC"):
 try:
  with st.spinner("Retrieving ERA5 hourly history in five-year batches..."):
   st.session_state['design_history']=(history_key,*cached_history(*history_key))
 except Exception as exc:
  st.session_state.pop('design_history',None)
  st.error("Historical sizing unavailable: "+str(exc)+". No forecast substitution is used.")
design_result=None
record=st.session_state.get('design_history')
if record and record[0]==history_key:
 history,history_urls=record[1:]
 def peak_load(out,rhout,irr,**kwargs):
  terms=load(out,rhout,irr,**kwargs)
  terms['Equipment']=peak_equipment
  return terms
 design_result=design_analysis(history,peak_load,design_indoor,design_margin,stress_uplift,design_ach)
 d=design_result
 outage=redundancy(d['required_kw'],[unit_tr]*unit_count,derating)
 st.metric("Historical extreme design cooling including allowance",f"{d['required_kw']:.2f} kW")
 st.write(f"Governing hour: {d['governing_hour']} IST; dry bulb {d['governing_temperature']:.2f} C; coincident RH {d['governing_rh']:.1f}%; GHI {d['governing_ghi']:.1f} W/m2. {len(history):,} hourly records, {history_start}-{history_end}, ERA5 via Open-Meteo.")
 st.write(f"After largest unit fails: {outage['surviving_kw']:.2f} kW available; design requirement {d['required_kw']:.2f} kW.")
 (st.success if outage['pass_n_plus_one'] else st.error)("N+1 capacity check: "+("PASS" if outage['pass_n_plus_one'] else "FAIL"))
 alternatives=[]
 for count in [2,3,4]:
  per_unit=d['required_kw']/((count-1)*3.517*derating)
  alternatives.append({'Installed units':count,'Duty units':count-1,'Standby units':1,'Minimum nominal TR/unit':per_unit,'Installed minimum TR':per_unit*count})
 redundancy_table=pd.DataFrame(alternatives)
 st.dataframe(redundancy_table.round(3),hide_index=True)
 # Loss of one of N duty units until standby starts; no credit for PV availability.
 lost_duty_capacity=max(0,(unit_count-2)*unit_tr*3.517*derating)
 shortfall=max(0,d['required_kw']-lost_duty_capacity)
 estimated_rise=shortfall*activation_delay/60/resilience_mass
 st.write(f"Simplified temperature after standby delay: {failure_initial+estimated_rise:.2f} C (rise {estimated_rise:.2f} C).")
 if failure_initial+estimated_rise>design_indoor: st.error("Standby-delay screening exceeds design temperature limit.")
 st.caption("Constant peak-load lumped thermal estimate only; no hotspot, sensor/control delay distribution, compressor restart or moisture dynamics. N+1 capacity is not proof of transient or common-power-failure resilience. PV receives no firm-capacity credit.")
 st.bar_chart(d['components'])
 st.dataframe(d['percentiles'],hide_index=True)
 st.line_chart(d['annual'].set_index('Year'))
 st.download_button("Download historical annual extremes CSV",d['annual'].to_csv(index=False),'historical_extremes.csv','text/csv')
 st.caption("Empirical percentiles are not an ASHRAE design-weather certification. ERA5 gridded history can understate local extremes. Validate against available local IMD observations; historical maxima do not guarantee future extremes. Solar/envelope treatment remains a simplified steady-state screening model.")
else:
 st.info("Retrieve historical weather to establish design capacity. No extreme-weather sizing result has been calculated for the selected location/period.")
st.divider()
st.header("Operational forecast energy and solar optimization")
if weather_mode == "Open-Meteo forecast" and weather is None:
 st.stop()

q=load(T,rh/100,ghi)
peak=1.15*sum(q.values())
h=np.arange(24);temp=T-8+5*np.sin((h-9)*np.pi/12)
sun=np.maximum(0,ghi*np.sin((h-6)*np.pi/12))
rhhour=np.clip(rh/100-.12*np.sin((h-9)*np.pi/12),.1,.95)
if weather is not None:
 temp=weather.temperature_2m.to_numpy(dtype=float)
 rhhour=weather.relative_humidity_2m.to_numpy(dtype=float)/100
 sun=weather.shortwave_radiation.to_numpy(dtype=float)
 T=float(temp.max()); ghi=float(sun.max())
 q=load(float(temp[np.argmax(temp)]),float(rhhour[np.argmax(temp)]),float(sun[np.argmax(temp)]))
 peak=1.15*max(sum(load(t,r,s).values()) for t,r,s in zip(temp,rhhour,sun))

cool=np.array([1.15*sum(load(t,r,s).values()) for t,r,s in zip(temp,rhhour,sun)])
electric=cool/np.maximum(2,3.5-.025*np.maximum(0,temp-35))
pv=np.arange(0,20.25,.25)
discount=sum(1/(1.08)**j for j in range(1,21))
benefit=[]
for p in pv:
 gen=p*sun/1000*.78
 savings=(np.minimum(gen,electric).sum()*tariff+np.maximum(0,gen-electric).sum()*export)*365
 benefit.append(savings*discount-p*capex-p*capex*.01*discount)
best=pv[np.argmax(benefit)]
# Compare fixed and optimized admissible temperature settings.
# A warmer setpoint reduces sensible and dehumidification loads in this model.
# Optimization is constrained by a user-provided equipment temperature limit.
def simulate_setpoint(sp):
 components=pd.DataFrame([load(t,r,s,setpoint=sp) for t,r,s in zip(temp,rhhour,sun)])
 thermal=components.sum(axis=1).to_numpy()
 cop=np.maximum(2,3.5-.025*np.maximum(0,temp-35))
 ac_power=thermal/cop
 generation=pv_installed*sun/1000*.78
 imports=np.maximum(0,ac_power-generation)
 exports=np.maximum(0,generation-ac_power)
 return components,thermal,ac_power,generation,imports,exports

candidates=np.arange(min_target,max_target+.001,setpoint_step)
comparison=[]
for sp in candidates:
 comp,th,power,gen,imports,exports=simulate_setpoint(sp)
 comparison.append({"Setpoint C":sp,"Cooling kWh/day":th.sum(),
                    "AC electricity kWh/day":power.sum(),
                    "Grid import kWh/day":imports.sum(),
                    "Grid export kWh/day":exports.sum(),
                    "Net daily cost Rs":imports.sum()*tariff-exports.sum()*export})
comparison=pd.DataFrame(comparison)
optimal=comparison.loc[comparison["Grid import kWh/day"].idxmin()]
opt_sp=float(optimal["Setpoint C"])
components,thermal,power,solar_generation,grid_import,grid_export=simulate_setpoint(opt_sp)
fixed_components,fixed_thermal,fixed_power,_,fixed_import,_=simulate_setpoint(target)

st.subheader("Adaptive hourly temperature schedule — research simulation")
thermal_mass = st.slider("Effective thermal capacitance (kWh per deg C)", 0.5, 20.0, 4.0, 0.5)
max_rate = st.slider("Maximum hourly setpoint movement (deg C)", 0.5, 4.0, 1.0, 0.5)
start_temp = min_target if min_target == max_target else st.slider("Starting room temperature (deg C)", min_target, max_target, min_target, 0.5)
dynamic_objective = st.selectbox("Hourly optimization objective", ["Minimum grid imports", "Minimum electricity cost"])
states = np.round(np.arange(min_target, max_target + 0.001, 0.5), 2)
start_idx = int(np.argmin(np.abs(states - start_temp)))
pv_output = pv_installed * sun / 1000 * 0.78
hour_cop = np.maximum(2.0, 3.5 - 0.025 * np.maximum(0, temp - 35))

def transition(hour, previous, setting):
    gains = sum(load(float(temp[hour]), float(rhhour[hour]), float(sun[hour]), setpoint=float(setting)).values())
    cooling = gains + thermal_mass * (previous - setting)
    if cooling < -1e-9:
        return np.inf, 0.0, 0.0, 0.0, 0.0
    cooling = max(0.0, cooling)
    power = cooling / hour_cop[hour]
    imports = max(0.0, power - pv_output[hour])
    exports = max(0.0, pv_output[hour] - power)
    penalty = imports if dynamic_objective == "Minimum grid imports" else imports * tariff - exports * export
    return penalty, cooling, power, imports, exports

dp = np.full((25, len(states)), np.inf)
parents = np.full((24, len(states)), -1, dtype=int)
dp[0, start_idx] = 0.0
for hour in range(24):
    for i, before in enumerate(states):
        if not np.isfinite(dp[hour, i]):
            continue
        for j, after in enumerate(states):
            if abs(after - before) > max_rate + 0.00001:
                continue
            score, _, _, _, _ = transition(hour, before, after)
            cost = dp[hour, i] + score
            if cost < dp[hour + 1, j]:
                dp[hour + 1, j] = cost
                parents[hour, j] = i

# Close the daily cycle at its original temperature to avoid artificial savings.
selected = start_idx
if not np.isfinite(dp[24, selected]):
    st.error("No feasible closed-cycle schedule. Review temperature constraints.")
    st.stop()
schedule = np.zeros(24)
for hour in range(23, -1, -1):
    schedule[hour] = states[selected]
    selected = parents[hour, selected]
rows = []
previous = float(states[start_idx])
for hour, setting in enumerate(schedule):
    _, cooling, dyn_power, imports, exports = transition(hour, previous, setting)
    rows.append({"Hour": hour, "Room setpoint C": setting, "Outside temperature C": temp[hour],
                 "Cooling load kW": cooling, "AC power kW": dyn_power,
                 "Solar generation kW": pv_output[hour], "Grid import kW": imports,
                 "Grid export kW": exports})
    previous = setting
dynamic_table = pd.DataFrame(rows)
baseline_import = sum(transition(hour, float(states[start_idx]), float(states[start_idx]))[3] for hour in range(24))
a1, a2, a3 = st.columns(3)
a1.metric("Adaptive grid imports", "%.1f kWh/day" % dynamic_table["Grid import kW"].sum())
a2.metric("Fixed start-temperature imports", "%.1f kWh/day" % baseline_import)
a3.metric("Estimated grid savings", "%.1f kWh/day" % (baseline_import - dynamic_table["Grid import kW"].sum()))
st.plotly_chart(px.line(dynamic_table, x="Hour", y=["Room setpoint C", "Outside temperature C"],
                        title="Hourly room temperature schedule"), width="stretch")
st.plotly_chart(px.line(dynamic_table, x="Hour",
                        y=["AC power kW", "Solar generation kW", "Grid import kW"],
                        title="Hourly electricity balance"), width="stretch")
st.dataframe(dynamic_table.round(2), hide_index=True, width="stretch")
st.download_button("Download adaptive schedule CSV", dynamic_table.to_csv(index=False),
                   "adaptive_temperature_schedule.csv", mime="text/csv")
st.warning("Illustrative lumped-capacitance model with selected weather source, not a validated control algorithm. Follow approved relay and signalling-room temperature and humidity requirements. No direct control of AC or signalling equipment is implemented.")

st.subheader("Energy balance and optimal AC temperature")
k1,k2,k3,k4=st.columns(4)
k1.metric("Optimal setpoint",f"{opt_sp:.1f} °C")
k2.metric("Peak cooling load",f"{thermal.max():.2f} kW")
k3.metric("AC consumption",f"{power.sum():.1f} kWh/day")
k4.metric("External grid import",f"{grid_import.sum():.1f} kWh/day",
          delta=f"{grid_import.sum()-fixed_import.sum():.1f} kWh vs manual",delta_color="inverse")
st.caption("Optimization minimizes grid imports subject to the user-entered permitted temperature range. The highest permitted setpoint will generally win in this simplified model; do not raise it beyond equipment specifications.")
energy=pd.DataFrame({"Hour":h,"Ambient °C":temp,"Outdoor RH %":rhhour*100,
 "Equipment heat kW":components["Equipment"],"Solar heat gain kW":components["Solar"],
 "Roof/wall/window/door heat kW":components[["Roof","Walls","Window","Door"]].sum(axis=1),
 "Infiltration/other heat kW":components[["Infiltration sensible","Infiltration latent","Lighting"]].sum(axis=1),
 "Cooling load kW":thermal,"AC electric demand kW":power,
 "Solar PV generation kW":solar_generation,"Grid import kW":grid_import,"Grid export kW":grid_export})
st.plotly_chart(px.line(energy,x="Hour",y=["Ambient °C"],title="Hourly ambient temperature"),width="stretch")
st.plotly_chart(px.area(energy,x="Hour",y=["Equipment heat kW","Solar heat gain kW","Roof/wall/window/door heat kW","Infiltration/other heat kW"],title="Hourly heat-load contributions (kW)"),width="stretch")
st.plotly_chart(px.line(energy,x="Hour",y=["Cooling load kW","AC electric demand kW","Solar PV generation kW","Grid import kW"],title="Thermal load, electrical load, PV and grid import"),width="stretch")
st.plotly_chart(px.line(comparison,x="Setpoint C",y=["Grid import kWh/day","AC electricity kWh/day","Cooling kWh/day"],title="Setpoint optimization: daily energy versus permitted temperature"),width="stretch")
st.download_button("Download optimized hourly energy balance CSV",energy.to_csv(index=False),"relay_room_hourly_energy.csv",mime="text/csv")
st.download_button("Download setpoint optimization CSV",comparison.to_csv(index=False),"setpoint_optimization.csv",mime="text/csv")
st.info("Selected day weather: preliminary screening only. Cooling thermal kWh and electrical kWh are different. Grid imports use hourly coincidence without storage. Real sizing requires hourly measured/weather data, equipment limits, humidity control, cycling/part-load COP and reliability validation.")

a,b,c=st.columns(3)
a.metric("Peak thermal kW (+15%)",f"{peak:.2f}")
b.metric("Nominal ton equivalent",f"{peak/3.517:.2f} TR")
c.metric("Illustrative PV economic optimum",f"{best:.2f} kWp")
tab1,tab2,tab3=st.tabs(["Heat map and sources","Humidity / door / window","Solar insolation and NPV"])
with tab1:
 st.bar_chart(pd.Series(q))
 x=np.linspace(0,L,70);y=np.linspace(0,W,45);X,Y=np.meshgrid(x,y)
 raw=3.2*(1-np.exp(-np.hypot(X-acx,Y-acy)/4))+1.8*np.exp(-((X-rx)**2/.36+(Y-ry)**2/.42))
 iy=np.argmin(abs(y-ry));ix=np.argmin(abs(x-rx))
 Z=target+raw-raw[iy,ix]
 fig=px.imshow(Z,x=x,y=y,origin="lower",aspect="auto",color_continuous_scale="RdYlBu_r",labels={"color":"°C"})
 fig.add_scatter(x=[acx],y=[acy],mode="markers",name="AC",marker=dict(size=12))
 fig.add_scatter(x=[rx],y=[ry],mode="markers",name="Relay",marker=dict(size=12))
 st.plotly_chart(fig,width="stretch")
with tab2:
 rows=[{"Outdoor RH %":r,"Peak cooling kW":1.15*sum(load(T,r/100,ghi).values())} for r in range(20,100,10)]
 st.line_chart(pd.DataFrame(rows).set_index("Outdoor RH %"))
 st.dataframe(pd.DataFrame([{"Envelope":"Existing","Peak kW":peak},{"Envelope":"Better double glazing and sealed door","Peak kW":1.15*sum(load(T,rh/100,ghi,window=1.8,solar=.3,door=1.8,air=ach*.5).values())},{"Envelope":"Above plus insulated roof","Peak kW":1.15*sum(load(T,rh/100,ghi,roof=.5,window=1.8,solar=.3,door=1.8,air=ach*.5).values())}]),hide_index=True)
with tab3:
 hourly=pd.DataFrame({"hour":h,"ac_kW":electric,"solar_kW":best*sun/1000*.78,"ghi_Wm2":sun})
 st.line_chart(hourly.set_index("hour"))
 st.line_chart(pd.DataFrame({"PV kWp":pv,"NPV Rs proxy":benefit}).set_index("PV kWp"))
 st.download_button("Download hourly CSV",hourly.to_csv(index=False),"hourly.csv")
 st.warning("Selected 24-hour weather repeated 365 times; not real hourly insolation or investment-grade sizing. Verify with site 8760-hour GHI/DNI/DHI, shading and tariff data. Check redundancy and signalling safety.")


st.subheader("Complete design report")
def build_report():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, rightMargin=32, leftMargin=32)
    styles = getSampleStyleSheet()
    story = [Paragraph("Relay Room Thermal and Solar Design Report", styles["Title"])]
    def text(value):
        story.append(Paragraph(escape(str(value)), styles["BodyText"]))
        story.append(Spacer(1,6))
    text(f"Station: {station_name} ({station_code}); coordinates: {latitude}, {longitude}")
    text("Generated UTC: " + datetime.now(timezone.utc).isoformat())
    text("Weather source: " + weather_source + "; retrieved: " + fetched_at)
    text("Weather hours use Asia/Kolkata. Open-Meteo modelled forecast; attribution: https://open-meteo.com/, CC BY 4.0.")
    text("Preliminary screening only. Relay-end upper limit defaults to 21 C. The spatial map is illustrative, not CFD; forecast-day annualization is not investment-grade sizing. No AC control is implemented. Actual AC capacity and humidity dynamics are not modelled.")
    inputs = {key:globals()[key] for key in ["L","W","H","T","target","min_target","max_target","pv_installed","setpoint_step","rh","rh_in","Uroof","Uwall","Aw","Uw","shgc","Ad","Ud","ach","equipment","ghi","acx","acy","rx","ry","tariff","export","capex","thermal_mass","max_rate","start_temp","dynamic_objective"]}
    if design_result is not None:
        text("HISTORICAL EXTREME DESIGN: ERA5 via Open-Meteo; period " + str(history_start) + "-" + str(history_end))
        for key in ['required_kw','raw_peak_kw','governing_hour','governing_temperature','governing_rh','governing_ghi']: text(f"{key}: {design_result[key]}")
        for key in ['design_indoor','design_margin','stress_uplift','peak_equipment','design_ach','derating','unit_count','unit_tr','activation_delay','resilience_mass','failure_initial']: text(f"{key}: {globals()[key]}")
        text("Largest-unit-out verification: " + str(outage))
        text(f"Standby-delay estimated temperature: {failure_initial+estimated_rise:.3f} C")
        text("Historical request provenance: " + " ; ".join(history_urls))
    else:
        text("EXTREME DESIGN NOT EVALUATED: forecast-day sizing below is operational screening only.")
    story.append(Paragraph("Inputs (units match application labels)",styles["Heading1"]))
    for key,value in inputs.items(): text(f"{key}: {value}")
    text(f"Peak design cooling including 15% allowance: {peak:.3f} kW; {peak/3.517:.3f} TR")
    text(f"Illustrative PV economic optimum: {best:.2f} kWp; fixed optimum: {opt_sp:.1f} C")
    text(f"Adaptive import: {dynamic_table['Grid import kW'].sum():.3f} kWh; baseline import: {baseline_import:.3f} kWh")
    def table(title, frame):
        story.append(PageBreak())
        story.append(Paragraph(title,styles["Heading1"]))
        # Split wide tables into readable groups, repeating the time/key column.
        for offset in range(1,len(frame.columns),4):
            part=frame.iloc[:,[0]+list(range(offset,min(offset+4,len(frame.columns))))].round(3)
            rows=[[Paragraph(escape(str(c)),styles["BodyText"]) for c in part.columns]]+part.astype(str).values.tolist()
            t=LongTable(rows,repeatRows=1,colWidths=[100]*len(part.columns))
            t.setStyle([("GRID",(0,0),(-1,-1),.3,colors.grey),("FONTSIZE",(0,1),(-1,-1),7),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke)])
            story.extend([t,Spacer(1,12)])
    if design_result is not None:
        table("Historical annual extremes",design_result['annual'])
        table("Historical empirical percentiles",design_result['percentiles'])
        table("N+1 alternatives",redundancy_table)
        table("Governing-hour design heat sources",pd.DataFrame({'Source':list(design_result['components'].index),'kW':list(design_result['components'].values)}))
    if weather is not None: table("Hourly weather inputs",weather)
    table("Adaptive hourly results",dynamic_table)
    table("Heat load at peak ambient hour",pd.DataFrame({"Source":list(q),"kW":list(q.values())}))
    table("Humidity sensitivity",pd.DataFrame(rows))
    table("Fixed optimal setpoint energy and heat contributions",energy)
    table("Setpoint alternatives",comparison)
    table("PV economic alternatives (single-day annualization)",pd.DataFrame({"PV kWp":pv,"NPV Rs proxy":benefit}))
    text("Model: envelope UA delta-T + equipment + lighting + solar surrogate + sensible and latent infiltration. AC electricity = cooling/COP; PV = kWp x GHI/1000 x 0.78. Dynamic programming minimizes imports or cost with thermal capacitance, rate bounds and equal starting/ending temperature. Negative cooling transitions are rejected. No battery is modelled.")
    doc.build(story)
    return buffer.getvalue()
st.download_button("Download complete design report PDF", build_report(), "relay_room_design_report.pdf", mime="application/pdf")
