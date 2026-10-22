# Relay Room Heat Design — User Wiki

**Purpose:** Understand and explore air-conditioning demand, relay-room thermal conditions, solar PV output, grid imports and 24-hour temperature schedules.

**Start here:** [Quick start](Quick-Start.md) · [Physics](Thermal-Model.md) · [Hourly optimization](Hourly-Optimization.md) · [Data and validation](Data-and-Validation.md) · [FAQ and limitations](FAQ-and-Limitations.md)

> **Safety:** This is an exploratory Streamlit model, not a railway-approved temperature controller, CFD solver, procurement design or safety assurance. The spatial heat map is illustrative and the default weather is synthetic. Confirm relay/electronic equipment temperature and humidity requirements before considering any operational changes.

## What is implemented?
The Streamlit application in `app.py` exposes room dimensions, thermal properties, equipment heat, humidity, window/door properties, infiltration, solar irradiance, AC/relay positions, tariff and PV assumptions. It displays heat-load breakdowns, a surrogate heat map, humidity and envelope sensitivity, PV economics, fixed-temperature comparisons and an adaptive 24-hour setpoint schedule.

## What is not implemented?
Measured weather ingestion, calibrated heat-transfer/CFD, equipment internal temperature prediction, transient humidity storage, actual AC performance maps, battery optimization, tariff schedules, persistence, authentication, live sensors, approved controls and production-grade testing.

## Source of truth
- [Application](../../app.py)
- [Dependencies](../../requirements.txt)
- [Document index](../TECHNICAL_BUSINESS_DATA_IT_USER_MANUAL.md)
- The LaTeX/PDF manual is currently stored in the designated private OneDrive folder, linked from the document index.
