"""Offline regression checks: deterministic weather; no forecast dependency."""
import io
import json
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


def test_weather_report_and_temperature_bounds():
    fixture = {'hourly': {'time': [f'2026-10-23T{h:02d}:00' for h in range(24)],
        'temperature_2m': [30.] * 24, 'relative_humidity_2m': [55.] * 24,
        'shortwave_radiation': [max(0,800*(1-abs(h-12)/6)) for h in range(24)]}}
    with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(fixture).encode())):
        at = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=60).run()
    assert not at.exception
    assert not at.error
    assert len(at.get('download_button')) == 5
    assert at.text_input[0].value == 'Mancherial'
    assert at.text_input[1].value == 'MCI'
    at.radio[0].set_value('Synthetic demonstration').run(timeout=60)
    assert not at.exception
    # Exercise an adaptive range, rather than only the fixed 21 C default.
    next(s for s in at.slider if s.label == 'Maximum permitted relay-end temperature C').set_value(26.).run(timeout=60)
    assert not at.exception
