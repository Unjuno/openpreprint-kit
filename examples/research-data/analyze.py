"""Synthetic demonstration only; the kit never runs this from a provenance claim."""
import csv
from pathlib import Path
from statistics import mean

with (Path(__file__).parent / 'measurements.csv').open(newline='', encoding='utf-8') as stream:
    values = [float(row['value']) for row in csv.DictReader(stream)]
print(mean(values))
