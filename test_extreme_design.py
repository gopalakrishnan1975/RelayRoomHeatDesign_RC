import numpy as np
import pandas as pd
from extreme_design import design_analysis,redundancy

def test_redundancy_largest_unit_out():
 assert not redundancy(12,[4,4],.85)['pass_n_plus_one']
 assert redundancy(12,[2.5,2.5,2.5],.85)['pass_n_plus_one']
 assert np.isclose(redundancy(12,[1,2,8],.85)['surviving_kw'],(1+2)*3.517*.85)

def test_coincident_load_not_combined_independent_extremes():
 frame=pd.DataFrame({'time':pd.date_range('2020-01-01',periods=3,freq='h'),'temperature_2m':[45,30,35],'relative_humidity_2m':[10,90,50],'shortwave_radiation':[0,100,900]})
 def load(t,r,s,**kw):return {'equipment':2,'temperature':t/10,'humidity':r,'solar':s/100}
 d=design_analysis(frame,load,21,10,0,.5)
 assert d['governing_hour']=='2020-01-01 02:00:00'
 assert np.isclose(d['required_kw'],(2+3.5+.5+9)*1.1)
