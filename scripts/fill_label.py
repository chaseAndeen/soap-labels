#!/usr/bin/env python3
"""Fill the shared label template with a specific recipe's name/ingredients/
subtitle plus a given weight/price, export to a 300dpi PNG, then flatten+
convert to CMYK so the printer isn't doing its own (heavier) on-the-fly
RGB->CMYK conversion."""

import csv
import subprocess
import sys
from pathlib import Path
from typing import Optional
from lxml import etree
from PIL import Image

NSMAP = {"svg": "http://www.w3.org/2000/svg"}
SVG_NS = "{http://www.w3.org/2000/svg}"
OZ_TO_GRAMS = 28.3495
EXPORT_DPI = 300
NBSP = "\u00A0"

TEMPLATE_PATH = Path("templates/label.svg")
RECIPES_PATH = Path("recipes.csv")
BUILD_DIR = Path("build/labels")


def format_oz(oz: float) -> str:
    return f"{oz:g}"

def weight_display(oz: float) -> str:
    grams = round(oz * OZ_TO_GRAMS)
    return f"{format_oz(oz)} oz / {grams} g"


def price_display(price: Optional[int]) -> str:
    if price is None:
        return ""
    return f"${price}"


def format_ingredients(raw: str) -> str:
    """Replace spaces *within* each comma-separated ingredient with a
    non-breaking space, so the flowed text box only wraps right after a
    comma, never in the middle of a multi-word ingredient name."""
    segments = [s.strip() for s in raw.split(",")]
    return ", ".join(s.replace(" ", NBSP) for s in segments)


def load_recipes() -> dict:
    recipes = {}
    with RECIPES_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            recipes[row["recipe"]] = {
                "display_name": row["display_name"],
                "ingredients": row["ingredients"],
                "subtitle": row.get("subtitle", "") or "",
            }
    return recipes


def set_tspan_text(tree, element_id: str, text: str) -> None:
    tspan = tree.xpath(f'//*[@id="{element_id}"]//svg:tspan', namespaces=NSMAP)[0]
    tspan.text = text


def set_ingredients(tree, ingredients_raw: str) -> None:
    ingredients_el = tree.xpath('//*[@id="ingredients-text"]', namespaces=NSMAP)[0]
    for child in list(ingredients_el):
        ingredients_el.remove(child)
    new_tspan = etree.SubElement(ingredients_el, f"{SVG_NS}tspan")
    new_tspan.text = format_ingredients(ingredients_raw)


def fill_svg(recipe: str, oz: int, price: Optional[int]) -> Path:
    recipes = load_recipes()
    if recipe not in recipes:
        raise KeyError(f"No recipe data for '{recipe}' — check recipes.csv")
    data = recipes[recipe]

    tree = etree.parse(str(TEMPLATE_PATH))

    set_tspan_text(tree, "weight-text", weight_display(oz))
    set_tspan_text(tree, "price-text", price_display(price))
    set_tspan_text(tree, "name-text", data["display_name"])
    set_tspan_text(tree, "subtitle-text", data["subtitle"])
    set_ingredients(tree, data["ingredients"])

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    out_svg = BUILD_DIR / f"{recipe}_{format_oz(oz)}oz.svg"
    tree.write(str(out_svg))
    return out_svg


def export_png(svg_path: Path) -> Path:
    png_path = svg_path.with_suffix(".png")
    subprocess.run(
        [
            "inkscape", str(svg_path),
            "--export-type=png",
            f"--export-dpi={EXPORT_DPI}",
            f"--export-filename={png_path}",
        ],
        check=True,
    )
    return png_path


def convert_to_cmyk(png_path: Path) -> Path:
    im = Image.open(png_path).convert("RGBA")
    background = Image.new("RGB", im.size, (255, 255, 255))
    background.paste(im, mask=im.split()[3])
    cmyk = background.convert("CMYK")

    cmyk_path = png_path.with_suffix(".tiff")
    cmyk.save(cmyk_path)
    return cmyk_path


def build_label(recipe: str, oz: int, price: Optional[int]) -> Path:
    svg_path = fill_svg(recipe, oz, price)
    png_path = export_png(svg_path)
    return convert_to_cmyk(png_path)


if __name__ == "__main__":
    recipe, oz, price = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    result = build_label(recipe, oz, price)
    print(f"Built: {result}")