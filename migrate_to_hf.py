"""
This script can be used to migrate adapters from the original Hub repo to the HuggingFace Hub.

Usage:
python migrate_to_hf.py <folder> [--push] [--org_name <org_name>]
"""

from glob import glob
import os
import shutil

from adapters import AutoAdapterModel
from adapters.utils import download_cached
from huggingface_hub import HfApi
import yaml

from scripts.utils import REPO_FOLDER, SUBTASK_FOLDER, AVAILABLE_TYPES


OUTPUT_FOLDER = "hf_hub"
ERROR_FILE = "migration_errors.txt"
HUB_URL = "https://github.com/Adapter-Hub/Hub/blob/master/"
# Map from head types to HF labels used for widgets
MODEL_HEAD_MAP = {
    "classification": "text-classification",
    "multilabel_classification": "text-classification",
    "tagging": "token-classification",
    "multiple_choice": "multiple-choice",  # no widget ?
    "question_answering": "question-answering",
    "dependency_parsing": "dependency-parsing",  # no widget ?
    "masked_lm": "fill-mask",
    "causal_lm": "text-generation",
    "seq2seq_lm": "text2text-generation",
    "image_classification": "image-classification",
}

ADAPTER_CARD_TEMPLATE = """
---
tags:
{tags}
---

# Adapter `{adapter_repo_name}` for {model_name}

{description}

**This adapter was created for usage with the [Adapters](https://github.com/Adapter-Hub/adapters) library.**

## Usage

First, install `adapters`:

```
pip install -U adapters
```

Now, the adapter can be loaded and activated like this:

```python
from adapters import AutoAdapterModel

model = AutoAdapterModel.from_pretrained("{model_name}")
adapter_name = model.load_adapter("{org_name}/{adapter_repo_name}")
model.set_active_adapters(adapter_name)
```

## Architecture & Training

- Adapter architecture: {adapter_config}
- Prediction head: {head_type}
- Dataset: {dataset_name}

## Author Information

- Author name(s): {author_name}
- Author email: {author_email}
- Author links: {author_links}

{version_list}

## Citation

```bibtex
{citation}
```

*This adapter has been auto-imported from {original_file}*.

"""
DEFAULT_DESCRIPTION = "An adapter for the `{model_name}` model, trained on the {dataset_name} dataset{head_info}."


def load_subtasks() -> dict:
    subtasks = {}
    for dir in AVAILABLE_TYPES:
        for file in os.listdir(os.path.join(SUBTASK_FOLDER, dir)):
            with open(os.path.join(SUBTASK_FOLDER, dir, file), "r") as f:
                data = yaml.load(f, yaml.FullLoader)
            subtasks[data["task"] + "/" + data["subtask"]] = data

    return subtasks


def create_adapter_card(
    file_name,
    adapter_name,
    data,
    subtask_info,
    version=None,
    head_type=None,
    hf_org_name="AdapterHub",
    license="apache-2.0",
) -> str:
    # Key remains "adapter-transformers", see: https://github.com/huggingface/huggingface.js/pull/459
    all_tags = {"adapter-transformers"}
    # Dataset/ Task info
    dataset_url = None
    dataset_name = None
    datasets = set()
    if d_url := subtask_info.get("url", None):
        dataset_url = d_url
    if display_name := subtask_info.get("displayname", None):
        dataset_name = display_name
    if hf_id := subtask_info.get("hf_datasets_id", None):
        datasets.add(hf_id)
        if dataset_url is None:
            dataset_url = f"https://huggingface.co/datasets/{hf_id}"
            if dataset_name is None:
                dataset_name = hf_id
    if dataset_name is None:
        dataset_name = f"{data['task']}/{data['subtask']}"
    if dataset_url is None:
        dataset_url = f"https://adapterhub.ml/explore/{data['task']}/{data['subtask']}/"
    all_tags.add(f"adapterhub:{data['task']}/{data['subtask']}")

    all_tags.add(data["model_type"])
    if head_type in MODEL_HEAD_MAP:
        all_tags.add(MODEL_HEAD_MAP[head_type])
    tag_string = "\n".join([f"- {tag}" for tag in all_tags])
    if datasets:
        tag_string += "\ndatasets:\n"
        tag_string += "\n".join([f"- {tag}" for tag in datasets])
    # if language := subtask_info.get("language", None):
    #     tag_string += f"\nlanguage:\n- {language}"
    if data["type"] == "text_lang":
        lang = data["task"]
        tag_string += f"\nlanguage:\n- {lang}"
    if license:
        tag_string += f'\nlicense: "{license}"'

    if head_type is not None:
        head_type_display = " ".join(head_type.split("_"))
        head_info = f" and includes a prediction head for {head_type_display}"
    else:
        head_type_display = None
        head_info = ""

    description = data.get(
        "description",
        DEFAULT_DESCRIPTION.format(
            model_name=data["model_name"],
            dataset_name=f"[{dataset_name}]({dataset_url})",
            head_info=head_info,
        ),
    )
    author_links = []
    if url := data.get("url", ""):
        author_links.append(f"[Website]({url})")
    if gh := data.get("github", ""):
        if not gh.startswith("http"):
            gh = "https://github.com/" + gh
        author_links.append(f"[GitHub]({gh})")
    if tw := data.get("twitter", ""):
        if not tw.startswith("http"):
            tw = "https://twitter.com/" + tw
        author_links.append(f"[Twitter]({tw})")

    versions = []
    for item in data["files"]:
        version = f"`{item['version']}`"
        if item["version"] == data["default_version"]:
            version += " **(main)**"
        if desc := item.get("description", None):
            version += f": {desc}"
        versions.append(version)
    if len(versions) > 1:
        version_string = "## Versions\n- " + "\n- ".join(versions)
    else:
        version_string = ""

    adapter_card = ADAPTER_CARD_TEMPLATE.format(
        tags=tag_string,
        org_name=hf_org_name,
        adapter_repo_name=adapter_name,
        model_name=data["model_name"],
        description=description,
        dataset_name=f"[{dataset_name}]({dataset_url})",
        adapter_config=data["config"]["using"],
        head_type=head_type_display or "None",
        author_name=data["author"],
        author_email=data.get("email", ""),
        author_links=", ".join(author_links),
        version_list=version_string,
        citation=data.get("citation", ""),
        original_file=HUB_URL + file_name,
    )

    return adapter_card.strip()


def migrate_file(
    file: str,
    push: bool,
    hf_org_name: str,
    skip_existing: bool,
    subtasks_dict: dict,
    api=None,
):
    adapter_name = os.path.basename(file).split(".")[0]
    print(f"Migrating {adapter_name} ...")
    with open(file, "r") as f:
        data = yaml.load(f, yaml.FullLoader)
    subtask_info = subtasks_dict.get(data["task"] + "/" + data["subtask"])

    if push and skip_existing:
        if api.repo_exists(repo_id=hf_org_name + "/" + adapter_name):
            print(f"Skipping {adapter_name} as it already exists.")
            return

    # create a subfolder for each version in the output
    for version_data in data["files"]:
        version = version_data["version"]
        is_default = version == data["default_version"]
        version_folder = os.path.join(OUTPUT_FOLDER, adapter_name, version)
        os.makedirs(os.path.dirname(version_folder), exist_ok=True)

        # download the checkpoint
        dl_folder = download_cached(version_data["url"])
        shutil.move(dl_folder, version_folder)

        # try loading the adapter
        model = AutoAdapterModel.from_pretrained(data["model_name"])
        loaded_name = model.load_adapter(version_folder, set_active=True)
        model.save_adapter(version_folder, loaded_name)

        if loaded_name in model.heads:
            head_type = model.heads[loaded_name].config["head_type"]
        else:
            head_type = None

        adapter_card = create_adapter_card(
            file,
            adapter_name,
            data,
            subtask_info,
            version=version,
            head_type=head_type,
            hf_org_name=hf_org_name,
        )

        # write the adapter card
        with open(os.path.join(version_folder, "README.md"), "w") as f:
            f.write(adapter_card)

        del model

        if push:
            repo_id = hf_org_name + "/" + adapter_name
            api.create_repo(repo_id, exist_ok=True)
            if not is_default:
                api.create_branch(repo_id=repo_id, branch=version, exist_ok=True)
            api.upload_folder(
                repo_id=repo_id,
                folder_path=version_folder,
                revision="main" if is_default else version,
                commit_message=f"Add adapter {adapter_name} version {version}",
            )
            if is_default:
                api.create_branch(repo_id=repo_id, branch=version, exist_ok=True)


def migrate(
    files,
    push: bool = False,
    hf_org_name: str = "AdapterHub",
    skip_existing: bool = False,
):
    subtasks_dict = load_subtasks()
    if push:
        api = HfApi()
    else:
        api = None
    errors = []
    for file in files:
        try:
            migrate_file(file, push, hf_org_name, skip_existing, subtasks_dict, api)
        except Exception as e:
            errors.append(file)
            print(f"Error migrating {file}: {e}")

            with open(ERROR_FILE, "w") as f:
                f.write("\n".join(errors))


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "folder", type=str, help="Folder containing the adapter files to migrate"
    )
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--org_name", type=str, default="AdapterHub")
    parser.add_argument("--skip_existing", action="store_true")
    args = parser.parse_args()

    files = glob(os.path.join(REPO_FOLDER, args.folder, "*"))
    migrate(
        files,
        push=args.push,
        hf_org_name=args.org_name,
        skip_existing=args.skip_existing,
    )
