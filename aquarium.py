import pygame
import random
import sys
import os
import traceback

# --- Einstellungen ---
BREITE = 1000
HOEHE = 700
FPS = 60

WASSER = (20, 40, 70)


class Boid(pygame.sprite.Sprite):
    def __init__(self, x, y, anims: dict[str, list[pygame.Surface]]):
        super().__init__()
        
        # Animations-Zustände
        self.anims = anims
        self.zustand = "normal"
        self.frames = self.anims[self.zustand]
        
        self.current_frame = 0.0
        self.animation_speed = 0.12

        # Position und Bewegung
        self.position = pygame.math.Vector2(x, y)
        self.geschwindigkeit = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.geschwindigkeit.length() == 0:
            self.geschwindigkeit = pygame.math.Vector2(0.5, 0)
        self.beschleunigung = pygame.math.Vector2(0, 0)

        # Schwarm- & Verhalten-Parameter
        self.max_geschwindigkeit = 1.3
        self.max_kraft = 0.015
        self.wahrnehmungs_radius = 80.0
        self.reibung = 0.985

        self.wander_winkel = random.uniform(0, 360)

        self.update_intervall = random.randint(3, 7)
        self.frame_zaehler = random.randint(0, self.update_intervall)

        # Erstes Bild setzen
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def set_zustand(self, neuer_zustand: str):
        """Wechselt den Animationszustand und setzt das Frame zurück."""
        if neuer_zustand in self.anims and self.zustand != neuer_zustand:
            self.zustand = neuer_zustand
            self.frames = self.anims[neuer_zustand]
            self.current_frame = 0.0

    def steuere_kraft(self, ziel: pygame.math.Vector2) -> pygame.math.Vector2:
        gewuenscht = ziel - self.position
        if gewuenscht.length() > 0:
            gewuenscht = gewuenscht.normalize() * self.max_geschwindigkeit
            kraft = gewuenscht - self.geschwindigkeit
            if kraft.length() > self.max_kraft:
                kraft.scale_to_length(self.max_kraft)
            return kraft
        return pygame.math.Vector2(0, 0)

    def wandern(self) -> pygame.math.Vector2:
        self.wander_winkel += random.uniform(-15, 15)
        wander_vektor = pygame.math.Vector2(1, 0).rotate(self.wander_winkel) * 0.5
        return wander_vektor * self.max_kraft

    def separation(self, boids: list['Boid']) -> pygame.math.Vector2:
        lenkung = pygame.math.Vector2(0, 0)
        anzahl = 0
        gewuenschter_abstand = 50.0

        for anderer in boids:
            distanz = self.position.distance_to(anderer.position)
            if 0 < distanz < gewuenschter_abstand:
                diff = self.position - anderer.position
                diff /= (distanz * distanz)
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
        puffer = 120
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
        sep = self.separation(boids) * 1.8
        ali = self.alignment(boids) * 0.6
        coh = self.cohesion(boids) * 0.3
        rand = self.rand_vermeidung() * 1.5
        spontan = self.wandern() * 1.2

        self.beschleunigung += sep + ali + coh + rand + spontan

    def update(self, boids: list['Boid']):
        self.frame_zaehler += 1
        if self.frame_zaehler >= self.update_intervall:
            self.frame_zaehler = 0
            self.flocke(boids)

        self.geschwindigkeit += self.beschleunigung
        self.geschwindigkeit *= self.reibung
        if self.geschwindigkeit.length() > self.max_geschwindigkeit:
            self.geschwindigkeit.scale_to_length(self.max_geschwindigkeit)

        self.position += self.geschwindigkeit
        self.beschleunigung *= 0

        tempo = self.geschwindigkeit.length()

        if self.zustand in ["schnapp", "schock"]:
            if int(self.current_frame) >= len(self.frames) - 1:
                self.set_zustand("normal")
        else:
            if random.random() < 0.001:
                self.set_zustand("schnapp")

        if tempo > 0.05:
            speed_mult = 2.0 if self.zustand in ["schnapp", "schock"] else (tempo / self.max_geschwindigkeit)
            self.current_frame += self.animation_speed * speed_mult
            
            if self.current_frame >= len(self.frames):
                self.current_frame = 0.0

            basis_bild = self.frames[int(self.current_frame)]
            winkel = self.geschwindigkeit.angle_to(pygame.math.Vector2(1, 0))
            self.image = pygame.transform.rotate(basis_bild, winkel)
        
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))


def lade_spritesheet(pfad: str, spalten: int, zeilen: int, ziel_groesse: tuple = (90, 70)) -> list[pygame.Surface]:
    sheet = pygame.image.load(pfad).convert_alpha()
    sheet_b, sheet_h = sheet.get_size()

    frame_b = sheet_b // spalten
    frame_h = sheet_h // zeilen

    frames = []
    for z in range(zeilen):
        for s in range(spalten):
            rect = pygame.Rect(s * frame_b, z * frame_h, frame_b, frame_h)
            sub_surface = sheet.subsurface(rect)
            richtig_rum = pygame.transform.flip(sub_surface, True, False)
            skaliert = pygame.transform.scale(richtig_rum, ziel_groesse)
            frames.append(skaliert)

    return frames


def main():
    pygame.init()
    screen = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Interaktives Clownfisch-Aquarium")
    clock = pygame.time.Clock()

    anims = {}

    # 1. Haupt-Animation laden
    normal_pfad = os.path.join("assets", "normalswim.png")
    try:
        anims["normal"] = lade_spritesheet(normal_pfad, spalten=2, zeilen=2, ziel_groesse=(90, 70))
    except Exception as e:
        print(f"KRITISCHER FEHLER beim Laden von {normal_pfad}:")
        traceback.print_exc()
        pygame.quit()
        sys.exit()

    # 2. Schock-Animation laden (mit Fallback)
    schock_pfad = os.path.join("assets", "OuchShocked.png")
    try:
        anims["schock"] = lade_spritesheet(schock_pfad, spalten=3, zeilen=1, ziel_groesse=(90, 70))
    except Exception as e:
        print(f"Hinweis: '{schock_pfad}' konnte nicht geladen werden ({e}). Nutze Fallback.")
        anims["schock"] = anims["normal"]

    # 3. Schnapp-Animation laden (mit Fallback)
    schnapp_pfad = os.path.join("assets", "normaltiltupchomp.png")
    try:
        anims["schnapp"] = lade_spritesheet(schnapp_pfad, spalten=3, zeilen=1, ziel_groesse=(90, 70))
    except Exception as e:
        print(f"Hinweis: '{schnapp_pfad}' konnte nicht geladen werden ({e}). Nutze Fallback.")
        anims["schnapp"] = anims["normal"]

    fisch_gruppe = pygame.sprite.Group()
    fische_liste = []

    for _ in range(15):
        fisch = Boid(
            x=random.randint(150, BREITE - 150),
            y=random.randint(150, HOEHE - 150),
            anims=anims
        )
        fisch_gruppe.add(fisch)
        fische_liste.append(fisch)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                maus_pos = pygame.math.Vector2(pygame.mouse.get_pos())
                for fisch in fische_liste:
                    if fisch.position.distance_to(maus_pos) < 180:
                        flucht = (fisch.position - maus_pos).normalize() * 6.0
                        fisch.geschwindigkeit = flucht
                        fisch.set_zustand("schock")

        # Update
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