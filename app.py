import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Relay Room Thermal + Solar",layout="wide")
st.title("Interlocking Room | Thermal and Solar Simulator")
st.caption("Preliminary heat-balance screening. Spatial heat map is an illustrative surrogate, NOT CFD.")
with st.sidebar:
 L=st.slider("Length m",3.,20.,8.);W=st.slider("Width m",3.,15.,5.);H=st.slider("Height m",2.,6.,3.)
 T=st.slider("Outdoor peak temperature C",25.,50.,42.);target=st.slider("Manual relay-end air setpoint C",18.,30.,21.)
 min_target=st.slider("Minimum permitted relay-end temperature C",18.,30.,21.)
 max_target=st.slider("Maximum permitted relay-end temperature C",min_target,35.,max(26.,min_target))
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
 dt=max(0,out-sp)
 wall=2*(L+W)*H-Aw-Ad
 mdot=1.18*L*W*H*air/3600
 latent=max(0,mdot*2501*(w(out,rhout)-w(sp,rh_in/100)))
 terms={"Roof":roof*L*W*dt/1000,"Walls":Uwall*wall*dt/1000,
 "Window":window*Aw*dt/1000,"Door":door*Ad*dt/1000,
 "Solar":irr*(.15*L*W+.0192*wall+Aw*solar)/1000,
 "Equipment":equipment,"Lighting":.2,
 "Infiltration sensible":mdot*1.006*dt,"Infiltration latent":latent}
 return terms
q=load(T,rh/100,ghi)
peak=1.15*sum(q.values())
h=np.arange(24);temp=T-8+5*np.sin((h-9)*np.pi/12)
sun=np.maximum(0,ghi*np.sin((h-6)*np.pi/12))
rhhour=np.clip(rh/100-.12*np.sin((h-9)*np.pi/12),.1,.95)
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
st.plotly_chart(px.line(energy,x="Hour",y=["Ambient °C"],title="Hourly ambient temperature"),use_container_width=True)
st.plotly_chart(px.area(energy,x="Hour",y=["Equipment heat kW","Solar heat gain kW","Roof/wall/window/door heat kW","Infiltration/other heat kW"],title="Hourly heat-load contributions (kW)"),use_container_width=True)
st.plotly_chart(px.line(energy,x="Hour",y=["Cooling load kW","AC electric demand kW","Solar PV generation kW","Grid import kW"],title="Thermal load, electrical load, PV and grid import"),use_container_width=True)
st.plotly_chart(px.line(comparison,x="Setpoint C",y=["Grid import kWh/day","AC electricity kWh/day","Cooling kWh/day"],title="Setpoint optimization: daily energy versus permitted temperature"),use_container_width=True)
st.download_button("Download optimized hourly energy balance CSV",energy.to_csv(index=False),"relay_room_hourly_energy.csv",mime="text/csv")
st.download_button("Download setpoint optimization CSV",comparison.to_csv(index=False),"setpoint_optimization.csv",mime="text/csv")
st.info("Synthetic weather/insolation: representative day only. Cooling thermal kWh and electrical kWh are different. Grid imports use hourly coincidence without storage. Real sizing requires hourly measured/weather data, equipment limits, humidity control, cycling/part-load COP and reliability validation.")

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
 st.plotly_chart(fig,use_container_width=True)
with tab2:
 rows=[{"Outdoor RH %":r,"Peak cooling kW":1.15*sum(load(T,r/100,ghi).values())} for r in range(20,100,10)]
 st.line_chart(pd.DataFrame(rows).set_index("Outdoor RH %"))
 st.dataframe(pd.DataFrame([{"Envelope":"Existing","Peak kW":peak},{"Envelope":"Better double glazing and sealed door","Peak kW":1.15*sum(load(T,rh/100,ghi,window=1.8,solar=.3,door=1.8,air=ach*.5).values())},{"Envelope":"Above plus insulated roof","Peak kW":1.15*sum(load(T,rh/100,ghi,roof=.5,window=1.8,solar=.3,door=1.8,air=ach*.5).values())}]),hide_index=True)
with tab3:
 hourly=pd.DataFrame({"hour":h,"ac_kW":electric,"solar_kW":best*sun/1000*.78,"ghi_Wm2":sun})
 st.line_chart(hourly.set_index("hour"))
 st.line_chart(pd.DataFrame({"PV kWp":pv,"NPV Rs proxy":benefit}).set_index("PV kWp"))
 st.download_button("Download hourly CSV",hourly.to_csv(index=False),"hourly.csv")
 st.warning("Synthetic 24-hour weather repeated 365 times; not real hourly insolation or investment-grade sizing. Verify with site 8760-hour GHI/DNI/DHI, shading and tariff data. Check redundancy and signalling safety.")
