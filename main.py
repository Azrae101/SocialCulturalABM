import pygame
import sys
import random
from datetime import datetime, timedelta
import csv
import numpy as np
from scipy.stats import beta

from susceptible import Susceptible
from exposed import Exposed
from believer import Believer
from doubter import Doubter
from recovered import Recovered
from disinformant import Disinformant  

def change_probability(agent, influencer=None, environment_factor=1.0, misinformant_exposure=0):
    """
    Calculate the probability of an agent changing state.
    - agent: the agent being influenced (must have .emotional_valence, .skepticism, etc.)
    - influencer: the influencing agent (must have .influence if present)
    - environment_factor: float, multiplier for environmental context (e.g., higher in social media zone)
    - misinformant_exposure: int, number of recent exposures to misinformants
    Returns: probability (float between 0 and 1)
    """
    # Emotional valence: higher valence = more likely to change (Beta(2, 2) is a reasonable prior)
    valence_prob = beta.cdf(agent.emotional_valence, 2, 2)
    
    # Influence: from influencer (if present), otherwise default
    influence = getattr(influencer, 'influence', 1.0) if influencer else 1.0
    
    # Skepticism: higher means less likely to change
    skepticism = getattr(agent, 'skepticism', 0.5)
    skepticism_factor = 1.0 - skepticism  # 0 = never change, 1 = always change
    
    # Misinformant exposure: each exposure increases chance by 5% (capped at +25%)
    misinfo_bonus = min(0.05 * misinformant_exposure, 0.25)
    
    # Environment: e.g., 1.2 in social media, 1.0 elsewhere
    env = environment_factor
    
    # Combine all factors
    base_prob = 0.2  # Base probability for susceptible/exposed
    prob = base_prob * influence * valence_prob * skepticism_factor * env
    prob += misinfo_bonus

    # Make it rare for Doubters to become Believers
    if agent.__class__.__name__ == "Doubter" and (
        influencer and influencer.__class__.__name__ in ["Believer", "Disinformant"]
    ):
        prob *= 0.05  # Only 5% of the already small probability

    # Clamp between 0 and 1
    return max(0.0, min(1.0, prob))

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
]

class Clock:
    def __init__(self, x, y):
        self.font = pygame.font.SysFont('Consolas', 32)
        self.position = (x, y)
        self.simulation_time = datetime(2023, 1, 1, 6, 0)
        self.time_multiplier = 10  # 1 hour per real second (10 sec/hour)
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
        self.collision_group = pygame.sprite.Group()  # New group for collision checks
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

        self.home_grid_rows = 5
        self.home_grid_cols = 6
        self.home_grid_cells = self.home_grid_rows * self.home_grid_cols
        self.home_grid_assignments = {}  # agent -> (row, col)
        self.home_grid_agents = {}  # (row, col) -> [agents]

    def get_home_grid_rects(self):
        """Return a dict of (row, col): pygame.Rect for each grid cell in home zone."""
        zone = self.zones["home"]
        padding_top = 40  # Space for the title above the grid
        grid_top = zone.top + padding_top
        grid_height = zone.height - padding_top
        cell_w = zone.width // self.home_grid_cols
        cell_h = grid_height // self.home_grid_rows
        grid_rects = {}
        for row in range(self.home_grid_rows):
            for col in range(self.home_grid_cols):
                left = zone.left + col * cell_w
                top = grid_top + row * cell_h
                grid_rects[(row, col)] = pygame.Rect(left, top, cell_w, cell_h)
        return grid_rects

    def assign_agents_to_home_grid(self):
        """Assign agents to grid cells only if they don't already have an assignment."""
        agents = [a for a in self.all_sprites if self.zones["home"].collidepoint(a.rect.center) and (not hasattr(a, "home_grid_cell") or a.home_grid_cell is None)]
        if not agents:
            return  # No new agents to assign

        random.shuffle(agents)
        grid_cells = [(r, c) for r in range(self.home_grid_rows) for c in range(self.home_grid_cols)]
        # Only consider cells with space (max 3 per cell)
        cell_agents = self.home_grid_agents if hasattr(self, "home_grid_agents") else {cell: [] for cell in grid_cells}

        # Build a list of available cells (cells with < 3 agents)
        available_cells = [cell for cell in grid_cells if len(cell_agents.get(cell, [])) < 3]
        random.shuffle(available_cells)

        agent_idx = 0
        for cell in available_cells:
            while len(cell_agents.get(cell, [])) < 3 and agent_idx < len(agents):
                agent = agents[agent_idx]
                if cell not in cell_agents:
                    cell_agents[cell] = []
                cell_agents[cell].append(agent)
                agent.home_grid_cell = cell
                # Move agent to random position within their assigned cell
                grid_rects = self.get_home_grid_rects()
                rect = grid_rects[cell]
                agent.rect.center = (
                    random.randint(rect.left + 10, rect.right - 10),
                    random.randint(rect.top + 10, rect.bottom - 10)
                )
                agent_idx += 1
            if agent_idx >= len(agents):
                break

        self.home_grid_agents = cell_agents

    def clear_home_grid_assignment(self, agent):
        """Clear agent's grid assignment when leaving home zone."""
        if hasattr(agent, "home_grid_cell"):
            cell = agent.home_grid_cell
            if cell in self.home_grid_agents and agent in self.home_grid_agents[cell]:
                self.home_grid_agents[cell].remove(agent)
            agent.home_grid_cell = None

    def enforce_home_grid_boundaries(self, agent):
        """Keep agent within their assigned grid cell in home zone."""
        if hasattr(agent, "home_grid_cell"):
            grid_rects = self.get_home_grid_rects()
            rect = grid_rects[agent.home_grid_cell]
            # Clamp agent position to grid cell
            agent.rect.left = max(agent.rect.left, rect.left + 2)
            agent.rect.right = min(agent.rect.right, rect.right - 2)
            agent.rect.top = max(agent.rect.top, rect.top + 2)
            agent.rect.bottom = min(agent.rect.bottom, rect.bottom - 2)

    def set_next_switch_time(self, agent, current_time, to_social):
        if to_social:
            # Social media: 20-30 min
            minutes = random.randint(20, 30)
        else:
            # Home: 5-15 min
            minutes = random.randint(5, 15)
        agent.next_switch_time = (current_time.hour * 60 + current_time.minute) + minutes

    def main_menu(self):
        font = pygame.font.SysFont('Consolas', 44)
        small_font = pygame.font.SysFont('Consolas', 32)
        one_day_button = pygame.Rect(self.screen_width//2 - 200, 300, 400, 80)
        week_button = pygame.Rect(self.screen_width//2 - 200, 420, 400, 80)
        running = True
        choice = None
        while running:
            self.screen.fill((240, 240, 240))
            title = font.render("Misinformation Simulation", True, (30, 30, 30))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 120))
            pygame.draw.rect(self.screen, (0, 120, 0), one_day_button)
            pygame.draw.rect(self.screen, (0, 0, 120), week_button)
            one_day_text = small_font.render("Run for 1 Day (24h)", True, (255,255,255))
            week_text = small_font.render("Run for 1 Week", True, (255,255,255))
            self.screen.blit(one_day_text, (one_day_button.x + 40, one_day_button.y + 20))
            self.screen.blit(week_text, (week_button.x + 40, week_button.y + 20))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if one_day_button.collidepoint(event.pos):
                        choice = "day"
                        running = False
                    elif week_button.collidepoint(event.pos):
                        choice = "week"
                        running = False
            self.clock.tick(30)
        return choice

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
            title = font.render("Set Initial Agent Counts", True, (30, 30, 30))
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
        return {slider.label: slider.value for slider in sliders}

    def initialize_agents(self, counts):
        agent_class_map = {
            "Susceptible": (Susceptible, self.susceptible_group, "susceptible_count"),
            "Exposed": (Exposed, self.exposed_group, "exposed_count"),
            "Believer": (Believer, self.believer_group, "believer_count"),
            "Doubter": (Doubter, self.doubter_group, "doubter_count"),
            "Recovered": (Recovered, self.recovered_group, "recovered_count"),
            "Disinformant": (Disinformant, self.disinformant_group, "disinformant_count"),
        }
        home_zone = self.zones["home"]
        for agent_type, count in counts.items():
            if agent_type in agent_class_map:
                agent_class, group, count_attr = agent_class_map[agent_type]
                for _ in range(count):
                    agent = agent_class(group, self.all_sprites)
                    # Place agent in home zone at spawn
                    padding = 10
                    new_x = random.randint(home_zone.left + padding, home_zone.right + padding)
                    new_y = random.randint(home_zone.top + padding, home_zone.bottom + padding)
                    agent.rect.center = (new_x, new_y)
                    agent.direction_vector = pygame.math.Vector2(
                        random.choice([-0.5, 0.5]),
                        random.choice([-0.5, 0.5])
                    ).normalize()
                    agent.next_switch_time = 0  # <-- This is correct!
                    self.collision_group.add(agent)
                    self.all_sprites.add(agent)
                    group.add(agent)
                    setattr(self, count_attr, getattr(self, count_attr) + 1)

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

        # Draw grid lines in home zone
        grid_rects = self.get_home_grid_rects()
        for rect in grid_rects.values():
            pygame.draw.rect(self.screen, (180, 180, 180), rect, 1)
    
    def enforce_zone_boundaries(self, agent):
        """Keep agent within their current zone boundaries and help them escape corners"""
        current_zone = None

        # Determine which zone the agent is in
        for zone_name, zone_rect in self.zones.items():
            if zone_rect.collidepoint(agent.rect.center):
                current_zone = zone_rect
                break

        if current_zone:
            padding = 10  # Small buffer from edges
            # Store old position for comparison
            old_left, old_top = agent.rect.left, agent.rect.top
            old_right, old_bottom = agent.rect.right, agent.rect.bottom

            # Clamp position
            agent.rect.left = max(agent.rect.left, current_zone.left + padding)
            agent.rect.right = min(agent.rect.right, current_zone.right - padding)
            agent.rect.top = max(agent.rect.top, current_zone.top + padding)
            agent.rect.bottom = min(agent.rect.bottom, current_zone.bottom - padding)

            # If agent was clamped (i.e., touching a wall), randomize direction away from wall
            stuck = (
                agent.rect.left == current_zone.left + padding or
                agent.rect.right == current_zone.right - padding or
                agent.rect.top == current_zone.top + padding or
                agent.rect.bottom == current_zone.bottom - padding
            )
            if stuck:
                # Pick a direction away from the wall/corner
                dx = random.choice([-1, 1])
                dy = random.choice([-1, 1])
                # If at left or right wall, force x direction away
                if agent.rect.left == current_zone.left + padding:
                    dx = 1
                elif agent.rect.right == current_zone.right - padding:
                    dx = -1
                # If at top or bottom wall, force y direction away
                if agent.rect.top == current_zone.top + padding:
                    dy = 1
                elif agent.rect.bottom == current_zone.bottom - padding:
                    dy = -1
                agent.direction_vector = pygame.math.Vector2(dx, dy).normalize()

    def update_agent_locations(self):
        current_hour = self.game_clock.get_hour()
        current_minute = self.game_clock.get_minute()

        # Force all agents to home zone during sleep (00:00–07:00)
        if 0 <= current_hour < 7:
            zone = self.zones["home"]
            for agent in self.all_sprites:
                if not zone.collidepoint(agent.rect.center):
                    self.move_agent_to_zone(agent, zone)
                # Assign grid cell if not already assigned
                if not hasattr(agent, "home_grid_cell") or agent.home_grid_cell is None:
                    self.assign_agents_to_home_grid()
            return

        # Determine target zone based on time
        if 6 <= current_hour < 7:
            target_zone = "home"
        elif 8 <= current_hour < 16:
            target_zone = "work"
        elif (7 <= current_hour < 8) or (19 <= current_hour < 21):  # Social media hours
            current_total_minutes = current_hour * 60 + current_minute
            for agent in self.all_sprites:
                # If agent doesn't have a next_switch_time, set it based on current state
                if not hasattr(agent, "next_switch_time") or agent.next_switch_time == 0:
                    if not agent.in_social:
                        self.set_next_switch_time(agent, self.game_clock.simulation_time, to_social=True)
                    else:
                        self.set_next_switch_time(agent, self.game_clock.simulation_time, to_social=False)

                # Time to switch?
                if current_total_minutes >= agent.next_switch_time:
                    agent.in_social = not agent.in_social
                    self.set_next_switch_time(agent, self.game_clock.simulation_time, to_social=agent.in_social)

                target_zone = "social" if agent.in_social else "home"
                zone = self.zones[target_zone]
                if not zone.collidepoint(agent.rect.center):
                    self.move_agent_to_zone(agent, zone)
                    if target_zone != "home":
                        self.clear_home_grid_assignment(agent)
                # --- Only assign grid cell if agent is in home and has no assignment ---
                if target_zone == "home" and (not hasattr(agent, "home_grid_cell") or agent.home_grid_cell is None):
                    self.assign_agents_to_home_grid()
        else:
            target_zone = "home"

        # For non-social-media hours or agents not in social-media pattern
        if not ((7 <= current_hour < 8) or (19 <= current_hour < 21)):
            zone = self.zones[target_zone]
            for agent in self.all_sprites:
                if not zone.collidepoint(agent.rect.center):
                    self.move_agent_to_zone(agent, zone)
                    # If leaving home, clear grid assignment
                    if target_zone != "home":
                        self.clear_home_grid_assignment(agent)
                # --- Only assign grid cell if agent is in home and has no assignment ---
                if target_zone == "home" and (not hasattr(agent, "home_grid_cell") or agent.home_grid_cell is None):
                    self.assign_agents_to_home_grid()

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
        # --- Main menu for simulation duration ---
        sim_choice = self.main_menu()
        if sim_choice == "day":
            sim_days = 1
        else:
            sim_days = 7

        # Setup and start simulation as before
        characters = 0
        counts = self.setup_screen()
        self.initialize_agents(counts)
        self.setup_logging()  # Initialize logging system

        # Set simulation start and end time
        sim_start_time = datetime(2023, 1, 1, 6, 0)
        sim_end_time = sim_start_time + timedelta(days=sim_days)

        # --- Ensure clock is reset to 6:00 every run ---
        self.game_clock.simulation_time = sim_start_time
        self.game_clock.last_update = pygame.time.get_ticks()

        running = True
        while running:
            current_hour = self.game_clock.get_hour()
            current_minute = self.game_clock.get_minute()

            # --- SLEEP HOURS: 00:00-06:00 ---
            if 0 <= current_hour < 6:
                # Agents do not move or update, just draw them grayed out and clamped to home zone
                home_zone = self.zones["home"]
                padding = 10
                for agent in self.all_sprites:
                    # Clamp agent position to be fully inside home zone
                    agent.rect.left = max(agent.rect.left, home_zone.left + padding)
                    agent.rect.right = min(agent.rect.right, home_zone.right + padding)
                    agent.rect.top = max(agent.rect.top, home_zone.top + padding)
                    agent.rect.bottom = min(agent.rect.bottom, home_zone.bottom + padding)
                # Draw everything (see your drawing code below)
                self.screen.fill((255, 255, 255))
                self.draw_zones()
                self.game_clock.draw(self.screen)
                for agent in self.all_sprites:
                    sleeping_img = pygame.Surface((agent.rect.width, agent.rect.height))
                    sleeping_img.fill((200, 200, 200))  # Light gray
                    sleeping_img.set_alpha(200)
                    self.screen.blit(sleeping_img, agent.rect)
                # ...draw stats etc...
                pygame.display.flip()
                self.clock.tick(self.fps)
                self.game_clock.update()
                # Logging and quit checks
                if self.game_clock.simulation_time >= sim_end_time:
                    print("Simulation complete.")
                    self.log_current_state(self.game_clock.simulation_time)
                    running = False
                continue

            # --- HOME ZONE (not sleep): 06:00-08:00, 16:00-24:00, and when not in social/work ---
            # Determine if agent is in home zone and not sleeping
            # Social media hours: 07:00-08:00 and 19:00-21:00
            in_social_media_hours = (7 <= current_hour < 8) or (19 <= current_hour < 21)
            in_work_hours = (8 <= current_hour < 16)
            # If not in work or social, agents are in home
            if not in_work_hours and not in_social_media_hours:
                # Agents are in home grid and can move, but only within their grid cell
                self.update_agent_locations()  # This will assign agents to home grid if needed

                # Only check collisions within each grid cell
                for cell, agents in self.home_grid_agents.items():
                    for i, agent in enumerate(agents):
                        for other in agents[i+1:]:
                            # --- Restrict Recovered interaction to home zone only ---
                            if (
                                agent.__class__.__name__ == "Recovered"
                                or other.__class__.__name__ == "Recovered"
                            ):
                                # Both are in home, so allow interaction
                                pass
                            if pygame.sprite.collide_rect(agent, other):
                                agent.handle_collision(other)
                                other.handle_collision(agent)
                # Update and restrict agents to their grid cell
                self.all_sprites.update()
                for agent in self.all_sprites:
                    self.enforce_home_grid_boundaries(agent)
            elif in_work_hours:
                # --- WORK ZONE DYNAMICS: Move slower except during break periods ---
                # Agents move at normal speed during first 10 minutes of each hour,
                # very fast from 12:00-12:30, otherwise move at reduced speed
                fast_period = False
                very_fast_period = False
                if current_minute < 10:
                    fast_period = True
                if current_hour == 12 and 0 <= current_minute < 30:
                    very_fast_period = True

                collisions = pygame.sprite.groupcollide(
                    self.collision_group, 
                    self.collision_group, 
                    False, 
                    False,
                    collided=pygame.sprite.collide_rect_ratio(0.8)
                )
                for sprite, collided_list in collisions.items():
                    for other in collided_list:
                        if sprite != other:
                            # --- Prevent Recovered from interacting outside home ---
                            if (
                                sprite.__class__.__name__ == "Recovered"
                                or other.__class__.__name__ == "Recovered"
                            ):
                                home_zone = self.zones["home"]
                                if not (home_zone.collidepoint(sprite.rect.center) and home_zone.collidepoint(other.rect.center)):
                                    continue
                            # --- Defensive: skip collision if direction_vector is zero for either agent ---
                            if (
                                hasattr(sprite, "direction_vector") and
                                hasattr(other, "direction_vector") and
                                (sprite.direction_vector.length_squared() == 0 or other.direction_vector.length_squared() == 0)
                            ):
                                # Assign a random direction to avoid zero-length vector
                                if sprite.direction_vector.length_squared() == 0:
                                    sprite.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
                                if other.direction_vector.length_squared() == 0:
                                    other.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
                            sprite.handle_collision(other)
                            other.handle_collision(sprite)
                # Adjust agent speed
                for agent in self.all_sprites:
                    if self.zones["work"].collidepoint(agent.rect.center):
                        if very_fast_period:
                            agent.speed = getattr(agent, "base_speed", 2.0) * 2.5  # Very fast at lunch break
                        elif fast_period:
                            agent.speed = getattr(agent, "base_speed", 2.0)
                        else:
                            agent.speed = getattr(agent, "base_speed", 2.0) * 0.3
                self.all_sprites.update()
                # Always enforce boundaries and update locations
                for agent in self.all_sprites:
                    self.enforce_zone_boundaries(agent)
                self.update_agent_locations()
            else:
                # --- SOCIAL MEDIA HOURS ---
                # Normal collision and boundary logic
                collisions = pygame.sprite.groupcollide(
                    self.collision_group, 
                    self.collision_group, 
                    False, 
                    False,
                    collided=pygame.sprite.collide_rect_ratio(0.8)
                )
                for sprite, collided_list in collisions.items():
                    for other in collided_list:
                        if sprite != other:
                            # --- Prevent Recovered from interacting outside home ---
                            if (
                                sprite.__class__.__name__ == "Recovered"
                                or other.__class__.__name__ == "Recovered"
                            ):
                                home_zone = self.zones["home"]
                                if not (home_zone.collidepoint(sprite.rect.center) and home_zone.collidepoint(other.rect.center)):
                                    continue  # Skip interaction if not both in home
                            sprite.handle_collision(other)
                            other.handle_collision(sprite)
                self.all_sprites.update()
                for agent in self.all_sprites:
                    self.enforce_zone_boundaries(agent)
                self.update_agent_locations()

            # --- Believer forgetting logic ---
            for agent in list(self.believer_group):
                # 0.1% chance per frame to forget and become susceptible
                if random.random() < 0.001:
                    # Remove from believer group, add to susceptible
                    self.believer_group.remove(agent)
                    self.susceptible_group.add(agent)
                    agent.__class__ = Susceptible
                    self.believer_count -= 1
                    self.susceptible_count += 1

            self.game_clock.update()

            # --- Stop simulation if time is up ---
            if self.game_clock.simulation_time >= sim_end_time:
                print("Simulation complete.")
                self.log_current_state(self.game_clock.simulation_time)
                running = False
                continue

            # Log every 10 minutes
            current_minute = self.game_clock.get_minute()
            if current_minute % 10 == 0 and current_minute != self.last_log_time:
                self.log_current_state(self.game_clock.simulation_time)
                self.last_log_time = current_minute

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # --- Drawing section ---
            self.screen.fill((255, 255, 255))
            self.draw_zones()
            self.game_clock.draw(self.screen)
            # Show agents at all times except midnight-6am
            #if not (0 <= current_hour < 6):
            if True:
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
