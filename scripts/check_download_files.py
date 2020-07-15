import json
import logging
import sys
import yaml
from transformers import AutoConfig, AutoModel
from utils import REPO_FOLDER, ARCHITECTURE_FOLDER, build_config_from_yaml
from os.path import join


def _violation(s):
    print("VIOLATION:", s)


def get_checksum(file):
    for algo in ['sha1', 'sha256']:
        if algo in file:
            return algo, file[algo]


def check_download(adapter_file):
    """Checks if the download links of the given adapter description file are valid.
    """
    print("-"*5, f"Checking download of {adapter_file}", "-"*5)
    with open(adapter_file, 'r') as f:
        adapter_dict = yaml.load(f, yaml.FullLoader)
    # load adapter_config from yaml file
    adapter_config = build_config_from_yaml(adapter_dict['config'])
    config = AutoConfig.from_pretrained(adapter_dict['model_name'])
    if not config.model_type == adapter_dict['model_type']:
        _violation(
            f"Specified model_type '{adapter_dict['model_type']}' does not match loaded model_type '{config.model_type}'."
        )
        print(f"FAILED: {adapter_file}!\n")
        return True
    model = AutoModel.from_config(config)
    for file in adapter_dict['files']:
        checksum_algo, checksum = get_checksum(file)
        try:
            model.load_adapter(
                file['url'],
                adapter_dict['type'],
                config=adapter_config,
                load_as=file['version'],
                checksum_algo=checksum_algo,
                checksum=checksum
            )
        except Exception as e:
            _violation("[{}]: {}".format(e.__class__.__name__, e))
            print(f"FAILED: {adapter_file}!\n")
            return True
    print(f"PASSED: {adapter_file}.\n")
    return False


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    files = [f for f in sys.argv[1:] if f.startswith(REPO_FOLDER)]
    for file in files:
        has_error = check_download(file)
        if has_error:
            sys.exit(1)
