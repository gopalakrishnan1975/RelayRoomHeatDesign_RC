# Railway Facility Energy Design Studio
## Consolidated Technical, Business, Data, IT Architecture and User Manual
**Edition:** 1.0 · 24 October 2026 · **Status:** Engineering screening and software reference, not certified procurement design.

### Document control and precedence
This is the consolidated master for the GitHub application `gopalakrishnan1975/RelayRoomHeatDesign_RC`. It brings together the generic-room/site-energy manual, historical-extreme and N+1 guidance, running-room and station-version/grid-contract manual, station-code lookup manual, facility/transformer/BESS guide, hourly optimization and data/validation wiki, plus the implemented EV module. Earlier manuals remain as supporting source records. Where old documents say station codes are identifiers only, no BESS is supported, or the high-mast kiosk needs AC, **the current implementation and this master supersede those statements**. Recheck against source code for each release.

**Source register:** `docs/Generic_Room_Site_Energy_Manual.md`; `docs/Running_Room_Versions_Grid_Manual.md`; `docs/Station_Location_Lookup.md`; `docs/wiki/Extreme-Design-and-Redundancy.md`; `docs/wiki/Facility-Templates-Transformer-BESS.md`; `docs/wiki/Hourly-Optimization.md`; `docs/wiki/Thermal-Model.md`; `docs/wiki/Weather-and-PDF.md`; `docs/wiki/Data-and-Validation.md`; `docs/wiki/FAQ-and-Limitations.md`; original OneDrive `Relay_Room_Technical_Business_Data_IT_User_Manual.pdf`, `Extreme_Design_Redundancy_Update.md`, `hourly_ac_solar_optimization_paper.md`. This edition consolidates the documented capabilities, not a verbatim concatenation of every historical PDF.

### 1. Executive and business requirements
**Problem:** Railway facilities have heterogeneous loads (AC, critical electronics, occupancy, catering, lighting, EV chargers) but are frequently sized independently. This can lead to excess connected capacity, inadequate critical-room redundancy, inefficient solar/BESS sizing and inappropriate grid demand commitments.

**Objective:** Establish an auditable, station-specific design and scenario comparison workflow, balancing safety, comfort, energy cost, capital cost and operational feasibility. **Stakeholders:** DRM/divisional electrical, S&T, mechanical, engineering, commercial, finance, station managers, running-room managers, EV concessionaires and DISCOM. **Business outputs:** cooling TR with N+1 screening; peak coincident kW and transformer kVA; hourly/annual kWh; PV kWp and area; optional BESS kWh/kW; EV charging capacity and unserved energy; measured monthly kVA versus contracted demand; incremental cost and sensitivity; revision-controlled station design evidence.

**Decision gates:** (1) asset survey and source validation; (2) historical and occupancy design; (3) N+1 and electrical review; (4) meter-calibrated demand/economics; (5) tariff and DISCOM review; (6) approved procurement or contract modification outside the software. The app must never silently authorize equipment procurement, power sanction reduction or physical AC control.

### 2. Facility scope and templates
- **Relay rooms:** critical equipment heat, stringent approved target temperature, humidity, manufacturer derating, N+1 largest-unit-out, independent power/alarm protection.
- **Catering stall / food stall / kitchen:** equipment and refrigeration, people, lights, fans, cooking and exhaust; hood makeup air, combustion and latent process heat need separate detailed design.
- **Waiting halls:** variable crowds, peak occupancy and daylight/night lighting; do not assume constant occupancy equals a measured peak.
- **Running rooms:** model as a hotel-like building with individually enumerated bedrooms, beds/room, maximum simultaneous guests, staff, lobby/reception, dining, kitchen, bathrooms, laundry, corridors, pumps, hot water and exterior lights. Bedroom design checks full permitted bed occupancy. Hourly sleeping and meal profiles distribute guests between zones without double counting; shared service areas can be unconditioned. Inputs and electrical schedules must be replaced with actual building programme and rosters.
- **High-mast lights:** exterior-only luminaire load; kiosk/service zone is unconditioned and must not create phantom cooling.
- **Custom:** any combination of rooms and exterior circuits.
- **EV charging:** separate two-wheeler AC/slow (illustrative 1.5 kW), two-wheeler higher-power (3.3 kW), four-wheeler AC destination (7.4 kW), four-wheeler DC fast (64 kW). Ratings, counts, efficiencies, daily vehicle demand, battery energy per vehicle and charging windows are editable examples. Charger grid-input rating must include conversion losses appropriately and be validated against actual OEM equipment. Battery swapping inventory, queueing and charging taper are **not** simulated.

### 3. User workflow and essential inputs
1. Choose **Station code lookup** for an exact code match or **Manual coordinates** for a facility-level latitude/longitude and editable location name/description. Verify the station reference point versus actual building location.
2. Select a facility template and apply it. Review geometry, wall/opening areas, equipment kW, people, setpoint, AC-enabled status, AC units and TR. For a running room configure bedrooms, beds, peak guests/staff, cooking, hot-water and laundry connected loads.
3. Add lights/fans/other circuits with room/exterior assignment, quantity, watts and schedule. Never include a circuit again in room equipment kW.
4. Set historical complete-year range and load ERA5 hourly weather/sunrise/sunset. Forecast-day mode is for operations only, not installed capacity.
5. Set thermal assumptions (U-values, SHGC/solar factor, ACH, indoor RH, sensible/latent heat/person, COP, design allowance, derating) and inspect N+1 status.
6. Set transformer PF, utilization and reserve; PV area, performance ratio, tariffs and discount/capex; optional BESS kWh/kW/efficiency/cost; EV charger groups and managed/unmanaged scheduling.
7. Optionally upload interval-meter CSV and compare measured kVA peaks with candidate sanctioned demand and entered tariff terms.
8. Review heat contributions, design-hour conditions, whole-site peak and energy, solar/BESS dispatch, charging service levels and economics. Export hourly CSV, report PDF, inputs JSON and a station revision JSON. Retain revision files in a station-controlled folder and restore them for the next revision.

### 4. Data dictionary and provenance
| Entity / field | Type and unit | Origin | Validation / purpose |
|---|---|---|---|
| station_code, station_name | text | offline station directory or manual | normalized exact code; no stale fallback |
| latitude, longitude | decimal degrees | directory or surveyed coordinates | finite, latitude -90..90, longitude -180..180 |
| location_mode, location_source, location_details | text | user/directory | carried in report and revision |
| room dimensions, windows, doors | metres, m² | drawing/site survey | nonnegative, opaque wall area positive |
| people, occupancy_fraction, occupancy schedule | count, ratio, category | capacity/roster | peak guest allocation not double counted |
| equipment_kW, circuit watts/count | kW, W, integer | asset inventory/nameplate | assigned exactly once |
| Target_C, AC_enabled, AC_units, AC_TR_each | °C, bool, count, TR | S&T/OEM/engineering | largest-unit-out check for conditioned zones |
| weather time, T, RH, GHI, sunrise/sunset | IST, °C, %, W/m², time | Open-Meteo ERA5 | complete coincident historical hourly record |
| pv_kwp, pv_pr, usable_area | kWp, ratio, m² | design and installer | area constrained |
| bess_kwh, bess_kw, efficiency, SOC | kWh, kW, ratio | OEM/assumption | bounded charge/discharge and energy |
| EV Points, Grid_kW_per_point, Vehicles_per_day | count, kW, count/day | concessionaire/forecast | nonnegative, physical limits |
| measured timestamp, kva OR kw+pf | time, kVA or kW+ratio | utility meter CSV | no duplicate timestamps, sparse intervals rejected |
| contracted_kva, demand charges, reserve | kVA, ₹, ratio | utility bill/contract | tariff-specific screening only |
| station revision, parent_hash, content_hash | integer, SHA-256 | JSON revision engine | integrity and ancestry |

Station directory is a bundled, SHA-256-checked, MIT-licensed community snapshot with **8,697 coordinate-bearing station records**, not an authoritative Indian Railways asset master. Original source: https://github.com/prasenjit-27/Indian-Railway-Data (commit `1dc0ddbc6a06b09ef69d4825ff3127c1f29640fa`). No reverse geocoding. Manual coordinates preserve the exact facility location. Existing saved designs with explicit coordinates restore in manual mode.

Historical weather uses Open-Meteo ERA5 archive hourly T/RH/GHI plus daily sunrise/sunset, five-year batches, India timezone and strict completeness checks. Gridded reanalysis is not an on-site certified extreme; compare IMD/site measurements before equipment sanction. External API usage and attribution terms apply.

### 5. Thermal and AC engineering method
For a rectangular zone, floor area `A=L×W`, volume `V=L×W×H`, net opaque wall `Awall=2(L+W)H-Awindow-Adoor`. Sensible envelope cooling surrogate:
`Qenv=[Uroof A + Uwall Awall + Uwindow Awindow + Udoor Adoor] max(0,Tout-Tin)/1000` kW.
Solar surrogate: `Qsolar=GHI [roof_factor A + 0.0192 Awall + SHGC Awindow]/1000` kW.
Infiltration flow `m=1.18 V ACH/3600` kg/s; sensible `m×1.006×max(0,Tout-Tin)`; latent `max(0,m×2501×(wout-win))`, using the stated psychrometric humidity ratio. Add room equipment, scheduled indoor circuit heat and separate sensible/latent person loads. Exterior circuits do not add indoor heat.

**Design:** evaluate all components using weather variables from the **same hour**; select maximum coincident room load, add explicit allowance and compare with surviving AC capacity. For equal units, `N+1 usable kW=(units-1)×TR_each×3.517×available_capacity_fraction`. Fail when below required design cooling. Manufacturer sensible and total capacity, humidity control, common-mode supply failure, alarms and standby changeover remain external engineering tasks. AC operating kW uses hourly cooling/COP approximation; allowance is for design capacity, not an automatic annual energy multiplier.

**Model limits:** steady-state envelope, simplified horizontal-GHI solar gain, no CFD, dynamic wall storage, shading/orientation, inter-room coupling, actual compressor maps, humidity transients or verified kitchen hood air balance. Different rooms may govern at different historical hours; do not add noncoincident room design peaks as if simultaneous.

### 6. Hourly electrical demand, schedules and EV dispatch
Hourly site demand is equipment + circuits + AC compressor electricity + scheduled EV grid power. Schedules include Always, Off, Night, Daylight, Occupied hours and meal hours where relevant. Sunrise/sunset partial-hour overlap is applied; the hourly weather timestamp denotes the ending hour. The EV engine computes daily requested grid kWh as `vehicles_per_day × battery_kWh_per_vehicle / charging_efficiency`, caps delivery by `points × grid_kW_per_point` and allowed hours, and reports served/unserved demand. Managed mode allocates capacity preferentially to solar-surplus/cheaper hours subject to a shared import ceiling. It is an aggregate deterministic load planner, not a charger communication or vehicle queue model. Examine charging feasibility and unserved energy, not only peak kW.

### 7. Transformer, solar, battery and economic calculations
**Transformer preliminary kVA:** `max(peak_import_kW×(1+reserve), export_limit_or_PV_kW)/(PF×utilization)`, rounded to the next configured standard rating. It does not design feeder impedance, fault level, harmonics, protection, transformer thermal life, phase balance, EV fast-charge power quality or utility approval.

**PV:** `PV_kW = kWp × GHI/1000 × performance_ratio` with area cap `usable_area / m²_per_kWp`. Import `max(0,demand-PV)`, export `max(0,PV-demand)`; conservation `demand+export=PV+import`. This is an irradiance screening approximation, not bankable tilt/temperature/degradation modelling. Select PV in bounded 0.5-kWp candidates plus area limit by minimum discounted life-cycle cost; zero PV remains an option. Historical annual costs are averaged over selected complete years.

**BESS:** optional solar-surplus charge and deficit discharge with inverter power limit, bounded SOC and square-root split of round-trip efficiency. Initial SOC starts at minimum reserve so no free starting energy. It does not jointly optimize PV and battery size; no grid charging, demand-target dispatch, replacement, degradation, arbitrage, backup autonomy, end-SOC credit or safety certification. Battery capex/O&M and adjusted imports feed scenario economics; verify tariff, fixed charges and replacement assumptions before financial approval.

**Economic model:** discounted life-cycle cost and NPV from annual import energy bill, export credit, capex, O&M and user-supplied discount rate. Grid demand charges are compared separately; this is **not** a global co-optimization of PV/BESS/contract/operations.

### 8. Grid sanctioned demand and measured evidence
Accept CSV `timestamp,kva` **or** `timestamp,kw,pf`. Require multiple unique chronological interval readings, finite nonnegative values, valid PF and no gaps exceeding 60 minutes. Compute monthly observed kVA maxima and indicative coverage. Compare user-entered current/candidate contracted kVA, reserve, demand-charge rate, minimum billing fraction and excess-demand penalty; report annualized indicative demand charges, months exceeding contract and feasibility relative to measured peak plus reserve.

**Critical:** a modelled **hourly** peak is not a safe substitute for a utility's 15/30-minute billing demand. Meter data may already include PV/BESS effects; consider monsoon, low solar, battery outage and future EV additions. Do not recommend a contractual reduction solely from the simulated peak. Verify the applicable DISCOM tariff, billing ratchet, notice period, approval, deposits and load-growth reserve; the app cannot submit a contract amendment.

### 9. Station versioning and audit
Each station scenario includes station code, design label, notes, revision number, schema version, UTC creation time, parent hash, payload and SHA-256 content hash. The revision JSON is **portable and immutable by convention**; edited or corrupted files fail hash verification, and a child must match its parent station code. Users manually download/store/upload revisions (for example station folder in OneDrive). There is **no central authenticated registry, automated sync, user permissions, concurrent editing or electronic approval workflow**. Separate facility designs under the same station should have distinct labels and asset identifiers. Store weather provenance, input assumptions, meter evidence and PDF alongside the JSON for reproducibility.

### 10. Software/IT architecture
**Implemented modules:** `app.py` (Streamlit forms, scenario orchestration, reports), `site_energy.py` (weather, schedules, room/circuit energy and PV economics), `extreme_design.py` (historical extremes), `facility_design.py` (templates, transformer, battery), `station_design.py` (running room, revisions, meter/contract), `station_lookup.py` (offline directory), `ev_charging.py` (EV demand/managed scheduling), `legacy_app.py` (preserved relay simulator). `data/` contains station source and licence; `docs/` manuals; `test_*.py` regression tests. Python NumPy/Pandas computations run inside the Streamlit process. The current deployment has **no persistent database, REST API, SSO/RBAC, SCADA link, IoT ingestion, automated OneDrive station registry or physical actuation**.

**Proposed modular services (future, not implemented):** station master/asset registry; weather adapter; facility/occupancy thermal service; EV charging planner; transformer/electrical review; PV/BESS optimization; tariff/meter ingestion; scenario/revision service; reporting/audit; role-based approval API. Suggested relational entities: Station, Facility, Zone, Asset, Circuit, OccupancyProfile, ChargerGroup, WeatherObservation, MeterInterval, TariffVersion, DesignRevision, SimulationRun, HourlyResult, Approval. Store time series in a partitioned database, large outputs in object storage and content hashes in an immutable audit trail. API contract candidates: `POST /v1/designs`, `POST /v1/simulations`, `GET /v1/runs/{id}`, `POST /v1/meter-uploads`, `GET /v1/contract-options`; **illustrative only**. Data governance: coordinate precision, meter access, audit permissions, encryption, retention, versioned algorithms and source licences.

### 11. Verification, acceptance and release control
Run `python -m pytest -q` and Streamlit AppTest locally **before commit**. Test room geometry, weather completeness, coincident extremes, N+1, people/latent loads, unconditioned zones, circuit no-double-counting, dawn/dusk, energy conservation, PV optimization, battery SOC, EV served/unserved demand and import ceiling, two-/four-wheeler templates, running-room guest conservation, revision hash/restore, station lookup/manual coordinates, meter coverage and tariff scenarios. Verify report PDF/CSV/JSON and a historical-weather full-year case. Commit only after tests pass; require green GitHub Actions and separate live deployment smoke test. A CI success is not evidence of a browser UI success. Document release SHA, test count, failing tests, live evidence and any known deviations.

**Field acceptance:** compare measured versus predicted temperature/RH, AC kWh, peak kVA, PV output, EV utilization and contract billing over representative hot/humid/monsoon and low-demand periods. Require S&T sign-off for relay-room critical cooling, electrical protection sign-off, DISCOM agreement for demand changes and OEM sizing confirmation.

### 12. Known gaps and prioritized roadmap
**High priority:** calibrated facility-level sensor/meter feeds; proper interval-demand and sanctioned-load tariffs; more accurate kitchen exhaust/makeup air; transformer protection/harmonics and EV fast-charger diversity; weather/location authority validation; role-based station revision registry; automated field acceptance evidence.

**Medium priority:** solar tilt/shading and inverter clipping; BESS degradation/replacement, backup and demand peak-shaving optimization; joint PV/BESS/contract optimization; charger taper, queueing and swapping inventory; running-room occupancy stochasticity and hotel hot-water process; HVAC manufacturer performance maps.

**Future:** authenticated multi-station service architecture, API integration with approved railway asset/master data, utility bills and metering, alerting and engineering review workflow. Physical control remains outside scope until separately safety-certified.

### 13. Source and usage links
- [Streamlit application](https://relayroomheatdesignrc-fhfhpzvryxnksd7cef9kg8.streamlit.app/)
- [GitHub source and test suite](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC)
- [Open-Meteo historical documentation](https://open-meteo.com/en/docs/historical-weather-api)
- [Station directory source](https://github.com/prasenjit-27/Indian-Railway-Data)
- [Telangana electricity regulator (verify current category and tariff)](https://www.tgerc.telangana.gov.in/)
