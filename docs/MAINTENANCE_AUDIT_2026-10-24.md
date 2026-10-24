# Maintenance audit — 24 October 2026

**Baseline:** `main` commit `527a6ae46f88813ed2e42cd1d62a09a7bffc3d70`. **No application code changed.**  
**CI:** [run 40072402083](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/40072402083) succeeded on 24 October 2026: `pytest -q` reported **25 passed, 12 warnings in 6.54 s**. This is baseline regression evidence, not a live deployment verification.

Reviewed `app.py`, `station_design.py`, `station_lookup.py`, `site_energy.py`, `facility_design.py`, `extreme_design.py`, `ev_charging.py`, the relevant regression tests and the station-directory provenance. Isolated source-equivalent tests confirmed valid kW/PF conversion, invalid PF/duplicate/gap rejection, revision hash tamper rejection and parent-chain checks. The deployed Streamlit page could not be accessed from this run, so actual browser interactions, deployed SHA, PDF/CSV/JSON bytes and weather cache behavior are **unverified**.

## Defects and regression cases

1. **HIGH — Missing meter timestamps can understate demand.** `station_design.monthly_demand` uses `pd.to_datetime(..., errors='raise')` but does not reject `NaT`/null. A source-equivalent reproduction with rows `00:00 80 kVA`, `NaT 99 kVA`, `00:15 90 kVA` reports a **90-kVA** monthly peak because the 99-kVA row is dropped during grouping. Fix: reject null timestamps before grouping; add missing/blank/`NaT` tests.
2. **HIGH — Invalid replacement CSV may leave restored demand active.** In `app.py`, `measured_monthly` starts from restored revision data; if a new uploaded CSV fails parsing, the exception displays an error but leaves the restored data in the contract-comparison path. Fix: invalidate comparison on failed upload or require explicit selection of saved evidence; add Streamlit AppTest.
3. **MEDIUM — Editable sleeping profiles can leave guests unassigned.** With 16 peak guests outside meal hours, lobby 4, baths 2 and sleeping fraction 0, the current allocation accounts for only **6** guests; 10 are unassigned. This does not double count, but the 'peak guests present' pool is not fully accounted for. Add hourly unassigned count/warning and tests at sleeping fractions 0, 0.5, 1.
4. **MEDIUM — Managed EV/PV chosen capacity may be stale.** In `app.py`, the first PV optimum is selected, managed EV is re-dispatched at that size, and PV candidates are recalculated but the new best is discarded. Add a deterministic scenario verifying the displayed selected capacity matches the published cost ranking; retain the explicit no-joint-optimization limitation.

## Regression and safety coverage

| Area | Current evidence and caveat |
|---|---|
| Running room | Bedroom/bed capacity, shared dining/lobby/baths, kitchen/laundry/corridors, unconditioned-zone tests in CI; guest-accounting gap above. |
| Station revision | SHA-256 hash, parent hash, station restriction, create/download/restore baseline tests; **portable JSON only**, no central registry, automatic sync or approval. |
| Station code / manual coordinates | Exact normalized lookup, unknown-code blocking, editable manual coordinates and legacy saved-coordinate tests; community catalogue of 8,697 coordinate-bearing stations with source SHA-256; not an authoritative asset master. |
| Weather cache | Code keys on latitude, longitude, years and basis and rejects stale loaded weather; deployed behavior not inspected. |
| Facility templates | Relay, waiting, catering/food, kitchen, high mast, running room, custom source reviewed; no live walkthrough. |
| Historical extreme/N+1 | Coincident same-hour T/RH/GHI and largest-unit-out derating baseline tests; not certified OEM sizing. |
| Sunrise/site energy | Fractional sunrise/sunset and energy-conservation baseline tests. |
| Transformer/BESS/PV/EV | Preliminary transformer, bounded SOC with no free initial energy, PV lifecycle candidates, EV served/unserved and managed ceiling baseline tests; managed PV issue above. |
| PDF/CSV/JSON | Download controls and AppTests exist; live downloaded bytes unverified. |

**Mandatory safeguards:** Never use simulated hourly peaks to authorize reduced contracted kVA. Require utility billing-interval (15/30-minute as applicable) data with complete seasonal evidence (preferably >=12 months), CT/PT multipliers, tariff-specific ratchets/penalties, PV/BESS outage, future EV growth, reserve and **DISCOM approval**. Preserve physics, derating and N+1 assumptions. No physical AC/charger control or utility contract submission. Fixes must pass the complete `pytest -q` and Streamlit AppTest suite **before code commit**, followed by CI and deployed-browser smoke testing.

**Status:** Audit documentation only. No code repair or live-deployment certification was performed because a full local source checkout and originating browser context were unavailable.
