import math
from typing import Union
from dataclasses import dataclass

@dataclass
class UnitInfo:
    unit: str
    converter: Union[float, int]

@dataclass
class LatencyStat:
    maxLatency: int
    minLatency: int
    invocation: int
    sumLatency: int

    unitMeta: UnitInfo
    
    @property
    def avgLatency(self):
        return self.sumLatency / self.invocation if self.invocation > 0 else 0
    
    def add_entry(self, latency: int):
        if self.maxLatency < latency:
            self.maxLatency = latency
        if self.minLatency > latency:
            self.minLatency = latency
        self.sumLatency += latency
        self.invocation += 1
    
    @staticmethod
    def new():
        return LatencyStat(
            maxLatency=0,
            minLatency=math.inf, # type: ignore
            invocation=0,
            sumLatency=0,
            unitMeta=UnitInfo(unit="ms", converter=1e6)
        )