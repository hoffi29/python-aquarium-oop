import random
import time

class AquariumObjekt:
    """Basisklasse für alles, was im Aquarium lebt."""
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y

    def aktualisieren(self):
        """Wird in jedem Simulationsschritt aufgerufen."""
        pass


class Alge(AquariumObjekt):
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)
        self.hoehe = 1

    def aktualisieren(self):
        # Algen wachsen gelegentlich
        if random.random() < 0.3:
            self.hoehe += 1
            print(f"🌿 {self.name} ist gewachsen (Höhe: {self.hoehe}).")


class Fisch(AquariumObjekt):
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)
        self.lebendig = True

    def schwimmen(self):
        # Zufällige Bewegung im Raster (0-10)
        self.x = max(0, min(10, self.x + random.choice([-1, 0, 1])))
        self.y = max(0, min(10, self.y + random.choice([-1, 0, 1])))

    def aktualisieren(self):
        if self.lebendig:
            self.schwimmen()
            print(f"🐟 {self.name} schwimmt zu Pos ({self.x}, {self.y}).")


class Hai(Fisch):
    """Der Hai erbt von Fisch, hat aber ein eigenes Jagdverhalten."""
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)
        self.magen = 0

    def fressen(self, fische: list[Fisch]):
        # Prüfen, ob ein Fisch an der gleichen Position ist
        for fisch in fische:
            if fisch.lebendig and fisch.x == self.x and fisch.y == self.y:
                fisch.lebendig = False
                self.magen += 1
                print(f"🦈 CHOMP! {self.name} hat {fisch.name} gefressen!")
                break

    def aktualisieren_mit_kontext(self, fische: list[Fisch]):
        if self.lebendig:
            self.schwimmen()
            print(f"🦈 {self.name} patrouilliert bei Pos ({self.x}, {self.y}).")
            self.fressen(fische)


class Aquarium:
    """Die Hauptklasse, die alle Objekte verwaltet."""
    def __init__(self):
        self.bewohner: list[AquariumObjekt] = []

    def hinzufuegen(self, objekt: AquariumObjekt):
        self.bewohner.append(objekt)

    def simulationsschritt(self):
        print("\n--- Neuer Tag im Aquarium ---")
        
        # Fische für den Hai herausfiltern
        fische = [b for b in self.bewohner if isinstance(b, Fisch) and not isinstance(b, Hai)]

        for bewohner in self.bewohner:
            if isinstance(bewohner, Hai):
                bewohner.aktualisieren_mit_kontext(fische)
            else:
                bewohner.aktualisieren()

        # Tote Fische aufräumen
        self.bewohner = [b for b in self.bewohner if getattr(b, 'lebendig', True)]


# --- Testlauf ---
if __name__ == "__main__":
    mein_aquarium = Aquarium()
    
    # Bewohner hinzufügen
    mein_aquarium.hinzufuegen(Fisch("Nemo", 2, 3))
    mein_aquarium.hinzufuegen(Fisch("Dorie", 5, 5))
    mein_aquarium.hinzufuegen(Alge("Kelpi", 0, 0))
    mein_aquarium.hinzufuegen(Hai("Bruce", 2, 2))

    # 5 Simulationsschritte durchlaufen
    for _ in range(5):
        mein_aquarium.simulationsschritt()
        time.sleep(1)