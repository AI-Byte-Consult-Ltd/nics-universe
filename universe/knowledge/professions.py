from typing import Dict, Set
import random

from universe.knowledge.domains import DOMAINS, PROFESSION_PREFIXES

UNLOCK_THRESHOLD = 2.0


class ProfessionRegistry:
    """Профессии не заданы списком — они рождаются из освоенных областей знаний."""

    def __init__(self):
        self.unlocked_domains: Set[str] = set()
        self.available: Set[str] = set()

    def to_dict(self) -> dict:
        return {
            "unlocked_domains": list(self.unlocked_domains),
            "available": list(self.available),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProfessionRegistry":
        reg = cls()
        reg.unlocked_domains = set(d.get("unlocked_domains", []))
        reg.available = set(d.get("available", []))
        return reg

    def refresh(self, domain_levels: Dict[str, float], tick: int) -> list:
        newly_unlocked = []
        for domain, level in domain_levels.items():
            if level >= UNLOCK_THRESHOLD and domain not in self.unlocked_domains:
                self.unlocked_domains.add(domain)
                root = random.choice(DOMAINS[domain]["profession_roots"])
                for _ in range(random.randint(1, 3)):
                    if random.random() < 0.5:
                        name = f"{random.choice(PROFESSION_PREFIXES)} {root}"
                    else:
                        name = root.capitalize()
                    self.available.add(name)
                newly_unlocked.append((domain, root))
        return newly_unlocked

    def maybe_assign(self, agent) -> bool:
        if agent.profession or not self.available:
            return False
        ambition = agent.trait("ambition", 30) + agent.trait("curiosity", 30)
        chance = 0.01 * (ambition / 100)
        if random.random() < chance:
            agent.profession = random.choice(list(self.available))
            return True
        return False
