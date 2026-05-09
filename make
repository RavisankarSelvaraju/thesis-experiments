#! /bin/bash 

echo "Running make script"

#check if the present working directory ends with experiments/
if [[ "$PWD" != *"experiments"* ]]; then
    echo "Please run this script from the experiments/ directory."
    exit 1
fi

print_params() {
    echo "Parameter 1: $1"
    echo "Parameter 2: $2"
}

rename_dataset_in_yaml() {
    local filepath="$1"
    local dataset_id="$2"

    python3 - <<EOF
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

filepath = "$filepath"
dataset_id = "$dataset_id"

with open(filepath, "r") as f:
    data = yaml.load(f)

# Update only the target field
data["dataset_id"] = dataset_id

with open(filepath, "w") as f:
    yaml.dump(data, f)
EOF
}

make_dataset() {
    
    if [ -d "$PWD/datasets/$2" ]; then
        echo "Dataset $2 already exists. Please choose a different name."
        echo
        echo "Following datasets are available:"
        ls $PWD/datasets/
        exit 1
    fi
    
    echo "Making dataset with name: $2"

    
    mkdir -p $PWD/datasets/$2
    echo "Dataset $2 directory created successfully."
    
    cp $PWD/templates/template_dataset.yaml $PWD/datasets/$2/info.yaml
    echo "Template dataset.yaml copied to $PWD/datasets/$2/info.yaml"
    
    rename_dataset_in_yaml "$PWD/datasets/$2/info.yaml" "$2"
    echo "Dataset info.yaml updated with dataset name: $2"
}

make_evaluation() {
    
    if [ -d "$PWD/evaluations/$2" ]; then
        echo "Evaluation $2 already exists. Please choose a different name."
        echo "Following evaluations are available:"
        ls $PWD/evaluations/
        exit 1
    fi
    
    echo "Making evaluation with name: $2"

    mkdir -p $PWD/evaluations/$2
    echo "Evaluation $2 directory created successfully."
    
    mkdir -p $PWD/evaluations/$2/EVAL_01_baseline/
    cp $PWD/templates/template_evaluation.yaml $PWD/evaluations/$2/EVAL_01_baseline/info.yaml
    echo "Template evaluation.yaml copied to $PWD/evaluations/$2/EVAL_01_baseline/info.yaml"
    
    mkdir -p $PWD/evaluations/$2/EVAL_02_contact/
    cp $PWD/templates/template_evaluation.yaml $PWD/evaluations/$2/EVAL_02_contact/info.yaml
    echo "Template evaluation.yaml copied to $PWD/evaluations/$2/EVAL_02_contact/info.yaml"

    mkdir -p $PWD/evaluations/$2/EVAL_03_combined/
    cp $PWD/templates/template_evaluation.yaml $PWD/evaluations/$2/EVAL_03_combined/info.yaml
    echo "Template evaluation.yaml copied to $PWD/evaluations/$2/EVAL_03_combined/info.yaml"

    mkdir -p $PWD/evaluations/$2/EVAL_04_contact_velocity/
    cp $PWD/templates/template_evaluation.yaml $PWD/evaluations/$2/EVAL_04_contact_velocity/info.yaml
    echo "Template evaluation.yaml copied to $PWD/evaluations/$2/EVAL_04_contact_velocity/info.yaml"

    echo "Evaluation subdirectories created successfully."    
}

# we need to get two parameters, the first one is "dataset" or "evaluation", second one is the name of the dataset 
VAR1=$1
VAR2=$2

# check if both parameters are provided
if [ -z "$VAR1" ] || [ -z "$VAR2" ]; then
    echo "Please provide both parameters. Usage: ./make.sh [dataset|evaluation] [dataset name]"
    exit 1
fi

print_params $VAR1 $VAR2

if [ "$VAR1" == "dataset" ]; then
    make_dataset $VAR1 $VAR2
elif [ "$VAR1" == "evaluation" ]; then
    make_evaluation $VAR1 $VAR2
else
    echo "Invalid parameter. Please use 'dataset' or 'evaluation' followed by the name of the dataset."
    exit 1
fi

