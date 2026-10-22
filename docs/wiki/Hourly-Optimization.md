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
