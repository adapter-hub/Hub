import hashlib
import json
import os
from typing import Mapping
import yaml


dir_path = os.path.dirname(os.path.realpath(__file__))

AVAILABLE_TYPES = ['text_task', 'text_lang']

# user contrib
ARCHITECTURE_FOLDER = "architectures"
REPO_FOLDER = "adapters"
TASK_FOLDER = "tasks"
SUBTASK_FOLDER = "subtasks"

# generated/ pre-defined
INDEX_FOLDER = "index_{}"
SCHEMA_FOLDER = os.path.join(dir_path, "schemas")
TEMPLATE_FOLDER="TEMPLATES"


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


def build_config_from_yaml(config_yaml):
    adapter_config_file = os.path.join(ARCHITECTURE_FOLDER, config_yaml['using']+".yaml")
    with open(adapter_config_file, 'r') as f:
        adapter_config = yaml.load(f, yaml.FullLoader)['config']
    for k,v in config_yaml.items():
        if k != 'using':
            adapter_config[k] = v
    return adapter_config
