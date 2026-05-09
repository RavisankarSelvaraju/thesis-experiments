#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
from ruamel.yaml import YAML
import shutil
import sys

yaml = YAML()
yaml.preserve_quotes = True

ROOT = Path.cwd()

DATASET_ROOT = ROOT / "datasets"
EVALUATION_ROOT = ROOT / "evaluations"
TEMPLATE_DATASET = ROOT / "templates" / "template_dataset.yaml"
TEMPLATE_EVALUATION = ROOT / "templates" / "template_evaluation.yaml"


# ============================================================
# Utility
# ============================================================

def check_working_directory():
    if "experiments" not in str(ROOT):
        print("Please run this script from the experiments/ directory.")
        sys.exit(1)


def ask(prompt, required=True, default=None):
    while True:

        if default:
            value = input(f"{prompt} [{default}]: ").strip()

            if value == "":
                value = default
        else:
            value = input(f"{prompt}: ").strip()

        if value or not required:
            return value

        print("This field is required.")


def load_yaml(filepath):
    with open(filepath, "r") as f:
        return yaml.load(f)


def save_yaml(filepath, data):
    with open(filepath, "w") as f:
        yaml.dump(data, f)


# ============================================================
# Dataset
# ============================================================
def create_dataset():

    print("\n==============================")
    print(" Create Dataset")
    print("==============================\n")

    print("Available datasets:\n")

    if DATASET_ROOT.exists():

        dataset_dirs = sorted(
            [d for d in DATASET_ROOT.iterdir() if d.is_dir()]
        )

        if len(dataset_dirs) == 0:
            print("  (none)")
        else:
            for d in dataset_dirs:
                print(f"  - {d.name}")

    else:
        print("  datasets/ directory does not exist yet")

    print()

    dataset_id = ask("Dataset name")
    description = ask("Brief description")

    dataset_dir = DATASET_ROOT / dataset_id

    if dataset_dir.exists():
        print(f"\nDataset '{dataset_id}' already exists.\n")
        sys.exit(1)

    print(f"\nCreating dataset: {dataset_id}")

    dataset_dir.mkdir(parents=True)

    info_yaml = dataset_dir / "info.yaml"

    shutil.copy(TEMPLATE_DATASET, info_yaml)

    print(f"Copied template YAML -> {info_yaml}")

    data = load_yaml(info_yaml)

    # Update YAML fields
    data["dataset_id"] = dataset_id
    data["description"] = description
    data["created_at"] = datetime.now().isoformat()

    save_yaml(info_yaml, data)

    print("\nDataset created successfully.")
    print(f"Location: {dataset_dir}")

# ============================================================
# Evaluation
# ============================================================

def create_evaluation():

    print("\n==============================")
    print(" Create Evaluation")
    print("==============================\n")

    evaluation_id = ask("Evaluation name")
    description = ask("Brief description")

    evaluation_dir = EVALUATION_ROOT / evaluation_id

    if evaluation_dir.exists():

        print(f"\nEvaluation '{evaluation_id}' already exists.\n")

        print("Available evaluations:\n")

        for d in sorted(EVALUATION_ROOT.iterdir()):
            if d.is_dir():
                print(f"  - {d.name}")

        sys.exit(1)

    print(f"\nCreating evaluation: {evaluation_id}")

    evaluation_dir.mkdir(parents=True)

    evaluation_variants = [
        "EVAL_01_baseline",
        "EVAL_02_contact",
        "EVAL_03_combined",
        "EVAL_04_contact_velocity",
    ]

    for eval_name in evaluation_variants:

        subdir = evaluation_dir / eval_name
        subdir.mkdir(parents=True)

        info_yaml = subdir / "info.yaml"

        shutil.copy(TEMPLATE_EVALUATION, info_yaml)

        data = load_yaml(info_yaml)

        data["evaluation_id"] = eval_name
        data["parent_evaluation"] = evaluation_id
        data["description"] = description
        data["created_at"] = datetime.now().isoformat()

        save_yaml(info_yaml, data)

        print(f"Created: {subdir}")

    print("\nEvaluation created successfully.")
    print(f"Location: {evaluation_dir}")


# ============================================================
# Main
# ============================================================

def main():

    check_working_directory()

    print("\n==============================")
    print(" Experiment Manager")
    print("==============================\n")

    print("1. Create Dataset")
    print("2. Create Evaluation")
    print()

    choice = ask("Select option")

    if choice == "1":
        create_dataset()

    elif choice == "2":
        create_evaluation()

    else:
        print("\nInvalid option.")
        sys.exit(1)


if __name__ == "__main__":
    main()
