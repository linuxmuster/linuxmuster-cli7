# import json
import typer
from datetime import datetime
from .state import state


def warn(text):
    typer.secho(text, fg=typer.colors.YELLOW)

def error(text):
    typer.secho(text, fg=typer.colors.RED)

def convert_sophomorix_time(t):
    try:
        return  datetime.strptime(t, '%Y%m%d%H%M%S.%fZ').strftime("%d %b %Y %H:%M:%S")
    except Exception:
        return t

def outformat(value, fieldname=""):
    if "Date" in fieldname:
        return convert_sophomorix_time(value)

    if isinstance(value, list):
        return ','.join(value)
    if str(value) == 'True':
        return ":white_heavy_check_mark:"
    if str(value) == 'False':
        return ":cross_mark:"
    return value

class Format:
    """
    Class to export data as csv or raw, in order to grep the results.
    """

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