from facility_design import TEMPLATES, template_data, transformer_design
from site_energy import validate_rooms

def test_templates():
    for name in TEMPLATES:
        rooms, loads = template_data(name)
        validate_rooms(rooms, loads)

def test_transformer():
    result = transformer_design(100, 10)
    assert result['standard_kva'] == 200


def test_all_facility_templates_have_finite_hourly_energy_and_expected_ac():
    import numpy as np
    from site_energy import calculate
    from test_site_energy import fixture,params
    for name in TEMPLATES:
        rooms,loads=template_data(name)
        summary,hourly,_=calculate(fixture(),rooms,loads,params())
        assert np.isfinite(hourly['Total demand kW']).all(),name
        assert (hourly['Total demand kW']>=0).all(),name
        if name=='High mast lights':
            assert (summary['N+1']=='Not conditioned').all()
            assert np.allclose(hourly['AC kW'],0.)
