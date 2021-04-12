import json
import logging
import sys
import yaml
from transformers import AutoConfig, AutoModel
from utils import REPO_FOLDER, ARCHITECTURE_FOLDER, build_config_from_yaml, check_download
from os.path import join


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    files = [f for f in sys.argv[1:] if f.startswith(REPO_FOLDER)]
    for file in files:
        has_error = check_download(file)
        if has_error:
            sys.exit(1)
