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
