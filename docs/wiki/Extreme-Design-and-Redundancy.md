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
