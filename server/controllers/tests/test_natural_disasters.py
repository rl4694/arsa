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
        nd.LATITUDE: float,
        nd.LONGITUDE: float,
        nd.DESCRIPTION: str,
    }
)

class TestValidate:
    def test_valid(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '2000-01-01',
            nd.LATITUDE: 1.0,
            nd.LONGITUDE: 1.0,
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_valid_3_digit_year(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '500-01-01',
            nd.LATITUDE: 1.0,
            nd.LONGITUDE: 1.0,
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_valid_negative_year(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '-500-01-01',
            nd.LATITUDE: 1.0,
            nd.LONGITUDE: 1.0,
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_valid_1_digit_year(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '5-01-01',
            nd.LATITUDE: 1.0,
            nd.LONGITUDE: 1.0,
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_invalid_date(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: 'invalid-date',
                nd.LATITUDE: 1.0,
                nd.LONGITUDE: 1.0,
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_invalid_month(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-13-01',
                nd.LATITUDE: 1.0,
                nd.LONGITUDE: 1.0,
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_invalid_day(self):
        with pytest.raises(ValueError):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-02-30',
                nd.LATITUDE: 1.0,
                nd.LONGITUDE: 1.0,
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_valid_coordinates_boundaries(self):
        disasters.validate({
            nd.NAME: SAMPLE_NAME,
            nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
            nd.DATE: '2000-01-01',
            nd.LATITUDE: -180.0,
            nd.LONGITUDE: 180.0,
            nd.DESCRIPTION: SAMPLE_DESCRIPTION,
        })

    def test_invalid_latitude_out_of_range(self):
        with pytest.raises(ValueError, match='Latitude'):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-01-01',
                nd.LATITUDE: 181.0,
                nd.LONGITUDE: 0.0,
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })

    def test_invalid_longitude_out_of_range(self):
        with pytest.raises(ValueError, match='Longitude'):
            disasters.validate({
                nd.NAME: SAMPLE_NAME,
                nd.DISASTER_TYPE: SAMPLE_DISASTER_TYPE,
                nd.DATE: '2000-01-01',
                nd.LATITUDE: 0.0,
                nd.LONGITUDE: -181.0,
                nd.DESCRIPTION: SAMPLE_DESCRIPTION,
            })
