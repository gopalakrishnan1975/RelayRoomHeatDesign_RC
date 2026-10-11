import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Relay Room Thermal + Solar",layout="wide")
st.title("Interlocking Room | Thermal and Solar Simulator")
st.caption("Preliminary heat-balance screening. Spatial heat map is an illustrative surrogate, NOT CFD.")
with st.sidebar:
 L=st.slider("Length m",3.,20.,8.);W=st.slider("Width m",3.,15.,5.);H=st.slider("Height m",2.,6.,3.)
 T=st.slider("Outdoor temperature C",25.,50.,42.);target=st.slider("Relay-end air target C",18.,28.,21.)
 rh=st.slider("Outdoor RH %",10,95,55);rh_in=st.slider("Indoor RH %",35,65,50)
 Uroof=st.slider("Roof U value W/m2K",.2,5.,2.5);Uwall=st.slider("Wall U value",.2,4.,1.8)
 Aw=st.slider("Window m2",0.,15.,3.);Uw=st.slider("Window U value",.7,7.,5.7)
 shgc=st.slider("Window SHGC",.1,.9,.75);Ad=st.slider("Door m2",0.,6.,2.);Ud=st.slider("Door U value",.7,6.,3.)
 ach=st.slider("Air changes per hour",.05,3.,.35);equipment=st.slider("Equipment kW",.1,10.,2.)
 ghi=st.slider("Peak solar W/m2",0.,1100.,800)
 acx=st.slider("AC X m",0.,float(L),0.);acy=st.slider("AC Y m",0.,float(W),float(W/2))
 rx=st.slider("Relay X m",0.,float(L),float(L*.8));ry=st.slider("Relay Y m",0.,float(W),float(W/2))
 tariff=st.number_input("Import Rs/kWh",value=8.);export=st.number_input("Export Rs/kWh",value=2.)
 capex=st.number_input("PV Rs/kWp",value=50000.)

def sat(t):return 610.94*np.exp(17.625*t/(t+243.04))
def w(t,r):
 p=sat(t)*r
 return .62198*p/(101325-p)
def load(out,rhout,irr,roof=Uroof,window=Uw,solar=shgc,door=Ud,air=ach):
 dt=max(0,out-target)
 wall=2*(L+W)*H-Aw-Ad
 mdot=1.18*L*W*H*air/3600
 latent=max(0,mdot*2501*(w(out,rhout)-w(target,rh_in/100)))
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
