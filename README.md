# Generic Room Heat Load and Site Energy Planner

[Open Streamlit app](https://relayroomheatdesignrc-fhfhpzvryxnksd7cef9kg8.streamlit.app/)

Run `pip install -r requirements.txt` and `streamlit run app.py`.

The main page now exposes room length/width/height, total window and door areas, equipment kW and people. Add rooms, set target temperatures and proposed AC units, and assign fans/lights/other circuits to rooms or Site exterior. Night/daylight schedules follow daily Open-Meteo sunrise/sunset; occupied hours are configurable.

Historical ERA5 weather supports extreme coincident AC sizing with derated largest-unit-out N+1 checks. Aggregate electricity includes AC, equipment, fans, lights and other circuits without double-counting. Historical hourly demand and solar feed area-constrained PV life-cycle cost optimization with base/peak import and export tariffs. Forecast mode remains operations-only.

Download PDF design report, full hourly demand CSV and input/provenance JSON. See the [rewritten integrated manual](docs/Generic_Room_Site_Energy_Manual.md) and [wiki](docs/wiki/Home.md).

The previous relay calculator remains available from the Calculator selector. Both are engineering screening tools, not CFD, certified HVAC procurement designs or physical AC controllers. No battery or demand-charge optimization is included.

Tests: `pip install pytest` then `pytest -q`. Daily GitHub Actions and maintenance checks cover the application.
