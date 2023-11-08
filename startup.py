#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import argparse as _argparse

from application.config.config import DefaultConfig
from application.factory import create_app

_DESCRIPTION_MSG = """ """

_EPILOG_MSG = """
    Examples:
"""


class MainArgParse(object):
    def __init__(self):
        self._g_help = False
        self.__verbose__ = False

        self._subparser_name = None
        self.app = None

        self.configuration = ""
        self.host_setting = ""
        self.port = None

        self.psr = _argparse.ArgumentParser(
            prog=__file__,
            description=_DESCRIPTION_MSG,
            epilog=_EPILOG_MSG,
            formatter_class=_argparse.RawTextHelpFormatter,
        )

        self._add_generic_args(self.psr)

        self._add_subparser(self.psr)

        self.psr.parse_args(args=self._sort_args(), namespace=self)

    def apply(self):
        config = DefaultConfig("python")
        config.obtain_environment_variables()

        self.app = create_app(config=config)

        if self.app is None:
            print("Unable to startup, exiting.")
            sys.exit(1)

        self.host_setting = self.app.config["FLASK_RUN_HOST"]
        self.port = self.app.config["FLASK_RUN_PORT"]

    def _add_subparser(self, psr):
        # sub = psr.add_subparsers(
        #     dest="_subparser_name", metavar="sub_commands", help="this is help"
        # )

        # Example
        # sub_command = sub.add_parser("sub_command")

        # Add sub commands to list
        self._sub_list = []

        for item in self._sub_list:
            self._add_generic_args(item)

    @staticmethod
    def _add_generic_args(psr):
        psr.add_argument(
            "-v",
            "--verbose",
            dest="__verbose__",
            action="store_true",
            default=False,
            help="enable verbose output debug",
        )

    def _sort_args(self):
        """
        Move all subparsers to the front
        """

        sub_names = [x.prog.split()[1] for x in self._sub_list]

        sargs = sys.argv[1:]

        for f in sub_names:
            if f in sargs:
                sargs.remove(f)
                sargs.insert(0, f)
        return sargs

    def __str__(self):
        return "\n".join(["Class info goes here!"])


##############################################################################
if __name__ == "__main__":
    """
    Main script entry point
    """

    _arg = MainArgParse()

    _arg.apply()

    if _arg.app is not None:
        _arg.app.run(host=_arg.host_setting, port=_arg.port)
