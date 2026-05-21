#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
from ruamel.yaml import YAML
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
import shutil
import sys

yaml = YAML()
yaml.preserve_quotes = True

ROOT = Path.cwd()

DATASET_ROOT = ROOT / "datasets"
TEMPLATE_DATASET = ROOT / "templates" / "template_dataset.yaml"


# ============================================================
# ODS PARSER
# ============================================================

def read_ods(file_path):

    doc = load(str(file_path))

    rows_data = []

    sheets = doc.spreadsheet.getElementsByType(Table)

    for sheet in sheets:

        for row in sheet.getElementsByType(TableRow):

            row_data = []

            cells = row.getElementsByType(TableCell)

            for cell in cells:

                text_content = ""

                paragraphs = cell.getElementsByType(P)

                if paragraphs:

                    text_content = "\n".join(
                        "".join(
                            node.data
                            for node in p.childNodes
                            if hasattr(node, "data")
                        )
                        for p in paragraphs
                    )

                repeat = cell.getAttribute("numbercolumnsrepeated")
                repeat = int(repeat) if repeat else 1

                for _ in range(repeat):
                    row_data.append(text_content.strip())

            if any(v != "" for v in row_data):
                rows_data.append(row_data)

    return rows_data


# ============================================================
# YAML
# ============================================================

def load_yaml(filepath):

    with open(filepath, "r") as f:
        return yaml.load(f)


def save_yaml(filepath, data):

    with open(filepath, "w") as f:
        yaml.dump(data, f)


# ============================================================
# DATASET CREATION
# ============================================================

def create_dataset(dataset_id):

    dataset_dir = DATASET_ROOT / dataset_id

    dataset_dir.mkdir(parents=True, exist_ok=True)

    info_yaml = dataset_dir / "README.yaml"

    if not info_yaml.exists():

        shutil.copy(TEMPLATE_DATASET, info_yaml)

        print(f"  -> created template {info_yaml}")

    return info_yaml


# ============================================================
# UPDATE DATASET
# ============================================================

def update_dataset(row_dict):

    status = row_dict.get("Status", "").strip().lower()

    # only process completed datasets
    if status != "completed":
        return

    dataset_id = row_dict.get("Dataset id", "").strip()

    if dataset_id == "":
        return

    print(f"\nProcessing {dataset_id}")

    # --------------------------------------------------------
    # Create dataset directory if missing
    # --------------------------------------------------------

    info_yaml = create_dataset(dataset_id)

    # --------------------------------------------------------
    # Load YAML
    # --------------------------------------------------------

    data = load_yaml(info_yaml)

    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------

    data["dataset_id"] = dataset_id
    
    data["dataset_collection_date"] = \
        row_dict.get("Date", "")
    
    data["description"] = \
        row_dict.get("Experiment Description", "")

    data["file_created_at"] = datetime.now().isoformat()

    data["dataset_log_directory"] = \
        row_dict.get("Log dir name", "")

    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

    data["environment"]["location"] = \
        row_dict.get("Location", "")

    data["environment"]["terrain"] = \
        row_dict.get("Terrain", "")

    slope = row_dict.get("Slope", "0")

    data["environment"]["slope_deg"] = slope

    # --------------------------------------------------------
    # MOTION
    # --------------------------------------------------------

    data["motion"]["velocity"] = \
        row_dict.get("Velocity", "")

    data["motion"]["trajectory"] = \
        row_dict.get("Trajectory", "")

    data["motion"]["trajectory_description"] = \
        row_dict.get("Experiment Description", "")

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    video = str(row_dict.get("Video?"))

    has_video = False

    if video.lower() not in ["", "no", "false", "0"]:
        has_video = True

    if has_video:
        data["sensors"]["video"]["id"] = dataset_id.replace("DATA", "VIDEO")
        data["sensors"]["video"]["reference_number"] = video
    else:
        data["sensors"]["video"]["id"] = "Not Available"
        data["sensors"]["video"]["reference_number"] = "Not Available"
    data["sensors"]["video"]["available"] = has_video

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_yaml(info_yaml, data)


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print("Usage:")
        print("  python3 sync_datasets.py experiments.ods")
        sys.exit(1)

    ods_file = Path(sys.argv[1])

    if not ods_file.exists():

        print(f"File not found: {ods_file}")
        sys.exit(1)

    rows = read_ods(ods_file)

    if len(rows) < 2:

        print("No spreadsheet data found.")
        sys.exit(1)

    header = rows[0]

    for row in rows[1:]:

        row_dict = dict(zip(header, row))

        update_dataset(row_dict)

    print("\nDone.")


if __name__ == "__main__":
    main()