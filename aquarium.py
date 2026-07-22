import pygame
import random
import sys

# --- Einstellungen ---
BREITE = 1000
HOEHE = 700
FPS = 60

# Farben
WASSER = (20, 40, 70)
FISCH_FARBE = (255, 180, 50)
FISCH_KOPF = (255, 230, 150)


class Boid(pygame.sprite.Sprite):
    """Ein einzelner Fisch im Schwarm, gesteuert durch Boid-Regeln."""
    def __init__(self, x, y):
        super().__init__()
        
        # Position und Bewegung als Vektoren
        self.position = pygame.math.Vector2(x, y)
        self.geschwindigkeit = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        if self.geschwindigkeit.length() == 0:
            self.geschwindigkeit = pygame.math.Vector2(1, 1)
        self.beschleunigung = pygame.math.Vector2(0, 0)

        # Schwarm-Parameter
        self.max_geschwindigkeit = 4.0   # Höchstgeschwindigkeit
        self.max_kraft = 0.1             # Wie schnell der Fisch wenden kann
        self.wahrnehmungs_radius = 60.0  # Wie weit der Fisch seine Nachbarn sieht

        # Aussehen (Ein kleiner Pfeil/Dreieck als Fisch)
        self.image_original = pygame.Surface((16, 10), pygame.SRCALPHA)
        pygame.draw.polygon(self.image_original, FISCH_FARBE, [(0, 0), (16, 5), (0, 10)])
        pygame.draw.circle(self.image_original, FISCH_KOPF, (12, 5), 2)
        
        self.image = self.image_original
        self.rect = self.image.get_rect(center=(x, y))

    def steuere_kraft(self, ziel: pygame.math.Vector2) -> pygame.math.Vector2:
        """Berechnet die Lenkkraft in Richtung eines Zielvektors."""
        gewuenscht = ziel - self.position
        if gewuenscht.length() > 0:
            gewuenscht = gewuenscht.normalize() * self.max_geschwindigkeit
            kraft = gewuenscht - self.geschwindigkeit
            if kraft.length() > self.max_kraft:
                kraft.scale_to_length(self.max_kraft)
            return kraft
        return pygame.math.Vector2(0, 0)

    # --- Die 3 Boid-Regeln ---

    def separation(self, boids: list['Boid']) -> pygame.math.Vector2:
        lenkung = pygame.math.Vector2(0, 0)
        anzahl = 0
        gewuenschter_abstand = 25.0

        for anderer in boids:
            distanz = self.position.distance_to(anderer.position)
            if 0 < distanz < gewuenschter_abstand:
                diff = self.position - anderer.position
                diff /= (distanz * distanz) # Je näher, desto stärkere Abstoßung
                lenkung += diff
                anzahl += 1

        if anzahl > 0:
            lenkung /= anzahl
            if lenkung.length() > 0:
                lenkung = lenkung.normalize() * self.max_geschwindigkeit
                kraft = lenkung - self.geschwindigkeit
                if kraft.length() > self.max_kraft:
                    kraft.scale_to_length(self.max_kraft)
                return kraft
        return pygame.math.Vector2(0, 0)

    def alignment(self, boids: list['Boid']) -> pygame.math.Vector2:
        durchschnitts_geschw = pygame.math.Vector2(0, 0)
        anzahl = 0

        for anderer in boids:
            distanz = self.position.distance_to(anderer.position)
            if 0 < distanz < self.wahrnehmungs_radius:
                durchschnitts_geschw += anderer.geschwindigkeit
                anzahl += 1

        if anzahl > 0:
            durchschnitts_geschw /= anzahl
            if durchschnitts_geschw.length() > 0:
                durchschnitts_geschw = durchschnitts_geschw.normalize() * self.max_geschwindigkeit
                kraft = durchschnitts_geschw - self.geschwindigkeit
                if kraft.length() > self.max_kraft:
                    kraft.scale_to_length(self.max_kraft)
                return kraft
        return pygame.math.Vector2(0, 0)

    def cohesion(self, boids: list['Boid']) -> pygame.math.Vector2:
        zentrum = pygame.math.Vector2(0, 0)
        anzahl = 0

        for anderer in boids:
            distanz = self.position.distance_to(anderer.position)
            if 0 < distanz < self.wahrnehmungs_radius:
                zentrum += anderer.position
                anzahl += 1

        if anzahl > 0:
            zentrum /= anzahl
            return self.steuere_kraft(zentrum)
        return pygame.math.Vector2(0, 0)

    def rand_vermeidung(self) -> pygame.math.Vector2:
        """Sanftes Umkehren, wenn der Fisch dem Bildschirmrand zu nahe kommt."""
        puffer = 80
        kraft = pygame.math.Vector2(0, 0)

        if self.position.x < puffer:
            kraft.x = self.max_geschwindigkeit
        elif self.position.x > BREITE - puffer:
            kraft.x = -self.max_geschwindigkeit

        if self.position.y < puffer:
            kraft.y = self.max_geschwindigkeit
        elif self.position.y > HOEHE - puffer:
            kraft.y = -self.max_geschwindigkeit

        if kraft.length() > 0:
            kraft = kraft.normalize() * self.max_geschwindigkeit - self.geschwindigkeit
            if kraft.length() > self.max_kraft:
                kraft.scale_to_length(self.max_kraft)

        return kraft

    def flocke(self, boids: list['Boid']):
        """Kombiniert alle Kräfte mit Gewichtung."""
        sep = self.separation(boids) * 1.5   # Abstoßung leicht priorisieren
        ali = self.alignment(boids) * 1.0
        coh = self.cohesion(boids) * 1.0
        rand = self.rand_vermeidung() * 2.0  # Ränder stark meiden

        self.beschleunigung += sep + ali + coh + rand

    def update(self, boids: list['Boid']):
        # Schwarmkräfte berechnen
        self.flocke(boids)

        # Physik anwenden
        self.geschwindigkeit += self.beschleunigung
        if self.geschwindigkeit.length() > self.max_geschwindigkeit:
            self.geschwindigkeit.scale_to_length(self.max_geschwindigkeit)
        
        self.position += self.geschwindigkeit
        self.beschleunigung *= 0 # Beschleunigung für den nächsten Frame zurücksetzen

        # Grafik an Bewegung anpassen (Rotation in Schwimmrichtung)
        self.rect.center = (round(self.position.x), round(self.position.y))
        winkel = self.geschwindigkeit.angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.image_original, winkel)
        self.rect = self.image.get_rect(center=self.rect.center)


# --- Hauptprogramm ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Fischschwarm Simulator (Boids)")
    clock = pygame.time.Clock()

    # Schwarm erzeugen (z. B. 60 Fische)
    fisch_gruppe = pygame.sprite.Group()
    fische_liste = []

    for _ in range(60):
        fisch = Boid(random.randint(100, BREITE - 100), random.randint(100, HOEHE - 100))
        fisch_gruppe.add(fisch)
        fische_liste.append(fisch)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Klick mit der Maus spaltet/erschreckt den Schwarm
            elif event.type == pygame.MOUSEBUTTONDOWN:
                maus_pos = pygame.math.Vector2(pygame.mouse.get_pos())
                for fisch in fische_liste:
                    if fisch.position.distance_to(maus_pos) < 150:
                        # Drückt Fische von der Maus weg
                        flucht = (fisch.position - maus_pos).normalize() * 8.0
                        fisch.geschwindigkeit = flucht

        # Alle Boids aktualisieren
        for fisch in fische_liste:
            fisch.update(fische_liste)

        # Zeichnen
        screen.fill(WASSER)
        fisch_gruppe.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()