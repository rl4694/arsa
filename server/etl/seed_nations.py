"""
ETL script for seeding nation data
"""

import sys
import server.etl.common as common
import server.controllers.nations as nt


def transform(raw: list) -> list:
    """Transform nation data into format CRUD API can understand"""
    transformed = []
    for nation in raw:
        transformed.append({
            nt.CODE: nation['code'],
            nt.NAME: nation['name'],
        })
    return transformed


def seed_nations(filename: str):
    """Main seed function to be exported"""
    raw = common.extract_csv(filename, delimiter='\t')
    transformed = transform(raw)
    common.load(nt.nations, transformed)


if __name__ == '__main__':
    seed_nations(common.NATIONS_FILE)
