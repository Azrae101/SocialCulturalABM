import pygame
import sys
import random
from datetime import datetime, timedelta
import csv

from susceptible import Susceptible
from exposed import Exposed
from believer import Believer
from doubter import Doubter
from recovered import Recovered
from disinformant import Disinformant  

AGENT_TYPES = [
    ("Susceptible", (106, 168, 79)),
    #("Exposed", (255, 255, 0)),
    #("Believer", (204, 0, 0)),
    ("Doubter", (61, 133, 198)),
    #("Recovered", (128, 128, 128)),
    ("Disinformant", (180, 0, 180)),
]

OTHER_FACTORS = [
    ("Emotional Valence", (250, 10, 10)),
    #("Social Influence", (10, 10, 250)),
]

class Clock:
    def __init__(self, x, y):
        self.font = pygame.font.SysFont('Consolas', 32)
        self.position = (x, y)
        self.simulation_time = datetime(2023, 1, 1, 6, 30)  # Start at 6
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
        self.screen_width = 1400
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
            "home": pygame.Rect(0, 100, 380, 650),  # Increased width from 380
            "work": pygame.Rect(390, 100, 380, 650),  # Increased width from 380
            "social": pygame.Rect(780, 100, 380, 650)  # Moved right, kept similar width
        }
        self.total_misinformed = 0

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.susceptible_group = pygame.sprite.Group()
        self.exposed_group = pygame.sprite.Group()
        self.believer_group = pygame.sprite.Group()
        self.doubter_group = pygame.sprite.Group()
        self.recovered_group = pygame.sprite.Group()
        self.disinformant_group = pygame.sprite.Group()  # Uncomment if you have this agent

        # Agent counts
        self.susceptible_count = 0
        self.exposed_count = 0
        self.believer_count = 0
        self.doubter_count = 0
        self.recovered_count = 0
        self.disinformant_count = 0

        # Initialize button click flags
        self.add_susceptible = False
        self.add_believer = False
        self.add_doubter = False
        self.add_disinformant = False

        self.point_count = 0
        self.spawn = pygame.Rect(self.screen_width - 1140, self.screen_height - 800, 920, 605)

    def setup_screen(self):
        font = pygame.font.SysFont('Consolas', 32)
        sliders = []
        y = 120
        for name, color in AGENT_TYPES:
            sliders.append(Slider(200, y, 0, 30, color, name, font))
            y += 80
        
        for name, color in OTHER_FACTORS:
            sliders.append(Slider(200, y, 0, 10, color, name, font))
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
        for _ in range(counts.get("Disinformant", 0)):
             new_misinfo = Disinformant(self.disinformant_group, self.all_sprites)
             self.all_sprites.add(new_misinfo)
             self.disinformant_group.add(new_misinfo)
             self.disinformant_count += 1

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
    
    def enforce_zone_boundaries(self, agent):
        """Keep agent within their current zone boundaries"""
        current_zone = None
        
        # Determine which zone the agent is in
        for zone_name, zone_rect in self.zones.items():
            if zone_rect.collidepoint(agent.rect.center):
                current_zone = zone_rect
                break
        
        if current_zone:
            # Keep agent within zone boundaries with some padding
            padding = 10  # Small buffer from edges
            agent.rect.left = max(agent.rect.left, current_zone.left + padding)
            agent.rect.right = min(agent.rect.right, current_zone.right - padding)
            agent.rect.top = max(agent.rect.top, current_zone.top + padding)
            agent.rect.bottom = min(agent.rect.bottom, current_zone.bottom - padding)

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
        padding = 10  # Same padding as enforce_zone_boundaries
        new_x = random.randint(zone.left + padding, zone.right - padding)
        new_y = random.randint(zone.top + padding, zone.bottom - padding)
        agent.rect.center = (new_x, new_y)
        
        # Reset direction to prevent immediate boundary collision
        agent.direction_vector = pygame.math.Vector2(
            random.choice([-0.5, 0.5]),
            random.choice([-0.5, 0.5])
        ).normalize()

    def setup_logging(self):
        """Initialize logging system with CSV file"""
        self.log_file = open('simulation_log.csv', 'w', newline='')
        self.log_writer = csv.writer(self.log_file)
        # Write header row
        self.log_writer.writerow([
            'Time', 
            'Susceptible', 
            'Exposed', 
            'Believer', 
            'Doubter', 
            'Recovered', 
            'Disinformant',
            'Total_Misinformed'
        ])
        self.last_log_time = -1  # Initialize to ensure first log at 00:00

    def log_current_state(self, current_time):
        """Log current agent counts to file"""
        time_str = current_time.strftime("%H:%M")
        self.log_writer.writerow([
            time_str,
            self.susceptible_count,
            self.exposed_count,
            self.believer_count,
            self.doubter_count,
            self.recovered_count,
            self.disinformant_count,
            self.total_misinformed
        ])
        self.log_file.flush()  # Ensure data is written to disk

    def run(self):
        characters = 0
        counts = self.setup_screen()
        self.initialize_agents(counts)
        self.setup_logging()  # Initialize logging system
        running = True

        while running:
            self.game_clock.update()
            # Log every 10 minutes
            current_minute = self.game_clock.get_minute()
            if current_minute % 10 == 0 and current_minute != self.last_log_time:
                self.log_current_state(self.game_clock.simulation_time)
                self.last_log_time = current_minute
            current_hour = self.game_clock.get_hour()
            current_minute = self.game_clock.get_minute()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Update agents except during deep sleep (00:00-06:00)
            if not (0 <= current_hour < 6):
                self.all_sprites.update()
                #self.all_sprites.update(zones=self.zones)

                for agent in self.all_sprites:
                    self.enforce_zone_boundaries(agent)
                
                self.update_agent_locations()   

                # Only process interactions after 7:00 or during wake-up time (6:45-7:00)
                #if current_hour >= 7 or (current_hour == 6 and current_minute >= 30):
                
                # Susceptible + Believer -> Exposed
                for sus in self.susceptible_group:
                    for bel in self.believer_group:
                        if pygame.sprite.collide_rect(sus, bel):
                            prob = 0.1 * bel.influence * (1 + sus.emotional_valence)
                            if random.random() < prob:
                                sus.kill()
                                self.susceptible_count -= 1
                                new_exp = Exposed(self.exposed_group, self.all_sprites)
                                new_exp.rect.center = sus.rect.center
                                new_exp.emotional_valence = sus.emotional_valence  # carry over
                                self.all_sprites.add(new_exp)
                                self.exposed_group.add(new_exp)
                                self.exposed_count += 1

                # Exposed -> Believer or Doubter after exposure time
                for exp in self.exposed_group:
                    if exp.exposure_time > 180:
                        prob = (0.7 - 0.4 * exp.skepticism) * (1 + exp.emotional_valence)
                        if random.random() < prob:
                            exp.kill()
                            self.exposed_count -= 1
                            new_bel = Believer(self.believer_group, self.all_sprites)
                            new_bel.rect.center = exp.rect.center
                            new_bel.emotional_valence = exp.emotional_valence
                            self.all_sprites.add(new_bel)
                            self.believer_group.add(new_bel)
                            self.believer_count += 1
                            self.total_misinformed = self.believer_count + self.disinformant_count
                        else:
                            exp.kill()
                            self.exposed_count -= 1
                            new_doub = Doubter(self.doubter_group, self.all_sprites)
                            new_doub.rect.center = exp.rect.center
                            new_doub.emotional_valence = exp.emotional_valence
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

            characters = (self.susceptible_count + self.exposed_count +
                        self.believer_count + self.doubter_count + self.recovered_count)
            self.point_count = self.doubter_count * 2 + self.recovered_count * 3 - self.believer_count
            self.total_misinformed = self.believer_count + self.disinformant_count

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

            # Interface:
            # Draw the stats box first
            stats_box_rect = pygame.Rect(self.screen_width - 220, self.screen_height - 640, 180, 300)  # Narrower (180px) and further right
            pygame.draw.rect(self.screen, (50, 50, 50), stats_box_rect)

            # Draw the counts inside the box, in white
            font32 = pygame.font.SysFont('Concolas', 32)
            font35 = pygame.font.SysFont('Concolas', 35)

            # MISINFORMED section (adjust positions relative to the new box)
            pygame.draw.circle(self.screen, (160, 0, 0), (self.screen_width - 130, self.screen_height - 205), 65)  # Smaller circle (65 radius)
            points_label = pygame.font.SysFont('Concolas', 30).render('Misinformed', True, (20, 20, 10))  # Smaller font
            points_text = pygame.font.SysFont('Concolas', 45).render(str(self.total_misinformed), True, (255, 255, 255))  # Smaller font
            self.screen.blit(points_label, (self.screen_width - 210, self.screen_height - 320))  # Adjusted position
            self.screen.blit(points_text, (self.screen_width - 145, self.screen_height - 220))  # Adjusted position

            # COUNT title
            count_title = pygame.font.SysFont('Concolas', 30).render('COUNT', True, (255, 255, 255))  # Smaller font
            self.screen.blit(count_title, (self.screen_width - 200, self.screen_height - 660))  # Adjusted position

            # Update the draw_count function for narrower layout:
            def draw_count(label, count, y):
                label_surf = font32.render(label, True, (255, 255, 255))
                count_surf = font35.render(str(count), True, (255, 255, 255))
                self.screen.blit(label_surf, (self.screen_width - 210, y))  # Adjusted left position
                self.screen.blit(count_surf, (self.screen_width - 120, y))  # Adjusted right position
                
            # Call with proper vertical spacing
            draw_count('SU:', self.susceptible_count, self.screen_height - 620)
            draw_count('EX:', self.exposed_count, self.screen_height - 580)
            draw_count('BE:', self.believer_count, self.screen_height - 540)
            draw_count('DO:', self.doubter_count, self.screen_height - 500)
            draw_count('RE:', self.recovered_count, self.screen_height - 460)
            draw_count('DI:', self.disinformant_count, self.screen_height - 420)

            pygame.display.flip()
            self.clock.tick(self.fps)

            def __del__(self):
                """Cleanup method to close log file"""
                if hasattr(self, 'log_file'):
                    self.log_file.close()

if __name__ == "__main__":
    game = Game()
    game.run()
