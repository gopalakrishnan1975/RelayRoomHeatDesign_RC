"""Service-day accounting regressions: Time IST marks the END of each hourly bin."""
import numpy as np
import pandas as pd
import pytest
from ev_charging import charging_profile, EV_DEFAULTS

P={'pv_pr':.78,'peak_start':18,'peak_end':22,'peak_tariff':10.,'tariff':8.,'export_tariff':2.}

def hourly(start,n):
    return pd.DataFrame({'Time IST':pd.date_range(start,periods=n,freq='h'),
                         'Total demand kW':np.zeros(n),'GHI W/m2':np.zeros(n)})

def group(start,end,energy=2.,power=1.):
    return pd.DataFrame([dict(EV_DEFAULTS[0],Points=1,Grid_kW_per_point=power,
                              Efficiency=1.,Vehicles_per_day=1,
                              Battery_kWh_per_vehicle=energy,
                              Start_hour=start,End_hour=end)])

def test_daytime_two_days_not_three():
    ev,summary,_=charging_profile(hourly('2025-01-01 01:00',48),group(8,10),0,P)
    assert summary['Requested grid kWh (period)'].iloc[0]==4
    assert ev.sum()==4

def test_overnight_two_complete_windows():
    h=hourly('2025-01-01 01:00',49)
    ev,summary,_=charging_profile(h,group(23,1),0,P)
    assert summary['Requested grid kWh (period)'].iloc[0]==4
    assert ev.sum()==4
    assert ev[h['Time IST'].dt.hour.eq(0)].sum()==2

def test_overnight_incomplete_trailing_window_excluded():
    ev,summary,_=charging_profile(hourly('2025-01-01 01:00',48),group(23,1),0,P)
    assert summary['Requested grid kWh (period)'].iloc[0]==2
    assert ev.sum()==2
    assert summary['Incomplete service windows excluded'].iloc[0]>=1

def test_all_day_window_48_bins_at_midnight_or_one_am():
    for start in ['2025-01-01 00:00','2025-01-01 01:00']:
        ev,summary,_=charging_profile(hourly(start,48),group(0,0,20,20),0,P)
        assert summary['Requested grid kWh (period)'].iloc[0]==40
        assert ev.sum()==40

def test_all_day_49_bins_does_not_create_third_day():
    ev,summary,_=charging_profile(hourly('2025-01-01 00:00',49),group(0,0,20,20),0,P)
    assert summary['Requested grid kWh (period)'].iloc[0]==40
    assert ev.sum()==40
    assert summary['Incomplete service windows excluded'].iloc[0]==1

def test_overnight_year_boundary():
    ev,summary,_=charging_profile(hourly('2025-12-31 01:00',49),group(23,1),0,P)
    assert summary['Requested grid kWh (period)'].iloc[0]==4
    assert ev.sum()==4

def test_managed_import_ceiling():
    h=hourly('2025-01-01 01:00',49)
    h['Total demand kW']=9.
    ev,summary,_=charging_profile(h,group(23,1,2.,10.),0,P,True,10.)
    assert np.all(ev<=1+1e-9)
    assert summary['Unserved battery kWh (period)'].iloc[0]==0

def test_invalid_hourly_sequence_rejected():
    h=hourly('2025-01-01 01:00',48)
    bad=[h.drop(2).reset_index(drop=True),h.assign(**{'Time IST':h['Time IST'].mask(h.index==2,h['Time IST'].iloc[1])})]
    for frame in bad:
        with pytest.raises(ValueError,match='complete, unique'):
            charging_profile(frame,group(8,10),0,P)
