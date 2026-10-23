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
