from facility_design import TEMPLATES, template_data, transformer_design
from site_energy import validate_rooms

def test_templates():
    for name in TEMPLATES:
        rooms, loads = template_data(name)
        validate_rooms(rooms, loads)

def test_transformer():
    result = transformer_design(100, 10)
    assert result['standard_kva'] == 200
