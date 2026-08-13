from typing import Dict, List, Optional
import random
from universe.agents.agent import Agent
from universe.core.genome import Genome

class Universe:
    def __init__(self):
        self.year = 0
        self.tick = 0
        self.agents: Dict[str, Agent] = {}
        self.event_log: List[str] = []
        self.next_id = 1

    def _new_id(self) -> str:
        agent_id = f"{self.next_id:03d}"
        self.next_id += 1
        return agent_id

    def generate_name(self, sex: str) -> str:
        vowels = "aeiouy"
        consonants = "bcdfghjklmnpqrstvwxz"

        def syllable():
            patterns = [
                random.choice(consonants) + random.choice(vowels),
                random.choice(consonants) + random.choice(vowels) + random.choice(consonants),
                random.choice(vowels) + random.choice(consonants),
            ]
            return random.choice(patterns)

        length = random.randint(2, 4)
        name = "".join(syllable() for _ in range(length))
        name = name.capitalize()

        if sex == "female" and random.random() < 0.4:
            name += random.choice(["a", "ia", "ra", "elle", "ine"])
        elif sex == "male" and random.random() < 0.3:
            name += random.choice(["on", "ar", "el", "an", "or"])

        return name

    def create_agent(self, name: str = None, sex: str = None, genome: Genome = None, parents: list = None) -> Agent:
        if sex is None:
            sex = random.choice(["male", "female"])
        if name is None:
            name = self.generate_name(sex)
        if genome is None:
            genome = Genome.random_genome()

        agent = Agent(
            id=self._new_id(),
            name=name,
            sex=sex,
            genome=genome,
            parents=parents or [],
            location=(random.randint(0, 19), random.randint(0, 19))
        )
        self.agents[agent.id] = agent
        self.log(f"Born: {agent.name} ({agent.id})")
        return agent

    def genesis(self):
        adam = self.create_agent(name="Adam", sex="male")
        eva = self.create_agent(name="Eva", sex="female")
        self.log("Genesis complete. Two primordial programs exist.")
        return adam, eva

    def reproduce(self, parent1: Agent, parent2: Agent) -> Optional[Agent]:
        if not parent1.alive or not parent2.alive:
            return None
        if parent1.sex == parent2.sex:
            return None
        if parent1.energy < 25 or parent2.energy < 25:
            return None

        child_genome = Genome.crossover(parent1.genome, parent2.genome)
        child_genome = child_genome.mutate(rate=0.18, strength=0.20)

        sex = random.choice(["male", "female"])
        name = self.generate_name(sex)

        child = self.create_agent(
            name=name,
            sex=sex,
            genome=child_genome,
            parents=[parent1.id, parent2.id]
        )

        parent1.children.append(child.id)
        parent2.children.append(child.id)
        parent1.energy -= 18
        parent2.energy -= 18

        self.log(f"Reproduction: {parent1.name} + {parent2.name} → {child.name}")
        return child

    def advance_time(self, ticks: int = 1):
        for _ in range(ticks):
            self.tick += 1
            if self.tick % 24 == 0:
                self.year += 1

            for agent in list(self.agents.values()):
                if not agent.alive:
                    continue

                agent.age += 1

                # Медленное изменение потребностей
                agent.hunger = min(100, agent.hunger + random.uniform(0.15, 0.45))
                agent.thirst = min(100, agent.thirst + random.uniform(0.12, 0.35))
                agent.fatigue = min(100, agent.fatigue + random.uniform(0.10, 0.30))

                # Очень медленная потеря энергии
                agent.energy = max(0, agent.energy - random.uniform(0.05, 0.18))

                # Естественное восстановление
                if agent.hunger > 40 and random.random() < 0.35:
                    agent.hunger = max(0, agent.hunger - random.uniform(8, 18))
                    agent.energy = min(100, agent.energy + random.uniform(4, 12))

                if agent.thirst > 35 and random.random() < 0.40:
                    agent.thirst = max(0, agent.thirst - random.uniform(7, 15))
                    agent.energy = min(100, agent.energy + random.uniform(3, 9))

                if agent.fatigue > 50 and random.random() < 0.30:
                    agent.fatigue = max(0, agent.fatigue - random.uniform(10, 25))
                    agent.energy = min(100, agent.energy + random.uniform(5, 14))

                # Смерть только при критических значениях
                if agent.energy <= 0 or agent.hunger >= 98 or agent.health <= 0:
                    agent.alive = False
                    self.log(f"Death: {agent.name} ({agent.id})")

            # Размножение
            living = [a for a in self.agents.values() if a.alive]
            males = [a for a in living if a.sex == "male" and a.age > 12]
            females = [a for a in living if a.sex == "female" and a.age > 12]

            if males and females and random.random() < 0.22:
                father = random.choice(males)
                mother = random.choice(females)
                self.reproduce(father, mother)

    def view_agent(self, identifier: str):
        agent = None
        for a in self.agents.values():
            if a.id == identifier or a.name.lower() == identifier.lower():
                agent = a
                break

        if agent is None:
            print(f"Существо '{identifier}' не найдено.")
            return

        print("\n" + "=" * 55)
        print(f"ПРОГРАММА: {agent.name} ({agent.id})")
        print("=" * 55)
        print(f"Вид:          {agent.species}")
        print(f"Пол:          {agent.sex}")
        print(f"Возраст:      {agent.age}")
        print(f"Жив:          {agent.alive}")
        print(f"Энергия:      {agent.energy:.1f}")
        print(f"Здоровье:     {agent.health:.1f}")
        print(f"Голод:        {agent.hunger:.1f}")
        print(f"Жажда:        {agent.thirst:.1f}")
        print(f"Усталость:    {agent.fatigue:.1f}")
        print(f"Локация:      {agent.location}")
        print(f"Родители:     {agent.parents or 'Нет'}")
        print(f"Дети:         {agent.children or 'Нет'}")
        print("-" * 55)
        print("ГЕНЫ:")
        for gene, value in sorted(agent.genome.genes.items()):
            print(f"  {gene:20}: {value:5.1f}")
        print("-" * 55)
        print("ХАРАКТЕРИСТИКИ:")
        for key, value in sorted(agent.characteristics.items()):
            print(f"  {key:20}: {value}")
        print("=" * 55 + "\n")

    def status(self, detailed: bool = False):
        living = [a for a in self.agents.values() if a.alive]
        print("\n" + "=" * 60)
        print("NICS SELF-EVOLVING UNIVERSE")
        print("=" * 60)
        print(f"Year:              {self.year}")
        print(f"Tick:              {self.tick}")
        print(f"Living population: {len(living)}")
        print(f"Total ever born:   {len(self.agents)}")
        print("-" * 60)

        for agent in living:
            line = (
                f"[{agent.id}] {agent.name:14} | {agent.sex:6} | Age: {agent.age:3} | "
                f"Energy: {agent.energy:5.1f}"
            )
            print(line)
            if detailed:
                print(f"         Parents:  {agent.parents or 'None'}")
                print(f"         Children: {agent.children or 'None'}")

        print("=" * 60 + "\n")

    def log(self, message: str):
        entry = f"[Year {self.year:04d} | Tick {self.tick:05d}] {message}"
        self.event_log.append(entry)
        print(entry)