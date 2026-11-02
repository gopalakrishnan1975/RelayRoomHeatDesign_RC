"""Portable station lookup revisions retain the saved geographical basis."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from station_lookup import find_station


def _app_with_saved(code='MCI'):
    at=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
    assert not at.exception
    at.session_state['restored_payload']={
        'station':'Historical facility location','code':code,
        'location_mode':'Station code lookup','latitude':18.872,'longitude':79.444,
        'location_source':{'source':'Original saved station directory','source_commit':'historic'},
        'basis':'Historical extreme design + annual energy'}
    at.session_state['restore_epoch']=1
    at.run()
    return at


def test_lookup_revision_retains_saved_coordinates_and_allows_explicit_adoption():
    at=_app_with_saved()
    assert not at.exception
    assert next(x for x in at.radio if x.label=='Location entry').value=='Station code lookup'
    assert next(x for x in at.number_input if x.label=='Latitude').value==18.872
    assert next(x for x in at.number_input if x.label=='Longitude').value==79.444
    assert next(x for x in at.text_input if x.label=='Station / site name').value=='Historical facility location'
    assert next(x for x in at.button if x.label=='Load weather and sunrise/sunset').disabled is False
    next(x for x in at.checkbox if x.label.startswith('Adopt current catalogue coordinates')).set_value(True).run()
    assert not at.exception
    assert next(x for x in at.number_input if x.label=='Latitude').value==find_station('MCI')['latitude']
    assert next(x for x in at.number_input if x.label=='Longitude').value==find_station('MCI')['longitude']


def test_lookup_revision_retains_saved_location_when_code_missing_from_current_catalogue():
    at=_app_with_saved('ZZOLD')
    assert not at.exception
    assert next(x for x in at.number_input if x.label=='Latitude').value==18.872
    assert next(x for x in at.number_input if x.label=='Longitude').value==79.444
    assert next(x for x in at.button if x.label=='Load weather and sunrise/sunset').disabled is False
    next(x for x in at.text_input if x.label=='Station code').set_value('ZZNOTREAL').run()
    assert next(x for x in at.button if x.label=='Load weather and sunrise/sunset').disabled is True
    next(x for x in at.radio if x.label=='Location entry').set_value('Manual coordinates').run()
    assert not at.exception
    assert next(x for x in at.number_input if x.label=='Latitude').value is None
    assert next(x for x in at.number_input if x.label=='Longitude').value is None
    assert next(x for x in at.button if x.label=='Create station design revision').disabled is True
