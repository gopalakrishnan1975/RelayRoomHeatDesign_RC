"""Railway facility templates and preliminary transformer / battery sizing."""
import numpy as np
import pandas as pd
from site_energy import ROOM_DEFAULT

TEMPLATES = {
 "Custom / blank": ([], []),
 "Relay room": ([dict(Room='Relay room',Length_m=8.,Width_m=5.,Height_m=3.,Window_m2=1.,Door_m2=2.,Equipment_kW=3.,People=1,Target_C=21.,Occupancy='Always')], [('Relay room lights','Relay room','Light',6,18,'Always')]),
 "Catering stall": ([dict(Room='Catering stall',Length_m=4.,Width_m=3.,Height_m=3.,Window_m2=2.,Door_m2=2.,Equipment_kW=2.,People=3,Target_C=26.,Occupancy='Occupied hours')], [('Stall lights','Catering stall','Light',6,15,'Occupied hours'),('Stall exhaust','Catering stall','Fan',2,90,'Occupied hours')]),
 "Waiting hall": ([dict(Room='Waiting hall',Length_m=20.,Width_m=12.,Height_m=4.,Window_m2=35.,Door_m2=12.,Equipment_kW=1.,People=80,Target_C=26.,Occupancy='Always')], [('Hall lights','Waiting hall','Light',35,20,'Night'),('Hall fans','Waiting hall','Fan',18,75,'Always')]),
 "Running room": ([dict(Room='Running room',Length_m=12.,Width_m=10.,Height_m=3.2,Window_m2=18.,Door_m2=6.,Equipment_kW=2.,People=18,Target_C=25.,Occupancy='Always')], [('Running room lights','Running room','Light',18,15,'Night'),('Running room fans','Running room','Fan',10,60,'Always')]),
 "Kitchen": ([dict(Room='Kitchen',Length_m=9.,Width_m=7.,Height_m=3.5,Window_m2=5.,Door_m2=5.,Equipment_kW=12.,People=8,Target_C=26.,Occupancy='Occupied hours')], [('Kitchen lights','Kitchen','Light',12,20,'Occupied hours'),('Kitchen exhaust','Kitchen','Fan',3,500,'Occupied hours')]),
 "Food stall": ([dict(Room='Food stall',Length_m=5.,Width_m=3.,Height_m=3.,Window_m2=2.,Door_m2=3.,Equipment_kW=4.,People=4,Target_C=26.,Occupancy='Occupied hours')], [('Food stall lights','Food stall','Light',8,15,'Occupied hours'),('Food stall fans','Food stall','Fan',2,75,'Occupied hours')]),
 "High mast lights": ([dict(Room='Unconditioned electrical kiosk - REMOVE AC FOR FINAL DESIGN',Length_m=3.,Width_m=3.,Height_m=3.,Window_m2=0.,Door_m2=2.,Equipment_kW=0.,People=0,Target_C=30.,Occupancy='Off')], [('High mast luminaires','Site exterior','Light',12,200,'Night')]),
}
def template_data(name):
    rooms, loads=TEMPLATES[name]
    r=pd.DataFrame([dict(ROOM_DEFAULT,**item) for item in rooms]) if rooms else pd.DataFrame([ROOM_DEFAULT])
    c=pd.DataFrame([dict(Load=label,Room=room,Type=kind,Count=count,Watts_each=watts,Schedule=sched) for label,room,kind,count,watts,sched in loads])
    return r,c

STANDARD_KVA=(16,25,63,100,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000)
def transformer_design(peak_kw, pv_kwp, power_factor=.9, utilization=.8, reserve=.2, export_limit_kw=None):
    """Conservative preliminary apparent-power screening, not fault/protection design."""
    if not (0<power_factor<=1 and 0<utilization<=1 and reserve>=0):raise ValueError('Invalid PF, utilization or reserve')
    if peak_kw<0 or pv_kwp<0:raise ValueError('Negative demand or PV')
    import_kva=peak_kw*(1+reserve)/(power_factor*utilization)
    export_kw=pv_kwp if export_limit_kw is None else min(pv_kwp,max(0,export_limit_kw))
    export_kva=export_kw/(power_factor*utilization)
    required=max(import_kva,export_kva)
    selected=next((x for x in STANDARD_KVA if x>=required),None)
    return dict(import_design_kva=import_kva,export_design_kva=export_kva,required_kva=required,standard_kva=selected,oversize_warning=selected is None)

def battery_dispatch(hourly,pv_kwp,capacity_kwh,power_kw,roundtrip_eff=.9,initial_soc=.5,min_soc=.1,max_soc=.9):
    """Hourly self-consumption dispatch: charge from surplus PV, discharge against load.
    No grid charging, time-of-use arbitrage, backup reserve or degradation model.
    """
    if capacity_kwh<0 or power_kw<0 or not (0<roundtrip_eff<=1) or not (0<=min_soc<=initial_soc<=max_soc<=1):
        raise ValueError('Invalid battery configuration')
    demand=hourly['Total demand kW'].to_numpy(float)
    pv=pv_kwp*hourly['GHI W/m2'].to_numpy(float)/1000
    soc=capacity_kwh*initial_soc
    eta=np.sqrt(roundtrip_eff)
    imports=np.zeros(len(demand));exports=np.zeros(len(demand));soc_trace=np.zeros(len(demand))
    for i,(d,s) in enumerate(zip(demand,pv)):
        surplus=max(0,s-d);deficit=max(0,d-s)
        charge=min(surplus,power_kw,(capacity_kwh*max_soc-soc)/eta) if capacity_kwh else 0
        soc+=charge*eta
        discharge=min(deficit,power_kw,(soc-capacity_kwh*min_soc)*eta) if capacity_kwh else 0
        soc-=discharge/eta
        imports[i]=deficit-discharge;exports[i]=surplus-charge;soc_trace[i]=soc
    return pd.DataFrame({'Grid import kW':imports,'Grid export kW':exports,'Battery SOC kWh':soc_trace},index=hourly.index)
