import glob
import json
import sys
from argparse import ArgumentParser, Namespace
from os.path import dirname, join, realpath

from transformers.adapters.utils import download_cached
from transformers.commands import BaseTransformersCLICommand

from .utils import check_against_schema, check_download


SCHEMA_URL_BASE = "https://raw.githubusercontent.com/Adapter-Hub/Hub/master/scripts/schemas/"


def check_command_factory(args: Namespace):
    return CheckCommand(args.files, args.type)


class CheckCommand(BaseTransformersCLICommand):
    @staticmethod
    def register_subcommand(parser: ArgumentParser):
        check_parser = parser.add_parser("check", help="Validate yaml files to be submitted to AdapterHub, such as adapters.")
        check_parser.add_argument("files", metavar="FILE", type=str, nargs="+", help="specify a file to check")
        check_parser.add_argument(
            "-t", "--type", type=str, default="adapter",
            choices=["adapter", "architecture", "task", "subtask"],
            help="specify the schema against which to check (default: adapter)",
        )
        check_parser.set_defaults(func=check_command_factory)

    def __init__(self, files: list, file_type: str) -> None:
        self.files = files
        self.file_type = file_type

    def load_schema(self, name):
        schema_file = download_cached(SCHEMA_URL_BASE + f"{name}.schema.json")
        with open(schema_file, 'r') as f:
            return json.load(f)

    def check_file(self, file, schema, download=False):
        has_error = check_against_schema(file, schema)
        if not has_error and download:
            has_error = check_download(file)
        if has_error:
            sys.exit(1)

    def run(self):
        schema = self.load_schema(self.file_type)
        download = self.file_type == "adapter"
        for file in self.files:
            self.check_file(file, schema, download=download)
