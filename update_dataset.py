#!/usr/bin/env python3
"""
update_dataset.py

Generate dataset README YAML entries from CSV rows and optionally create a single
overview README.md file containing all generated dataset sections.

Usage:
  python3 update_dataset.py experiment_details.csv [search_root] [--dataset-info [output_dir]] [--test [LOG_DIR_NAME | DATASET_ID]]

Arguments:
  experiment_details.csv   CSV file containing dataset metadata.
  search_root             Optional root folder to search for existing log directories.
                          Defaults to the current working directory.

Options:
  --dataset-info [output_dir]
      When present, the script collects the YAML content for each processed row and
      writes a single README.md file in the specified output folder.
      If no directory is provided, it defaults to ./dataset_info.

  --test
      Process only the first completed row from the CSV.

  --test=VALUE
      Process only the row whose Dataset id or Log dir name matches VALUE.

CSV runtime support:
  If the CSV contains columns named Runtime, runtime, Runtime [s], or runtime_s,
  their value will be written into the generated YAML as motion.runtime_s.

Behavior:
  - If an existing log directory is found under search_root, the script updates its README.yaml.
  - If --dataset-info is used, the script also generates a single README.md file with
    one YAML section per processed log dir.
  - The file_created_at field is omitted from the README.md overview sections.

  Example:
  python3 update_dataset.py experiment_details.csv /202605_contact_velocity_odometry/ --dataset-info /202605_contact_velocity_odometry/
"""

from pathlib import Path
from datetime import datetime
from ruamel.yaml import YAML
import csv
import shutil
import sys


yaml = YAML()
yaml.preserve_quotes = True

ROOT = Path.cwd()
TEMPLATE_DATASET = ROOT / "template_dataset.yaml"


# ============================================================
# CSV PARSER
# ============================================================

def load_csv(file_path):
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []

        for row in reader:
            stripped_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
            if any((value or "").strip() != "" for value in stripped_row.values()):
                rows.append(stripped_row)

    return rows


# ============================================================
# YAML
# ============================================================

def load_yaml(filepath):

    with open(filepath, "r") as f:
        return yaml.load(f)


def save_yaml(filepath, data):

    with open(filepath, "w") as f:
        yaml.dump(data, f)


def save_yaml_text(data):

    from io import StringIO

    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def yaml_markdown_section(header, data):
    section_data = dict(data)
    section_data.pop("file_created_at", None)
    yaml_content = save_yaml_text(section_data).strip()
    return f"## {header}\n\n{yaml_content}\n"


# ============================================================
# DATASET CREATION
# ============================================================

def prepare_readme_path(log_dir_name, search_root):

    matches = [p for p in search_root.rglob(log_dir_name) if p.is_dir()]

    if not matches:
        return None

    if len(matches) > 1:
        print(f"  -> multiple directories found for '{log_dir_name}', using first match: {matches[0]}")

    dataset_dir = matches[0]
    info_yaml = dataset_dir / "README.yaml"

    if not info_yaml.exists():
        shutil.copy(TEMPLATE_DATASET, info_yaml)

    return info_yaml


# ============================================================
# UPDATE DATASET
# ============================================================

def update_dataset(row_dict, dataset_root, dataset_info_dir=None):

    status = row_dict.get("Status", "").strip().lower()

    # only process completed datasets
    if status != "completed":
        return False, False, None

    dataset_id = row_dict.get("Dataset id", "").strip()
    log_dir_name = row_dict.get("Log dir name", "").strip()

    if dataset_id == "" or log_dir_name == "":
        return False, False, None

    print(f"\nProcessing {dataset_id} ({log_dir_name})")

    # --------------------------------------------------------
    # Prepare README path in existing dataset log directory
    # --------------------------------------------------------

    info_yaml = prepare_readme_path(log_dir_name, dataset_root)
    missing_dir = info_yaml is None
    if missing_dir:
        print(f"  -> target dataset directory not found: {log_dir_name}")

    # --------------------------------------------------------
    # Load or create YAML data
    # --------------------------------------------------------

    if info_yaml is not None:
        data = load_yaml(info_yaml)
    else:
        data = load_yaml(TEMPLATE_DATASET)

    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------
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

    runtime_value = row_dict.get("Runtime", "") or row_dict.get("runtime", "") or row_dict.get("Runtime [s]", "") or row_dict.get("runtime_s", "")
    runtime_value = runtime_value.strip() if isinstance(runtime_value, str) else runtime_value
    if runtime_value != "":
        try:
            data["motion"]["runtime_s"] = float(runtime_value)
        except (ValueError, TypeError):
            data["motion"]["runtime_s"] = runtime_value

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    video = str(row_dict.get("Video", row_dict.get("Video?", "")))

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

    if info_yaml is not None:
        save_yaml(info_yaml, data)

    section = None
    if dataset_info_dir is not None:
        section = yaml_markdown_section(log_dir_name, data)

    processed = not missing_dir or dataset_info_dir is not None
    return processed, missing_dir, section


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print("Usage:")
        print("  python3 update_dataset.py experiments.csv [search_root] [--dataset-info [output_dir]] [--test [LOG_DIR_NAME | DATASET_ID]]")
        print("  (generated files will be YAML, e.g. dataset_info/DATA_01_02.yaml)")
        print("  --test: process only one row. Optionally supply a log dir name or dataset id.")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    search_root = ROOT
    dataset_info_dir = None
    test_filter = None
    test_first = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--dataset-info":
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                dataset_info_dir = Path(args[i + 1])
                i += 1
            else:
                dataset_info_dir = ROOT / "dataset_info"
        elif arg.startswith("--dataset-info="):
            dataset_info_dir = Path(arg.split("=", 1)[1])
        elif arg == "--test":
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                test_filter = args[i + 1]
                i += 1
            else:
                test_first = True
        elif arg.startswith("--test="):
            test_filter = arg.split("=", 1)[1]
        else:
            search_root = Path(arg)
        i += 1

    if not csv_file.exists():

        print(f"File not found: {csv_file}")
        sys.exit(1)

    rows = load_csv(csv_file)

    if len(rows) == 0:

        print("No CSV data found.")
        sys.exit(1)

    total_dirs = 0
    missing_dirs = 0
    created_readmes = 0
    dataset_info_files = 0
    summary_sections = []

    if test_filter is not None or test_first:
        print("Test mode enabled: processing only one row.")

    for row_dict in rows:
        if test_filter is not None:
            dataset_id = row_dict.get("Dataset id", "").strip()
            log_dir_name = row_dict.get("Log dir name", "").strip()
            if dataset_id != test_filter and log_dir_name != test_filter:
                continue

        processed, missing, section = update_dataset(row_dict, search_root, dataset_info_dir)
        if processed or missing:
            total_dirs += 1
        if processed:
            created_readmes += 1
        if missing:
            missing_dirs += 1
        if section is not None:
            summary_sections.append(section)
            dataset_info_files += 1

        if test_filter is not None or test_first:
            break

    if dataset_info_dir is not None:
        dataset_info_dir.mkdir(parents=True, exist_ok=True)
        output_file = dataset_info_dir / "README.md"
        output_file.write_text("\n".join(summary_sections).rstrip() + "\n", encoding="utf-8")

    print("\nDone.")
    print(f"Processed {total_dirs} completed log dirs.")
    print(f"Missing existing directories: {missing_dirs} of {total_dirs}")
    print(f"README files created/updated: {created_readmes}")
    if dataset_info_dir is not None:
        print(f"Generated dataset summary markdown in: {output_file}")
        print(f"Dataset sections added: {dataset_info_files}")

    
if __name__ == "__main__":
    main()