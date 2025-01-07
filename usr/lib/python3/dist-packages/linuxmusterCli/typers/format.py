# import json
import typer
from .state import state


def warn(text):
    typer.secho(text, fg=typer.colors.YELLOW)

def error(text):
    typer.secho(text, fg=typer.colors.RED)

class Format:

    def format(self, data):
        if state.raw:
            self._format = self.raw
        if state.csv:
            self._format = self.csv

        self._format(data)

    @staticmethod
    def raw(data):
        """
        Print data with tabular as separator.
        """


        for entry in data:
            print(*entry, sep="\t")

    @staticmethod
    def csv(data):
        """
        Print data with semi-colon as separator.
        """


        for entry in data:
            print(*entry, sep=";")


    # Maybe json for later
    # def json(self, data):
    #     """
    #     Export data as json.
    #     """
    #
    #
    #     print(json.dumps(data))
    #

printf = Format()