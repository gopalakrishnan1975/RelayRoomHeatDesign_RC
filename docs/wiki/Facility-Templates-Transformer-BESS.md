# Railway Facility Energy Design Studio — design revision

## Scope
The Streamlit app now supports editable starting templates for catering stall, relay room, waiting hall, running room, kitchen, food stall and high-mast lighting. Choose a template, click **Apply template**, then review every row. Existing multi-room inputs remain supported.

## Minimum inputs
Location and coordinates; historical weather period; room length, width, height, window and door area; connected equipment kW; number of people; room setpoint; AC unit count and unit TR; assigned light/fan/other circuits with number, watts and schedules; tariff; available PV area; design power factor, utilization and reserve. Optional BESS requires nominal kWh, inverter kW, efficiency and installed cost.

## Method
Cooling = envelope conduction + approximate solar heat gain + infiltration sensible/latent + equipment + occupants + assigned indoor circuits. Each circuit is counted once electrically; exterior circuits do not add indoor cooling load. Capacity uses historical coincident weather extremes with an N+1 largest-unit-out check. Site kW is equipment + circuits + AC consumption. Sunrise/sunset drive light schedules.

Transformer preliminary apparent power = max(peak import kW*(1+reserve), PV export rating kW) / (power factor * allowed utilization). Choose the next standard kVA. This is *not* short-circuit, protection, starting current, harmonic, feeder or sanction design.

Optional BESS dispatch uses an hourly state of charge, power limits, minimum 10% and maximum 90% SOC, and square-root split of round-trip efficiency. It charges from surplus PV and discharges against coincident site load. Grid imports/exports are recomputed after battery dispatch. Battery capital and annual O&M enter discounted lifecycle cost. Current optimization selects PV **without** co-optimizing BESS capacity; the entered BESS is evaluated separately. It does not model tariff arbitrage, backup autonomy, cycling degradation, replacement, demand charges, or safety systems.

## Important template qualifications
The defaults are illustrative, not sanctioned load schedules. Kitchen and catering design must explicitly consider hood exhaust, replacement air, moisture and cooking fuel. Waiting halls need peak crowd scenarios. Relay rooms require S&T-approved temperature, redundancy, hotspot and equipment constraints. Running rooms need variable occupancy. High-mast template currently creates a placeholder electrical kiosk to satisfy the multi-room calculation; its artificial AC consumption must be removed or a true exterior-only mode implemented before using a high-mast-only demand result.

## Verification
The regression workflow runs Python tests including template validation and transformer arithmetic. A green test is not a substitute for browser deployment verification or professional electrical/HVAC design review.
