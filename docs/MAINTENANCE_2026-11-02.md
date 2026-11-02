# Maintenance audit — 2 November 2026

## Baseline and regression evidence

- Inspected `app.py`, `ev_charging.py`, `station_design.py`, `station_lookup.py` and their regression tests on `main`.
- Latest completed baseline GitHub Actions run: [41409192998](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/41409192998), 2 November 2026, SHA `5ba3f254d0ec47cf24f736668eee8d6f54999546`, **29 passed, 12 warnings**. This tests the existing main branch.
- Reran the revised EV scheduler in an isolated local environment: **15 focused tests passed**. Coverage: 48-hour daytime, overnight, all-day, incomplete windows, year-end, managed ceiling, zero points and invalid timestamps.
- Opened [draft PR #3](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/3) on `fix/ev-service-day-2026-11-02` with the EV correction and eight additional repository regression tests. Do not merge before the complete branch CI passes.

## Defect and proposed correction

`ev_charging.py` groups hour-ending timestamps by their calendar date, creating phantom daily charging requests and incorrect overnight attribution. The branch correction groups by **hour-start/service-day**, requires complete, unique, chronological hourly bins and excludes incomplete charging windows rather than claiming unobserved service. The implementation preserves the existing aggregate, deterministic model, not a vehicle-level queue or controller.

## Open issues

- **Station-code revision restore:** `app.py` resolves the current catalogue coordinates even when the uploaded portable station revision saved different coordinates under Station code lookup. A catalogue update can silently move an old engineering design. Preserve saved coordinates and provenance by default; display new catalogue coordinates separately and require explicit adoption. Existing tests cover Manual coordinates, but not this lookup-mode case.
- **Managed EV/PV economics:** after re-dispatching EV load at the initially selected PV capacity, the application recalculates the PV cost candidates but does not update `chosen` to match the new candidate minimum. Treat displayed capacity/ranking as provisional until corrected and regression tested. No claim of global PV/EV co-optimization.
- **Live deployment:** the deployed Streamlit URL was not accessible through the available web reader; interactive browser access also requires an originating browser context. The live commit and actual PDF/CSV/JSON downloads are unverified.
- **OneDrive:** upload to `user/202507_DRM/AI_generated_technical_reports/Relay_Room_Thermal_Solar_Optimization` was attempted but rejected with `BLOCKED_FILE_REFERENCE`. Existing OneDrive documents remain unchanged.

## Existing coverage, not new end-to-end certification

The baseline suite covers running-room bedrooms, guest conservation, shared areas, kitchen/laundry/unconditioned zones, portable revision hashes and parent chain, meter timestamp/PF validation, contract-kVA screening, station-code and Manual coordinates, location-dependent weather invalidation, facility templates, historical N+1, sunrise/sunset, whole-site electricity, transformer/BESS, PV economics and Streamlit download controls. The proposed EV change needs a complete CI run and live smoke test before release.

**Safety and governance:** station revision JSON files are portable and hash-protected, not a central registry or approval system. Hourly simulated peaks cannot authorize grid-commitment reduction; complete seasonal utility billing-interval evidence, meter multipliers, tariff verification and DISCOM approval remain mandatory. No physical AC control or utility submission was performed. Thermal physics and approved safety assumptions were not changed.
