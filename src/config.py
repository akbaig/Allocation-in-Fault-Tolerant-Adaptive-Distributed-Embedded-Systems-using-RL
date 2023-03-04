import argparse

parser = argparse.ArgumentParser()
arg_lists = []

def str2bool(v):
    return v.lower() in ("true", "1")

parameters_definition = {

    "min_item_size": { "value": 200, "type": int, "desc": "Minimum item size"},
    "max_item_size": { "value": 800, "type": int, "desc": "Maximum item size"},
    "min_num_items": { "value": 10, "type": int, "desc": "Minimum number of items"},
    "max_num_items": { "value": 10, "type": int, "desc": "Maximum number of items"},

    "min_bin_size": { "value": 1000, "type": int, "desc": "Minimum bin size"},
    "max_bin_size": { "value": 2000, "type": int, "desc": "Maximum bin size"},
    "total_bins":{ "value": 4, "type": int, "desc": "Total number of bins"},

    "number_of_copies": {"value": 2, "type": int, "desc": "Number of critical item copies"},
    "number_of_critical_items": {"value": 3, "type": int, "desc": "Number of critical item"},

    # TRAINING PARAMETERS #
    "seed": { "value": 3, "type": int, "desc": "Random seed"},
    "n_episodes": { "value": 1000, "type": int, "desc": "Number of episodes"},
    "batch_size": { "value": 1, "type": int, "desc": "Batch size"},
    "lr": { "value": 1.0e-3, "type": float, "desc": "Initial learning rate"},
    "alpha": {"value": 0.3, "type": float, "desc": "Alpha Value to compute reward"},


    # RUN OPTIONS #
    "device": { "value": "cpu", "type": str, "desc": "Device to use (if no GPU available, value should be 'cpu')"},
    "inference": {"value": False, "type": str2bool, "desc": "Do not train the model"},


    # REWARD SHAPING

}

def get_config():
    parser = argparse.ArgumentParser()
    for arg, arg_def in parameters_definition.items():
        parser.add_argument(f"--{arg}", type=arg_def["type"], default=arg_def["value"], help=arg_def["desc"])
    config, unparsed = parser.parse_known_args()
    return config, unparsed
