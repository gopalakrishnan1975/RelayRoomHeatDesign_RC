"""Offline station-code directory with explicit provenance; no fuzzy code matching."""
import base64,gzip,hashlib,json,math,re
from functools import lru_cache
from pathlib import Path

DATA=Path(__file__).parent/'data'

@lru_cache(maxsize=1)
def catalogue():
    meta=json.loads((DATA/'stations_metadata.json').read_text())
    decoded=gzip.decompress(base64.b64decode((DATA/'stations.json.gz.b64').read_text(),validate=True))
    if hashlib.sha256(decoded).hexdigest()!=meta['sha256']:raise ValueError('Station directory integrity check failed')
    rows=json.loads(decoded);index={}
    for code,name,lat,lon in rows:
        if code in index:raise ValueError('Duplicate station code in catalogue')
        if not name or not math.isfinite(lat) or not math.isfinite(lon) or not (6<=lat<=38 and 68<=lon<=98):raise ValueError('Invalid station directory record')
        index[code]=dict(code=code,name=name,latitude=lat,longitude=lon)
    if len(index)!=meta['valid_records']:raise ValueError('Station directory count mismatch')
    return index,meta


def find_station(code):
    normalized=str(code).strip().upper()
    if not re.fullmatch(r'[A-Z0-9-]{1,12}',normalized):raise ValueError('Enter a valid station code or select Manual coordinates')
    index,meta=catalogue()
    if normalized not in index:raise ValueError(f'Station code {normalized} was not found with usable coordinates. Select Manual coordinates to enter this location.')
    return dict(index[normalized],source=meta['source'],source_commit=meta['commit'],directory_date=meta['retrieved'])


def coordinate_location(name,latitude,longitude,code=''):
    lat=float(latitude);lon=float(longitude)
    if not math.isfinite(lat) or not math.isfinite(lon) or not (-90<=lat<=90 and -180<=lon<=180):raise ValueError('Latitude/longitude must be finite and in range')
    identifier=code.strip().upper() or 'LOC_'+hashlib.sha256(f'{lat:.6f},{lon:.6f}'.encode()).hexdigest()[:10].upper()
    return dict(name=name.strip() or f'Location {lat:.5f}, {lon:.5f}',code=identifier,latitude=lat,longitude=lon,source='User-entered coordinates')
