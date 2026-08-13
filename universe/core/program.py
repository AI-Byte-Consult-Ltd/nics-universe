"""Program — универсальная сущность вселенной.

Люди, животные, растения, предметы, технологии, открытия, профессии —
всё это Program, различающееся только полем `kind`/`domain` и набором
характеристик. Никаких отдельных классов-исключений: поведение
диктуется данными, а не наследованием.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from universe.core.genome import Genome

LIVING = "living"
INANIMATE = "inanimate"
ABSTRACT = "abstract"


@dataclass
class Program:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Безымянная программа"
    kind: str = "program"
    domain: str = ABSTRACT
    sapient: bool = False

    era_born: str = ""
    created_tick: int = 0

    sex: Optional[str] = None
    age: int = 0
    energy: float = 100.0
    health: float = 100.0
    alive: bool = True

    location: Optional[str] = None
    society: Optional[str] = None

    genome: Optional[Genome] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    knowledge: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    profession: Optional[str] = None

    relationships: Dict[str, float] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)

    hunger: float = 10.0
    thirst: float = 10.0
    fatigue: float = 5.0
    last_reproduced_tick: int = -9999

    def trait(self, key: str, default: float = 30.0) -> float:
        if self.genome and key in self.genome.genes:
            return self.genome.genes[key]
        return self.attributes.get(key, default)

    def add_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["genome"] = self.genome.to_dict() if self.genome else None
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Program":
        d = dict(d)
        genome_data = d.pop("genome", None)
        genome = Genome.from_dict(genome_data) if genome_data else None
        return cls(genome=genome, **d)
