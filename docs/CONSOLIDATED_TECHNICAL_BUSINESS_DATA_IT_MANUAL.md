# Railway Facility Energy Design Studio
## Consolidated Technical, Business, Data, IT Architecture and User Manual
**Edition:** 2.0 — expanded book · 24 October 2026 · **Status:** Engineering screening and software reference, not certified procurement design.

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


---

# Part II — Detailed engineering, demand assessment, commercial and implementation handbook

This part expands the preceding consolidated overview into a practical design and governance handbook. It preserves the historical relay-room work as a separate legacy research method while identifying the current multi-facility code path. **Version distinction:** the legacy dynamic setpoint optimizer, spatial heat-map surrogate and synthetic-weather demonstration are not capabilities of the default generic-room design engine. Likewise proposed REST endpoints, authenticated database and automated sanctioned-load revision are future architecture, not implemented services.

## Chapter 14. Engineering design basis and survey protocol

### 14.1 Define the site boundary
A railway station can include S&T relay rooms, station offices, passenger waiting areas, booking halls, commercial stalls, public toilets, parking/EV chargers, running rooms, pumps, outdoor high-mast lighting and shared transformers. Define an electrical boundary before adding loads. Record whether the boundary is one DISCOM meter, a transformer secondary, a distribution board or a collection of buildings. A meter may cover multiple consumers and concessionaires; assign their loads to a distinct owner and billing point to avoid duplicate demand or incorrectly claimed solar savings.

A **site** is a geographical/electrical study boundary; a **facility** is a building or installation; a **zone** is a thermally or operationally distinct room; an **asset** is a load, generator, meter or HVAC unit; a **circuit** is the scheduled electrical load connecting assets; a **scenario** is a set of assumptions. A station may contain multiple site studies, and a running room may have a different supply, tariff and owner from the passenger station.

### 14.2 Site survey form
Capture the station code and location mode, surveyed GPS of each facility, elevation if known, north orientation, drawings, measured room dimensions, construction material and insulation, roof exposure, glazing SHGC and shading, door usage, occupancy roster, equipment inventory, HVAC nameplates, electrical single-line diagram, transformer and feeder ratings, sanctioned contract demand, tariff category, PV rooftop usability, inverter/meter position and historical electricity bills. Record the measurement method, surveyor, date, uncertainty, photo/drawing reference and responsible approving department. The offline station-code directory is a navigation aid, not a substitute for survey.

For each room: length, width, height, roof exposure fraction, opaque wall area, window/door area and type, ACH or ventilation rate, indoor temperature/RH target, maximum simultaneous occupants, occupancy schedule, continuous equipment kW, scheduled lighting/fans/other loads, AC count and OEM capacity at design conditions. Where building materials are unknown, flag U-values as **assumed** and conduct sensitivity runs; do not present defaults as measured facts.

### 14.3 Load classification
Classify every electrical asset as critical continuous, ordinary continuous, scheduled, occupancy-linked, seasonal, weather-driven, charging/flexible, generation or storage. For example: signalling racks are critical continuous; lighting follows daylight and operating hours; AC follows weather and setpoint; hot water follows guest demand; EV load is flexible only within the customer's charging window. Distinguish nameplate power, measured steady power, starting power, coincident maximum and annual energy. The sum of nameplates is **connected load**, not automatically the site's maximum demand.

### 14.4 Design cases
Maintain separate cases for historical cooling extreme; maximum coincident electrical demand; annual energy and bills; summer high-temperature/low-PV condition; humid monsoon; low occupancy; high guest turnover; relay-room AC unit failure; grid outage; BESS at minimum reserve; and EV charging surge. Record which cases are actually simulated by the current tool and which require engineering review outside it.

## Chapter 15. Detailed demand assessment methodology

### 15.1 Bottom-up demand model
For load group g and hourly bin t, define `P_g,t = N_g × p_g × u_g,t × d_g,t`, where N is equipment count, p is electrical input kW/item, u is utilization or on/off duty fraction, and d is an optional derating/diversity factor justified by field data. Do **not** apply arbitrary diversity to critical continuous loads. For HVAC, derive `P_AC,t = Q_cooling,t / COP_t`; for EV, use the charger scheduler rather than multiplying connected charger kW by 24 hours. Sum groups only after establishing the same timestamp and electrical boundary: `P_site,t = Σ_g P_g,t`.

Peak coincident power `P_peak=max_t P_site,t`; energy `E=Σ_t P_site,t Δt`. For one-hour bins, numerical kW values summed over time yield kWh. Monthly maximum kVA is computed from measured kVA or measured kW/PF, **not** by dividing all months by an assumed common PF. Use 15- or 30-minute data where the utility demand register is based on that interval. The current meter parser accepts up to one-hour gaps but does not certify billing-interval conformity.

### 15.2 Illustrative load register
| Facility / asset | Quantity basis | Duty assumption | Peak driver | Evidence |
|---|---|---|---|---|
| S&T racks | measured rack input kW | 24×7 | nameplate/telemetry and future equipment | S&T asset register |
| Relay-room AC | calculated cooling / COP | continuous setpoint | coincident extreme T/RH/GHI and equipment | OEM maps, sensors |
| Waiting-hall lights | fixture count × input W | daylight/night or operating | sunrise/sunset and occupancy | electrical survey |
| High-mast lighting | luminaire count × W | night | fixture schedule | lighting asset register |
| Running-room bedrooms | rooms × occupants + AC | guest sleeping profile | peak permitted guests | room register |
| Kitchen / dining | equipment and exhaust | meal windows | meal count and appliance duty | catering survey |
| Hot water / laundry | heater and motor kW | occupied windows | guest turnover | meters and process cycle |
| EV AC/DC charging | connectors × input kW | arrival/window and energy | served sessions and simultaneous charging | concessionaire logs |
| Water pumping | pump input kW | controlled cycle | tank refill and water demand | pump schedule |

This table defines an inventory method, not default procurement quantities. Connected charger power is an upper bound; actual delivered kWh depends on energy request, duration, available connectors and the import ceiling. Do not equate **requested** charging with **served** charging; record unserved energy as a service-level failure.

### 15.3 Load duration, diversity and uncertainty
Report the distribution of hourly kW, not just a single maximum: annual kWh, top 1% demand hours, monthly peaks, daytime/nighttime averages, seasonal peaks and load factor `LF = E/(P_peak × hours)`. For a multi-building station, compare `max_t Σ_b P_b,t` with `Σ_b max_t P_b,t` to quantify coincident diversity. Use actual meter/asset telemetry to calibrate duty fractions and uncertainty intervals. When a station has new EV chargers, a planned kitchen, or a proposed waiting hall, include a future-growth case before sizing the transformer or revising sanctioned demand.

### 15.4 Time conventions and quality
The historical engine uses IST and hour-ending weather timestamps. Align demand and irradiance to the preceding one-hour interval; sunrise/sunset overlap can be fractional. Normalize daylight-saving issues if later extending beyond India. Maintain a single time-zone-aware canonical time in future databases, with UTC stored and IST displayed. Reject missing, duplicated, nonfinite or misordered weather intervals. For measured meters, annotate gaps, unit conversions, CT/PT multipliers and estimated reads. **A complete weather year is not evidence that measured utility data are complete.**

### 15.5 Demand assessment worked illustration
Suppose a *hypothetical* facility has 10 kW critical electronics, 3 kW night lighting, 8 kW daytime commercial loads, 12 kW cooling at the governing hour and a 64 kW DC charger. A naïve connected sum is 97 kW. If the charger is inactive during the critical cooling hour, the coincident demand is only 33 kW at that hour; at a later charger-active hour, demand may exceed it. The true peak requires the full synchronized hourly profile. These figures illustrate the method only and are not results for any real station.

## Chapter 16. HVAC thermal physics, reliability and acceptance

### 16.1 Heat-flow components
The envelope conduction, solar surrogate, infiltration sensible/latent, people and internal electrical components are defined in Part I. The humidity ratio is `w=0.62198 p_v/(101325-p_v)`, with `p_v=RH × 610.94 exp[17.625T/(T+243.04)]` Pa when RH is a fraction. Total cooling is the sum of sensible and latent terms; room heat gain and compressor electrical input are distinct quantities. The default generic-room method clips negative outward-to-inward conduction, so it does not calculate free cooling or heating.

For the relay room, ensure the actual control sensor and maximum equipment temperature correspond to the **relay-end hotspot**, not merely the average air temperature. A hypothetical uniform spatial heat map is not CFD and cannot certify rack hot spots. Evaluate infiltration from doors, cable penetrations and required ventilation, not only nominal ACH.

### 16.2 Historical coincident design
For each candidate historical hour h, compute `Q_h=Q(T_h,RH_h,GHI_h,occupants_max,equipment_max)`; select `Q_design=(1+allowance) max_h Q_h`. Do not combine the hottest dry-bulb of one hour with the maximum RH and solar from other hours and call it a historical observation. Optional temperature uplift is a stress sensitivity, not an observed return-period event. Historical empirical percentiles (0.4%, 1%, 2%) are descriptive and not certified ASHRAE conditions.

### 16.3 Redundancy and common-mode risks
For installed equal AC units, `Q_surviving=(N-1)×TR×3.517×f`. This screens the loss of one largest unit. It does not guarantee duty rotation, standby startup, independent power, humidity, airflow, or failure of the control panel. A separate legacy relay-room failure-delay sensitivity uses `ΔT≈(cooling shortfall × delay_hours)/thermal_capacitance`; this lumped approximation does not predict equipment temperature gradients or moisture transients. Critical S&T rooms require separate sign-off for independent sensors, alarms, electrical redundancy, backup and fault-response procedures.

### 16.4 Engineering acceptance
Record room setpoint and tolerance, RH range, hotspot temperature, equipment heat rejection, installed AC total/sensible capacity at actual ambient, compressor restart restrictions, condenser airflow, unit placement, air distribution, condensate routing and backup supply. Conduct site trials under hot/humid periods and simulated unit-out conditions only under approved safe procedures. Calibrate model temperature and kWh errors and retain test certificates.

## Chapter 17. Running-room demand as a hotel operation

A running room is not a single air-conditioned rectangle. It has bedrooms, lobby, dining, kitchen, toilets/bathrooms, laundry, corridors, pumps, hot-water loads and staff. Configure number of bedrooms, beds per bedroom, maximum guests and staff. The software generates bedroom zones and service areas, while every row remains editable. Capacity check: `peak_guests ≤ rooms × beds_per_room`. Sleeping fractions reflect peak guests; shared-zone allocations avoid simultaneous double counting. Design capacity per bedroom may conservatively use all its beds even if typical energy simulation assumes partial occupancy.

Use at least three operational profiles: normal roster, full occupancy and surge/irregular train arrivals. Meal windows and laundry/heating duty are editable placeholders, not measured catering demand. For more accurate demand, model occupancy arrival/departure, bath/shower hot-water litres per guest, water inlet temperature, heater COP/efficiency, storage losses, kitchen meal production, cooking fuel and exhaust/makeup air. These are **future detailed process models**, not current engine outputs.

A running room's commercial assessment should include electricity per occupied bed-night, AC kWh/bed-night, hot-water kWh/guest, connected kVA per room, annual demand charge and solar self-consumption. Capital options may include efficient HVAC, occupancy-linked controls, solar water heating, PV and BESS; compare all against comfort, hygiene and staff requirements.

## Chapter 18. EV charging demand, flexibility and concession economics

### 18.1 Two-wheeler and four-wheeler demand
Use distinct charger groups for two-wheelers and four-wheelers, AC destination charging and DC fast charging. Example grid input powers in the application are editable; verify actual input power and electrical safety requirements. Requested battery energy per day is `vehicles/day × battery_kWh/session`. Requested grid energy divides by charger efficiency. Installed connection capacity is `points × input_kW/point`. The charging algorithm attempts to serve energy in allowed time windows; unserved battery kWh is a visible service deficit.

### 18.2 Managed charging
The managed heuristic favors surplus PV and lower-tariff hours and limits incremental EV charging to an entered site import ceiling. The ceiling should be treated as **enforced** only where a verified external controller exists; otherwise it is a planning scenario. The model is not an ISO 15118/OCPP integration, queue simulator or network-constrained optimal power flow. DC charger nameplate output and mains input are different; transformer and cable selection require the latter plus harmonic and power-quality assessment.

### 18.3 Commercial evaluation
Consider concessionaire business model: owned/leased chargers, connection and transformer cost, energy purchase, demand charges, customer tariff per kWh or session, idle fees, uptime, parking revenue, maintenance, payment gateway, taxes, battery degradation where owned, and utilization ramp-up. Annual contribution can be screened as `charging revenue + ancillary revenue - energy bill - demand charges - operating cost`; investment NPV discounts this net contribution and capital/replacement cash flows. No concession tariff or utilization forecast is embedded as a factual assumption in the software. If station solar and charger ownership differ, define commercial settlement explicitly.

### 18.4 Future EV features
Add stochastic arrivals and queueing, charger sharing, vehicle-specific charging taper, minimum service level, station peak management, time-of-use and parking pricing, battery swapping inventory, two-wheeler pack charging racks, demand response and power-quality constraints. Label swapping as unsupported in the current code despite the historical example row that mentions it.

## Chapter 19. PV, storage and transformer planning

### 19.1 Solar resource and siting
The current PV proxy uses hourly GHI, nominal DC kWp and performance ratio. Detailed feasibility requires usable roof/land polygons, structural loading, tilt/azimuth, shade study, inverter AC capacity, temperature coefficients, wiring losses, clipping, soiling, cleaning access, fire and electrical clearances, export permissions and actual net-metering settlement. Distinguish kWp (DC rating), inverter kW (AC rating), annual kWh and instantaneous coincident PV contribution. **Do not treat annual solar savings as guaranteed reduction in sanctioned kVA.**

### 19.2 Battery operation and limits
The existing dispatch charges from solar surplus and discharges against load subject to power and SOC limits. If round-trip efficiency is η, use symmetric charge/discharge efficiency `sqrt(η)`. Enforce `SOC_min ≤ SOC_t ≤ SOC_max` and no artificial energy at the first interval. Distinguish nominal battery kWh, usable kWh, inverter kW, backup duration and power reserve. The tool does not design BMS, PCS, fire protection, thermal runaway mitigation, battery degradation, replacement or grid-forming capability.

### 19.3 Transformer assessment
The current preliminary screen uses demand, reserve, PF and utilization plus possible export. Actual design additionally requires diversified phase currents, voltage drop, short circuit, fault withstand, breaker selectivity, earth fault, harmonics from chargers/inverters, thermal derating, duty cycle, redundancy and sanctioned connection conditions. Separate transformer **rated kVA** from utility **contracted demand kVA**; neither can be optimized safely from a single annual kWh number.

### 19.4 Combined dispatch scenarios
Evaluate base case, PV-only, PV+BESS, PV+managed EV and PV+BESS+managed EV against the same weather, facility schedule and tariff. Compare hourly import/export, demand exceedances, battery throughput, unserved EV demand, annual bill, lifecycle cost and reliability. The current software does not solve a global multi-variable optimization across PV, BESS, EV, AC setpoints and contract kVA; scenario comparisons are a practical interim method.

## Chapter 20. Commercial, procurement and financial decision framework

### 20.1 Stakeholders and cost ownership
Railways may pay facility electricity while concessionaires pay for commercial equipment or charging. Record owner, tariff account, metering point, capital funding source, maintenance obligation and energy reimbursement for each asset. Savings should be allocated only to the party that bears the underlying cost. For a common supply, use submetered allocation or an agreed transparent method; do not treat concessionaire loads as free railway energy.

### 20.2 Cost and benefit categories
| Category | Required input | Treatment |
|---|---|---|
| HVAC | purchase, installation, service, electricity, failure risk | room capacity and operating energy; external reliability appraisal |
| Transformer/distribution | transformer, cable, protection, civil works, losses | preliminary kVA only; detailed capex external |
| PV | ₹/kWp, annual O&M, life, export rate, degradation | current PV optimizer excludes degradation and many tariffs |
| BESS | ₹/kWh and inverter, O&M, replacement, salvage | current simulation excludes replacement and degradation |
| EV | charger capex, connection, energy, revenue, maintenance | energy modeled; concession P&L external |
| Grid contract | sanctioned kVA, billed demand formula, penalties, minimum billing | candidate screen from uploaded intervals |
| Reliability | downtime, service loss, critical safety consequence | qualitative or externally monetized; not embedded |
| Carbon | emissions factor, policy value, reporting boundary | future extension; not automatically credited |

### 20.3 Life-cycle cost and NPV
For investment I, annual benefit B_y and annual operating cost O_y, `NPV=-I+Σ_y(B_y-O_y)/(1+r)^y`. Compare alternatives over a common economic horizon and real/nominal convention. Include replacements, salvage and tariff escalation only when explicitly modeled. Payback is supplementary and cannot replace NPV when options have different life or risk. The present PV module minimizes its own discounted lifecycle cost on a bounded capacity grid; do not present that as proof of a globally optimal station investment.

### 20.4 Sanctioned-load change decision
Use **actual billing interval data**, ideally 12 months or more covering seasonal conditions, and examine monthly maximum kVA, demand ratchets, billing minimums, overdrawal penalties, planned load growth, PV/BESS outage, charger additions and minimum redundancy. Obtain tariff-specific approval from the appropriate utility. A simulated lower grid import or annual energy saving is insufficient to reduce contracted capacity. The tool's contract comparison is an analytical aid, not an electronic application or regulatory approval.

### 20.5 Procurement gate and audit
The decision package should include: validated asset inventory; surveyed geometry and weather basis; equipment OEM performance curves; demand and power-quality study; N+1 and electrical safety checks; 15/30-minute meter evidence; sensitivity and uncertainty; tariff order and bill calculations; lifecycle cash flow; risk register; department approvals; installation and commissioning plan; as-built documentation; and post-commissioning M&V.

## Chapter 21. Data architecture, dictionary and governance

### 21.1 Canonical entities and keys
| Table | Primary key | Selected fields | Data stewardship |
|---|---|---|---|
| Station | station_id | code, name, lat, lon, source_version | railway station master |
| Site | site_id | station_id, electrical_boundary, tariff_account | electrical department |
| Facility | facility_id | site_id, facility_type, survey_date | owning department |
| Zone | zone_id | facility_id, geometry, target, ACH, exposed_roof | engineering/S&T |
| Asset | asset_id | zone_id, class, rated_kw, OEM, serial, criticality | asset owner |
| Circuit | circuit_id | asset_id, meter_id, duty_schedule | electrical department |
| OccupancyProfile | profile_id | facility_id, timestamps, guests, staff | facility manager |
| ChargerGroup | group_id | site_id, connectors, input_kw, efficiency, windows | EV operator |
| WeatherObservation | site_id + timestamp | temperature, RH, GHI, source, quality | weather adapter |
| MeterInterval | meter_id + timestamp | kw, kva, pf, interval, quality, multiplier | utility/electrical |
| TariffVersion | tariff_id | category, effective_dates, charges, approval | finance/electrical |
| DesignRevision | design_id + revision | parent_hash, config, author, approval | design custodian |
| SimulationRun | run_id | design_hash, model_commit, weather_version, status | application |
| HourlyResult | run_id + timestamp | thermal, load, PV, BESS, EV, import/export | simulation engine |
| Approval | approval_id | design_revision, approver, decision, time | workflow owner |

The above is a **proposed database schema**, not a description of tables already deployed. In the current Streamlit version, session data are in memory; JSON/CSV/PDF exports are manual. Prefer immutable revision payloads and content-addressed model artefacts. Keep private station drawings, meter records, personal occupancy data and access credentials out of public GitHub.

### 21.2 Data validation contracts
Weather: strict hourly completeness, source URL, retrieval UTC, units, timezone, model and no silent substitution. Station directory: exact code, source hash, coordinate bounds, fallback disabled. Geometry: nonnegative dimensions, valid wall opening area, unique room identifiers. Electrical: kW versus kVA explicit, PF valid, schedules bounded, one load-one owner. Meter: unique timestamps, correct interval and multipliers, measured-versus-estimated flags, monthly coverage. Financial: tariff effective date, currency, discount convention and bill reconciliation. Model: run SHA, scenario hash, engine version, input and output checksums.

### 21.3 Future ingestion APIs
Weather adapter: historical ERA5 archive and forecast with cache, throttling, retry and provenance. Asset adapter: approved railway asset register (not a guessed public station code). Meter adapter: CSV first, then read-only utility/AMI API with delegated credentials and audit. EV adapter: charger availability and transaction totals, with personally identifiable vehicle/customer information minimized. Every adapter needs versioned schemas, idempotency, error logs, source latency, credential rotation and rate-limit handling. Do not write directly to operational control systems from the planning application.

### 21.4 Information security
Separate public algorithm documentation from restricted drawings and operating data. Use least-privilege RBAC, MFA/SSO, encryption at rest/in transit, access logs, tenant boundaries, retention schedules, backups, change approvals and secret management. Do not publish meter account numbers, staff personal details, concessionaire commercial terms or live infrastructure diagrams in a public repository.

## Chapter 22. IT implementation, services, API and deployment

### 22.1 Current logical architecture
`Streamlit app.py → station lookup / weather → thermal site_energy / extreme_design → facility_design / station_design / ev_charging → reports and downloadable JSON/CSV/PDF`. `legacy_app.py` retains original relay-room adaptive-temperature research. Source modules are separate Python files, but execute inside the same Streamlit process; they are **not independently deployed microservices**.

### 22.2 Target modular architecture
Introduce independently testable services: (1) station/asset master; (2) weather and solar resource; (3) facility thermal/occupancy; (4) electric demand aggregation; (5) EV service-level planning; (6) PV/BESS dispatch and economics; (7) meter/tariff validation; (8) scenario registry; (9) reporting; (10) approval/audit. Use REST or event contracts between services, immutable versioned inputs, a relational transactional store, time-series partitions and object storage for long hourly outputs. Maintain stateless compute workers for multi-year simulations. Do not introduce infrastructure complexity before stable schemas and a tested pilot.

### 22.3 Proposed API examples
```text
POST /v1/stations/{station_id}/facilities
POST /v1/designs                 create draft with parent revision
GET  /v1/designs/{id}/revisions  retrieve audit history
POST /v1/simulations            submit immutable design and weather references
GET  /v1/runs/{run_id}          status, input hash, model SHA
GET  /v1/runs/{run_id}/hourly   paginated results or signed export
POST /v1/meters/{id}/intervals  ingest validated time series
POST /v1/contracts/evaluate    candidate demand billing scenarios
POST /v1/reviews/{id}/decision  signed approval/rejection
```
These endpoints are a **requirements proposal only**. A typical run request should contain `design_revision_id`, `weather_source_version`, `scenario_parameters`, `model_commit_sha` and `requested_outputs`; response should include `run_id`, `status`, `validation_errors`, `provenance` and checksum. Repeated identical submissions should be idempotent.

### 22.4 Testing and CI/CD
Before a code commit: compile Python; run pytest, deterministic weather fixtures, thermal and energy conservation, station lookup, EV and battery boundary conditions, revision hash checks, meter validation and Streamlit AppTest. After commit: GitHub Actions, package dependency and licence review, smoke test on deployed Streamlit, generate/inspect report PDF and validate a complete historical-year calculation. CI pass is not equivalent to production browser verification. Pin critical dependencies and retain rollback reference. Record run duration and memory use for long weather histories.

### 22.5 Performance and observability
The current engine uses vectorized Pandas/NumPy, five-year weather batches and caching. A fleet-scale platform should benchmark 8,760-hour and 30-year cases, avoid copying large tables across services, use asynchronous jobs and result caching keyed by source+config+model hashes, and monitor failures, API limits, queue times, model drift, report errors and cloud spend. Add observability without collecting sensitive facility details in public logs.

## Chapter 23. Verification, measurement and validation plan

### 23.1 Unit and integration tests
- Geometry and invalid opening area; indoor versus exterior circuit heat; unique loads and circuit ownership.
- Simultaneous temperature, humidity and GHI in historical extremes; no synthetic fallback; missing-hour rejection.
- Room cooling versus AC electrical conversion; N+1 largest-unit-out and derating; no phantom cooling in unconditioned zones.
- Running-room bed capacity, guest allocations, staff counts and schedule changes.
- EV group input validation, connected kW, requested/served/unserved energy, managed import ceiling, 2W/4W categories and day-boundary behavior.
- PV and grid conservation; SOC and battery power bounds; zero-PV and bounded optimum.
- Measured kVA from kW/PF, duplicate intervals, sparse readings, monthly coverage and tariff candidate calculation.
- Station lookup exactness, manual coordinate limits, changed-station weather invalidation and older revision restoration.
- Report data provenance, JSON hash integrity, PDF/CSV download, legacy calculator isolation.

### 23.2 Pilot acceptance metrics
| Metric | Suggested measurement | Acceptance principle |
|---|---|---|
| AC energy error | predicted versus submetered daily/monthly kWh | threshold agreed after baseline study |
| Temperature/RH | calibrated sensors near equipment and occupied zones | never exceed approved critical limits |
| Site peak demand | simulated versus 15/30-min billed kVA | tariff-specific error and reserve review |
| PV generation | inverter AC kWh versus model | weather/shading-normalized assessment |
| BESS SOC/energy | meter and BMS log | power/SOC constraints, no energy creation |
| EV service | sessions and requested/served kWh | explicit service-level target |
| Running-room efficiency | kWh/occupied bed-night | normalize occupancy and climate |
| Finance | modelled bill versus actual utility bill | explain demand/fixed/tax differences |

Thresholds must be set by engineering and finance after obtaining actual baseline data; the software cannot certify itself by passing synthetic tests. For critical rooms, operational safety limits override optimization benefits.

### 23.3 Traceability matrix
Map every requirement to input, code module, test, report field, data source, approval owner and release version. Example: station-code lookup → `station_lookup.py` → `test_station_lookup.py` → location provenance → electrical survey confirmation. Meter billing → `station_design.py` → `test_station_design.py` → contract-options table → finance/DISCOM verification. EV served energy → `ev_charging.py` → `test_ev_charging.py` → charging summary → concessionaire operating logs.

## Chapter 24. User operating procedures and troubleshooting

**New station:** open Streamlit; choose station lookup and verify exact code, or manual coordinates; apply facility template; survey all room/asset rows; choose historical years; load weather; enter tariff, PV/BESS and EV inputs; run; review warnings; export PDF/CSV/JSON; create and archive station revision.

**Revise station:** upload an existing revision JSON; verify displayed station, location, parent hash and revision; edit design assumptions; create next revision with notes; retain both old and new records. A hash-protected revision is not a central registry or signed approval.

**Assess contracted kVA:** obtain measured interval data with correct unit/PF and utility interval; upload CSV; inspect coverage and monthly peaks; enter current sanction and applicable tariff; compare candidates with seasonal and outage reserve; seek utility approval. Do not change a contract from simulated hourly power alone.

**Unexpected cooling failure:** check geometry, doors/windows, ACH, people, setpoint, equipment and circuit duplication; confirm same-hour weather and available OEM derating. **Unexpected EV shortfall:** check daily energy requested, connectors, input kW, allowed hours, managed import ceiling and charging efficiency. **Unexpected PV optimum:** check usable area, export credit, tariff, performance ratio, cost/discount assumptions and whether a forecast day was mistaken for a historical annual study. **Invalid station code:** switch to manual coordinates or correct the exact code; never rely on a stale previous station.

## Chapter 25. Change history, supersession and document retention

The project evolved from a relay-room AC and solar proof of concept to a multi-facility site-energy planner, then historical extreme/N+1 design, running-room hotel-like occupancy, station revision and grid commitment analysis, EV charging, and finally station-code lookup with manual facility coordinates. Legacy papers may describe synthetic weather, one-room heat maps, no storage, no station-code lookup or a single running-room zone. Those statements are historical and should not be treated as the current default application specification.

**Retention policy recommendation:** keep this book as the current master; retain old manuals and LaTeX/PDF technical derivations in a clearly labelled superseded archive until checked for unique formulas, test evidence, design assumptions and provenance. Do not permanently delete source documents merely because they have been summarized. Any future deletion requires a separate explicit confirmation.

### Bibliography and source register
1. GitHub master, generic-room manual, running-room/grid manual, station lookup manual and wiki pages in `docs/`.
2. Original OneDrive relay-room technical/business/data/IT manual, hourly AC/solar optimization paper, historical-extreme update and weather/PDF update; listed for provenance. Their complete contents were not re-extracted in this edition.
3. Open-Meteo historical API: https://open-meteo.com/en/docs/historical-weather-api ; ERA5 gridded reanalysis and attribution as documented.
4. Station directory: https://github.com/prasenjit-27/Indian-Railway-Data ; verify against authoritative railway data for operational use.
5. Applicable utility tariff order and OEM HVAC/transformer/EV/BESS product documentation must be supplied and versioned per site.

**Publication note:** This expanded edition is a source-backed consolidation of accessible GitHub manuals and documented OneDrive file inventory, with additional engineering, business and IT requirements analysis. It is not a verbatim merger of inaccessible OneDrive PDF/TeX contents, and no engineering field calibration is implied.
