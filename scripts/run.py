#!/usr/bin/env python3
"""Read a batch manifest, build any label PDFs it needs, and expand quantities
into a flat print-order list."""

import csv
from pathlib import Path

import fill_label

MANIFEST_PATH = Path("manifest.csv")
PRICING_PATH = Path("pricing.csv")


def load_pricing():
    pricing = {}
    with PRICING_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            price_str = row["price"].strip()
            price = int(price_str) if price_str else None
            pricing[(row["recipe"], int(row["oz"]))] = price
    return pricing


def load_manifest():
    rows = []
    with MANIFEST_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append((row["recipe"], int(row["oz"]), int(row["qty"])))
    return rows


def build_flat_label_list():
    pricing = load_pricing()
    manifest = load_manifest()

    flat_list = []
    for recipe, oz, qty in manifest:
        key = (recipe, oz)
        if key not in pricing:
            raise KeyError(f"No price found for {recipe} at {oz}oz — check pricing.csv")
        price = pricing[key]

        pdf_path = fill_label.build_label(recipe, oz, price)
        flat_list.extend([pdf_path] * qty)

    return flat_list


if __name__ == "__main__":
    labels = build_flat_label_list()
    print(f"{len(labels)} labels to print:")
    for path in labels:
        print(f"  {path}")