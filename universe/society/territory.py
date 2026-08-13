from dataclasses import dataclass, field
from typing import List, Optional
import random

from universe.core.namegen import generate_place_name


@dataclass
class Territory:
    id: str
    name: str
    x: int
    y: int
    fertility: float
    capacity: int
    society_id: Optional[str] = None
    neighbors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Territory":
        return cls(**d)


def generate_territory(territory_id: str, x: int, y: int) -> Territory:
    name = generate_place_name()
    fertility = round(random.uniform(0.4, 1.4), 2)
    capacity = max(4, int(6 + fertility * 10 + random.randint(-2, 4)))
    return Territory(id=territory_id, name=name, x=x, y=y, fertility=fertility, capacity=capacity)


def potential_expansion_coords(t: Territory, territories: dict) -> List[tuple]:
    options = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = t.x + dx, t.y + dy
        tid = f"T{nx}_{ny}"
        if tid not in territories:
            options.append((nx, ny))
    return options


def expand_at(territories: dict, x: int, y: int) -> Territory:
    """Мир не имеет заранее заданных границ: при нехватке места рождается новая территория."""
    tid = f"T{x}_{y}"
    if tid in territories:
        return territories[tid]

    t = generate_territory(tid, x, y)
    territories[tid] = t
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        ntid = f"T{nx}_{ny}"
        if ntid in territories:
            t.neighbors.append(ntid)
            territories[ntid].neighbors.append(tid)
    return t


def build_grid(width: int, height: int) -> dict:
    """Создаёт сетку территорий с соседством по 4 направлениям."""
    territories = {}
    for y in range(height):
        for x in range(width):
            tid = f"T{x}_{y}"
            territories[tid] = generate_territory(tid, x, y)

    for y in range(height):
        for x in range(width):
            tid = f"T{x}_{y}"
            neighbors = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append(f"T{nx}_{ny}")
            territories[tid].neighbors = neighbors

    return territories
