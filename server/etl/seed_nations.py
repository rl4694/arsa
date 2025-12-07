#!/usr/bin/env python3

import sys
import csv
import server.controllers.nations as nt

NATIONS_FILE = 'server/etl/nations.csv'

def extract() -> list:
    """Extract nation data from its CSV file"""
    extracted = []
    try:
        with open(NATIONS_FILE) as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                extracted.append(row)
    except Exception as e:
        print(f'Problem reading csv file: {str(e)}')
        exit(1)
    return extracted


def transform(raw: list) -> list:
    """Transform nation data into format CRUD API can understand"""
    transformed = []
    for nation in raw:
        transformed.append({
            nt.CODE: nation[0],
            nt.NAME: nation[1],
        })
    return transformed


def load(transformed: list):
    """Load nation data into database"""
    for nation in transformed:
        nt.nations.create(nation)


def seed_nations():
    """Main seed function to be exported"""
    raw = extract()
    transformed = transform(raw)
    load(transformed)


if __name__ == '__main__':
    seed_nations()