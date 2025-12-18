import re
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

def _check_schoolclass_number(schoolclass):
    """
    Get number in a schoolclass name.

    :param schoolclass: Dict of schoolclass attributes from LDAP.
    """


    n = re.findall(r'\d+', schoolclass['cn'])
    if n:
        return int(n[0])
    else:
        return 10000000 # just a big number to come after all schoolclasses

def sort_schoolclasses(schoolclasses):
    """
    Sort a list of schoolclasses data from LDAP.
    """


    return sorted(schoolclasses, key=lambda s: (_check_schoolclass_number(s), s['cn']))

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