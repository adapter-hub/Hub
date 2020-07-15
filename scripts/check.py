#!/use/bin/env python3
import argparse
import glob
import json
from os.path import join, dirname, realpath
import sys
from check_format import check_against_schema
from check_download_files import check_download
from utils import REPO_FOLDER


dir_path = dirname(realpath(__file__))
repo_path = join(dirname(dir_path), REPO_FOLDER)


def load_schema(name):
    with open(join(dir_path, 'schemas', f'{name}.schema.json'), 'r') as f:
        return json.load(f)


def check_file(file, schema, download=False):
    has_error = check_against_schema(file, schema)
    if not has_error and download:
        has_error = check_download(file)
    if has_error:
        sys.exit(1)


def check_user(username):
    print(f"Checking all files of user '{username}'\n")
    schema = load_schema("adapter")
    files = glob.glob(join(repo_path, username, "**"))
    for file in files:
        check_file(file, schema, download=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use this script to validate your adapter yaml files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, action="append", help="specify a file to check")
    group.add_argument('-u', '--user', type=str, help="specify a username for which to check all files")
    parser.add_argument(
        '--schema', type=str, default="adapter",
        choices=["adapter", "architecture", "task", "subtask"],
        help="specify the schema against which to check (default: adapter)",
    )
    args = parser.parse_args()

    schema = load_schema(args.schema)
    download = args.schema=="adapter"
    if args.file:
        for file in args.file:
            check_file(file, schema, download=download)
    elif args.user:
        check_user(args.user)
