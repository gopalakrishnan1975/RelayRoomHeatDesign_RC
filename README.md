# Generic Room Heat Load and Site Energy Planner

[Open Streamlit app](https://relayroomheatdesignrc-fhfhpzvryxnksd7cef9kg8.streamlit.app/)

Run `pip install -r requirements.txt` and `streamlit run app.py`.

The main page now exposes room length/width/height, total window and door areas, equipment kW and people. Add rooms, set target temperatures and proposed AC units, and assign fans/lights/other circuits to rooms or Site exterior. Night/daylight schedules follow daily Open-Meteo sunrise/sunset; occupied hours are configurable.

Historical ERA5 weather supports extreme coincident AC sizing with derated largest-unit-out N+1 checks. Aggregate electricity includes AC, equipment, fans, lights and other circuits without double-counting. Historical hourly demand and solar feed area-constrained PV life-cycle cost optimization with base/peak import and export tariffs. Forecast mode remains operations-only.

Download PDF design report, full hourly demand CSV and input/provenance JSON. See the [rewritten integrated manual](docs/Generic_Room_Site_Energy_Manual.md) and [wiki](docs/wiki/Home.md).

The previous relay calculator remains available from the Calculator selector. Both are engineering screening tools, not CFD, certified HVAC procurement designs or physical AC controllers. No battery or demand-charge optimization is included.

Tests: `pip install pytest` then `pytest -q`. Daily GitHub Actions and maintenance checks cover the application.


## Running rooms, station revisions and grid commitments (24 October 2026)
Running room now expands into individual bedrooms plus kitchen, dining, lobby, baths, laundry and corridors. Peak guests and a sleeping profile drive operating heat, with shared-zone guest allocation to avoid double counting. Full zone occupancy remains the conservative room AC sizing basis. Non-conditioned service zones do not incur artificial AC demand.

Create/download a station revision JSON, retain it in the station's OneDrive folder, then upload/restore it to create the next revision with a parent hash. This is portable versioning, not a central authenticated registry or automatic OneDrive sync.

Upload actual interval demand CSV (`timestamp,kva` or `timestamp,kw,pf`) for monthly peaks and contract-kVA cost comparisons under explicitly entered demand charges/minimums/penalties. Simulated hourly comparisons are clearly labelled; contract reductions require adequate seasonal meter evidence and utility approval. The app never submits a contract change.

See the [running room / station versions / grid demand manual](docs/Running_Room_Versions_Grid_Manual.md).
