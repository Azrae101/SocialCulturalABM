import pygame
import random
import numpy as np
from susceptible import Susceptible
from exposed import Exposed
from believer import Believer
from doubter import Doubter
from recovered import Recovered

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Setup display
        self.screen_width = 1140
        self.screen_height = 680
        pygame.display.set_caption("Misinformation Spread Simulation")
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.susceptible_group = pygame.sprite.Group()
        self.exposed_group = pygame.sprite.Group()
        self.believer_group = pygame.sprite.Group()
        self.doubter_group = pygame.sprite.Group()
        self.recovered_group = pygame.sprite.Group()
        
        # Initialize counts
        self.susceptible_count = 0
        self.exposed_count = 0
        self.believer_count = 0
        self.doubter_count = 0
        self.recovered_count = 0
        
        # Create buttons
        self.button_susceptible = pygame.Rect(20, self.screen_height - 60, 200, 40)
        self.button_believer = pygame.Rect(240, self.screen_height - 60, 200, 40)
        self.button_reset = pygame.Rect(460, self.screen_height - 60, 200, 40)
        
        # Simulation parameters
        self.parameters = {
            "base_transmission": 0.3,    # α
            "doubt_development": 0.2,    # β1
            "belief_adoption": 0.5,      # β2
            "secondary_infection": 0.1,  # γ
            "recovery_rate": 0.1         # μ
        }
        
        # Initialize fonts
        self.font = pygame.font.SysFont('Arial', 24)
        
    def add_agent(self, state="Susceptible"):
        new_agent = Agent(None, None)  # We don't use these parameters as in the original code
        new_agent.state = state
        new_agent.image.fill(Agent.STATES[state])
        
        self.all_sprites.add(new_agent)
        
        # Add to the appropriate group
        if state == "Susceptible":
            self.susceptible_group.add(new_agent)
            self.susceptible_count += 1
        elif state == "Exposed":
            self.exposed_group.add(new_agent)
            self.exposed_count += 1
        elif state == "Believer":
            self.believer_group.add(new_agent)
            self.believer_count += 1
        elif state == "Doubter":
            self.doubter_group.add(new_agent)
            self.doubter_count += 1
        elif state == "Recovered":
            self.recovered_group.add(new_agent)
            self.recovered_count += 1
            
        return new_agent
        
    def handle_state_change(self, agent, new_state):
        # Remove from current group
        if agent.state == "Susceptible":
            self.susceptible_group.remove(agent)
            self.susceptible_count -= 1
        elif agent.state == "Exposed":
            self.exposed_group.remove(agent)
            self.exposed_count -= 1
        elif agent.state == "Believer":
            self.believer_group.remove(agent)
            self.believer_count -= 1
        elif agent.state == "Doubter":
            self.doubter_group.remove(agent)
            self.doubter_count -= 1
        elif agent.state == "Recovered":
            self.recovered_group.remove(agent)
            self.recovered_count -= 1
            
        # Change state and add to new group
        agent.change_state(new_state)
        
        # Add to new group
        if new_state == "Susceptible":
            self.susceptible_group.add(agent)
            self.susceptible_count += 1
        elif new_state == "Exposed":
            self.exposed_group.add(agent)
            self.exposed_count += 1
        elif new_state == "Believer":
            self.believer_group.add(agent)
            self.believer_count += 1
        elif new_state == "Doubter":
            self.doubter_group.add(agent)
            self.doubter_count += 1
        elif new_state == "Recovered":
            self.recovered_group.add(agent)
            self.recovered_count += 1
    
    def run(self):
        running = True
        
        # Initial population
        for _ in range(45):
            self.add_agent("Susceptible")
        for _ in range(5):
            self.add_agent("Believer")
            
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_susceptible.collidepoint(event.pos):
                        self.add_agent("Susceptible")
                    elif self.button_believer.collidepoint(event.pos):
                        self.add_agent("Believer")
                    elif self.button_reset.collidepoint(event.pos):
                        # Clear all agents
                        self.all_sprites.empty()
                        self.susceptible_group.empty()
                        self.exposed_group.empty()
                        self.believer_group.empty()
                        self.doubter_group.empty()
                        self.recovered_group.empty()
                        
                        # Reset counts
                        self.susceptible_count = 0
                        self.exposed_count = 0
                        self.believer_count = 0
                        self.doubter_count = 0
                        self.recovered_count = 0
                        
                        # Add new initial population
                        for _ in range(45):
                            self.add_agent("Susceptible")
                        for _ in range(5):
                            self.add_agent("Believer")
            
            # Check collisions - Susceptible & Believer
            for susceptible in self.susceptible_group:
                for believer in self.believer_group:
                    if pygame.sprite.collide_rect(susceptible, believer):
                        # Transmission probability based on believer's influence
                        transmission_prob = self.parameters["base_transmission"] * believer.influence
                        if random.random() < transmission_prob:
                            self.handle_state_change(susceptible, "Exposed")
            
            # Check collisions - Doubter & Believer
            for doubter in self.doubter_group:
                for believer in self.believer_group:
                    if pygame.sprite.collide_rect(doubter, believer):
                        # Chance for doubter to become a believer (peer pressure)
                        if random.random() < self.parameters["secondary_infection"] * believer.influence:
                            self.handle_state_change(doubter, "Believer")
            
            # Check collisions - Recovered & Believer
            for recovered in self.recovered_group:
                for believer in self.believer_group:
                    if pygame.sprite.collide_rect(recovered, believer):
                        # Small chance to become susceptible again (memory decay)
                        if random.random() < 0.01 * believer.influence:
                            self.handle_state_change(recovered, "Susceptible")
            
            # Check collisions - Susceptible & Doubter
            for susceptible in self.susceptible_group:
                for doubter in self.doubter_group:
                    if pygame.sprite.collide_rect(susceptible, doubter):
                        # Chance for susceptible to become a doubter (preemptive skepticism)
                        if random.random() < 0.05 * doubter.influence:
                            self.handle_state_change(susceptible, "Doubter")
            
            # Update sprites
            self.all_sprites.update()
            
            # Manually apply state changes when sprites update themselves
            for agent in self.all_sprites:
                current_state = agent.state
                if current_state == "Exposed" and agent in self.exposed_group:
                    if agent.state != current_state:  # Check if update changed state
                        self.handle_state_change(agent, agent.state)
                elif current_state == "Believer" and agent in self.believer_group:
                    if agent.state != current_state:
                        self.handle_state_change(agent, agent.state)
                elif current_state == "Doubter" and agent in self.doubter_group:
                    if agent.state != current_state:
                        self.handle_state_change(agent, agent.state)
            
            # Draw background
            self.screen.fill((240, 240, 240))
            
            # Draw all agents
            self.all_sprites.draw(self.screen)
            
            # Draw UI
            pygame.draw.rect(self.screen, (200, 200, 255), self.button_susceptible)
            pygame.draw.rect(self.screen, (255, 150, 150), self.button_believer)
            pygame.draw.rect(self.screen, (200, 200, 200), self.button_reset)
            
            # Draw button labels
            self.screen.blit(self.font.render("Add Susceptible", True, (0, 0, 0)), (30, self.screen_height - 55))
            self.screen.blit(self.font.render("Add Believer", True, (0, 0, 0)), (260, self.screen_height - 55))
            self.screen.blit(self.font.render("Reset", True, (0, 0, 0)), (520, self.screen_height - 55))
            
            # Draw counts
            count_text = f"S: {self.susceptible_count} | E: {self.exposed_count} | B: {self.believer_count} | D: {self.doubter_count} | R: {self.recovered_count}"
            self.screen.blit(self.font.render(count_text, True, (0, 0, 0)), (20, 20))
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()



# Create a game instance and run it
if __name__ == "__main__":
    game = Game()
    game.run()
