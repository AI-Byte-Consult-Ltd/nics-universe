from universe.world.universe import Universe

def main():
    print("NICS SELF-EVOLVING UNIVERSE")
    print("===========================\n")

    universe = Universe()
    universe.genesis()
    universe.status()

    print("Запускаем саморазвитие...")
    print("Можно остановить в любой момент Ctrl+C\n")

    try:
        while True:
            universe.advance_time(50)          # каждые 50 тиков показываем статус
            universe.status()
            
            living = [a for a in universe.agents.values() if a.alive]
            if not living:
                print("Вселенная опустела.")
                break
                
    except KeyboardInterrupt:
        print("\n\nСимуляция остановлена пользователем.")
        universe.status(detailed=True)

    print("\nGenesis + Evolution finished.")

if __name__ == "__main__":
    main()