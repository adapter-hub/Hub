import json
import os
import shutil
import sys
from collections import defaultdict
from glob import glob
from os.path import basename, dirname, join, relpath, splitext

import yaml

from utils import *


def generate_adapter_repo(files, config_index, dist_folder="dist", hub_version=2):
    """Generates adapter repo and index files."""
    index = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
    full_list = []
    # add all files to index
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            adapter_dict = yaml.load(f, yaml.FullLoader)
        # generate config id
        if adapter_dict["config"]["using"] not in config_index:
            raise ValueError("Unknown adapter config identifier '{}'.".format(adapter_dict["config"]))
        full_config = build_config_from_yaml(adapter_dict["config"], version=hub_version)
        a_id = get_adapter_config_hash(full_config)
        path_split = file.split(os.sep)
        a_model_name = adapter_dict["model_name"]
        a_type = adapter_dict["type"]
        a_task = adapter_dict["task"]
        a_name = adapter_dict["subtask"]
        org_name = path_split[-2]
        if a_type not in AVAILABLE_TYPES:
            raise ValueError("Invalid type '{}'.".format(a_type))

        ### Create generated json file
        file_base = splitext(basename(file))[0]
        gen_file = join(dist_folder, REPO_FOLDER, org_name, file_base + ".json")
        os.makedirs(dirname(gen_file), exist_ok=True)
        # create dict entry with download files
        if not adapter_dict["default_version"] in [file["version"] for file in adapter_dict["files"]]:
            raise ValueError("Specified default_version is not in files.")
        files = {}
        for file in adapter_dict["files"]:
            version = file.pop("version")
            file.pop("description", None)
            files[version] = file
        gen_dict = {"config_id": a_id, "default_version": adapter_dict["default_version"], "files": files}

        ### Create & append adapter info
        adapter_info = {
            "source": "ah",
            "adapter_id": f"@{org_name}/{file_base}",
            "model_name": a_model_name,
            "task": a_task,
            "subtask": a_name,
            "username": org_name,
            "adapter_config": full_config,
            "sha1_checksum": files[adapter_dict["default_version"]].get("sha1"),
        }
        if hub_version >= 2:
            gen_dict["info"] = adapter_info
        full_list.append(adapter_info)

        with open(gen_file, "w") as f:
            json.dump(gen_dict, f, sort_keys=True)
        
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
        # set task default if not set
        # TODO set default based on score
        subtask_dict = index[a_type][a_model_name][a_task][a_name]
        if "default" not in subtask_dict or adapter_dict["config"]["using"] == "pfeiffer":
            subtask_dict["default"] = relpath(gen_file, dist_folder)
        # TODO change default version to something more useful
        # id_dict["default"] = org_name

    # write index files to disc
    for a_type, adapters in index.items():
        for a_model_name, adapters in adapters.items():
            index_file = join(
                dist_folder, "index_{}".format(a_type) if hub_version <= 1 else "index", "{}.json".format(a_model_name)
            )
            # For v2, the index might already exist as text_task & text_lang are put into the same file but handled separately.
            if os.path.exists(index_file):
                with open(index_file, "r") as f:
                    index = json.load(f)
                index = {**index, **adapters}
                with open(index_file, "w") as f:
                    json.dump(index, f, indent=4, sort_keys=True)
            else:
                os.makedirs(dirname(index_file), exist_ok=True)
                with open(index_file, "x") as f:
                    json.dump(adapters, f, indent=4, sort_keys=True)
    # write full list
    if hub_version >= 2:
        with open(join(dist_folder, "all.json"), "w") as f:
            json.dump(full_list, f)
    return index


def generate_architecture_index(files, dist_folder="dist", hub_version=2):
    index = {}
    valid_ids = []
    for file in files:
        with open(file, "r") as f:
            config = yaml.load(f, yaml.FullLoader)
        if config["name"] in index:
            raise ValueError("Duplicate adapter architecture name '{}'".format(config["name"]))
        version_config_key = f"config_v{hub_version}"
        adapter_config = config.get(version_config_key if version_config_key in config else "config")
        config_id = get_adapter_config_hash(adapter_config)
        if config_id in valid_ids:
            raise ValueError("Duplicate adapter architecture with id '{}'".format(config_id))
        index[config["name"]] = adapter_config
        valid_ids.append(config_id)
    with open(join(dist_folder, "{}.json".format(ARCHITECTURE_FOLDER)), "x") as f:
        json.dump(index, f, indent=4, sort_keys=True)
    return index


if __name__ == "__main__":
    version_map = {
        1: "dist",
        2: "dist/v2",
    }
    for hub_version, dist_folder in version_map.items():
        print(f"Generating index for version {hub_version} ...")
        # clean up
        if os.path.isdir(dist_folder):
            shutil.rmtree(dist_folder)
        os.makedirs(dist_folder)
        # generate config files
        config_glob = join(ARCHITECTURE_FOLDER, "*")
        files = glob(config_glob)
        config_index = generate_architecture_index(files, dist_folder=dist_folder, hub_version=hub_version)
        # generate adapter files
        repo_glob = join(REPO_FOLDER, "**", "*")
        files = glob(repo_glob)
        generate_adapter_repo(files, config_index, dist_folder=dist_folder, hub_version=hub_version)
