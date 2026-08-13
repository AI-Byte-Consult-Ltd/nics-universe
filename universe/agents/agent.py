from dataclasses import dataclass, field
from universe.core.entity import Entity
from universe.core.genome import Genome
import random

@dataclass
class Agent(Entity):
    genome: Genome = field(default_factory=Genome)
    species: str = "Human"
    goals: list = field(default_factory=list)
    relationships: dict = field(default_factory=dict)
    hunger: float = 20.0
    thirst: float = 15.0
    fatigue: float = 10.0

    def __post_init__(self):
        # Характеристики берутся из генома + добавляются случайные
        for gene, value in self.genome.genes.items():
            if gene not in self.characteristics:
                self.characteristics[gene] = value

        # Иногда появляются дополнительные характеристики, которых нет в геноме
        extra_traits = ["luck", "mood", "focus_level", "energy_efficiency"]
        for trait in extra_traits:
            if random.random() < 0.35 and trait not in self.characteristics:
                self.characteristics[trait] = round(random.uniform(10, 90), 1)