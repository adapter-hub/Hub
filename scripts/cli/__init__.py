from argparse import ArgumentParser

from .check import CheckCommand
from .download import AdapterDownloadCommand
from .pack import AdapterPackCommand


def main():
    parser = ArgumentParser("AdapterHub CLI tool")
    command_parser = parser.add_subparsers(help="adapter-cli commands")

    # Register commands
    CheckCommand.register_subcommand(command_parser)
    AdapterPackCommand.register_subcommand(command_parser)
    AdapterDownloadCommand.register_subcommand(command_parser)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        exit(1)

    # Run command
    service = args.func(args)
    service.run()


if __name__ == "__main__":
    main()
