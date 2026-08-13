from universe.core.namegen import generate_era_name

SEED_ERAS = [
    (0, "Доисторическая эпоха"),
    (3, "Эпоха первого огня"),
    (7, "Эпоха каменных орудий"),
    (12, "Эпоха земледелия"),
    (18, "Бронзовый век"),
    (26, "Железный век"),
    (36, "Эпоха ранних государств"),
    (48, "Классическая эпоха"),
    (64, "Эпоха философии и науки"),
    (84, "Эпоха великих открытий"),
]

_STEP_BEYOND_SEED = 20


def era_for(total_discoveries: int) -> str:
    current = SEED_ERAS[0][1]
    for threshold, name in SEED_ERAS:
        if total_discoveries >= threshold:
            current = name
        else:
            break

    last_threshold = SEED_ERAS[-1][0]
    if total_discoveries > last_threshold:
        index = (total_discoveries - last_threshold) // _STEP_BEYOND_SEED
        if index > 0:
            current = generate_era_name(index)

    return current
