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
TROOP_SPEED = 2
SPAWN_INTERVAL = 2000  # in milliseconds
MONEY_INCREMENT = 10

# Classes
class Tower:
    def __init__(self, x, y, is_enemy=False):
        self.rect = pygame.Rect(x, y, TOWER_SIZE, TOWER_SIZE)
        self.health = 100
        self.is_enemy = is_enemy
        self.last_spawn_time = pygame.time.get_ticks()  # Track last spawn time

    def shoot(self, troops):
        """Damage any troop within the tower's range."""
        for troop in troops:
            if self.rect.colliderect(troop.get_rect()):
                troop.health -= 1

    def spawn_troop(self, troops, current_time):
        """Spawn a troop at intervals."""
        if current_time - self.last_spawn_time > SPAWN_INTERVAL:
            x = self.rect.centerx - TROOP_SIZE // 2
            # Adjust Y position based on whether it's an enemy or player tower
            y = self.rect.top - TROOP_SIZE if self.is_enemy else self.rect.bottom
            direction = -1 if self.is_enemy else 1
            troops.append(Troop(x, y, direction, is_enemy=self.is_enemy))  # Add troop to correct list
            self.last_spawn_time = current_time

    def draw(self):
        """Render the tower on the screen."""
        pygame.draw.rect(screen, RED if self.is_enemy else BLUE, self.rect)



class Base(Tower):  # Base extends Tower for simplicity
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y, is_enemy)
        self.health = 200  # Bases have more health

    def draw(self):
        pygame.draw.rect(screen, RED if self.is_enemy else BLUE, self.rect)


class Troop:
    def __init__(self, x, y, direction, is_enemy=False):
        self.x = x
        self.y = y
        self.direction = direction
        self.is_enemy = is_enemy
        self.health = 10
        self.size = TROOP_SIZE

    def move(self):
        self.y -= TROOP_SPEED * self.direction

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
    screen.blit(player_money_text, (10, 10))
    screen.blit(enemy_money_text, (10, 50))


# Game Loop
def main():
    player_towers = [
        Tower(100, SCREEN_HEIGHT - 150),
        Tower(300, SCREEN_HEIGHT - 150),
        Base(SCREEN_WIDTH // 2 - BASE_SIZE // 2, SCREEN_HEIGHT - BASE_SIZE),
    ]
    enemy_towers = [
        Tower(100, 100, is_enemy=True),
        Tower(300, 100, is_enemy=True),
        Base(SCREEN_WIDTH // 2 - BASE_SIZE // 2, 50, is_enemy=True),
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

        # Ensure correct troop lists are used for spawning
        current_time = pygame.time.get_ticks()
        for tower in player_towers:
            tower.spawn_troop(player_troops, current_time)  # Player troops spawn from player towers
        for tower in enemy_towers:
            tower.spawn_troop(enemy_troops, current_time)  # Enemy troops spawn from enemy towers

        # Troop Movement and Combat
        for troop in player_troops + enemy_troops:
            troop.move()

        for player_troop in player_troops:
            for enemy_troop in enemy_troops:
                if player_troop.get_rect().colliderect(enemy_troop.get_rect()):
                    player_troop.health -= 1
                    enemy_troop.health -= 1

        # Remove dead troops
        player_troops = [troop for troop in player_troops if troop.health > 0]
        enemy_troops = [troop for troop in enemy_troops if troop.health > 0]

        # Update money
        player_money += len([troop for troop in enemy_troops if troop.health <= 0]) * MONEY_INCREMENT
        enemy_money += len([troop for troop in player_troops if troop.health <= 0]) * MONEY_INCREMENT

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