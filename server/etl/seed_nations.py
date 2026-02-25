import sys
import csv
import server.controllers.nations as nt


def extract(filename: str) -> list:
    """Extract nation data from its CSV file"""
    try:
        with open(filename) as f:
            extracted = csv.DictReader(f, delimiter='\t')
            return list(extracted)
    except Exception as e:
        print(f'Problem reading csv file: {str(e)}')
        exit(1)


def transform(raw: list) -> list:
    """Transform nation data into format CRUD API can understand"""
    transformed = []
    for nation in raw:
        transformed.append({
            nt.CODE: nation['code'],
            nt.NAME: nation['name'],
        })
    return transformed


def load(transformed: list):
    """Load nation data into database"""
    for nation in transformed:
        nt.nations.create(nation)


def seed_nations(filename: str):
    """Main seed function to be exported"""
    raw = extract(filename)
    transformed = transform(raw)
    load(transformed)


if __name__ == '__main__':
    seed_nations('server/etl/nations.csv')
