import pygame
import sys
import random
from datetime import datetime, timedelta

from susceptible import Susceptible
from exposed import Exposed
from believer import Believer
from doubter import Doubter
from recovered import Recovered
from misinformant import Misinformant  

AGENT_TYPES = [
    ("Susceptible", (106, 168, 79)),
    ("Exposed", (255, 255, 0)),
    ("Believer", (204, 0, 0)),
    ("Doubter", (61, 133, 198)),
    ("Recovered", (128, 128, 128)),
    ("Misinformant", (180, 0, 180)),
]

class Clock:
    def __init__(self, x, y):
        self.font = pygame.font.SysFont('Consolas', 32)
        self.position = (x, y)
        self.simulation_time = datetime(2023, 1, 1, 18, 30)  # Start at 6
        self.time_multiplier = 6  # 6 game minutes per real second (10 sec/hour)
        self.last_update = pygame.time.get_ticks()
    
    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.last_update
        
        # Convert milliseconds to seconds and apply time multiplier
        game_minutes_elapsed = (elapsed / 1000) * self.time_multiplier
        
        # Advance time (convert to minutes and add)
        self.simulation_time += timedelta(minutes=game_minutes_elapsed)
        self.last_update = current_time

    def draw(self, screen):
        time_str = self.simulation_time.strftime("%H:%M")
        time_surface = self.font.render(time_str, True, (0, 0, 0))
        screen.blit(time_surface, self.position)
    
    def get_hour(self):
        return self.simulation_time.hour
    
    def get_minute(self):
        return self.simulation_time.minute

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
        self.total_misinformed = 0

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
        self.screen_height = 750
        pygame.display.set_caption("Misinformation Spread Simulation")
        gameIcon = pygame.image.load('Images/running_down_1.png')
        pygame.display.set_icon(gameIcon)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()  
        self.fps = 60

        # Create game clock
        self.game_clock = Clock(self.screen_width // 2 - 50, 10)
        
        # Define environment zones
        self.zones = {
            "home": pygame.Rect(0, 100, 380, 650),
            "work": pygame.Rect(380, 100, 380, 650),
            "social": pygame.Rect(760, 100, 380, 650)
        }
        self.total_misinformed = 0

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
        self.spawn = pygame.Rect(self.screen_width - 1140, self.screen_height - 800, 920, 605)

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

    def draw_zones(self):
        # Draw zone backgrounds
        pygame.draw.rect(self.screen, (230, 240, 255), self.zones["home"])  # Light blue for home
        pygame.draw.rect(self.screen, (255, 230, 230), self.zones["work"])  # Light red for work
        pygame.draw.rect(self.screen, (230, 255, 230), self.zones["social"])  # Light green for social
        
        # Draw zone labels
        font = pygame.font.SysFont('Consolas', 24)
        home_label = font.render("HOME", True, (0, 0, 0))
        work_label = font.render("WORK", True, (0, 0, 0))
        social_label = font.render("SOCIAL MEDIA", True, (0, 0, 0))
        
        self.screen.blit(home_label, (self.zones["home"].x + 150, self.zones["home"].y + 10))
        self.screen.blit(work_label, (self.zones["work"].x + 150, self.zones["work"].y + 10))
        self.screen.blit(social_label, (self.zones["social"].x + 120, self.zones["social"].y + 10))
        
        # Draw zone borders
        pygame.draw.rect(self.screen, (0, 0, 0), self.zones["home"], 2)
        pygame.draw.rect(self.screen, (0, 0, 0), self.zones["work"], 2)
        pygame.draw.rect(self.screen, (0, 0, 0), self.zones["social"], 2)
    
    def update_agent_locations(self):
        current_hour = self.game_clock.get_hour()
        current_minute = self.game_clock.get_minute()
        
        if 0 <= current_hour < 6:  # Deep sleep
            return
            
        # Determine target zone based on time
        if 6 <= current_hour < 7:
            target_zone = "home"
        elif 8 <= current_hour < 16:
            target_zone = "work"
        elif (7 <= current_hour < 8) or (19 <= current_hour < 21):  # Social media hours
            # For each agent, decide if they should be in social or home based on time pattern
            for agent in self.all_sprites:
                if not hasattr(agent, 'social_media_timer'):
                    # Initialize timers and random duration if they don't exist
                    agent.social_media_timer = 0
                    agent.in_social = True
                    agent.social_duration = random.randint(20, 30)  # 20-30 mins
                    agent.home_duration = random.randint(5, 15)  # 2-10 minutes at home
                    
                # Update timer based on game time
                agent.social_media_timer += self.game_clock.time_multiplier / 60  # Convert to game minutes
                
                if agent.in_social:
                    if agent.social_media_timer >= agent.social_duration:  # Use random duration
                        agent.in_social = False
                        agent.social_media_timer = 0
                else:
                    if agent.social_media_timer >= agent.home_duration:  # 10 minutes in home
                        agent.in_social = True
                        agent.social_media_timer = 0
                        agent.social_duration = random.randint(20, 30)  # Get new random duration for next session
                
                # Set zone based on current state
                target_zone = "social" if agent.in_social else "home"
                zone = self.zones[target_zone]
                
                # Move agent if not already in correct zone
                if not zone.collidepoint(agent.rect.center):
                    self.move_agent_to_zone(agent, zone)
        else:
            target_zone = "home"
        
        # For non-social-media hours or agents not in social-media pattern
        if not ((7 <= current_hour < 8) or (19 <= current_hour < 21)):
            zone = self.zones[target_zone]
            for agent in self.all_sprites:
                if not zone.collidepoint(agent.rect.center):
                    self.move_agent_to_zone(agent, zone)

    def move_agent_to_zone(self, agent, zone):
        buffer = 20  # Same buffer as in agent class
        new_x = random.randint(zone.left + buffer, zone.right - buffer)
        new_y = random.randint(zone.top + buffer, zone.bottom - buffer)
        agent.rect.center = (new_x, new_y)
        
        # Reset direction to prevent immediate boundary collision
        agent.direction_vector = pygame.math.Vector2(
            random.choice([-0.5, 0.5]),  # Smaller initial values
            random.choice([-0.5, 0.5])
        ).normalize()

    def run(self):
        characters = 0
        counts = self.setup_screen()
        self.initialize_agents(counts)
        running = True

        while running:
            self.game_clock.update()
            current_hour = self.game_clock.get_hour()
            current_minute = self.game_clock.get_minute()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Update agents except during deep sleep (00:00-06:00)
            if not (0 <= current_hour < 6):
                self.all_sprites.update()

                self.update_agent_locations()
                
                # Only process interactions after 7:00 or during wake-up time (6:45-7:00)
                if current_hour >= 7 or (current_hour == 6 and current_minute >= 30):
                    # Susceptible + Believer -> Exposed
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
                        self.total_misinformed = self.believer_count + self.misinformant_count
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
            self.total_misinformed = self.believer_count + self.misinformant_count

            # --- Drawing ---
            self.screen.fill((255, 255, 255))
            self.draw_zones()
            self.game_clock.draw(self.screen)
            
            # Show agents at all times except midnight-6am
            if not (0 <= current_hour < 6):
                # 06:00-06:45 - Show sleeping agents
                if 6 <= current_hour < 7 and current_minute < 30:
                    for agent in self.all_sprites:
                        sleeping_img = pygame.Surface((agent.rect.width, agent.rect.height))
                        sleeping_img.fill((200, 200, 200))  # Light gray
                        sleeping_img.set_alpha(200)  # Slightly transparent
                        self.screen.blit(sleeping_img, agent.rect)
                else:
                    # Normal drawing for active agents
                    self.all_sprites.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(self.fps)

        '''

            # Interface:
            # Draw the stats box first
            stats_box_rect = pygame.Rect(self.screen_width - 218, self.screen_height - 640, 200, 300)
            pygame.draw.rect(self.screen, (50, 50, 50), stats_box_rect)

            # MISINFORMED section
            pygame.draw.circle(self.screen, (160, 0, 0), (self.screen_width - 118, self.screen_height - 205), 75)
            points_label = pygame.font.SysFont('Concolas', 35).render('Misinformed', True, (20, 20, 10))
            points_text = pygame.font.SysFont('Concolas', 50).render(str(self.total_misinformed), True, (255, 255, 255))
            self.screen.blit(points_label, (self.screen_width - 180, self.screen_height - 320))
            self.screen.blit(points_text, (self.screen_width - 128, self.screen_height - 220))

            # Draw the counts inside the box, in white
            font32 = pygame.font.SysFont('Concolas', 32)
            font35 = pygame.font.SysFont('Concolas', 35)

            # Draw COUNT title above agent list
            count_title = pygame.font.SysFont('Concolas', 35).render('COUNT', True, (255, 255, 255))
            self.screen.blit(count_title, (self.screen_width - 180, self.screen_height - 660))

            # Define new function for count drawing
            def draw_count(label, count, y):
                label_surf = font32.render(label, True, (255, 255, 255))
                count_surf = font35.render(str(count), True, (255, 255, 255))
                self.screen.blit(label_surf, (self.screen_width - 190, y))
                self.screen.blit(count_surf, (self.screen_width - 60, y))

            # Call with proper vertical spacing
            draw_count('S:', self.susceptible_count, self.screen_height - 620)
            draw_count('E:', self.exposed_count, self.screen_height - 580)
            draw_count('B:', self.believer_count, self.screen_height - 540)
            draw_count('D:', self.doubter_count, self.screen_height - 500)
            draw_count('R:', self.recovered_count, self.screen_height - 460)
            draw_count('M:', self.misinformant_count, self.screen_height - 420)
        '''

if __name__ == "__main__":
    game = Game()
    game.run()
