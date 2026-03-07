from __future__ import annotations

try: 
    from digilab_simulators.simulators.base import Simulator, SimulatorConfig, SimulatorMeta
    
except ImportError: 
    from abc import ABC, abstractmethod
    from dataclasses import dataclass, field
    from typing import Any

    from pydantic import BaseModel, ConfigDict

        
    @dataclass
    class SimulatorMeta:
        name: str
        description: str
        version: str
        tags: list[str] = field(default_factory=list)


    class SimulatorConfig(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)


    class Simulator(ABC):
        @abstractmethod
        def forward(self, X: list[list[float]], **kwargs: Any) -> list[dict]:
            raise NotImplementedError
