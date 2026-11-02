# Maintenance audit — 2 November 2026

## Baseline and regression evidence

- Inspected `app.py`, `ev_charging.py`, `station_design.py`, `station_lookup.py` and their regression tests on `main`.
- Latest completed baseline GitHub Actions run: [41409192998](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/41409192998), 2 November 2026, SHA `5ba3f254d0ec47cf24f736668eee8d6f54999546`, **29 passed, 12 warnings**. This tests the existing main branch.
- Reran the revised EV scheduler in an isolated local environment: **15 focused tests passed**. Coverage: 48-hour daytime, overnight, all-day, incomplete windows, year-end, managed ceiling, zero points and invalid timestamps.
- Opened [draft PR #3](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/3) on `fix/ev-service-day-2026-11-02` with the EV correction and eight additional repository regression tests. **Merged into main** after complete branch CI [41484879915](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/41484879915) passed **37 tests, 12 warnings**. Squash merge SHA: `21ac3dfd2ee4de65bef9a7cbc1197d6a69a58bb5`. Live Streamlit verification remains separate.

## Defect and proposed correction

`ev_charging.py` groups hour-ending timestamps by their calendar date, creating phantom daily charging requests and incorrect overnight attribution. The branch correction groups by **hour-start/service-day**, requires complete, unique, chronological hourly bins and excludes incomplete charging windows rather than claiming unobserved service. The implementation preserves the existing aggregate, deterministic model, not a vehicle-level queue or controller.

## Open issues

- **Station-code revision restore — FIXED:** [PR #4](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/4) preserves saved coordinates/provenance by default, displays current catalogue coordinates separately and requires explicit adoption. Old saved coordinates are retained even if the code is no longer in the current directory; a newly typed unknown code remains blocked. Two new Streamlit AppTests passed with the complete branch suite: **39 passed, 12 warnings**, [run 41485575755](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/41485575755). Merge SHA `71fcf48075644300420b79ffe09706e895f910f0`. [PR #5](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/5) additionally corrected the displayed provenance caption (merge SHA `a2faf0e90d53373e86034fa054be48dc4945fe40`), after successful full CI [41485832502](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/41485832502).
- **Managed EV/PV economics:** after re-dispatching EV load at the initially selected PV capacity, the application recalculates the PV cost candidates but does not update `chosen` to match the new candidate minimum. Treat displayed capacity/ranking as provisional until corrected and regression tested. No claim of global PV/EV co-optimization.
- **Live deployment:** the deployed Streamlit URL was not accessible through the available web reader; interactive browser access also requires an originating browser context. The live commit and actual PDF/CSV/JSON downloads are unverified.
- **OneDrive:** upload to `user/202507_DRM/AI_generated_technical_reports/Relay_Room_Thermal_Solar_Optimization` was attempted but rejected with `BLOCKED_FILE_REFERENCE`. Existing OneDrive documents remain unchanged.

## Existing coverage, not new end-to-end certification

The baseline suite covers running-room bedrooms, guest conservation, shared areas, kitchen/laundry/unconditioned zones, portable revision hashes and parent chain, meter timestamp/PF validation, contract-kVA screening, station-code and Manual coordinates, location-dependent weather invalidation, facility templates, historical N+1, sunrise/sunset, whole-site electricity, transformer/BESS, PV economics and Streamlit download controls. The EV and station-restoration corrections passed full branch CI and were merged; the deployed Streamlit build and live downloads still require a separate smoke test.

**Safety and governance:** station revision JSON files are portable and hash-protected, not a central registry or approval system. Hourly simulated peaks cannot authorize grid-commitment reduction; complete seasonal utility billing-interval evidence, meter multipliers, tariff verification and DISCOM approval remain mandatory. No physical AC control or utility submission was performed. Thermal physics and approved safety assumptions were not changed.
