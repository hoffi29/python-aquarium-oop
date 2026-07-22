import pygame
import random
import sys
import os

# --- Einstellungen ---
BREITE = 1000
HOEHE = 700
FPS = 60

WASSER = (20, 40, 70)


class Boid(pygame.sprite.Sprite):
    def __init__(self, x, y, frames: list[pygame.Surface]):
        super().__init__()
        
        # Spritesheet-Frames
        self.frames = frames
        self.current_frame = 0.0
        self.animation_speed = 0.12 # Sanfte Flossenbewegung

        # Position und Bewegung
        self.position = pygame.math.Vector2(x, y)
        self.geschwindigkeit = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.geschwindigkeit.length() == 0:
            self.geschwindigkeit = pygame.math.Vector2(0.5, 0)
        self.beschleunigung = pygame.math.Vector2(0, 0)

        # Schwarm- & Verhalten-Parameter
        self.max_geschwindigkeit = 1.3
        self.max_kraft = 0.015       # Weiche, lange Kurven
        self.wahrnehmungs_radius = 80.0
        self.reibung = 0.985

        # Spontaner Wanderdrang (Zufallswinkel für spontane Richtungswechsel)
        self.wander_winkel = random.uniform(0, 360)

        self.update_intervall = random.randint(3, 7)
        self.frame_zaehler = random.randint(0, self.update_intervall)

        # Erstes Bild setzen
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def steuere_kraft(self, ziel: pygame.math.Vector2) -> pygame.math.Vector2:
        gewuenscht = ziel - self.position
        if gewuenscht.length() > 0:
            gewuenscht = gewuenscht.normalize() * self.max_geschwindigkeit
            kraft = gewuenscht - self.geschwindigkeit
            if kraft.length() > self.max_kraft:
                kraft.scale_to_length(self.max_kraft)
            return kraft
        return pygame.math.Vector2(0, 0)

    # --- Spontanes Dahingleiten / Erkunden ---
    def wandern(self) -> pygame.math.Vector2:
        """Erzeugt eine kleine, zufällige Kraft für spontane Richtungswechsel."""
        # Winkel sanft verändern
        self.wander_winkel += random.uniform(-15, 15)
        
        # Vektor leicht vor dem Fisch berechnen und abwinkeln
        wander_vektor = pygame.math.Vector2(1, 0).rotate(self.wander_winkel) * 0.5
        return wander_vektor * self.max_kraft

    # --- Boid Regeln ---

    def separation(self, boids: list['Boid']) -> pygame.math.Vector2:
        lenkung = pygame.math.Vector2(0, 0)
        anzahl = 0
        gewuenschter_abstand = 50.0  # Größerer Abstand, da die Fische jetzt größer sind!

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
        coh = self.cohesion(boids) * 0.3      # Sehr sanfter Zusammenhalt (viel Freiraum)
        rand = self.rand_vermeidung() * 1.5
        spontan = self.wandern() * 1.2         # Spontane Richtungswechsel / Entdecken

        self.beschleunigung += sep + ali + coh + rand + spontan

    def update(self, boids: list['Boid']):
        self.frame_zaehler += 1
        if self.frame_zaehler >= self.update_intervall:
            self.frame_zaehler = 0
            self.flocke(boids)

        # Physik
        self.geschwindigkeit += self.beschleunigung
        self.geschwindigkeit *= self.reibung
        if self.geschwindigkeit.length() > self.max_geschwindigkeit:
            self.geschwindigkeit.scale_to_length(self.max_geschwindigkeit)

        self.position += self.geschwindigkeit
        self.beschleunigung *= 0

        # --- ANIMATION & ROTATION ---
        tempo = self.geschwindigkeit.length()
        if tempo > 0.05:
            self.current_frame += self.animation_speed * (tempo / self.max_geschwindigkeit)
            if self.current_frame >= len(self.frames):
                self.current_frame = 0

            basis_bild = self.frames[int(self.current_frame)]

            # Winkel berechnen & Rotation anwenden
            winkel = self.geschwindigkeit.angle_to(pygame.math.Vector2(1, 0))
            self.image = pygame.transform.rotate(basis_bild, winkel)
        
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))


def lade_spritesheet(pfad: str, spalten: int = 2, zeilen: int = 2, ziel_groesse: tuple = (90, 70)) -> list[pygame.Surface]:
    """Lädt das Spritesheet, dreht die Bilder richtig herum und skaliert sie größer."""
    sheet = pygame.image.load(pfad).convert_alpha()
    sheet_b, sheet_h = sheet.get_size()

    frame_b = sheet_b // spalten
    frame_h = sheet_h // zeilen

    frames = []
    for z in range(zeilen):
        for s in range(spalten):
            rect = pygame.Rect(s * frame_b, z * frame_h, frame_b, frame_h)
            sub_surface = sheet.subsurface(rect)
            
            # WICHTIG: Bild horizontal spiegeln (True), damit der Fisch vorwärts schwimmt!
            richtig_rum = pygame.transform.flip(sub_surface, True, False)
            
            # Größer skalieren
            skaliert = pygame.transform.scale(richtig_rum, ziel_groesse)
            frames.append(skaliert)

    return frames


# --- Hauptprogramm ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Entspannter Clownfisch-Schwarm")
    clock = pygame.time.Clock()

    pfad_zu_bild = os.path.join("assets", "normalswim.png")
    
    try:
        # Fische deutlich größer gemacht: 90x70 Pixel (vorher 45x35)
        clownfisch_frames = lade_spritesheet(pfad_zu_bild, spalten=2, zeilen=2, ziel_groesse=(90, 70))
    except Exception as e:
        print(f"Fehler beim Laden von {pfad_zu_bild}: {e}")
        pygame.quit()
        sys.exit()

    fisch_gruppe = pygame.sprite.Group()
    fische_liste = []

    # Nur noch 15 Fische (statt 40)
    for _ in range(15):
        fisch = Boid(
            x=random.randint(150, BREITE - 150),
            y=random.randint(150, HOEHE - 150),
            frames=clownfisch_frames
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