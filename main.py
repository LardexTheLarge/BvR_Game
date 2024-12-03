import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions and settings
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
FPS = 60
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blue vs Red")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game Variables
TOWER_SIZE = 50
BASE_SIZE = 100
TROOP_SIZE = 10
TROOP_SPEED = 1
SPAWN_INTERVAL = 2000  # in milliseconds
MONEY_INCREMENT = 10

# Classes
class Tower:
    def __init__(self, x, y, is_enemy=False):
        self.rect = pygame.Rect(x, y, TOWER_SIZE, TOWER_SIZE)
        self.health = 100
        self.max_health = 100  # For percentage calculation
        self.is_enemy = is_enemy
        self.last_spawn_time = pygame.time.get_ticks()  # Track last spawn time

    def draw_health_bar(self, screen):
        """Draw a health bar on top of the tower."""
        bar_width = self.rect.width
        bar_height = 8
        health_percentage = self.health / self.max_health
        green_width = int(bar_width * health_percentage)

        # Bar position
        bar_x = self.rect.x
        bar_y = self.rect.y - bar_height - 5

        # Draw background (red)
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Draw health (green)
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, green_width, bar_height))

    def shoot(self, troops):
        """Damage any troop within the tower's range."""
        for troop in troops:
            if self.rect.colliderect(troop.get_rect()):
                troop.health -= 1

    def spawn_troop(self, troops, current_time):
        """Spawn a troop at intervals."""
        if current_time - self.last_spawn_time > SPAWN_INTERVAL:
            x = self.rect.centerx
            # Adjust Y position based on whether it's an enemy or player tower
            y = self.rect.bottom - TROOP_SIZE if self.is_enemy else self.rect.top
            direction = -1 if self.is_enemy else 1
            troops.append(Troop(x, y, direction, is_enemy=self.is_enemy))  # Add troop to correct list
            self.last_spawn_time = current_time

    def draw(self):
        """Render the tower on the screen."""
        pygame.draw.rect(screen, RED if self.is_enemy else BLUE, self.rect)
        # Draw health bar
        self.draw_health_bar(screen)


class Base(Tower):  # Base extends Tower for simplicity
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y, is_enemy)
        self.health = 200  # Bases have more health
        self.max_health = 200  # For percentage calculation

    def draw_health_bar(self, screen):
        """Draw a health bar on top of the tower."""
        bar_width = self.rect.width
        bar_height = 8
        health_percentage = self.health / self.max_health
        green_width = int(bar_width * health_percentage)

        # Bar position
        bar_x = self.rect.x
        bar_y = self.rect.y - bar_height - 5

        # Draw background (red)
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Draw health (green)
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, green_width, bar_height))

    def draw(self):
        pygame.draw.rect(screen, RED if self.is_enemy else BLUE, self.rect)
        # Draw health bar
        self.draw_health_bar(screen)


class Troop:
    def __init__(self, x, y, direction, is_enemy=False):
        self.x = x
        self.y = y
        self.direction = direction
        self.is_enemy = is_enemy
        self.health = 10
        self.max_health = 10  # For calculating percentage
        self.size = TROOP_SIZE
        self.attacking = False  # Whether the troop is attacking
        self.attack_timer = 20  # Timer for the attack animation
        self.attack_phase = "retreat"  # "back" for retreat, "forward" for attack

    def draw_health_bar(self, screen):
        """Draw a health bar above the troop."""
        bar_width = self.size
        bar_height = 5
        health_percentage = self.health / self.max_health
        green_width = int(bar_width * health_percentage)
        
        # Bar position
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.size // 2 - bar_height - 10

        # Draw background (red)
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Draw health (green)
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, green_width, bar_height))

    def move(self):
        """Handle movement and attacking animation."""
        if self.attacking:
            print(f"Troop attacking. Phase: {self.attack_phase}, Timer: {self.attack_timer}")
            # Perform attack animation
            if self.attack_phase == "retreat":
                self.y += TROOP_SPEED * self.direction
                self.attack_timer -= 1
                if self.attack_timer <= 0:
                    self.attack_phase = "advance"
                    self.attack_timer = 100  # Reset timer for the next phase
            elif self.attack_phase == "advance":
                self.y -= TROOP_SPEED * self.direction
                self.attack_timer -= 1
                if self.attack_timer <= 0:
                    self.attack_phase = "retreat"
                    self.attack_timer = 100  # Reset timer for the next phase
        else:
            # Regular movement when not attacking
            self.y -= TROOP_SPEED * self.direction

    def start_attack(self):
        """Start the attacking animation."""
        if not self.attacking:  # Prevent re-initializing
            self.attacking = True
            self.attack_phase = "retreat"
            self.attack_timer = 100  # Adjust for retreat duration

    def stop_attack(self):
        """Stop the attacking animation."""
        self.attacking = False
        self.attack_timer = 0
        self.attack_phase = "retreat"  # Reset for the next attack

    def draw(self, screen):
        if self.is_enemy:
            # Draw enemy troop (red circle with white border)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), self.size // 2 + 2)  # Border
            pygame.draw.circle(screen, RED, (self.x, self.y), self.size // 2)  # Inner
        else:
            # Draw player's troop (blue square with white border)
            rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
            pygame.draw.rect(screen, WHITE, rect.inflate(4, 4))  # Border
            pygame.draw.rect(screen, BLUE, rect)  # Inner

        # Draw the health bar
        self.draw_health_bar(screen)
    
    def get_rect(self):
        """Return a pygame.Rect for collision detection."""
        if self.is_enemy:
            # Treat the circle as a bounding square for simplicity
            return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        else:
            # Return the rectangle directly for the player's troop
            return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)

# Functions
def draw_ui(player_money, enemy_money):
    font = pygame.font.Font(None, 26)
    player_money_text = font.render(f"Player Money: ${player_money}", True, WHITE)
    enemy_money_text = font.render(f"Enemy Money: ${enemy_money}", True, WHITE)
    screen.blit(player_money_text, (330, 780))
    screen.blit(enemy_money_text, (10, 10))


# Game Loop
def main():
    player_towers = [
        Tower(50, SCREEN_HEIGHT - 150),
        Tower(400, SCREEN_HEIGHT - 150),
        Base(SCREEN_WIDTH // 2 - BASE_SIZE // 4, SCREEN_HEIGHT - BASE_SIZE),
    ]
    enemy_towers = [
        Tower(50, 100, is_enemy=True),
        Tower(400, 100, is_enemy=True),
        Base(SCREEN_WIDTH // 2 - BASE_SIZE // 4, 50, is_enemy=True),
    ]
    player_troops = []
    enemy_troops = []

    player_money = 100
    enemy_money = 100

    running = True
    while running:
        screen.fill(BLACK)
        current_time = pygame.time.get_ticks()

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for tower in player_towers:
            tower.spawn_troop(player_troops, current_time)  # Player troops spawn from player towers
        for tower in enemy_towers:
            tower.spawn_troop(enemy_troops, current_time)  # Enemy troops spawn from enemy towers


        # Move player troops, checking for collisions with enemy troops
        for player_troop in player_troops:
            player_troop.move()

        # Move enemy troops, checking for collisions with player troops
        for enemy_troop in enemy_troops:
            enemy_troop.move()

        # Example collision handling in game loop
        for player_troop in player_troops:
            player_collision = False  # Tracks if this player troop is colliding with any enemy
            for enemy_troop in enemy_troops:
                if player_troop.get_rect().colliderect(enemy_troop.get_rect()):
                    player_collision = True
                    # Stop movement and initiate attack
                    player_troop.start_attack()
                    enemy_troop.start_attack()

                    # Reduce health
                    player_troop.health -= 0.1
                    enemy_troop.health -= 0.1
                    
            # Resume movement if no collisions occurred
            if not player_collision:
                player_troop.stop_attack()

        for enemy_troop in enemy_troops:
            enemy_collision = False  # Tracks if this enemy troop is colliding with any player
            for player_troop in player_troops:
                if enemy_troop.get_rect().colliderect(player_troop.get_rect()):
                    enemy_collision = True

            # Resume movement if no collisions occurred
            if not enemy_collision:
                enemy_troop.stop_attack()


        # Update money based on dead troops
        player_money += len([troop for troop in enemy_troops if troop.health <= 0]) * MONEY_INCREMENT
        enemy_money += len([troop for troop in player_troops if troop.health <= 0]) * MONEY_INCREMENT

        # Remove dead troops
        player_troops = [troop for troop in player_troops if troop.health > 0]
        enemy_troops = [troop for troop in enemy_troops if troop.health > 0]


        # Draw everything
        for tower in player_towers + enemy_towers:
            tower.draw()  # Ensure tower also takes screen as a parameter if needed
        for troop in player_troops + enemy_troops:
            troop.draw(screen)  # Pass the screen object here

        draw_ui(player_money, enemy_money)

        # Victory condition
        if any(base.health <= 0 for base in player_towers + enemy_towers if isinstance(base, Base)):
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
