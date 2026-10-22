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
