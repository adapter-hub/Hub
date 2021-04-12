import json
import os
from os.path import join
import sys
from utils import *


if __name__ == "__main__":
    # get the type of files we want to check
    file_type = sys.argv[1]
    additional_check_func = None
    if file_type == "adapter":
        files = [f for f in sys.argv[2:] if f.startswith(REPO_FOLDER)]
    elif file_type == "architecture":
        files = [f for f in sys.argv[2:] if f.startswith(ARCHITECTURE_FOLDER)]
    elif file_type == "task":
        files = [f for f in sys.argv[2:] if f.startswith(TASK_FOLDER)]
    elif file_type == "subtask":
        files = [f for f in sys.argv[2:] if f.startswith(SUBTASK_FOLDER)]
    else:
        sys.exit("Invalid entry type '{}'".format(file_type))
    # load schema
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(join(dir_path, 'schemas', '{}.schema.json'.format(file_type)), 'r') as f:
        schema = json.load(f)
    # check files
    for file in files:
        has_error = check_against_schema(file, schema)
        if not has_error and additional_check_func:
            has_error = additional_check_func(file)
        if has_error:
            sys.exit(1)
