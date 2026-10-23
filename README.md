# Relay Room Thermal and Solar Simulator

Run `pip install -r requirements.txt` then `streamlit run app.py`.

Enter station name/code (default Mancherial/MCI) and verified coordinates. Open-Meteo supplies hourly temperature, humidity and solar radiation. Changing name/code alone does not locate another station: update coordinates too. Live requests are cached for one hour; API failures stop with a visible error. Synthetic demonstration is an explicit alternative.

Download the current design inputs and numerical outputs using **Download complete design report PDF**. See [weather and PDF guide](docs/wiki/Weather-and-PDF.md).

Hourly dynamic programming includes thermal inertia, temperature/rate constraints and closed daily cycle. Default maximum relay-end temperature is 21 C. Spatial heat map is illustrative, not CFD. PV NPV extrapolates one day and is not investment-grade annual sizing. No AC equipment is controlled.

Tests: `pip install pytest` then `pytest -q`. GitHub Actions runs on changes and daily. Live forecast, mocked forecast, synthetic mode and PDF generation have been exercised locally. The deployed Streamlit URL is still needed for independent website verification.
