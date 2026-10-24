# Railway Facility Energy Design Studio
## Consolidated Technical, Business, Data, IT Architecture and User Manual
**Edition:** 24 October 2026 | **Status:** Engineering screening and software design reference

**Application:** https://relayroomheatdesignrc-fhfhpzvryxnksd7cef9kg8.streamlit.app/  
**Source:** https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC

### Document control and precedence
This is the **single consolidated reference** for the facility energy simulator, assembling the previously separate manuals in full, with a current capability matrix and clarifications. It includes earlier relay-room research material as a **legacy appendix**; legacy references to synthetic weather, missing BESS or absent station-code lookup are historical, not descriptions of the current default planner. The running-room building programme supersedes the old single-room template description. The high-mast electrical kiosk is **unconditioned** in the current implementation. Station lookup is from a non-authoritative offline community dataset and must be field verified.

**Audience:** Railway divisional engineering, electrical, S&T, commercial, operations and finance officers; data engineers, application developers, reviewers and procurement teams. **Not a procurement certificate, utility sanction, safety approval, or physical equipment controller.**

### Executive business case
The tool compares facility HVAC, connected equipment, lighting, EV charging, solar PV, battery storage and grid-import commitments on a common hourly energy basis. Station-wise portable revision JSONs allow design alternatives to be archived and restored. Expected business outcomes are transparent capex screening, lower avoidable energy and demand charges, evidence-led contracted-capacity reviews, auditable engineering assumptions and repeatable station designs. Actual savings require site metering, tariff validation and operational confirmation.

### Current capabilities and boundaries
| Domain | Implemented now | Not yet implemented / not certified |
|---|---|---|
| Location | Exact station-code lookup; editable manual lat/lon; location provenance | Authoritative station master or reverse geocoding |
| Weather | Historical ERA5 hourly temperature, RH, GHI, sunrise/sunset; forecast-day mode | IMD station calibration, guaranteed future extremes |
| Thermal | Multi-room envelope, infiltration, people/equipment/circuits, N+1 screening | CFD, dynamic humidity, inter-room heat transfer, certified HVAC selection |
| Templates | Relay, catering, waiting, running room, kitchen, food stall, high mast | Fully engineered kitchen exhaust or building-services design |
| Running room | Bedrooms, beds, occupancy profile, kitchen, lobby, dining, baths, laundry | Hotel-grade hot-water, exhaust and occupancy stochastic simulation |
| Electrical | Whole-site hourly demand, preliminary transformer kVA | Short-circuit, harmonic, cable, earthing, protection or utility sanction |
| EV | Two-/four-wheeler slow, destination and fast groups; connected kW; served/unserved energy; managed charging ceiling | Queueing, individual vehicle SOC/taper, actual swapping inventory |
| Solar/BESS | Area-constrained PV economics; hourly surplus-PV BESS dispatch | Joint PV+BESS+contract optimization, degradation, backup autonomy |
| Grid contract | Meter CSV monthly peaks, contract candidate comparison | Automatic contract changes or reproduction of all utility tariff rules |
| Revisions | Portable, hash-checked, parent-linked JSON station revisions | Central authenticated database, OneDrive auto-sync, signed approvals |
| Reporting | Hourly CSV, PDF design report, JSON export | Certified design dossier or guaranteed accuracy |

### Business and financial decision rules
1. Distinguish connected load (kW), coincident peak import (kW), apparent demand (kVA), transformer rating (kVA), contract demand (kVA) and purchased energy (kWh).
2. Use measured billing-interval demand and complete seasonal coverage to assess contract reduction; hourly simulations alone may miss short peaks.
3. Keep tariff energy charges, demand charges, excess penalties, PV export credit, battery capex/O&M and transformer procurement costs distinct. Do not double-count savings or imply that PV/BESS optimization jointly minimizes all of them.
4. For each proposal compare baseline, engineered alternative, measured/calibrated demand, annualized savings, discounted lifecycle cost, sensitivity and safety/approval constraints.
5. Require railway engineering approval, relevant electricity-utility permissions and site-specific manufacturer data before procurement or contract changes.

### EV charging functional specification and energy accounting
Configure each charging group with vehicle category, point count, charger **grid input kW per point**, charging efficiency, vehicles per day, battery energy required per vehicle and permitted start/end hours. Example defaults: two-wheeler slow 1.5 kW, two-wheeler higher-power 3.3 kW, four-wheeler AC destination 7.4 kW and four-wheeler DC fast 64 kW. These are **illustrative editable inputs**, not vehicle compatibility claims. Group connected load is points × grid kW/point. Daily requested grid energy is vehicles/day × battery kWh/vehicle ÷ efficiency. Scheduling is bounded by available charger capacity and the permitted hours; unmet charging energy must be reported. Managed charging considers PV coincidence, electricity rates and a shared site-import ceiling. The current method is aggregate hourly allocation, not a queueing model or battery-swap inventory model. Validate charger nameplate input, phase, diversity, connector compatibility and protection separately.

### Data contracts and governance
**Station master:** code, station name, source, latitude, longitude, location mode, source version, verification date. **Design revision:** station code, design label, revision number, parent hash, content hash, creation UTC, input payload and notes. **Rooms/zones:** unique zone ID, geometry, openings, equipment, peak people, temperature, conditioned flag, schedule, proposed AC units/TR. **Circuits:** circuit ID, room/exterior, type, count, watts, schedule. **EV:** group, vehicle class, connectors, grid input kW, efficiency, vehicles/day, battery kWh/vehicle, hours, served/unserved energy. **Meter:** timestamp plus kVA, or kW and measured PF, interval provenance, missingness/coverage. **Results:** timestamp, heat components, AC kW, other loads, EV kW, PV kW, BESS SOC, grid import/export, peak and annual totals. Track model version, assumptions, input hashes and weather source per run.

### IT architecture — as built versus target
**As built:** modular Python calculation modules (site_energy.py, facility_design.py, station_design.py, station_lookup.py, ev_charging.py, extreme_design.py) behind Streamlit app.py, with a separate legacy_app.py; in-session data, user-uploaded meter CSV, downloadable revision JSON and report exports. GitHub Actions regression workflow; no central persistent user database or authentication.

**Target (proposal, not deployed):** Streamlit/web client → authenticated station/scenario API → weather ingestion and station-master service → thermal/EV/PV/BESS simulation services → optimization/contract-demand service → report service; PostgreSQL for station/scenario/asset/revision metadata, time-series partitioning for meter/weather observations, object storage for source CSV and immutable PDF/JSON outputs. Require role-based access, approval workflow, audit logs, backups, encryption, secrets management, version migrations and independent engineering sign-off. Do not place restricted railway asset or meter information in a public GitHub repository.

### Acceptance and validation gates
- Verify station-code resolution, invalid-code rejection, manual-coordinate persistence and station-centre-versus-facility distinction.
- Validate weather completeness and coincident extreme selection; room geometry, latent/sensible loads, unconditioned zones, occupancy conservation and N+1.
- Check load aggregation without duplicate circuits, sunrise/sunset schedules, EV served/unserved conservation and import-ceiling adherence.
- Check PV/import/export balance, battery SOC bounds, transformer sizing and consistent economic reporting.
- Validate meter timestamps, PF conversion, duplicate/gap detection, seasonal coverage and conservative contract-candidate screening.
- Round-trip revision JSON, parent hashes, station separation, backward compatibility and PDF/CSV outputs.
- Run automated regression **before commit**, GitHub Actions after commit and live Streamlit smoke test after deployment. A green test is not a safety certificate.

### Source hierarchy
The sections below reproduce the underlying manuals and specialist wiki references. Where statements conflict, **the current capability matrix and newest running-room/location sections above take precedence**; legacy appendix documents are preserved for research traceability.

---


---

# CURRENT SPECIALIST REFERENCE 1: docs/Generic_Room_Site_Energy_Manual.md

# Generic Room Heat Load and Site Energy Planner
Technical, business, data, IT and user manual - 24 October 2026

## 1. Purpose and scope
The application calculates cooling demand for one or more generic rooms and aggregates AC electricity, continuous equipment, fans, lights and other circuits into a station or site demand profile. It sizes AC capacity against historical extreme coincident weather with a largest-unit-out N+1 check, and selects solar PV capacity within a user-entered available area to minimize discounted energy cost. The previous relay-room calculator remains available from the Calculator selector, including its illustrative spatial map and hourly temperature scheduler. The new default planner does not claim a CFD temperature field or direct AC control.

## 2. Bare essential inputs
Station/site name and code are report identifiers. Latitude and longitude determine weather. Historical start/end years determine the design basis, defaulting to the last 30 complete years. For each room enter a unique name, length, width, height, total window area, total door area, continuous equipment electricity in kW and maximum people simultaneously present. A second compact room table contains target temperature, occupancy schedule, installed AC unit count (including standby) and nominal TR per unit. For each fan/light/other circuit enter name, assigned room or Site exterior, type, count, watts per item and schedule. Site cost inputs are import tariff, optional peak tariff and hours, export credit, available PV area, area per kWp and an independently evaluated PV capacity. Shared engineering and finance assumptions are placed in collapsed sections to keep the main input flow short.

## 3. User workflow
1. Enter the station and verified coordinates. Changing station text alone does not relocate weather retrieval.
2. Select Historical extreme design + annual energy. Choose complete years from 1940 through the latest complete year. Forecast day is explicitly operations-only.
3. Add one row per room. Windows and doors are areas, not widths: multiply width by height and sum all openings. The gross wall area must exceed their combined area.
4. Set each room's temperature, maximum occupancy schedule and proposed AC arrangement. All AC operates continuously at the specified target; occupancy changes heat generation, not the AC availability schedule.
5. Enter room and exterior fans/lights/other loads. Each electrical item must appear once. Do not repeat a listed circuit in Equipment_kW.
6. Choose schedules: Always, Daylight, Night, Occupied hours, or Off. Night is sunset to sunrise; Daylight is sunrise to sunset. Occupied hours are daily clock hours. Equal start/end means 24 hours; overnight windows are supported. Weekends/holidays are not separately modelled.
7. Enter tariffs and PV constraints; review shared engineering assumptions.
8. Click Load weather and sunrise/sunset. Edits to room/circuit/cost assumptions recalculate against the loaded weather. Changing weather location, basis or period requires retrieval again.
9. Review each room's N+1 result, governing weather and heat contributions. Then review peak site electrical kW, annual kWh, PV optimum and discounted costs. Select a plot date for up to seven days of detailed graphs.
10. Download the PDF, full hourly demand CSV and JSON of all input settings and provenance. JSON is an audit/export format; the interface does not yet import it automatically.

## 4. Data sources and quality
The Open-Meteo archive endpoint is https://archive-api.open-meteo.com/v1/archive with models=era5. Inputs requested are hourly temperature_2m (C), relative_humidity_2m (%) and shortwave_radiation (W/m2), plus daily sunrise and sunset. Forecast uses https://api.open-meteo.com/v1/forecast for one day. Timezone is Asia/Kolkata; this version is intended for Indian station/site scheduling. Historical requests are batched by five years, with 90-second request timeouts and 24-hour application caching. The forecast uses a 25-second timeout and the same caching wrapper; it is a planning snapshot, not a real-time control feed.

Every expected hourly timestamp must be present, unique and ordered. Null, nonfinite or out-of-range RH/radiation data block the calculation. Unavailable or invalid sunrise/sunset also blocks calculations; polar sun cases are not supported. There is no silent synthetic or forecast replacement for historical data. Provenance records source, exact request URLs and retrieval UTC. Source documentation: https://open-meteo.com/en/docs/historical-weather-api and https://open-meteo.com/en/docs . Attribution: Open-Meteo / ECMWF ERA5, CC BY 4.0 as provided by Open-Meteo. Service usage limits and terms apply.

ERA5 is gridded reanalysis, not a measured station extreme. Longer available history can be selected, but the historical maximum is not a guarantee against future extremes. Verify against available IMD/local measurements and site conditions before procurement. No independent IMD dataset is automatically ingested by this release.

## 5. Thermal equations and assumptions
For room floor area A=L*W, volume V=A*H, and net opaque wall area Awall=2*(L+W)*H-Awindow-Adoor, sensible envelope conduction is [Uroof*A + Uwall*Awall + Uwindow*Awindow + Udoor*Adoor] * max(0,Tout-Tin) / 1000 kW. Clipping negative conduction is conservative for cooling in cool conditions; free cooling and heating are not modelled. Shared U-values are user-editable; the default does not represent a measured building construction.

Solar heat uses GHI * [effective roof solar factor*A + 0.0192*Awall + SHGC*Awindow] / 1000. This is a screening surrogate, not orientation-specific sol-air conduction, dynamic roof thermal storage or a radiation-view-factor calculation. The roof factor is adjustable and the fixed wall coefficient is disclosed here. No shading or tilted façade irradiance is inferred from room geometry.

Infiltration mass flow is 1.18*V*ACH/3600 kg/s. Sensible infiltration is mass_flow*1.006*max(0,Tout-Tin) kW. Latent infiltration is max(0,mass_flow*2501*(wout-win)) kW, where w=0.62198*pwater/(101325-pwater), and saturation pressure is 610.94*exp(17.625*T/(T+243.04)) Pa. Constant standard pressure and air density are used. Indoor RH is an assumed design moisture state; no humidity-control or condensation transient is solved.

People contribute separate editable sensible and latent heat rates, default 75 W and 55 W/person. Operating heat follows occupancy schedule. Cooling capacity design uses full entered people and all connected room circuits simultaneously as a conservative internal-load case, combined with each historical weather hour. Equipment electricity is continuous and assumed fully dissipated inside the room. Room-assigned lights, fans and other electrical circuits add equal heat; exterior circuits add no room cooling load. No heat transfer between rooms is solved.

The maximum coincident total load for each room is multiplied by (1+design allowance/100). Each room may have a different governing hour. The sum of individual cooling maxima is not reported as the coincident site electrical peak; site peak is computed from the aggregated hourly electrical profile.

## 6. AC capacity, redundancy and electricity
Required nominal capacity per equal unit = design_cooling / [(installed_units-1)*3.517*available_capacity_fraction]. Proposed surviving capacity = (installed_units-1)*TR_each*3.517*available_capacity_fraction. N+1 passes only when surviving capacity meets design cooling. At least two units are required in this planner. The nominal TR and available fraction must be checked against manufacturer total AND sensible capacity at the actual indoor/outdoor design conditions. The default fraction 0.85 is illustrative.

Operational AC electricity equals scheduled hourly thermal cooling / COP. COP=max(1,COPbase-COPslope*max(0,Tout-35)). Defaults are 3.5 and 0.025/C. This is an editable engineering approximation, not an inverter compressor map. The design allowance affects installed capacity, not every operating energy hour. Electricity assumes sufficient cooling capacity; a failing N+1 result is flagged rather than silently limiting power and pretending the indoor target was maintained.

N+1 is a steady-state unit-out capacity check, not proof of resilience against common electrical supply or control failure. Independent protection, power backup, alarms, duty rotation, standby activation, restart delays and critical hotspot/humidity protection require site engineering. The preserved relay-room calculator retains its separate simplified standby-delay screening; the generic planner does not calculate room transient failure trajectories. Solar is given no firm AC capacity credit.

## 7. Sunrise/sunset and scheduling
All energy bins end at the displayed weather timestamp, aligning with preceding-hour mean shortwave radiation. Lights/fans/occupancy use overlap between that preceding hour and sunrise/sunset to avoid treating a partial dawn/dusk hour as a full hour. Temperature and RH at the ending timestamp approximate conditions in that bin. Business and peak-tariff integer hours use the corresponding bin start hour. Midnight uses the preceding day's solar interval approximation; for Indian sites it remains a night hour. Calendar-year energy totals follow the ending timestamps. This boundary convention is explicitly shared across demand, PV, tariff and exports.

Demand = equipment electricity + lights + fans + other circuits + AC electricity. Every assigned circuit appears once in demand. Its cooling penalty is additional compressor electricity, not a duplicate circuit entry. Exterior loads bypass indoor cooling. Fans do not automatically reduce room setpoints or cooling demand; their electricity becomes indoor heat if located in the room.

## 8. PV sizing and cost optimization
Hourly PV = kWp * GHI/1000 * performance ratio. Default performance ratio is 0.78. This is a horizontal-irradiance proxy without tilt, shading, clipping, snow, detailed temperature loss or degradation. Available area / area per kWp establishes the maximum feasible PV. The entered area must already exclude obstructions and unsuitable surfaces; it is not automatically inferred from all room floor areas. Default area per kWp is 5 m2.

Grid import=max(0,demand-PV); export=max(0,PV-demand). Check demand+export=PV+import. Import tariff may have one daily peak window, including overnight windows; equal peak start/end means peak tariff all day. Export credit is independent. No battery, sanctioned-load demand charge, fixed charge, tax, subsidy, tariff escalation or storage is included.

For historical data, energy and bills are averaged over the selected complete calendar years. Baseline is the same hourly demand with zero PV. Annual bill saving = baseline bill - PV case net bill. Annual O&M = PV capex*O&M_percent/100. Incremental NPV = sum over economic years of (annual bill saving - O&M)/(1+real_discount)^year - capex. Discounted life-cycle cost = capex + sum (annual bill+O&M)/(1+real_discount)^year. Select PV capacity minimizing life-cycle cost among 0.5 kWp steps and the exact area limit. Zero PV remains a candidate. An independently entered PV size is also evaluated; if it exceeds area it is labelled infeasible and excluded from the constrained optimum. The tool limits interactive search to 500 kWp.

Cost optimization changes PV size only. It does not alter approved room temperatures, attendance, working hours or required lighting. To compare a schedule change, edit its explicit inputs and compare results. Annual sizing is not extrapolated from the forecast day. Forecast mode evaluates only its entered PV and daily bill; it does not claim an annual economic optimum.

## 9. Outputs and audit trail
PDF: all room/circuit inputs, shared assumptions, site and weather provenance, period, room design maxima and N+1 checks, governing heat-source breakdown, annual demand/PV/import/export, selected-week hourly demand and all PV economic alternatives. The PDF includes first/last-week sunrise/sunset samples; full hourly results are in the companion CSV to avoid a multi-decade report with hundreds of thousands of rows. JSON records input assumptions, selected/evaluated PV sizes and provenance. Results remain in memory; no external database or physical control integration is implemented.

## 10. Software architecture and performance
app.py handles the generic UI, validation messages, visualization and exports. site_energy.py handles room/circuit validation, weather ingestion, schedules, vectorized heat/electric calculations and cost optimization. legacy_app.py preserves the previous relay calculator; extreme_design.py retains its historical sizing utility. There are no new cloud credentials. Station coordinates and requested periods are transmitted to Open-Meteo; room inputs are calculated in the running Streamlit app.

Thermal and schedule calculations use NumPy/Pandas arrays across weather hours. Plotting is restricted to seven days while energy optimization uses every selected hour. Five-year fetch batches bound request size, caches avoid repeat retrieval, and PV search uses a bounded candidate set. CSV/PDF export generation can take longer for a multi-decade run. This is a modular Streamlit research app, not a fleet-scale real-time microservice platform.

## 11. Validation and limitations
Automated tests cover largest-unit-out redundancy, historical coincident extreme selection, day/night complement and fractional dawn/dusk hours, people sensible/latent effects, circuit heat and non-duplication, exterior load treatment, exact room aggregation, PV/grid conservation, zero-PV optimization and invalid geometry. The previous relay UI retains regression coverage. Live 2025 Open-Meteo retrieval with sunrise/sunset returned 8,760 complete hours. A generic UI run with this data generated charts, annual costs, a constrained PV optimum and a PDF. Further deployment evidence is recorded in release notes after testing.

No CFD, calibrated material dynamics, inter-room coupling, room humidity transient, occupancy stochasticity, thermostat cycling, AC electrical starting current, distribution-board sizing or equipment certification is implied. The model should be calibrated with room measurements, nameplate/actual electrical readings and manufacturer performance data. Energy-economic screening is distinct from approved electrical protection and procurement design.

## 12. Release verification - 24 October 2026
Eight automated tests passed locally and on GitHub Actions. The full 1996-2025 Mancherial retrieval contained 262,992 complete hourly records with daily sunrise/sunset. A two-room vectorized calculation and 41 PV candidate costs completed in approximately 0.7 seconds on the development runtime, excluding download, UI rendering and export generation. A full 30-year generic UI run completed and generated the design PDF. After restarting Streamlit, the deployed website showed the new generic planner, successfully calculated the same 30-year weather period and downloaded PDF, full hourly CSV and input JSON. Example default single-room results were 7.83 kW peak electrical demand and 34,566 kWh average annual demand; the PV optimum was 4.80 kWp at the default 24 m2 usable area / 5 m2 per kWp constraint. These are software test inputs and results, not a proposed actual station procurement design. Per-room temperature/AC settings are retained when additional room rows are added, and removing all rooms shows a prompt rather than crashing.



---

# CURRENT SPECIALIST REFERENCE 2: docs/Running_Room_Versions_Grid_Manual.md

# Running Rooms, Station Design Versions and Grid Commitments
Railway Facility Energy Design Studio - 24 October 2026

## Running room as a building
The Running room template is now a lodging building, with one row for every bedroom and separate kitchen, dining hall, lobby/reception, bathrooms/toilets, laundry/services and corridors. Inputs include bedrooms, beds per bedroom, peak simultaneous guests, peak staff, connected cooking, water heating and laundry loads. The starting example is 10 two-bed bedrooms; it is not surveyed Mancherial data. Each zone's geometry, equipment, target temperature, occupancy, AC enabled flag and proposed AC units remain editable.

Bedroom cooling capacity checks full permitted bed occupancy and historical extreme weather. Operating energy uses peak guests and an editable 24-hour sleeping occupancy profile. Dining, lobby and bathroom guests are allocated first and removed from the bedroom pool; the same guest is not heated in two zones simultaneously. The accounted guest count never exceeds the entered peak. Any unallocated guests are outside the simulated zones. Zone design maxima remain separate conservative capacity scenarios, not claims that every zone's full occupants are present simultaneously. Staff are split among reception, kitchen and laundry in the template; actual rosters and zone assignments must be verified.

Kitchen cooking/exhaust and dining occupancy use meal windows 06:00-09:00, 12:00-15:00 and 19:00-22:00 IST. Refrigeration/equipment base load remains continuous. Water heating, laundry and pump loads follow the daily occupied-hours window. Lights may follow sunrise/sunset. All values are editable connected-load examples, not meal-per-person or hot-water process engineering. Kitchen capture hoods, combustion, fresh-air makeup, moisture extraction, actual geyser cycling and laundry duty require site design.

Unconditioned kitchen, bathrooms, laundry and corridors contribute their electrical loads without an artificial AC load. Bedroom/shared conditioned spaces retain AC capacity and N+1 checks. All enabled ACs continue to maintain their targets; the profile changes people heat, not AC permission. The high-mast placeholder kiosk is also unconditioned, removing its previous phantom cooling demand. Shared envelope assumptions and per-room exposed roofs remain simplified; use actual construction and exposure data before procurement.

Changing the building programme regenerates room/circuit rows, so manual row changes must be reviewed again. Peak guest changes update bedroom occupancy fractions. Saved template target temperatures are now respected rather than replaced with a universal 21 C.

## Station-specific immutable design revisions
Choose a station code and design label, enter revision notes, then click Create station design revision. Download the resulting JSON to the station's own folder, for example OneDrive/Station Designs/MCI. Filename includes station code, revision number and content-hash prefix. A revision contains station coordinates, building programme, room and circuit tables, schedules, engineering/finance assumptions, transformer/BESS settings, PV area/capacity inputs, grid-contract assumptions and any uploaded monthly demand summary. Raw meter intervals are not embedded. Weather can be retrieved again using the saved basis.

To update a design later, upload its revision JSON and click Restore station design. Edit and create a new revision. Revision number increments and parent hash links the previous snapshot. A different station starts its own revision chain. Integrity checking detects accidental changes to the file; the hash is not a signature, approval or proof of authorship. Keep previous files rather than overwriting them. The separate Download design inputs JSON is an unversioned audit export; restore expects a station revision file.

Storage boundary: revision files are downloaded and re-uploaded by the user. Streamlit session history is temporary. This release does not silently publish station designs to the public GitHub repository, synchronize OneDrive from the web app or provide a central authenticated multiuser registry. Download each revision to retain it. A later central database/OneDrive integration requires service authentication and access controls; no credentials are embedded.

## Actual demand and grid contract comparison
Transformer nameplate kVA, contracted grid kVA and energy purchase kWh are distinct. Transformer sizing remains a physical equipment screening calculation. Grid commitment comparison uses user-entered contract demand, demand charge per kVA/month, minimum billing fraction, additional excess-demand charge, growth/uncertainty reserve and contract step size.

Upload actual demand CSV as timestamp,kva or timestamp,kw,pf. Each record must be an interval demand value at the utility's billing interval, not a cumulative energy reading. kW is converted to kVA only when measured PF is supplied. Duplicate timestamps, nonfinite/negative demand and gaps greater than one hour are rejected. The app reports monthly maximum demand, approximate interval coverage and observed median interval length. Less than 12 months or under 95% coverage triggers a warning: a short sample is not evidence of an annual design peak. Compare complete seasonal records, preferably including hot-season running-room occupancy peaks.

For each candidate contract C and monthly recorded peak D, the illustrative charge is demand_rate*max(D, minimum_fraction*C) + additional_excess_rate*max(0,D-C). The tool displays observed-period charges, an indicative annualization and months exceeding contract. Candidate selection is restricted to C at least maximum observed peak*(1+reserve); it does not choose a lower commitment by trading reliable supply for penalties. Rates default to zero so actual tariff inputs are required before financial interpretation. The app does not claim to reproduce every utility's tariff, demand ratchet, approval process or contract-change conditions.

If no meter data are provided, the app displays a clearly labelled simulated hourly planning comparison. By default this uses gross demand with no PV or BESS capacity credit. A user may explicitly compare modelled net import, but solar/cloud variation, battery availability and finer interval peaks remain unresolved. Actual meter data may itself include PV/BESS operation, so outage and low-generation cases must be reviewed before reducing commitments. The tool neither submits a contract change nor certifies a proposed reduction. Actual reduction/increase is subject to the applicable utility tariff, sanctioned-demand rules and approval.

Tariff reference for verification, not a hardcoded model: Telangana Electricity Regulatory Commission, Retail Supply Tariff Schedule FY 2026-27, https://www.tgerc.telangana.gov.in/file_upload/uploads/Tariff%20Orders/Tariff%20Schedule/Tariff%20Schedule%202026-27.pdf . Verify the relevant category and current order for each station.

## Economics and reports
Grid fixed/demand-charge alternatives are shown separately from PV/BESS energy economics; the tool does not jointly optimize PV, BESS, contract demand and hotel operations. Optional BESS starts at minimum reserve SOC so it does not create free usable energy in its first interval. Battery-adjusted grid imports, exports, annual bill savings and NPV are kept consistent with its incremental life-cycle cost. End-SOC credit, replacements and demand-target dispatch are not modelled; the battery remains a surplus-solar self-consumption simulation.

The PDF includes running-room programme and expanded zone tables, design assumptions, transformer/BESS summary, grid-contract inputs, measurement versus simulation basis and candidate comparison. It is not a substitute for a utility application or a measured demand report. CSV exports include full hourly electrical results and grid-contract options. The revision JSON is the restorable design record.

## Validation
Automated tests cover bedroom count and bed capacity, peak guest allocation, no guest double counting, unconditioned services, programme edits in the UI, revision numbering and parent hashes, modified-file rejection, station separation, kW/PF conversion, duplicate meter records, partial coverage, safe contract candidates, positive demand-charge savings and no free initial BESS energy. Existing historical thermal, room aggregation, solar balance, template, transformer, report-control and legacy UI tests remain in the suite. A live-weather 2025 running-room UI test completed the expanded building calculation, PDF and contract comparison. Website test evidence is recorded in the final release check.

## Release test record
17 regression tests passed locally after the final UI restoration fixes. The GitHub Actions run for the final application-code commit also passed. The running-room building UI was tested with 8,760 downloaded ERA5 weather hours for 2025 and generated the PDF and grid-contract comparison successfully. Live deployment exposes the bedroom/bed/guest/staff programme and station revision creation controls. Final refresh is required when Streamlit retains a previous code revision. All default room sizes and electrical loads remain examples pending station-specific survey data.



---

# CURRENT SPECIALIST REFERENCE 3: docs/Station_Location_Lookup.md

# Station-code lookup and manual facility locations
Railway Facility Energy Design Studio - 24 October 2026

## Automatic station mode
The default Location entry mode is Station code lookup. Enter a code and press Enter or leave the field. The application normalizes whitespace/case and matches the code exactly, then fills the station name and decimal-degree latitude/longitude. Read-only fields prevent an old station name from being paired with a newly entered code. Unknown, blank or unusable codes do not fall back to Mancherial or fuzzy matching; weather retrieval and revision creation remain disabled until a valid station or manual location is supplied.

The offline directory contains 8,697 records with usable coordinates from the MIT-licensed community dataset https://github.com/prasenjit-27/Indian-Railway-Data , source commit 1dc0ddbc6a06b09ef69d4825ff3127c1f29640fa, retrieved 24 October 2026. 293 records lacking usable coordinates were excluded. The bundled compressed snapshot is checked against a SHA-256 digest and does not require a geocoding service at runtime. Original names are preserved; unrelated state/address/zone fields are omitted because some are stale or missing. Licence text and source metadata are retained in data/STATIONS_LICENSE.txt and data/stations_metadata.json.

This is not an authoritative Railway station master. Coordinates describe the station reference point, not necessarily a relay room, running room, EV parking area or individual building. Verify actual facility coordinates before final design. For example the directory resolves MCI to MANCHIRYAL at 18.878745 N, 79.448848 E; this differs from the earlier illustrative manually entered Mancherial coordinates.

## Manual coordinate mode
Select Manual coordinates to enter exact latitude/longitude directly. Station/site name, station code and an optional description/address are editable. There is no reverse-geocoding request and no automatic overwrite of coordinates. Latitude and longitude are required and must be finite, within -90 to +90 and -180 to +180. A blank name receives a coordinate-based display label. If the code is blank, a stable LOC_ identifier is derived from coordinates for version filenames. After an unsuccessful station lookup, manual coordinate fields start empty rather than retaining a different station's coordinates.

Current weather and schedule timezone remains Asia/Kolkata; this mode does not change the application's Indian-site scheduling convention. Polar sunrise/sunset limitations of the weather engine remain unchanged.

## Weather, versions and PDF
The resolved/manual coordinates are used consistently in weather cache keys, historical extremes, solar and sunrise/sunset calculations. Changing coordinates invalidates a previously loaded weather result. Each design revision and input export now records location_mode, location_details and location_source alongside the coordinates. The PDF reports the selected mode and provenance. Older saved revisions without location_mode reopen in Manual coordinates mode when they contain explicit coordinates, preserving the historical design location instead of silently moving it to the directory station centre.

## Verification
25 regression tests passed before commit. Added tests verify catalogue integrity/count, MCI/SC/NDLS matches, case/whitespace normalization, unknown/blank rejection, manual coordinate ranges and finite values, station-code changes updating displayed fields, blocking weather/revisions on failed lookup, empty manual inputs after a failed lookup, coordinate-based identifiers, and preservation of older saved coordinates. Existing thermal, EV, storage, grid commitment, running-room and versioning tests remain included.



---

# CURRENT SPECIALIST REFERENCE 4: docs/wiki/Facility-Templates-Transformer-BESS.md

# Railway Facility Energy Design Studio — design revision

## Scope
The Streamlit app now supports editable starting templates for catering stall, relay room, waiting hall, running room, kitchen, food stall and high-mast lighting. Choose a template, click **Apply template**, then review every row. Existing multi-room inputs remain supported.

## Minimum inputs
Location and coordinates; historical weather period; room length, width, height, window and door area; connected equipment kW; number of people; room setpoint; AC unit count and unit TR; assigned light/fan/other circuits with number, watts and schedules; tariff; available PV area; design power factor, utilization and reserve. Optional BESS requires nominal kWh, inverter kW, efficiency and installed cost.

## Method
Cooling = envelope conduction + approximate solar heat gain + infiltration sensible/latent + equipment + occupants + assigned indoor circuits. Each circuit is counted once electrically; exterior circuits do not add indoor cooling load. Capacity uses historical coincident weather extremes with an N+1 largest-unit-out check. Site kW is equipment + circuits + AC consumption. Sunrise/sunset drive light schedules.

Transformer preliminary apparent power = max(peak import kW*(1+reserve), PV export rating kW) / (power factor * allowed utilization). Choose the next standard kVA. This is *not* short-circuit, protection, starting current, harmonic, feeder or sanction design.

Optional BESS dispatch uses an hourly state of charge, power limits, minimum 10% and maximum 90% SOC, and square-root split of round-trip efficiency. It charges from surplus PV and discharges against coincident site load. Grid imports/exports are recomputed after battery dispatch. Battery capital and annual O&M enter discounted lifecycle cost. Current optimization selects PV **without** co-optimizing BESS capacity; the entered BESS is evaluated separately. It does not model tariff arbitrage, backup autonomy, cycling degradation, replacement, demand charges, or safety systems.

## Important template qualifications
The defaults are illustrative, not sanctioned load schedules. Kitchen and catering design must explicitly consider hood exhaust, replacement air, moisture and cooking fuel. Waiting halls need peak crowd scenarios. Relay rooms require S&T-approved temperature, redundancy, hotspot and equipment constraints. Running rooms need variable occupancy. High-mast template currently creates a placeholder electrical kiosk to satisfy the multi-room calculation; its artificial AC consumption must be removed or a true exterior-only mode implemented before using a high-mast-only demand result.

## Verification
The regression workflow runs Python tests including template validation and transformer arithmetic. A green test is not a substitute for browser deployment verification or professional electrical/HVAC design review.



---

# CURRENT SPECIALIST REFERENCE 5: docs/wiki/Data-and-Validation.md

# Data architecture, measurement and validation

## Current data handling
The Streamlit app holds slider values and calculated NumPy/Pandas tables in memory. It has no persistent database, API service, user accounts or real-time telemetry integration. Users can export selected hourly tables to CSV.

## Recommended pilot input dictionary
| Field | Unit | Source | Suggested cadence |
|---|---|---|---|
| station_id, room_id | text | S&T asset register | on change |
| room length, width, height | m | measured survey | on change |
| roof/wall/window/door areas | m² | measured drawings | on change |
| envelope U-value | W/(m² K) | construction/OEM | on change |
| glazing SHGC | ratio | glazing specification | on change |
| equipment electrical load | kW | meter/nameplate | 1–15 min |
| outdoor/relay-zone temperature | °C | calibrated sensors | 1–15 min |
| outdoor/indoor RH | % | calibrated sensors | 1–15 min |
| solar GHI, DNI, DHI | W/m² | site pyranometer/weather | hourly |
| AC input power | kW | submeter | 1–15 min |
| PV output/import/export | kW or kWh | inverter and bidirectional meter | 1–15 min |
| tariff and export credit | ₹/kWh | applicable utility contract | on change |
| AC COP/performance | dimensionless | OEM measured map | by condition |

## Suggested future relational tables
`site(site_id, station_code, lat, lon)`, `room(room_id, site_id, geometry, orientation)`, `asset(asset_id, room_id, asset_type, rated_power)`, `sensor(sensor_id, asset_id, metric, calibration_date)`, `observation(sensor_id, ts_utc, value, quality_flag)`, `weather(site_id, ts_utc, temperature, rh, ghi, dni, dhi)`, `tariff(site_id, effective_from, import_rate, export_rate)`, `scenario(scenario_id, room_id, model_version, config_json)`, `simulation_run(run_id, scenario_id, started_at, status)`, `simulation_hour(run_id, ts_utc, setpoint, cooling_kw, ac_kw, pv_kw, import_kw)`.

## Proposed future IT architecture
Streamlit frontend → scenario API → thermal model service → optimizer service → PV/economics service → relational database/object storage. Telemetry ingestion and alerting are separate services. These are proposed modules, **not present in the current code**.

## Validation and acceptance
Calibrate to measured hourly temperatures and AC energy across hot, humid, cloudy and low-load days. Assess MAE/RMSE and peak-error for room/relay temperatures, kWh error for AC demand, PV generation error, humidity violations and feasible AC ramp rates. Compare model schedules to an independently measured fixed-temperature baseline. Require S&T safety review and rollback/fail-safe rules before any control integration.



---

# LEGACY / HISTORICAL REFERENCE 6: docs/wiki/Extreme-Design-and-Redundancy.md

# Historical Extreme AC Design and Redundancy
23 October 2026

## Design intent
Select AC capacity from adverse historical coincident weather and peak equipment/infiltration loads. The daily weather forecast is used only for operational electricity and solar optimization. It must not establish installed cooling capacity.

## Weather basis
Open-Meteo Historical Weather API, model ERA5: hourly temperature_2m, relative_humidity_2m and shortwave_radiation. Source documentation: https://open-meteo.com/en/docs/historical-weather-api . ERA5 is available from 1940; the UI accepts 1940 through the last complete year. Default period is 30 complete years (1996-2025 as of this release). Requests are made in five-year batches and cached for 24 hours. Every requested hourly timestamp must appear exactly once; null, nonfinite, missing or invalid RH/radiation values block sizing. There is no silent substitution with forecast or synthetic data. Source: Open-Meteo and ECMWF ERA5; attribution CC BY 4.0 per Open-Meteo. The location coordinates are editable and must be verified.

For additional years, choose the required start/end period and click Retrieve historical weather and size AC. Long periods may take time and remain subject to API service limits. Failure is displayed and no historical design result is asserted. Gridded reanalysis is not a measured station record; verify against available local IMD observations before procurement. The maximum in a historical record does not guarantee future extremes.

## Calculation
For every hour calculate envelope conduction, solar-gain surrogate, maximum continuous equipment heat, lighting, sensible infiltration and latent infiltration at the specified design indoor temperature and RH. Use temperature, RH and radiation from the SAME hour. The governing design hour maximizes total cooling load, which can differ from the hottest dry-bulb hour. Show its timestamp, coincident weather and heat-source breakdown. Required cooling equals this maximum times (1 + explicit allowance/100).

An optional additional outdoor-temperature uplift provides a separate conservative stress sensitivity. It preserves RH, which increases moisture content; it is not a historical observation or a statistical return-period estimate. Report 0.4%, 1% and 2% empirical exceedance percentiles of dry-bulb temperature and total hourly load separately. These are not certified ASHRAE design conditions. Annual maxima plots help identify unusual years.

## N+1 capacity
For nominal capacities q_i in TR and manufacturer available-capacity fraction f, usable capacities are 3.517*f*q_i kW. Pass only if sum(usable capacities) minus the largest usable capacity is at least the required design cooling. UI currently configures equal units; the calculation utility supports unequal sizes. Default 3 x 3 TR and f=0.85 are illustrative inputs, not an approved selection. Compare 2 x 100%, 3 x 50% and 4 x 33.3% configurations by showing minimum nominal TR per unit after derating. Round UP to verified available equipment sizes; manufacturer total and sensible capacity at actual outdoor/indoor conditions must both be checked. There is no firm-capacity credit for PV.

## Failure-delay screening
Assume N duty units and one standby, with one duty unit failing. Available cooling until standby starts comes from installed count minus two surviving duty units. Temperature rise = positive cooling shortfall x delay_hours / effective thermal capacitance. Starting room temperature is explicit. Compare resulting temperature with the design limit. This constant-load approximation does not establish actual hotspot protection, RH control, compressor restart behavior or controller reliability. N+1 does not cover common power/control failures. Provide independent circuits/protection, suitable backup power, independent relay-end sensors, alarms, automatic changeover and duty rotation in the engineered installation.

## Model boundary
Historical screening uses a simplified steady-state envelope and radiation surrogate. It does not calculate orientation-specific dynamic roof/wall thermal lag, CFD airflow, AC capacity maps or humidity transients. A historical extreme result is therefore a screening basis, not a procurement certificate. Reliability, manufacturer data and site measurements remain required engineering inputs.

## UI and report
The historical sizing section precedes forecast energy optimization. Enter years, design indoor limit, peak equipment heat, adverse infiltration, design allowance, optional stress uplift, derating, unit count/TR and standby delay. Click Retrieve historical weather and size AC. Changing location or period invalidates the displayed historical result until retrieval; other design inputs recalculate using the selected history. The complete PDF includes period, historical request URLs, governing hour, coincident weather, all design assumptions, annual maxima, empirical percentiles, N+1 alternatives, selected-configuration pass/fail, estimated standby-delay temperature and governing load components. Without retrieved history, the PDF explicitly states EXTREME DESIGN NOT EVALUATED.

## Validation
Python compilation and three automated tests passed, including largest-unit-out redundancy and a fixture proving that independent weather extremes are not combined. Live ERA5 retrieval for 2025 returned 8,760 validated hours for Mancherial. Streamlit AppTest completed the historical sizing flow with that downloaded data; illustrative default inputs yielded 19.47 kW including allowance for 2025 alone. That is not the 30-year design result. Existing forecast and PDF controls remained functional in regression tests.

Website: https://relayroomheatdesignrc-fhfhpzvryxnksd7cef9kg8.streamlit.app/

## Completed 30-year deployment test
Live archive retrieval validated 262,992 hours for 1996-2025 at the approximate Mancherial coordinates. Highest dry-bulb temperature in this ERA5 record was 46.8 C. The coincident load governing hour was 21 May 2015 at 13:00 IST, with dry bulb 46.3 C, RH 18% and GHI 968 W/m2. With default model inputs (8 x 5 x 3 m room, 2 kW equipment, 21 C indoor limit, 0.35 ACH, existing envelope and 15% allowance), required design cooling was 21.23 kW. The deployed app correctly returned FAIL for 3 x 3 TR at f=0.85 (17.94 kW surviving) and PASS for 3 x 4 TR (23.92 kW surviving). Browser download of the historical design PDF succeeded. These are model screening results using default inputs, not a site-certified AC selection.



---

# LEGACY / HISTORICAL REFERENCE 7: docs/wiki/Hourly-Optimization.md

# 24-hour adaptive AC setpoint optimization

## Objective
Choose hourly room setpoints `T[0] ... T[23]` within user-specified bounds to minimize either:
- sum of hourly grid imports (kWh), or
- sum of `import_kWh * import_tariff - export_kWh * export_tariff` (₹).

## Dynamic-programming formulation
State: discretized room temperature (0.5°C increments). Transition: previous temperature to next temperature, restricted by the maximum change per hour. A lumped thermal capacitance `C` (kWh/°C) approximates stored heat.

```text
cooling_kWh[h] = max(0, heat_gain_kWh[h,Tnext] + C*(Tprev - Tnext))
AC_kWh[h]      = cooling_kWh[h] / COP[h]
PV_kWh[h]      = PV_kWp * synthetic_irradiance[h]/1000 * 0.78
grid_import[h] = max(0, AC_kWh[h] - PV_kWh[h])
grid_export[h] = max(0, PV_kWh[h] - AC_kWh[h])
```

The solver enumerates feasible temperature states each hour and reconstructs the lowest-cost path. It forces the end-of-day temperature back to the starting temperature to prevent artificially borrowing energy from the following day.

## Important constraints and caveats
- Temperature bounds are **user-provided scenario inputs**, not equipment-approved operating limits.
- The model has a single room temperature, not a separately predicted relay-end sensor temperature.
- No equipment thermal lag, condensation dynamics, fan energy, AC cycling, minimum run time, real tariff schedule or predictive uncertainty is represented.
- PV electricity is netted against AC load only, without batteries.
- A warmer permissible setpoint often reduces load; pre-cooling may help under solar-hour coincidence or export-value assumptions, but is not guaranteed.
- Fixed-baseline comparison uses the chosen starting temperature; it is not a calibrated measured baseline.

## Good practice
Run sensitivity cases with different thermal capacitance, RH, PV sizes and permitted temperatures. Verify temperature limits and humidity with S&T engineering and OEM specifications before making field recommendations.



---

# LEGACY / HISTORICAL REFERENCE 8: docs/wiki/Thermal-Model.md

# Thermal and psychrometric model

## Cooling heat-balance approximation
At each hour, the current code computes heat components in kW:
- Roof: `Uroof * length * width * max(Tout-Tset,0)/1000`.
- Walls: `Uwall * exposed_wall_area * max(Tout-Tset,0)/1000`.
- Windows/doors: `U * area * max(Tout-Tset,0)/1000`.
- Solar heat: a **heuristic** irradiance-weighted roof/wall term plus glazing `irradiance * window_area * SHGC / 1000`.
- Equipment: user-entered kW, treated as constant internal sensible gain.
- Lighting: fixed 0.2 kW.
- Infiltration sensible: `m_dot * 1.006 * max(Tout-Tset,0)`.
- Infiltration latent: `max(0, m_dot * 2501 * (w_out-w_in))`.

Here `m_dot=1.18 * volume * ACH / 3600` kg/s and humidity ratio is approximated by
`w = 0.62198 * p_v / (101325 - p_v)`, `p_v=RH_fraction * 610.94*exp(17.625*T/(T+243.04))`.

**Limitations:** U-values and irradiation coefficients are approximations; roof/wall thermal mass and radiation exchange are not solved explicitly. Latent loads depend on outdoor humidity and assumed indoor RH; condensate and dynamic moisture balance are not modelled. Cooling demand is clipped to nonnegative sensible temperature difference, so heating or beneficial free cooling is not simulated.

## Cooling to electricity
The code uses a simplified ambient-dependent COP: `max(2,3.5 - 0.025*max(0,Tout-35))`. Electrical AC demand is cooling kW divided by COP. Actual AC selection needs manufacturer performance at design ambient and part-load conditions.

## Spatial heat map
The heat map is a geometric distance-based illustrative function anchored at the relay point. It does not solve Navier–Stokes, turbulence, radiative exchange or air supply/return boundaries. Do not use it to select installation location without measurement or validated CFD.



---

# LEGACY / HISTORICAL REFERENCE 9: docs/wiki/Weather-and-PDF.md

# Relay Room Simulator: Weather and PDF Update
23 October 2026

## Operation
Enter station name and station code in the first row. Mancherial (MCI) is the default. Weather is selected by editable latitude/longitude (approximate Mancherial defaults 18.872 N, 79.444 E), not by the text name or railway code. For another station, enter its verified coordinates as well as its name/code.

Open-Meteo supplies one local calendar day of hourly temperature_2m (C), relative_humidity_2m (%) and shortwave_radiation (W/m2). Timezone: Asia/Kolkata. Endpoint: https://api.open-meteo.com/v1/forecast. Forecast is modelled gridded weather, not station instrumentation. Radiation is preceding-hour mean GHI; temperature/RH are timestamp values. Hourly bin coincidence is an approximation. Attribution: Open-Meteo, CC BY 4.0, https://open-meteo.com/.

Responses are cached for one hour. Requests time out after 20 seconds. Incomplete, null, nonfinite or out-of-range RH/radiation responses fail visibly. The app does not silently replace failed API data with synthetic weather. Select Synthetic demonstration explicitly to explore offline.

## Report
Download complete design report PDF generates a multipage report from the current run. It contains station identifiers, coordinates, weather provenance/retrieval time, all numerical inputs, cooling sizing, nominal TR, fixed and adaptive optimization results, hourly weather (live mode), heat-source breakdown, humidity sensitivity, hourly electricity balances, setpoint alternatives and PV economic alternatives. Tables use kW for hourly power and sums over one-hour periods for kWh. The illustrative spatial map is available in the app; it is not a calculated airflow field.

## Corrections
The dynamic optimizer rejects negative-cooling transitions: gains + C*(previous temperature - next temperature) must be nonnegative. Previously clipping this value at zero allowed physically impossible rapid passive warming. End temperature equals start temperature to avoid borrowing thermal energy from the next day. Equal minimum/maximum limits no longer cause a slider exception. The default relay-end maximum is 21 C. Wider limits require user specification. Negative opaque wall area is prevented by clamping to zero; geometrically invalid openings should still be checked by an engineer.

## Validation and automation
Python syntax compilation passed. Streamlit AppTest passed with deterministic mocked weather, synthetic weather and a variable 21-26 C range. PDF generation passed; first page visually inspected. These checks do not validate CFD, equipment reliability or deployed website behavior.

GitHub Actions runs offline regression tests on pushes, pull requests, manual dispatch and daily at 07:00 IST. A separate maintenance task can inspect failures, repair code and update this documentation. Streamlit deployment depends on the existing app being connected to the main branch. Its public URL has not been provided or independently verified.

## Engineering limits
The app has no direct AC control, capacity saturation, calibrated airflow, active humidity dynamics or measured relay hotspot model. AC COP and roof/wall solar gain factors are simplified. GHI times PV rating times 0.78 is a horizontal-irradiance proxy without tilt/shading modelling. Repeating one forecast day 365 times is only an illustrative PV NPV comparison, not procurement-grade annual energy or design-weather sizing. Use verified equipment limits, AC redundancy, site weather and 8760-hour analysis before implementation.



---

# LEGACY / HISTORICAL REFERENCE 10: docs/wiki/Quick-Start.md

# Quick start and dashboard walkthrough

## Install
```bash
git clone https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC.git
cd RelayRoomHeatDesign_RC
python -m pip install -r requirements.txt
streamlit run app.py
```

## Step-by-step
1. Enter length, width and height in metres. Confirm measured dimensions.
2. Enter peak outdoor temperature and RH; distinguish these from the hourly synthetic profile.
3. Set roof/wall/window/door U-values in W/(m²·K), glazing SHGC, window/door areas and air changes per hour.
4. Enter continuous equipment electrical heat in kW, solar peak irradiance in W/m², PV installed kWp, import/export tariffs and PV capital cost.
5. Set **manual target** and **permitted minimum/maximum**. The latter are modelling bounds, **not certified relay limits**.
6. Inspect the hourly heat sources, cooling thermal kW, AC electrical kW, PV generation and grid import.
7. For adaptive operation, select effective thermal capacitance, maximum hourly setpoint change, starting room temperature and optimization objective.
8. Compare the fixed-temperature baseline against the optimized 24-hour schedule; download CSVs.

## Charts
- Heat-source chart: equipment, solar, envelope, infiltration and lighting.
- Ambient profile: synthetic 24-hour outdoor temperature.
- Heat map: relative spatial gradient around AC and relay locations, **not CFD**.
- PV/electricity chart: coincident hourly generation and electrical consumption.
- Adaptive schedule: hourly selected temperature and grid import/export.
- Sensitivities: outdoor humidity, improved windows/doors and roof insulation.

## Common units
kW = instantaneous power; kWh = energy over an hour; kWp = nominal PV rating; TR = 3.517 kW of cooling; COP = cooling kW / electrical kW; RH = relative humidity.

## Interpreting results
Do not confuse peak cooling capacity with average electricity use. The model's 'solar heat gain' is heat entering the room; 'solar PV generation' is electricity produced on the roof.



---

# LEGACY / HISTORICAL REFERENCE 11: docs/wiki/FAQ-and-Limitations.md

# FAQ, troubleshooting and limitations

**Why does humidity increase cooling demand?** Infiltrating moist air may require dehumidification, which adds latent cooling load.

**Will a better door or window help?** Yes, via lower U-value, lower glazing SHGC and reduced leakage. Actual savings depend on solar exposure, orientation and opening frequency.

**Why are cooling kW and AC electrical kW different?** Electrical kW is approximately cooling kW divided by COP.

**Why does PV not eliminate nighttime imports?** No battery is modelled, and PV production is near zero at night.

**Does the room heat map locate the optimal AC?** No. It is a surrogate illustration and cannot establish air-velocity or relay-body-temperature compliance.

**Can I use the hourly setpoint schedule on a live relay room?** Not without independently approved equipment temperature/humidity constraints, calibrated sensors, validated controls, S&T engineering approval and fail-safe interlocks.

**What data drives the default weather?** A synthetic sinusoidal daily temperature and solar irradiance curve. It is not measured Hyderabad/Lucknow weather or a location-specific annual weather file.

**Can the app save scenarios?** Not currently; export the available CSVs and record slider settings externally.

**Troubleshooting:** Run `pip install -r requirements.txt`, then `streamlit run app.py`. Slider numeric types must be consistent; inspect Streamlit logs for any runtime error.

**Privacy of documents:** GitHub directories do not have independent permissions. A public repository cannot contain a private folder. Keep restricted source/PDF documents in OneDrive with restricted access or in a separate **private** GitHub repository. Do not commit confidential documents to public Git history.

