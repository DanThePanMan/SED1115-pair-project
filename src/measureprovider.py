from random import randint

class MeasureProvider():
    """
    Abstract base class representing a source of measurements.
    """
    def measure(self) -> int:
        """
        Get a measurement from the RC filter.
        """
        ...

class MockMeasureProvider(MeasureProvider):
    """
    Generates a fake measurement within a given range.
    """
    range: 'tuple[int, int]'
    
    def __init__(self, range: 'tuple[int, int]'):
        if range[0] < 0 or range[0] > range[1] or range[1] > 65535:
            raise ValueError("invalid range")
        self.range = range

    def measure(self) -> int:
        return randint(self.range[0], self.range[1])
    