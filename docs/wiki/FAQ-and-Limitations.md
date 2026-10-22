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
