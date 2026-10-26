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


## Follow-up — 25 October 2026

The repository's latest inspected commit remains `2f6ab8764f44245f46a17853df430232545df7cb` (audit documentation only); no application-code repair has been made. GitHub Actions [run 40116413793](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/40116413793) reports **25 passed, 12 warnings in 7.49 s** (24 October 2026, 17:30 UTC). The 12 warnings arise from Streamlit/Pandas deprecated `DataFrame.reset_index(inplace=True)` usage.

Reconfirmed the **missing meter timestamp** defect using a source-equivalent Python/Pandas reproduction of current `station_design.py` blob `39b1034c3d45b51e6ca512a48958d15f860c5e6e`: valid 80/99/90-kVA readings give a 99-kVA monthly peak, but assigning a null timestamp to the 99-kVA reading silently lowers the result to **90 kVA**. Two isolated assertions passed; this is **not** a fresh full-repository test. Reject null/NaT timestamps and add regression cases before any repair commit. The invalid-upload/stale-evidence, unassigned running-room guest, and managed-EV/PV-ranking findings remain open.

Live deployment still could not be accessed via web fetch, and the connected browser requires the originating browser context. The deployed SHA, station/weather cache behavior, and actual PDF/CSV/JSON downloads remain **unverified**. A complete local source checkout is blocked by GitHub DNS resolution; **no application code changed**. Preserve portable-JSON-only revision storage, complete seasonal billing-interval meter evidence, DISCOM approval and the prohibition on physical AC control or utility contract submission. The follow-up status is also prepared for OneDrive.


## Repair and verification — 26 October 2026

**Code fixes merged:** [PR #1](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/1), squash commit `1252bcfb7048cb4adbe5dc68d863bd47a22ff640`. The missing/blank/NaT timestamp defect in `monthly_demand` is fixed: invalid rows are rejected rather than silently excluded from the monthly peak. An invalid replacement meter CSV now stops downstream comparisons and revision exports instead of silently falling back to restored summary data; restored summaries are labelled unverified without their original interval CSV. Running-room allocation now conserves all peak guests: the sleeping profile sets a desired bedroom fraction, scheduled shared zones absorb available non-sleeping guests, and residual guests stay in bedrooms with `Guests requiring bedroom overflow` exposed in the hourly output. No heat-transfer, derating or N+1 safety physics were altered.

**Contract safeguards:** The lowest screened cost is explicitly *not* an approved or recommended contract. Incomplete seasonal meter coverage triggers warnings; require full billing-interval seasonal evidence, meter multipliers, tariff/ratchet verification, future growth/outage reserve and DISCOM approval. Hourly simulated peaks must not authorize contract reduction. Portable JSON revisions remain user-managed files with hashes, not a central registry or electronic approval. No physical AC control or utility submission.

**Tests:** Source-equivalent local meter/guest regression checks passed before branch changes. [Repair branch CI](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/40370504024) passed **27 tests, 12 warnings**; [main after merge](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/40370693607) also passed. [PR #2](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/pull/2), squash commit `7e61f3ab086e9ff65cc206503fc6409c493df6ef`, adds finite-energy screening for all facility templates (including unconditioned high-mast lighting) and a Streamlit AppTest that invalidates old weather results after a station-code/coordinate change. [Its CI](https://github.com/gopalakrishnan1975/RelayRoomHeatDesign_RC/actions/runs/40370783010) passed **29 tests, 12 warnings** before merge.

**Not certified:** Direct deployed Streamlit browser interaction remains unavailable without the originating browser context. The deployed SHA, live station/weather behavior and actual downloaded PDF/CSV/JSON bytes have not been independently checked. The managed-EV/PV two-pass candidate-ranking inconsistency remains open; no claim of joint global optimization. GitHub Actions and Streamlit AppTest do not prove live deployment.
