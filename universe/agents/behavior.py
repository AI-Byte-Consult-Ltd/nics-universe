"""Общая посекундная (потиковая) логика для любой живой Program.

Одни и те же правила действуют и для людей, и для животных —
разница только в поле `sapient` (способность исследовать/иметь профессию).
"""
import random

YEAR_TICKS = 24
MATURITY_TICKS = 16 * YEAR_TICKS
RESEARCH_MIN_AGE_TICKS = 10 * YEAR_TICKS
REPRODUCTION_COOLDOWN_TICKS = 3 * YEAR_TICKS
AFFINITY_THRESHOLD = 55.0
BASE_REPRODUCTION_CHANCE = 0.015
BASE_RESEARCH_CHANCE = 0.006


def age_years(agent) -> int:
    return agent.age // YEAR_TICKS


def update_needs(agent) -> None:
    agent.hunger = min(100, agent.hunger + random.uniform(0.15, 0.40))
    agent.thirst = min(100, agent.thirst + random.uniform(0.12, 0.32))
    agent.fatigue = min(100, agent.fatigue + random.uniform(0.10, 0.28))
    agent.energy = max(0, agent.energy - random.uniform(0.04, 0.15))

    if agent.hunger > 40 and random.random() < 0.35:
        agent.hunger = max(0, agent.hunger - random.uniform(8, 18))
        agent.energy = min(100, agent.energy + random.uniform(4, 12))
    if agent.thirst > 35 and random.random() < 0.40:
        agent.thirst = max(0, agent.thirst - random.uniform(7, 15))
        agent.energy = min(100, agent.energy + random.uniform(3, 9))
    if agent.fatigue > 50 and random.random() < 0.30:
        agent.fatigue = max(0, agent.fatigue - random.uniform(10, 25))
        agent.energy = min(100, agent.energy + random.uniform(5, 14))


def natural_lifespan_ticks(agent) -> int:
    resilience = agent.trait("resilience", 40)
    vitality = agent.trait("vitality", 40)
    base_years = 45 + resilience * 0.35 + vitality * 0.25
    return int(base_years * YEAR_TICKS)


def old_age_death_chance(agent) -> float:
    """Риск смерти растёт постепенно после наступления старости, а не обрывается стеной —
    это не даёт ровесникам с одинаковыми (дефолтными) генами умирать в один и тот же тик."""
    expected = natural_lifespan_ticks(agent)
    onset = expected * 0.6
    if agent.age < onset:
        return 0.0
    overshoot = (agent.age - onset) / max(1.0, onset)
    return min(0.35, overshoot ** 2 * 0.15)


def check_death(agent, log) -> bool:
    if agent.energy <= 0 or agent.hunger >= 98 or agent.health <= 0:
        agent.alive = False
        log(f"Смерть: {agent.name} ({agent.id}) — возраст {age_years(agent)} лет.")
        return True
    if random.random() < old_age_death_chance(agent):
        agent.alive = False
        log(f"Смерть от старости: {agent.name} ({agent.id}) — возраст {age_years(agent)} лет.")
        return True
    return False


def step_agent(agent, log) -> bool:
    """Старение и потребности. Возвращает True, если агент жив после тика."""
    agent.age += 1
    update_needs(agent)
    return not check_death(agent, log)


def update_affinity(a, b, delta_range=(0.3, 1.2)) -> None:
    delta = random.uniform(*delta_range)
    a.relationships[b.id] = min(100.0, a.relationships.get(b.id, 0.0) + delta)
    b.relationships[a.id] = min(100.0, b.relationships.get(a.id, 0.0) + delta)


def is_reproduction_eligible(a, b, tick: int) -> bool:
    if not (a.alive and b.alive):
        return False
    if a.sex == b.sex or a.sex is None or b.sex is None:
        return False
    if a.age < MATURITY_TICKS or b.age < MATURITY_TICKS:
        return False
    if a.energy < 35 or b.energy < 35:
        return False
    if tick - a.last_reproduced_tick < REPRODUCTION_COOLDOWN_TICKS:
        return False
    if tick - b.last_reproduced_tick < REPRODUCTION_COOLDOWN_TICKS:
        return False
    affinity = a.relationships.get(b.id, 0.0)
    return affinity >= AFFINITY_THRESHOLD


def reproduction_chance(a, b, population: int, capacity: int) -> float:
    logistic = max(0.0, 1 - population / max(1, capacity))
    affinity = min(100.0, (a.relationships.get(b.id, 0.0) + b.relationships.get(a.id, 0.0)) / 2)
    fertility = (a.trait("fertility", 40) + b.trait("fertility", 40)) / 200
    return BASE_REPRODUCTION_CHANCE * logistic * (affinity / 100) * (0.4 + fertility)


def research_chance(agent) -> float:
    intelligence = agent.trait("intelligence", 30)
    curiosity = agent.trait("curiosity", 30)
    focus = agent.trait("focus", 30)
    profession_bonus = 2.2 if agent.profession else 1.0
    return BASE_RESEARCH_CHANCE * ((intelligence + curiosity + focus) / 300) * profession_bonus
