#!/usr/bin/env python3
"""Composite a flat list of label PNGs into print-ready sheets: fixed 10-slot
grid, one-inch labels, centered top/bottom, unused slots left blank, with
edge marker cut lines at every slot boundary."""

import argparse
import subprocess
from pathlib import Path
from reportlab.pdfgen import canvas

SLOTS_PER_SHEET = 10
SLOT_HEIGHT = 72         # 1 inch, in points
PAGE_WIDTH = 612         # 8.5in Letter width, in points
PAGE_HEIGHT = 792        # 11in Letter height, in points
MARGIN_TOP = (PAGE_HEIGHT - SLOTS_PER_SHEET * SLOT_HEIGHT) / 2  # 36pt = 0.5in

CUT_LINE_GRAY_K = 0.5  # 50% black, defined in CMYK directly
CUT_LINE_WIDTH = 0.5
TICK_LENGTH = 18  

BUILD_SHEETS_DIR = Path("build/sheets")


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def build_sheet(label_pngs, out_path):
    c = canvas.Canvas(str(out_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for i, png_path in enumerate(label_pngs):
        if png_path is None:
            continue
        y = PAGE_HEIGHT - MARGIN_TOP - (i + 1) * SLOT_HEIGHT
        c.drawImage(str(png_path), x=0, y=y, width=PAGE_WIDTH, height=SLOT_HEIGHT)

    c.setStrokeColorCMYK(0, 0, 0, CUT_LINE_GRAY_K)
    c.setLineWidth(CUT_LINE_WIDTH)
    for i in range(SLOTS_PER_SHEET + 1):
        y = PAGE_HEIGHT - MARGIN_TOP - i * SLOT_HEIGHT
        c.line(0, y, TICK_LENGTH, y)                           # left edge tick
        c.line(PAGE_WIDTH - TICK_LENGTH, y, PAGE_WIDTH, y)     # right edge tick

    c.showPage()
    c.save()


def build_sheets(flat_label_list):
    BUILD_SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    sheet_paths = []
    for i, group in enumerate(chunk(flat_label_list, SLOTS_PER_SHEET), start=1):
        out_path = BUILD_SHEETS_DIR / f"sheet_{i:02d}.pdf"
        build_sheet(group, out_path)
        sheet_paths.append(out_path)
    return sheet_paths


def print_sheet(pdf_path, printer=None):
    cmd = ["lp"]
    if printer:
        cmd += ["-d", printer]
    cmd.append(str(pdf_path))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    import run  # scripts/run.py

    parser = argparse.ArgumentParser(description="Build label sheets from manifest.csv")
    parser.add_argument("--print", action="store_true", dest="do_print",
                         help="send generated sheets to the printer")
    parser.add_argument("--printer", default=None,
                         help="CUPS printer name (default: system default printer)")
    args = parser.parse_args()

    labels = run.build_flat_label_list()
    sheets = build_sheets(labels)
    print(f"Built {len(sheets)} sheet(s):")
    for path in sheets:
        print(f"  {path}")

    if args.do_print:
        for path in sheets:
            print(f"Printing {path} ...")
            print_sheet(path, printer=args.printer)