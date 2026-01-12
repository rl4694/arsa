import pytest
import server.controllers.natural_disasters as nd

SAMPLE_NAME = 'test'
SAMPLE_DISASTER_TYPE = nd.EARTHQUAKE
SAMPLE_DESCRIPTION = 'test'

disasters = nd.NaturalDisasters(
    'test',
    nd.KEY,
    {
        nd.NAME: str,
        nd.DISASTER_TYPE: str,
        nd.DATE: str,
        nd.LOCATION: str,
        nd.DESCRIPTION: str,
    }
)

class TestValidate:
    def test_valid(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '2000-01-01',
            nd.LOCATION: '1, 1',
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_invalid_date(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: 'invalid-date',
                nd.LOCATION: '1.0, 1.0',
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_invalid_location(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-01-01',
                nd.LOCATION: 'invalid',
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_invalid_coordinates(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-01-01',
                nd.LOCATION: 'invalid, location',
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })
