from dataclasses import dataclass, field
from typing import Dict
import random
import copy

@dataclass
class Genome:
    genes: Dict[str, float] = field(default_factory=dict)

    @staticmethod
    def random_genome(min_genes: int = 6, max_genes: int = 12) -> "Genome":
        possible_traits = [
            "intelligence", "strength", "curiosity", "aggression", "sociability",
            "creativity", "empathy", "resilience", "ambition", "intuition",
            "speed", "perception", "memory_capacity", "adaptability",
            "focus", "charisma", "patience", "courage", "wisdom", "dexterity"
        ]
        num = random.randint(min_genes, max_genes)
        selected = random.sample(possible_traits, num)
        genes = {trait: round(random.uniform(5, 95), 1) for trait in selected}
        return Genome(genes=genes)

    def mutate(self, rate: float = 0.15, strength: float = 0.18) -> "Genome":
        new_genes = copy.deepcopy(self.genes)

        for key in list(new_genes.keys()):
            if random.random() < rate:
                delta = random.uniform(-strength, strength)
                new_genes[key] = max(0.0, min(100.0, new_genes[key] + delta * 100))
                new_genes[key] = round(new_genes[key], 1)

        if random.random() < 0.12:
            new_trait = random.choice([
                "intelligence", "strength", "curiosity", "aggression", "sociability",
                "creativity", "empathy", "resilience", "ambition", "intuition",
                "speed", "perception", "memory_capacity", "adaptability",
                "focus", "charisma", "patience", "courage", "wisdom", "dexterity",
                "stealth", "endurance", "insight", "willpower"
            ])
            if new_trait not in new_genes:
                new_genes[new_trait] = round(random.uniform(10, 80), 1)

        if len(new_genes) > 5 and random.random() < 0.08:
            to_remove = random.choice(list(new_genes.keys()))
            del new_genes[to_remove]

        return Genome(genes=new_genes)

    @staticmethod
    def crossover(g1: "Genome", g2: "Genome") -> "Genome":
        child = {}
        all_keys = set(g1.genes.keys()) | set(g2.genes.keys())
        for key in all_keys:
            v1 = g1.genes.get(key, random.uniform(20, 60))
            v2 = g2.genes.get(key, random.uniform(20, 60))
            if random.random() < 0.5:
                value = (v1 + v2) / 2 + random.uniform(-8, 8)
            else:
                value = random.choice([v1, v2]) + random.uniform(-6, 6)
            child[key] = max(0.0, min(100.0, round(value, 1)))
        return Genome(genes=child)