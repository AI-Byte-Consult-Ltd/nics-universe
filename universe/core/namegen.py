"""Процедурная генерация имён, названий и понятий.

Никаких готовых списков имён — только фонемные банки, из которых
слоги собираются комбинаторно. Каждое общество получает свой
"языковой стиль" (свой набор согласных/гласных/окончаний), поэтому
культуры звучат по-разному и это же используется как один из
факторов при слиянии обществ.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import random

_ALL_CONSONANTS = list("bcdfghjklmnpqrstvwxz") + [
    "th", "sh", "kh", "zh", "dr", "tr", "kr", "br", "gr", "st", "sk", "vl", "ng", "rh"
]
_ALL_VOWELS = list("aeiouy") + ["ei", "ai", "ou", "ia", "ua", "oa", "ee"]

_MALE_ENDINGS = ["", "on", "ar", "us", "en", "or", "an", "eth", "ir", "ok", "ash"]
_FEMALE_ENDINGS = ["", "a", "ia", "el", "ith", "ra", "wen", "isa", "yn", "eya", "una"]
_NEUTRAL_ENDINGS = ["", "ix", "on", "ei", "ar", "um", "esh", "in"]

_PLACE_SUFFIXES = [
    "dor", "mark", "heim", "gard", "wick", "moor", "vale", "shire", "thorn",
    "haven", "reach", "hollow", "crest", "fen", "wynd", "stead",
]


@dataclass
class LanguageStyle:
    consonants: List[str]
    vowels: List[str]
    male_endings: List[str]
    female_endings: List[str]
    neutral_endings: List[str]

    @staticmethod
    def random_style() -> "LanguageStyle":
        return LanguageStyle(
            consonants=random.sample(_ALL_CONSONANTS, k=random.randint(7, 11)),
            vowels=random.sample(_ALL_VOWELS, k=random.randint(4, 7)),
            male_endings=random.sample(_MALE_ENDINGS, k=random.randint(4, 6)),
            female_endings=random.sample(_FEMALE_ENDINGS, k=random.randint(4, 6)),
            neutral_endings=random.sample(_NEUTRAL_ENDINGS, k=random.randint(3, 5)),
        )

    def to_dict(self) -> dict:
        return {
            "consonants": self.consonants,
            "vowels": self.vowels,
            "male_endings": self.male_endings,
            "female_endings": self.female_endings,
            "neutral_endings": self.neutral_endings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LanguageStyle":
        return cls(
            consonants=list(d["consonants"]),
            vowels=list(d["vowels"]),
            male_endings=list(d["male_endings"]),
            female_endings=list(d["female_endings"]),
            neutral_endings=list(d["neutral_endings"]),
        )


def _syllable(style: LanguageStyle) -> str:
    roll = random.random()
    if roll < 0.55:
        return random.choice(style.consonants) + random.choice(style.vowels)
    if roll < 0.85:
        return random.choice(style.consonants) + random.choice(style.vowels) + random.choice(style.consonants)
    return random.choice(style.vowels) + random.choice(style.consonants)


def generate_name(style: LanguageStyle, sex: Optional[str] = None) -> str:
    length = random.randint(2, 3)
    core = "".join(_syllable(style) for _ in range(length))

    if sex == "male":
        ending = random.choice(style.male_endings)
    elif sex == "female":
        ending = random.choice(style.female_endings)
    else:
        ending = random.choice(style.neutral_endings)

    name = (core + ending).capitalize()
    return name


_DEFAULT_STYLE = LanguageStyle(
    consonants=list("bkdgtmnszrlv"),
    vowels=list("aeiou"),
    male_endings=_MALE_ENDINGS,
    female_endings=_FEMALE_ENDINGS,
    neutral_endings=_NEUTRAL_ENDINGS,
)


def generate_place_name() -> str:
    core = "".join(_syllable(_DEFAULT_STYLE) for _ in range(random.randint(1, 2)))
    return (core + random.choice(_PLACE_SUFFIXES)).capitalize()


def generate_species_name() -> str:
    core = "".join(_syllable(_DEFAULT_STYLE) for _ in range(random.randint(2, 3)))
    suffix = random.choice(["", "us", "ax", "ok", "yn", "or", "eth"])
    return (core + suffix).capitalize()


_ERA_ADJECTIVES = [
    "Пробуждённая", "Стальная", "Забытая", "Сияющая", "Немая", "Разомкнутая",
    "Бескрайняя", "Тайная", "Обновлённая", "Расколотая", "Второе", "Иная",
    "Позднейшая", "Глубинная", "Внезапная",
]
_ERA_NOUNS = [
    "эпоха разума", "эпоха машин", "эпоха странствий", "эпоха покоя",
    "эпоха огня", "эпоха звёзд", "эпоха слова", "эпоха теней",
    "эпоха роста", "эпоха пределов", "эпоха связей", "эпоха пустоты",
]


def generate_era_name(index: int) -> str:
    rng = random.Random(index * 7919 + 17)
    adj = rng.choice(_ERA_ADJECTIVES)
    noun = rng.choice(_ERA_NOUNS)
    return f"{adj} {noun} (виток {index})"


_MERGE_REASONS = [
    "торговый союз и обмен ремёслами",
    "родство через смешанные браки",
    "совместная оборона от опасностей",
    "культурный обмен и общие праздники",
    "договор о разделе территорий",
    "объединение вокруг общего святилища",
    "союз ради общих исследований",
    "голод, заставивший объединить запасы",
]


def generate_merge_reason() -> str:
    return random.choice(_MERGE_REASONS)


_ADJECTIVE_EXCEPTIONS = {
    "потусторонний": ("потусторонний", "потусторонняя", "потустороннее"),
}
_HUSHING_CONSONANTS = ("ч", "щ", "ш", "ж")


def inflect_adjective(base: str) -> tuple:
    """Возвращает (муж., жен., ср.) формы прилагательного для согласования с родом."""
    if base in _ADJECTIVE_EXCEPTIONS:
        return _ADJECTIVE_EXCEPTIONS[base]

    if base.endswith("ий") and len(base) >= 3 and base[-3] in _HUSHING_CONSONANTS:
        stem = base[:-2]
        return base, stem + "ая", stem + "ее"

    if base.endswith(("ый", "ой", "ий")):
        stem = base[:-2]
        return base, stem + "ая", stem + "ое"

    return base, base, base
