from collections import defaultdict
from glob import glob
import json
import os
from os.path import join, basename, dirname, relpath, splitext
import sys
import shutil
import yaml
from utils import *


def generate_adapter_repo(files, config_index, dist_folder="dist"):
    """Generates adapter repo and index files.
    """
    index = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(dict)))))
    # add all files to index
    for file in files:
        with open(file, 'r') as f:
            adapter_dict = yaml.load(f, yaml.FullLoader)
        # generate config id
        if adapter_dict['config']['using'] not in config_index:
            raise ValueError(
                    "Unknown adapter config identifier '{}'.".format(adapter_dict['config'])
                )
        a_id = get_adapter_config_hash(build_config_from_yaml(adapter_dict['config']))
        path_split = file.split(os.sep)
        a_model_name = adapter_dict['model_name']
        a_type = adapter_dict['type']
        a_task = adapter_dict['task']
        a_name = adapter_dict['subtask']
        org_name = path_split[-2]
        if a_type not in AVAILABLE_TYPES:
            raise ValueError("Invalid type '{}'.".format(a_type))
        ### Create generated json file
        gen_file = join(dist_folder, REPO_FOLDER, org_name, splitext(basename(file))[0]+".json")
        os.makedirs(dirname(gen_file), exist_ok=True)
        # create dict entry with download files
        if not adapter_dict['default_version'] in [file['version'] for file in adapter_dict['files']]:
            raise ValueError("Specified default_version is not in files.")
        files = {}
        for file in adapter_dict['files']:
            version = file.pop('version')
            file.pop('description', None)
            files[version] = file
        gen_dict = {
            'config_id': a_id,
            'default_version': adapter_dict['default_version'],
            'files': files
        }
        with open(gen_file, 'w') as f:
            json.dump(gen_dict, f, indent=2, sort_keys=True)
        ### Create index entry
        id_dict = index[a_type][a_model_name][a_task][a_name][a_id]
        if "versions" not in id_dict:
            id_dict["versions"] = {}
        if org_name in id_dict["versions"]:
            raise ValueError(
                    "Duplicate adapter entry '{}/{}' for user/ organization {}. Please create one adapter entry per name and config.".format(
                        a_task, a_name, org_name
                    )
                )
        id_dict["versions"][org_name] = relpath(gen_file, dist_folder)
        # TODO change default version to something more useful
        # id_dict["default"] = org_name
    # write index files to disc
    for a_type, adapters in index.items():
        for a_model_name, adapters in adapters.items():
            index_file = join(
                dist_folder,
                INDEX_FOLDER.format(a_type),
                "{}.json".format(a_model_name)
            )
            os.makedirs(dirname(index_file), exist_ok=True)
            with open(index_file, 'x') as f:
                json.dump(adapters, f, indent=4, sort_keys=True)
    return index


def generate_architecture_index(files, dist_folder="dist"):
    index = {}
    valid_ids = []
    for file in files:
        with open(file, 'r') as f:
            config = yaml.load(f, yaml.FullLoader)
        if config['name'] in index:
            raise ValueError("Duplicate adapter architecture name '{}'".format(config['name']))
        config_id = get_adapter_config_hash(config['config'])
        if config_id in valid_ids:
            raise ValueError("Duplicate adapter architecture with id '{}'".format(config_id))
        index[config['name']] = config['config']
        valid_ids.append(config_id)
    with open(join(dist_folder, "{}.json".format(ARCHITECTURE_FOLDER)), 'x') as f:
        json.dump(index, f, indent=4, sort_keys=True)
    return index


if __name__ == "__main__":
    dist_folder = sys.argv[1] if len(sys.argv) > 1 else "dist"
    # clean up
    if os.path.isdir(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    # generate config files
    config_glob = join(ARCHITECTURE_FOLDER, "*")
    files = glob(config_glob)
    config_index = generate_architecture_index(files, dist_folder=dist_folder)
    # generate adapter files
    repo_glob = join(REPO_FOLDER, "**", "*")
    files = glob(repo_glob)
    generate_adapter_repo(files, config_index, dist_folder=dist_folder)
