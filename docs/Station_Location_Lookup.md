# Station-code lookup and manual facility locations
Railway Facility Energy Design Studio - 24 October 2026

## Automatic station mode
The default Location entry mode is Station code lookup. Enter a code and press Enter or leave the field. The application normalizes whitespace/case and matches the code exactly, then fills the station name and decimal-degree latitude/longitude. Read-only fields prevent an old station name from being paired with a newly entered code. Unknown, blank or unusable codes do not fall back to Mancherial or fuzzy matching; weather retrieval and revision creation remain disabled until a valid station or manual location is supplied.

The offline directory contains 8,697 records with usable coordinates from the MIT-licensed community dataset https://github.com/prasenjit-27/Indian-Railway-Data , source commit 1dc0ddbc6a06b09ef69d4825ff3127c1f29640fa, retrieved 24 October 2026. 293 records lacking usable coordinates were excluded. The bundled compressed snapshot is checked against a SHA-256 digest and does not require a geocoding service at runtime. Original names are preserved; unrelated state/address/zone fields are omitted because some are stale or missing. Licence text and source metadata are retained in data/STATIONS_LICENSE.txt and data/stations_metadata.json.

This is not an authoritative Railway station master. Coordinates describe the station reference point, not necessarily a relay room, running room, EV parking area or individual building. Verify actual facility coordinates before final design. For example the directory resolves MCI to MANCHIRYAL at 18.878745 N, 79.448848 E; this differs from the earlier illustrative manually entered Mancherial coordinates.

## Manual coordinate mode
Select Manual coordinates to enter exact latitude/longitude directly. Station/site name, station code and an optional description/address are editable. There is no reverse-geocoding request and no automatic overwrite of coordinates. Latitude and longitude are required and must be finite, within -90 to +90 and -180 to +180. A blank name receives a coordinate-based display label. If the code is blank, a stable LOC_ identifier is derived from coordinates for version filenames. After an unsuccessful station lookup, manual coordinate fields start empty rather than retaining a different station's coordinates.

Current weather and schedule timezone remains Asia/Kolkata; this mode does not change the application's Indian-site scheduling convention. Polar sunrise/sunset limitations of the weather engine remain unchanged.

## Weather, versions and PDF
The resolved/manual coordinates are used consistently in weather cache keys, historical extremes, solar and sunrise/sunset calculations. Changing coordinates invalidates a previously loaded weather result. Each design revision and input export now records location_mode, location_details and location_source alongside the coordinates. The PDF reports the selected mode and provenance. Older saved revisions without location_mode reopen in Manual coordinates mode when they contain explicit coordinates, preserving the historical design location instead of silently moving it to the directory station centre.

## Verification
25 regression tests passed before commit. Added tests verify catalogue integrity/count, MCI/SC/NDLS matches, case/whitespace normalization, unknown/blank rejection, manual coordinate ranges and finite values, station-code changes updating displayed fields, blocking weather/revisions on failed lookup, empty manual inputs after a failed lookup, coordinate-based identifiers, and preservation of older saved coordinates. Existing thermal, EV, storage, grid commitment, running-room and versioning tests remain included.
