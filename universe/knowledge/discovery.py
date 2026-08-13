from dataclasses import dataclass, field
from typing import Dict, Optional
import random

from universe.knowledge.domains import DOMAINS, DISCOVERY_TEMPLATES
from universe.core.namegen import inflect_adjective


@dataclass
class Discovery:
    id: str
    name: str
    domain: str
    tier: int
    discovered_by: Optional[str]
    discovered_by_name: str
    discovered_tick: int

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Discovery":
        return cls(**d)


class KnowledgeTree:
    """Растущее, ничем не ограниченное дерево знаний вселенной."""

    def __init__(self):
        self.discoveries: Dict[str, Discovery] = {}
        self.domain_levels: Dict[str, float] = {d: 0.0 for d in DOMAINS}
        self._counter = 0

    def to_dict(self) -> dict:
        return {
            "discoveries": {k: v.to_dict() for k, v in self.discoveries.items()},
            "domain_levels": self.domain_levels,
            "counter": self._counter,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KnowledgeTree":
        tree = cls()
        tree.discoveries = {k: Discovery.from_dict(v) for k, v in d.get("discoveries", {}).items()}
        tree.domain_levels = dict(d.get("domain_levels", tree.domain_levels))
        tree._counter = d.get("counter", 0)
        return tree

    def total_discoveries(self) -> int:
        return len(self.discoveries)

    def _choose_domain(self, agent) -> str:
        names = list(DOMAINS.keys())
        weights = []
        for name in names:
            interest = agent.attributes.get(f"interest_{name}", 0.0)
            weight = 1.0 + self.domain_levels[name] * 0.15 + interest * 0.05
            weights.append(weight)
        return random.choices(names, weights=weights, k=1)[0]

    def attempt_research(self, agent, tick: int) -> Optional[Discovery]:
        domain = self._choose_domain(agent)
        bank = DOMAINS[domain]
        tier = int(self.domain_levels[domain] // 3) + 1

        template = random.choice(DISCOVERY_TEMPLATES)
        noun, gender = random.choice(bank["nouns"])
        adj_base = random.choice(bank["adjectives"])
        masc, fem, neut = inflect_adjective(adj_base)
        adj = {"m": masc, "f": fem, "n": neut}.get(gender, masc)
        name = template.format(adj=adj.capitalize(), noun=noun.capitalize())

        self._counter += 1
        disc_id = f"D{self._counter:05d}"
        discovery = Discovery(
            id=disc_id,
            name=name,
            domain=domain,
            tier=tier,
            discovered_by=agent.id,
            discovered_by_name=agent.name,
            discovered_tick=tick,
        )
        self.discoveries[disc_id] = discovery
        self.domain_levels[domain] = round(self.domain_levels[domain] + 1, 2)

        agent.knowledge.append(disc_id)
        agent.attributes[f"interest_{domain}"] = agent.attributes.get(f"interest_{domain}", 0.0) + 1

        return discovery
