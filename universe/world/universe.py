import random
from typing import Dict, List, Optional

from universe.core.program import Program, LIVING
from universe.core.genome import Genome
from universe.core.namegen import LanguageStyle, generate_name, generate_species_name
from universe.agents import behavior
from universe.knowledge.discovery import KnowledgeTree
from universe.knowledge.professions import ProfessionRegistry
from universe.society.territory import (
    Territory, build_grid, potential_expansion_coords, expand_at,
)
from universe.society.society import (
    Society, found_society, recompute_culture, try_merge,
)
from universe.world import eras

GRID_SIZE = 4
WILDLIFE_TERRITORIES = 5
MIGRATION_CHECK_CHANCE = 0.05
LOW_POPULATION_THRESHOLD = 3
WANDERER_CHANCE = 0.02


class Universe:
    def __init__(self):
        self.tick = 0
        self.programs: Dict[str, Program] = {}
        self.territories: Dict[str, Territory] = {}
        self.societies: Dict[str, Society] = {}
        self.knowledge_tree = KnowledgeTree()
        self.professions = ProfessionRegistry()
        self.event_log: List[str] = []
        self.era = eras.era_for(0)
        self._next_id = 1
        self._next_society_id = 1

    # ---------------------------------------------------------- utilities
    def _new_id(self) -> str:
        pid = f"{self._next_id:04d}"
        self._next_id += 1
        return pid

    def _new_society_id(self) -> str:
        sid = f"S{self._next_society_id:03d}"
        self._next_society_id += 1
        return sid

    def log(self, message: str) -> None:
        entry = f"[Тик {self.tick:05d} | {self.era}] {message}"
        self.event_log.append(entry)
        print(entry)

    def living(self) -> List[Program]:
        return [p for p in self.programs.values() if p.alive and p.domain == LIVING]

    def find(self, identifier: str) -> Optional[Program]:
        for p in self.programs.values():
            if p.id == identifier or p.name.lower() == identifier.lower():
                return p
        return None

    # ------------------------------------------------------------ genesis
    def spawn_human(self, sex: Optional[str] = None, genome: Optional[Genome] = None,
                     location: Optional[str] = None, society_id: Optional[str] = None,
                     style: Optional[LanguageStyle] = None, parents: Optional[list] = None) -> Program:
        if sex is None:
            sex = random.choice(["male", "female"])
        if genome is None:
            genome = Genome.random_genome()
        if style is None:
            society = self.societies.get(society_id)
            style = society.get_language_style() if society else LanguageStyle.random_style()

        agent = Program(
            id=self._new_id(),
            name=generate_name(style, sex=sex),
            kind="human",
            domain=LIVING,
            sapient=True,
            era_born=self.era,
            created_tick=self.tick,
            sex=sex,
            genome=genome,
            location=location,
            society=society_id,
            parents=parents or [],
        )
        self.programs[agent.id] = agent
        return agent

    def _spawn_wildlife(self) -> None:
        territory_ids = list(self.territories.keys())
        sample = random.sample(territory_ids, k=min(WILDLIFE_TERRITORIES, len(territory_ids)))
        for tid in sample:
            species = generate_species_name()
            kind = f"animal:{species}"
            style = LanguageStyle.random_style()
            for sex in ("male", "female"):
                animal = Program(
                    id=self._new_id(),
                    name=generate_name(style, sex=sex),
                    kind=kind,
                    domain=LIVING,
                    sapient=False,
                    era_born=self.era,
                    created_tick=self.tick,
                    sex=sex,
                    genome=Genome.random_genome(),
                    location=tid,
                )
                self.programs[animal.id] = animal
            self.log(f"В землях «{self.territories[tid].name}» замечен новый вид: {species}.")

    def genesis(self):
        self.territories = build_grid(GRID_SIZE, GRID_SIZE)
        origin_id = f"T{GRID_SIZE // 2}_{GRID_SIZE // 2}"
        origin = self.territories[origin_id]

        society = found_society(self._new_society_id(), self.tick)
        origin.society_id = society.id
        society.territories.append(origin.id)
        self.societies[society.id] = society

        style = society.get_language_style()
        first = self.spawn_human(sex="male", location=origin.id, society_id=society.id, style=style)
        second = self.spawn_human(sex="female", location=origin.id, society_id=society.id, style=style)
        society.members.extend([first.id, second.id])

        self.log(f"Начало времён: {first.name} и {second.name} пробуждаются на земле «{origin.name}».")
        self.log(f"Общество «{society.name}» основано.")

        self._spawn_wildlife()
        self.era = eras.era_for(self.knowledge_tree.total_discoveries())
        return first, second

    # -------------------------------------------------------- simulation
    def advance_time(self, ticks: int = 1) -> None:
        for _ in range(ticks):
            self.tick += 1
            self._step_all()
            self._handle_reproduction()
            self._handle_research_and_professions()
            self._handle_migration()
            self._handle_society_merges()
            self._handle_replenishment()
            self.era = eras.era_for(self.knowledge_tree.total_discoveries())

    def _step_all(self) -> None:
        for p in list(self.programs.values()):
            if p.alive and p.domain == LIVING:
                behavior.step_agent(p, self.log)

    def reproduce(self, parent1: Program, parent2: Program) -> Program:
        child_genome = Genome.crossover(parent1.genome, parent2.genome).mutate(rate=0.12, strength=0.15)
        sex = random.choice(["male", "female"])
        society = self.societies.get(parent1.society)
        style = society.get_language_style() if society else LanguageStyle.random_style()

        child = Program(
            id=self._new_id(),
            name=generate_name(style, sex=sex),
            kind=parent1.kind,
            domain=LIVING,
            sapient=parent1.sapient,
            era_born=self.era,
            created_tick=self.tick,
            sex=sex,
            genome=child_genome,
            location=parent1.location,
            society=parent1.society,
            parents=[parent1.id, parent2.id],
        )
        self.programs[child.id] = child

        parent1.children.append(child.id)
        parent2.children.append(child.id)
        parent1.energy = max(10.0, parent1.energy - 20)
        parent2.energy = max(10.0, parent2.energy - 20)
        parent1.last_reproduced_tick = self.tick
        parent2.last_reproduced_tick = self.tick

        if society:
            society.members.append(child.id)

        self.log(f"Рождение: {parent1.name} + {parent2.name} → {child.name} ({child.kind}).")
        return child

    def _handle_reproduction(self) -> None:
        groups: Dict[tuple, List[Program]] = {}
        for p in self.living():
            groups.setdefault((p.location, p.kind), []).append(p)

        for (loc, _kind), members in groups.items():
            males = [m for m in members if m.sex == "male"]
            females = [m for m in members if m.sex == "female"]
            if not males or not females:
                continue

            territory = self.territories.get(loc)
            capacity = territory.capacity if territory else 20
            population = len(members)

            sample_size = min(3, len(males), len(females))
            pairs = set()
            attempts = 0
            while len(pairs) < sample_size and attempts < sample_size * 4:
                attempts += 1
                pairs.add((random.choice(males).id, random.choice(females).id))

            by_id = {m.id: m for m in members}
            for a_id, b_id in pairs:
                a, b = by_id[a_id], by_id[b_id]
                behavior.update_affinity(a, b)
                if behavior.is_reproduction_eligible(a, b, self.tick):
                    chance = behavior.reproduction_chance(a, b, population, capacity)
                    if random.random() < chance:
                        self.reproduce(a, b)
                        break

    def _handle_research_and_professions(self) -> None:
        for p in self.living():
            if not p.sapient:
                continue
            if p.age < behavior.RESEARCH_MIN_AGE_TICKS or p.energy < 40:
                continue

            if random.random() < behavior.research_chance(p):
                discovery = self.knowledge_tree.attempt_research(p, self.tick)
                self.log(f"Открытие ({discovery.domain}): {discovery.name} — {p.name}.")
                for domain, root in self.professions.refresh(self.knowledge_tree.domain_levels, self.tick):
                    self.log(f"Новое ремесло доступно ({domain}): {root}.")
            elif self.professions.maybe_assign(p):
                self.log(f"{p.name} осваивает призвание: {p.profession}.")

    def _handle_migration(self) -> None:
        occupancy: Dict[str, int] = {}
        for p in self.living():
            occupancy[p.location] = occupancy.get(p.location, 0) + 1

        for tid, population in list(occupancy.items()):
            territory = self.territories.get(tid)
            if not territory or population <= territory.capacity:
                continue
            if random.random() > MIGRATION_CHECK_CHANCE:
                continue

            candidates = [n for n in territory.neighbors
                          if occupancy.get(n, 0) < self.territories[n].capacity]
            if not candidates:
                options = potential_expansion_coords(territory, self.territories)
                if options:
                    nx, ny = random.choice(options)
                    new_t = expand_at(self.territories, nx, ny)
                    candidates = [new_t.id]
            if not candidates:
                continue

            movers = [p for p in self.living() if p.location == tid and not p.children]
            if not movers:
                continue

            mover = random.choice(movers)
            target_id = random.choice(candidates)
            target = self.territories[target_id]
            mover.location = target_id

            if target.society_id is None:
                if mover.society and mover.society in self.societies:
                    self.societies[mover.society].territories.append(target_id)
                    target.society_id = mover.society
            elif target.society_id != mover.society:
                other = self.societies.get(target.society_id)
                if other:
                    self.log(f"Контакт: {mover.name} достиг земель общества «{other.name}».")

            self.log(f"Миграция: {mover.name} переселяется в «{target.name}».")

    def _handle_society_merges(self) -> None:
        active = [s for s in self.societies.values() if not s.absorbed]
        for s in active:
            members = [self.programs[m] for m in s.members
                       if m in self.programs and self.programs[m].alive]
            recompute_culture(s, members)

        for i, a in enumerate(active):
            if a.absorbed:
                continue
            for b in active[i + 1:]:
                if b.absorbed:
                    continue
                if try_merge(a, b, self.territories, self.tick):
                    self.log(f"Слияние обществ: «{a.name}» поглотило «{b.name}».")
                    break

    def _handle_replenishment(self) -> None:
        """Малая изолированная популяция может вымереть от чистого невезения
        (например, все выжившие дети оказались одного пола). Изредка к роду
        прибивается одинокий странник — так угасание не необратимо."""
        sapient_count = sum(1 for p in self.living() if p.sapient)
        if sapient_count >= LOW_POPULATION_THRESHOLD:
            return
        if random.random() > WANDERER_CHANCE:
            return

        active_societies = [s for s in self.societies.values() if not s.absorbed and s.territories]
        if active_societies:
            society = random.choice(active_societies)
            location = random.choice(society.territories)
            society_id = society.id
        else:
            society = found_society(self._new_society_id(), self.tick)
            location = random.choice(list(self.territories.keys()))
            self.territories[location].society_id = society.id
            society.territories.append(location)
            self.societies[society.id] = society
            society_id = society.id

        males = sum(1 for p in self.living() if p.sapient and p.society == society_id and p.sex == "male")
        females = sum(1 for p in self.living() if p.sapient and p.society == society_id and p.sex == "female")
        sex = "female" if males >= females else "male"

        wanderer = self.spawn_human(sex=sex, location=location, society_id=society_id)
        wanderer.age = behavior.MATURITY_TICKS + random.randint(0, 4 * behavior.YEAR_TICKS)
        society.members.append(wanderer.id)
        self.log(f"Странник: {wanderer.name} приходит и остаётся в «{society.name}».")

    # ------------------------------------------------------------- views
    def status(self, detailed: bool = False) -> None:
        living = self.living()
        humans = [p for p in living if p.sapient]
        animals = [p for p in living if not p.sapient]
        active_societies = [s for s in self.societies.values() if not s.absorbed]

        print("\n" + "=" * 64)
        print("NICS SELF-EVOLVING UNIVERSE")
        print("=" * 64)
        print(f"Тик:                 {self.tick}  (~{self.tick // behavior.YEAR_TICKS} лет от начала)")
        print(f"Эпоха:               {self.era}")
        print(f"Разумные:            {len(humans)}   Всего рождено: "
              f"{sum(1 for p in self.programs.values() if p.sapient)}")
        print(f"Прочие живые виды:   {len(animals)}")
        print(f"Обществ:             {len(active_societies)}")
        print(f"Территорий:          {len(self.territories)}")
        print(f"Открытий:            {self.knowledge_tree.total_discoveries()}")
        print(f"Доступных ремёсел:   {len(self.professions.available)}")
        print("-" * 64)

        for s in active_societies:
            pop = sum(1 for m in s.members if m in self.programs and self.programs[m].alive)
            print(f"  «{s.name}»: {pop} жит., {len(s.territories)} земель")

        if detailed:
            print("-" * 64)
            for p in humans:
                print(f"  [{p.id}] {p.name:16} | {p.sex:6} | {behavior.age_years(p):3} лет | "
                      f"{p.profession or '—':22} | энергия {p.energy:5.1f}")

        print("=" * 64 + "\n")

    def view(self, identifier: str) -> None:
        p = self.find(identifier)
        if p is None:
            print(f"Программа «{identifier}» не найдена.")
            return

        print("\n" + "=" * 60)
        print(f"ПРОГРАММА: {p.name} ({p.id})")
        print("=" * 60)
        print(f"Тип:          {p.kind}  [{'разумный' if p.sapient else 'неразумный'}]")
        print(f"Пол:          {p.sex}")
        print(f"Возраст:      {behavior.age_years(p)} лет")
        print(f"Жив:          {p.alive}")
        print(f"Энергия:      {p.energy:.1f}   Здоровье: {p.health:.1f}")
        print(f"Голод/Жажда/Усталость: {p.hunger:.1f} / {p.thirst:.1f} / {p.fatigue:.1f}")
        territory = self.territories.get(p.location)
        print(f"Земля:        {territory.name if territory else p.location}")
        society = self.societies.get(p.society)
        print(f"Общество:     {society.name if society else '—'}")
        print(f"Профессия:    {p.profession or '—'}")
        print(f"Родители:     {p.parents or 'Нет'}")
        print(f"Дети:         {p.children or 'Нет'}")
        print(f"Известно открытий: {len(p.knowledge)}")
        print("-" * 60)
        print("ГЕНЫ:")
        if p.genome:
            for gene, value in sorted(p.genome.genes.items()):
                print(f"  {gene:20}: {value:5.1f}")
        print("=" * 60 + "\n")

    # -------------------------------------------------------- persistence
    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "era": self.era,
            "next_id": self._next_id,
            "next_society_id": self._next_society_id,
            "programs": {k: v.to_dict() for k, v in self.programs.items()},
            "territories": {k: v.to_dict() for k, v in self.territories.items()},
            "societies": {k: v.to_dict() for k, v in self.societies.items()},
            "knowledge_tree": self.knowledge_tree.to_dict(),
            "professions": self.professions.to_dict(),
            "event_log": self.event_log[-300:],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Universe":
        u = cls()
        u.tick = d["tick"]
        u.era = d["era"]
        u._next_id = d["next_id"]
        u._next_society_id = d["next_society_id"]
        u.programs = {k: Program.from_dict(v) for k, v in d["programs"].items()}
        u.territories = {k: Territory.from_dict(v) for k, v in d["territories"].items()}
        u.societies = {k: Society.from_dict(v) for k, v in d["societies"].items()}
        u.knowledge_tree = KnowledgeTree.from_dict(d["knowledge_tree"])
        u.professions = ProfessionRegistry.from_dict(d["professions"])
        u.event_log = list(d.get("event_log", []))
        return u
