import hashlib
import json
import os
from typing import Mapping

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from transformers import AutoConfig, AutoModel


dir_path = os.path.dirname(os.path.realpath(__file__))

AVAILABLE_TYPES = ["text_task", "text_lang"]

# user contrib
ARCHITECTURE_FOLDER = "architectures"
REPO_FOLDER = "adapters"
TASK_FOLDER = "tasks"
SUBTASK_FOLDER = "subtasks"

# generated/ pre-defined
SCHEMA_FOLDER = os.path.join(dir_path, "schemas")
TEMPLATE_FOLDER = "TEMPLATES"


def _minimize_dict(d):
    if isinstance(d, Mapping):
        return {k: _minimize_dict(v) for (k, v) in d.items() if v}
    else:
        return d


def get_adapter_config_hash(config, length=16):
    """Calculates the hash of a given adapter configuration which is used to identify this configuration.

    Returns:
        str: The resulting hash of the given config dict.
    """
    minimized_config = _minimize_dict(config)
    dict_str = json.dumps(minimized_config, sort_keys=True)
    h = hashlib.sha1()
    h.update(dict_str.encode(encoding="utf-8"))
    return h.hexdigest()[:length]


def build_config_from_yaml(config_yaml, version=2):
    adapter_config_file = os.path.join(ARCHITECTURE_FOLDER, config_yaml["using"] + ".yaml")
    with open(adapter_config_file, "r") as f:
        data = yaml.load(f, yaml.FullLoader)
    version_config_key = f"config_v{version}"
    adapter_config = data.get(version_config_key if version_config_key in data else "config")
    for k, v in config_yaml.items():
        if k != "using":
            adapter_config[k] = v
    return adapter_config


def _violation(s):
    print("VIOLATION:", s)


def get_checksum(file):
    for algo in ["sha1", "sha256"]:
        if algo in file:
            return algo, file[algo]


def check_against_schema(file, schema):
    print("-" * 5, f"Checking format of {file}", "-" * 5)
    # 1. load to dict
    with open(file, "r") as f:
        try:
            file_dict = yaml.load(f, Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            _violation("[{}]: {}".format(e.__class__.__name__, e))
            print(f"FAILED: {file}!\n")
            return True
    # 2. validate against schema
    try:
        validate(file_dict, schema)
    except ValidationError as e:
        _violation("[{}]: {}".format(e.__class__.__name__, e.message))
        print(f"FAILED: {file}!\n")
        return True
    print(f"PASSED: {file}.\n")
    return False


def check_download(adapter_file):
    """Checks if the download links of the given adapter description file are valid."""
    print("-" * 5, f"Checking download of {adapter_file}", "-" * 5)
    with open(adapter_file, "r") as f:
        adapter_dict = yaml.load(f, yaml.FullLoader)
    # load adapter_config from yaml file
    adapter_config = build_config_from_yaml(adapter_dict["config"])
    config = AutoConfig.from_pretrained(adapter_dict["model_name"])
    if not config.model_type == adapter_dict["model_type"]:
        _violation(
            f"Specified model_type '{adapter_dict['model_type']}' does not match loaded model_type '{config.model_type}'."
        )
        print(f"FAILED: {adapter_file}!\n")
        return True
    model = AutoModel.from_config(config)
    for file in adapter_dict["files"]:
        checksum_algo, checksum = get_checksum(file)
        try:
            model.load_adapter(
                file["url"],
                adapter_dict["type"],
                config=adapter_config,
                load_as=file["version"],
                checksum_algo=checksum_algo,
                checksum=checksum,
            )
        except Exception as e:
            _violation("[{}]: {}".format(e.__class__.__name__, e))
            print(f"FAILED: {adapter_file}!\n")
            return True
    print(f"PASSED: {adapter_file}.\n")
    return False
