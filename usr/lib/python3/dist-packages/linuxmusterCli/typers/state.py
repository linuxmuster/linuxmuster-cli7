class State:
    def __init__(self):
        # Output format raw, json or csv
        self.raw = False
        self.csv = False
        # self.json = False

        # Output format raw, json or csv activated or not
        self.format = False

state = State()