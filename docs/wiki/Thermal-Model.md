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
