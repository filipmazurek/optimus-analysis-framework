import numpy as np
from oaf.optimus_simulator.node import Node

class VirtualConnectionNode(Node):
    """Node which serves only to connect other nodes. This node node will always fail its check_data call
    so that it can force its dependencies to be checked at the same time. This is useful for creating dependencies
    between two nodes at the same level.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.failed = True

    def calibrate(self, time):
        pass
