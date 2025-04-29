import pygame
import sys
import random

from susceptible import Susceptible
from exposed import Exposed
from believer import Believer
from doubter import Doubter
from recovered import Recovered
from misinformant import Misinformant  # Uncomment if you have this agent

AGENT_TYPES = [
    ("Susceptible", (106, 168, 79)),
    ("Exposed", (255, 255, 0)),
    ("Believer", (204, 0, 0)),
    ("Doubter", (61, 133, 198)),
    ("Recovered", (128, 128, 128)),
    ("Misinformant", (180, 0, 180)),  # Uncomment if you have this agent
]

class Slider:
    def __init__(self, x, y, min_val, max_val, color, label, font):
        self.rect = pygame.Rect(x, y, 200, 8)
        self.handle_rect = pygame.Rect(x, y-8, 12, 24)
        self.min_val = min_val
        self.max_val = max_val
        self.value = min_val
        self.color = color
        self.label = label
        self.font = font
        self.dragging = False

    def draw(self, screen):
        # Draw line
        pygame.draw.rect(screen, self.color, self.rect)
        # Draw handle
        handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * (self.rect.width - 1))
        self.handle_rect.x = handle_x
        pygame.draw.rect(screen, (80, 80, 80), self.handle_rect)
        # Draw label and value
        label_surf = self.font.render(f"{self.label}: {self.value}", True, (0, 0, 0))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 30))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Move handle within slider bounds
            rel_x = min(max(event.pos[0], self.rect.x), self.rect.x + self.rect.width)
            percent = (rel_x - self.rect.x) / self.rect.width
            self.value = int(self.min_val + percent * (self.max_val - self.min_val))

class Game:
    def __init__(self):
        pygame.init()
        self.screen_width = 1140
        self.screen_height = 680
        pygame.display.set_caption("Misinformation Spread Simulation")
        gameIcon = pygame.image.load('Images/running_down_1.png')
        pygame.display.set_icon(gameIcon)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.susceptible_group = pygame.sprite.Group()
        self.exposed_group = pygame.sprite.Group()
        self.believer_group = pygame.sprite.Group()
        self.doubter_group = pygame.sprite.Group()
        self.recovered_group = pygame.sprite.Group()
        self.misinformant_group = pygame.sprite.Group()  # Uncomment if you have this agent

        # Agent counts
        self.susceptible_count = 0
        self.exposed_count = 0
        self.believer_count = 0
        self.doubter_count = 0
        self.recovered_count = 0
        self.misinformant_count = 0

        # Initialize button click flags
        self.add_susceptible = False
        self.add_believer = False
        self.add_doubter = False
        self.add_misinformant = False

        self.point_count = 0
        self.spawn = pygame.Rect(self.screen_width - 1140, self.screen_height - 680, 920, 575)

    def setup_screen(self):
        font = pygame.font.SysFont('Consolas', 32)
        sliders = []
        y = 120
        for name, color in AGENT_TYPES:
            sliders.append(Slider(200, y, 0, 30, color, name, font))
            y += 80

        start_button = pygame.Rect(500, y + 50, 200, 60)
        start_button_text = font.render("START", True, (255,255,255))
        running = True
        while running:
            self.screen.fill((240, 240, 240))
            title = pygame.font.SysFont('Consolas', 44).render("Set Initial Agent Counts", True, (30, 30, 30))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 40))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                for slider in sliders:
                    slider.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and start_button.collidepoint(event.pos):
                    running = False
            for slider in sliders:
                slider.draw(self.screen)
            pygame.draw.rect(self.screen, (0, 120, 0), start_button)
            self.screen.blit(start_button_text, (start_button.x + 60, start_button.y + 10))
            pygame.display.flip()
            self.clock.tick(30)
        # Return chosen counts as a dictionary
        return {slider.label: slider.value for slider in sliders}

    def initialize_agents(self, counts):
        for _ in range(counts.get("Susceptible", 0)):
            new_sus = Susceptible(self.susceptible_group, self.all_sprites)
            self.all_sprites.add(new_sus)
            self.susceptible_group.add(new_sus)
            self.susceptible_count += 1
        for _ in range(counts.get("Exposed", 0)):
            new_exp = Exposed(self.exposed_group, self.all_sprites)
            self.all_sprites.add(new_exp)
            self.exposed_group.add(new_exp)
            self.exposed_count += 1
        for _ in range(counts.get("Believer", 0)):
            new_bel = Believer(self.believer_group, self.all_sprites)
            self.all_sprites.add(new_bel)
            self.believer_group.add(new_bel)
            self.believer_count += 1
        for _ in range(counts.get("Doubter", 0)):
            new_doub = Doubter(self.doubter_group, self.all_sprites)
            self.all_sprites.add(new_doub)
            self.doubter_group.add(new_doub)
            self.doubter_count += 1
        for _ in range(counts.get("Recovered", 0)):
            new_rec = Recovered(self.recovered_group, self.all_sprites)
            self.all_sprites.add(new_rec)
            self.recovered_group.add(new_rec)
            self.recovered_count += 1
        for _ in range(counts.get("Misinformant", 0)):
             new_misinfo = Misinformant(self.misinformant_group, self.all_sprites)
             self.all_sprites.add(new_misinfo)
             self.misinformant_group.add(new_misinfo)
             self.misinformant_count += 1

    def run(self):
        characters = 0
        counts = self.setup_screen()
        self.initialize_agents(counts)
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_susceptible.collidepoint(event.pos):
                        self.add_susceptible = True
                    elif self.button_believer.collidepoint(event.pos):
                        self.add_believer = True
                    elif self.button_doubter.collidepoint(event.pos):
                        self.add_doubter = True
                    elif self.button_quit.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
            
            # Add agents on button press, max 50 total
            if self.add_susceptible and characters < 50:
                new_sus = Susceptible(self.susceptible_group, self.all_sprites)
                self.all_sprites.add(new_sus)
                self.susceptible_group.add(new_sus)
                self.susceptible_count += 1
                self.add_susceptible = False
            
            if self.add_believer and characters < 50:
                new_bel = Believer(self.believer_group, self.all_sprites)
                self.all_sprites.add(new_bel)
                self.believer_group.add(new_bel)
                self.believer_count += 1
                self.add_believer = False
            
            if self.add_doubter and characters < 50:
                new_doub = Doubter(self.doubter_group, self.all_sprites)
                self.all_sprites.add(new_doub)
                self.doubter_group.add(new_doub)
                self.doubter_count += 1
                self.add_doubter = False
            
            # Misinformation spread mechanics here (same as before)
            # Example: Susceptible + Believer -> Exposed
            for sus in self.susceptible_group:
                for bel in self.believer_group:
                    if pygame.sprite.collide_rect(sus, bel):
                        if random.random() < 0.1 * bel.influence:
                            sus.kill()
                            self.susceptible_count -= 1
                            new_exp = Exposed(self.exposed_group, self.all_sprites)
                            new_exp.rect.center = sus.rect.center
                            self.all_sprites.add(new_exp)
                            self.exposed_group.add(new_exp)
                            self.exposed_count += 1
            
            # Exposed -> Believer or Doubter after exposure time
            for exp in self.exposed_group:
                if exp.exposure_time > 180:
                    if random.random() < 0.7 - (0.4 * exp.skepticism):
                        exp.kill()
                        self.exposed_count -= 1
                        new_bel = Believer(self.believer_group, self.all_sprites)
                        new_bel.rect.center = exp.rect.center
                        self.all_sprites.add(new_bel)
                        self.believer_group.add(new_bel)
                        self.believer_count += 1
                    else:
                        exp.kill()
                        self.exposed_count -= 1
                        new_doub = Doubter(self.doubter_group, self.all_sprites)
                        new_doub.rect.center = exp.rect.center
                        self.all_sprites.add(new_doub)
                        self.doubter_group.add(new_doub)
                        self.doubter_count += 1
            for doub in self.doubter_group:
                for bel in self.believer_group:
                    if pygame.sprite.collide_rect(doub, bel):
                        if random.random() < 0.1 * doub.persuasiveness:
                            bel.kill()
                            self.believer_count -= 1
                            new_rec = Recovered(self.recovered_group, self.all_sprites)
                            new_rec.rect.center = bel.rect.center
                            self.all_sprites.add(new_rec)
                            self.recovered_group.add(new_rec)
                            self.recovered_count += 1
            for bel in self.believer_group:
                if random.random() < 0.01:
                    bel.kill()
                    self.believer_count -= 1
                    new_rec = Recovered(self.recovered_group, self.all_sprites)
                    new_rec.rect.center = bel.rect.center
                    self.all_sprites.add(new_rec)
                    self.recovered_group.add(new_rec)
                    self.recovered_count += 1

            characters = (self.susceptible_count + self.exposed_count +
                          self.believer_count + self.doubter_count + self.recovered_count)
            self.point_count = self.doubter_count * 2 + self.recovered_count * 3 - self.believer_count

            # --- Drawing ---
            self.screen.fill((255, 255, 255))
            pygame.draw.rect(self.screen, (253, 253, 253), self.spawn)

            # Drawing agents:
            self.all_sprites.update()
            self.all_sprites.draw(self.screen)
            
            # Interface:
            # Draw the stats box first
            stats_box_rect = pygame.Rect(self.screen_width - 218, self.screen_height - 616, 200, 270)
            pygame.draw.rect(self.screen, (50, 50, 50), stats_box_rect)

            # Points section
            pygame.draw.rect(self.screen, (50, 50, 50), pygame.Rect(self.screen_width - 218, self.screen_height - 616, 200, 270))
            pygame.draw.circle(self.screen, (160, 0, 0), (self.screen_width - 118, self.screen_height - 205), 75)
            points_label = pygame.font.SysFont('Concolas', 35).render('POINTS', True, (40, 40, 40))
            points_text = pygame.font.SysFont('Concolas', 50).render(str(self.believer_count), True, (255, 255, 255))
            self.screen.blit(points_label, (self.screen_width - 165, self.screen_height - 320))
            self.screen.blit(points_text, (self.screen_width - 128, self.screen_height - 220))

            # Draw the counts inside the box, in white
            font32 = pygame.font.SysFont('Concolas', 32)
            font35 = pygame.font.SysFont('Concolas', 35)
            y0 = self.screen_height - 616 + 20
            dy = 40
            def draw_count(label, count, y):
                label_surf = font32.render(label, True, (0, 0, 0))
                count_surf = font35.render(str(count), True, (255, 255, 255))
                self.screen.blit(label_surf, (self.screen_width - 218 + 10, y))
                self.screen.blit(count_surf, (self.screen_width - 218 + 150, y))

            draw_count('S:', self.susceptible_count, y0)
            draw_count('E:', self.exposed_count, y0 + dy)
            draw_count('B:', self.believer_count, y0 + 2*dy)
            draw_count('D:', self.doubter_count, y0 + 3*dy)
            draw_count('R:', self.recovered_count, y0 + 4*dy)
            draw_count('M:', self.misinformant_count, y0 + 5*dy)
        
            pygame.draw.rect(self.screen, (50, 50, 50), pygame.Rect(self.screen_width - 218, self.screen_height - 616, 200, 270))
            points_text = pygame.font.SysFont('Concolas', 50).render(str(self.point_count), True, (255, 255, 255))
            pygame.draw.circle(self.screen, (160, 0, 0), (self.screen_width - 118, self.screen_height - 205), 75)
            self.screen.blit(points_text, (self.screen_width - 128, self.screen_height - 220))
            
            pygame.display.flip()
            self.clock.tick(self.fps)

if __name__ == "__main__":
    game = Game()
    game.run()
