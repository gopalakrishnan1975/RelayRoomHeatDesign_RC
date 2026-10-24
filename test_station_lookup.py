import math
import pytest
from station_lookup import catalogue,find_station,coordinate_location

def test_directory_and_exact_normalized_codes():
 index,metadata=catalogue()
 assert len(index)==metadata['valid_records']==8697
 assert find_station(' mci ')['name']=='MANCHIRYAL'
 assert find_station('SC')['name']=='SECUNDERABAD JN'
 assert find_station('NDLS')['latitude']==28.642314
 with pytest.raises(ValueError,match='not found'):find_station('ZZNOTREAL')
 with pytest.raises(ValueError):find_station('')

def test_manual_coordinate_location():
 r=coordinate_location('Plant room',17.4,78.5,' sc ')
 assert r['name']=='Plant room' and r['code']=='SC' and r['latitude']==17.4
 generated=coordinate_location('',17.4,78.5)
 assert generated['code'].startswith('LOC_')
 assert generated['code']==coordinate_location('',17.4,78.5)['code']
 for lat,lon in [(91,0),(0,181),(float('nan'),0),(0,float('inf'))]:
  with pytest.raises(ValueError):coordinate_location('',lat,lon)

def test_lookup_changes_name_and_coordinates_and_blocks_unknown():
 from pathlib import Path
 from streamlit.testing.v1 import AppTest
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 assert not at.exception
 next(x for x in at.text_input if x.label=='Station code').set_value('sc').run()
 assert next(x for x in at.text_input if x.label=='Station / site name').value=='SECUNDERABAD JN'
 assert next(x for x in at.number_input if x.label=='Latitude').value==find_station('SC')['latitude']
 next(x for x in at.text_input if x.label=='Station code').set_value('ZZNOTREAL').run()
 assert not at.exception
 assert next(x for x in at.button if x.label=='Load weather and sunrise/sunset').disabled
 assert next(x for x in at.button if x.label=='Create station design revision').disabled
 next(x for x in at.radio if x.label=='Location entry').set_value('Manual coordinates').run()
 assert not at.exception
 assert next(x for x in at.number_input if x.label=='Latitude').value is None
 assert next(x for x in at.button if x.label=='Load weather and sunrise/sunset').disabled

def test_manual_revision_and_old_revision_coordinates_are_preserved():
 from pathlib import Path
 from streamlit.testing.v1 import AppTest
 at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
 at.session_state['restored_payload']={'station':'Exact building','code':'MCI','latitude':18.872,'longitude':79.444}
 at.session_state['restore_epoch']=1
 at.run()
 assert not at.exception
 assert next(x for x in at.radio if x.label=='Location entry').value=='Manual coordinates'
 assert next(x for x in at.number_input if x.label=='Latitude').value==18.872
 next(x for x in at.number_input if x.label=='Latitude').set_value(17.4).run()
 next(x for x in at.number_input if x.label=='Longitude').set_value(78.5).run()
 next(x for x in at.text_input if x.label=='Station code').set_value('').run()
 next(x for x in at.button if x.label=='Create station design revision').click().run()
 assert not at.exception
 saved=at.session_state['download_revision']
 assert saved['station_code'].startswith('LOC_')
 assert saved['payload']['latitude']==17.4 and saved['payload']['longitude']==78.5
 assert saved['payload']['location_mode']=='Manual coordinates'
