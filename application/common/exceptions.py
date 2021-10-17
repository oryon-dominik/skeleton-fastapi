
class UnknownTeapotException(Exception):
    def __init__(self, name: str):
        self.name = name

class CreateFixturesInTestmodeOnly(Exception):
    pass
