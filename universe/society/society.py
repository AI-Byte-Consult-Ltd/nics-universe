from dataclasses import dataclass, field
from typing import Dict, List
import random

from universe.core.namegen import LanguageStyle, generate_place_name, generate_merge_reason

CULTURE_TRAITS = ["sociability", "aggression", "curiosity", "creativity", "empathy", "ambition"]
MERGE_BASE_CHANCE = 0.03
MERGE_SIMILARITY_WEIGHT = 0.9


@dataclass
class Society:
    id: str
    name: str
    founded_tick: int
    members: List[str] = field(default_factory=list)
    territories: List[str] = field(default_factory=list)
    culture: Dict[str, float] = field(default_factory=dict)
    language_style: dict = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    absorbed: bool = False

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Society":
        return cls(**d)

    def get_language_style(self) -> LanguageStyle:
        return LanguageStyle.from_dict(self.language_style)


def found_society(society_id: str, tick: int) -> Society:
    style = LanguageStyle.random_style()
    name = generate_place_name() + " " + random.choice(["Род", "Клан", "Община", "Союз", "Народ"])
    return Society(
        id=society_id,
        name=name,
        founded_tick=tick,
        language_style=style.to_dict(),
        history=[f"[Тик {tick}] Основано общество «{name}»."],
    )


def recompute_culture(society: Society, members: List) -> None:
    if not members:
        return
    culture = {}
    for trait in CULTURE_TRAITS:
        values = [m.trait(trait, 30.0) for m in members]
        culture[trait] = round(sum(values) / len(values), 2)
    society.culture = culture


def similarity(a: Society, b: Society) -> float:
    keys = set(a.culture) & set(b.culture)
    if not keys:
        return 0.0
    diffs = [abs(a.culture[k] - b.culture[k]) for k in keys]
    avg_diff = sum(diffs) / len(diffs)
    return max(0.0, 1 - avg_diff / 100)


def territories_adjacent(a: Society, b: Society, territories: dict) -> bool:
    for tid in a.territories:
        t = territories.get(tid)
        if not t:
            continue
        for n in t.neighbors:
            if n in b.territories:
                return True
    return False


def try_merge(a: Society, b: Society, territories: dict, tick: int) -> bool:
    if a.absorbed or b.absorbed:
        return False
    if not territories_adjacent(a, b, territories):
        return False

    sim = similarity(a, b)
    chance = MERGE_BASE_CHANCE * (0.2 + MERGE_SIMILARITY_WEIGHT * sim)
    if random.random() >= chance:
        return False

    reason = generate_merge_reason()
    a.members.extend(b.members)
    a.territories.extend(t for t in b.territories if t not in a.territories)
    for tid in b.territories:
        if tid in territories:
            territories[tid].society_id = a.id
    a.history.append(f"[Тик {tick}] Поглотило «{b.name}»: {reason}.")
    b.absorbed = True
    b.members = []
    b.territories = []
    return True
