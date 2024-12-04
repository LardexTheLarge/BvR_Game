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
font = pygame.font.Font(None, 26)

# Colors
WHITE = (255, 255, 255)
BROWN = (150,75,0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game Variables
TOWER_SIZE = 50
BASE_SIZE = 100
TROOP_SIZE = 10
TROOP_SPEED = .5
SPAWN_INTERVAL = 2000  # in milliseconds
MONEY_INCREMENT = 10

# Classes
class Tower:
    def __init__(self, x, y, is_enemy=False):
        self.rect = pygame.Rect(x, y, TOWER_SIZE, TOWER_SIZE)
        self.health = 100
        self.max_health = 100  # For percentage calculation
        self.is_enemy = is_enemy
        self.spawn_interval = SPAWN_INTERVAL  # Instance-specific spawn interval
        self.attack_power = 1    
        self.last_spawn_time = pygame.time.get_ticks()  # Track last spawn time
        self.upgrades = {
            "health": {"value": 50, "cost": 50},
            "spawn_rate": {"value": -200, "cost": 100},  # Reduce spawn interval
            "attack": {"value": 1, "cost": 75},
        }
    def apply_upgrade(self, upgrade, player_money):
        """Apply an upgrade to this specific tower or base."""
        if self.is_enemy:
            return 0  # Do not allow upgrades for enemy towers

        if upgrade == "health" and player_money >= self.upgrades["health"]["cost"]:
            self.health = min(self.health + self.upgrades["health"]["value"], self.max_health)
            return self.upgrades["health"]["cost"]

        elif upgrade == "spawn_rate" and player_money >= self.upgrades["spawn_rate"]["cost"]:
            self.spawn_interval = max(500, self.spawn_interval + self.upgrades["spawn_rate"]["value"])
            return self.upgrades["spawn_rate"]["cost"]

        elif upgrade == "attack" and player_money >= self.upgrades["attack"]["cost"]:
            self.attack_power += self.upgrades["attack"]["value"]
            return self.upgrades["attack"]["cost"]

        return 0  # If upgrade is not applicable

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
        """Spawn a troop at intervals specific to this tower."""
        if current_time - self.last_spawn_time > self.spawn_interval:
            x = self.rect.centerx
            y = self.rect.top if not self.is_enemy else self.rect.bottom - TROOP_SIZE
            direction = -1 if self.is_enemy else 1
            troops.append(Troop(x, y, direction, self.is_enemy))
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

    def move(self, allies):
        """Handle movement and attacking animation."""
        if self.attacking:
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
            self.avoid_allies(allies)
            self.y -= TROOP_SPEED * self.direction

    def avoid_allies(self, allies):
        """Adjust horizontal position to avoid overlapping with allies."""
        for ally in allies:
            if ally != self and self.get_rect().colliderect(ally.get_rect()):
                if self.x < ally.x:
                    self.x -= 1  # Move left to avoid collision
                else:
                    self.x += 1  # Move right to avoid collision

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


class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback

    def draw(self, screen, font, color=WHITE, text_color=BLACK):
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surface = font.render(self.text, True, text_color)
        screen.blit(
            text_surface,
            (self.rect.centerx - text_surface.get_width() // 2,
             self.rect.centery - text_surface.get_height() // 2)
        )

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]  # Left click

# Functions
def upgrade_menu(screen, upgrades, player_money):
    """Display available upgrades dynamically."""
    menu_x, menu_y = 150, 350
    menu_width, menu_height = 200, len(upgrades) * 40 + 20

    # Draw menu background
    pygame.draw.rect(screen, WHITE, (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(screen, BLACK, (menu_x, menu_y, menu_width, menu_height), 2)

    # Render upgrade options
    font = pygame.font.Font(None, 26)
    for i, upgrade in enumerate(upgrades):
        upgrade_text = f"{upgrade['name']} (${upgrade['cost']})"
        text_surface = font.render(upgrade_text, True, BLACK)
        option_rect = pygame.Rect(menu_x + 10, menu_y + 10 + i * 40, menu_width - 20, 30)
        pygame.draw.rect(screen, GREEN if player_money >= upgrade['cost'] else RED, option_rect)
        pygame.draw.rect(screen, BLACK, option_rect, 2)
        screen.blit(
            text_surface,
            (option_rect.centerx - text_surface.get_width() // 2,
             option_rect.centery - text_surface.get_height() // 2)
        )

    return [(pygame.Rect(menu_x + 10, menu_y + 10 + i * 40, menu_width - 20, 30), upgrade)
            for i, upgrade in enumerate(upgrades)]


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

    buttons = [
        Button(10, 250, 30, 30, "T1", lambda: "tower1"),
        Button(10, 300, 30, 30, "T2", lambda: "tower2"),
        Button(10, 350, 30, 30, "Trp", lambda: "troops"),
        Button(10, 400, 30, 30, "B", lambda: "base"),
    ]

    selected_entity = None  # Currently selected upgradeable entity
    upgrade_options = []    # Options for the selected entity        # Tracks the position of the active menu

    running = True
    while running:
        screen.fill(BROWN)
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle button clicks
        for button in buttons:
            if button.is_clicked(mouse_pos, mouse_pressed):
                selected_entity = button.callback()  # Select the corresponding entity
                # Set upgrade options based on the selected entity
                if selected_entity == "tower1":
                    upgrade_options = player_towers[0].upgrades
                elif selected_entity == "tower2":
                    upgrade_options = player_towers[1].upgrades
                elif selected_entity == "troops":
                    upgrade_options = [
                        {"name": "Health +10", "cost": 50, "action": "health"},
                        {"name": "Spd +0.1", "cost": 75, "action": "speed"},
                        {"name": "Dmg +1", "cost": 100, "action": "damage"},
                    ]
                elif selected_entity == "base":
                    upgrade_options = player_towers[2].upgrades

        # Draw buttons
        for button in buttons:
            button.draw(screen, font)

        # Display the upgrade menu for the selected entity
        if selected_entity:
            options_rects = upgrade_menu(screen, upgrade_options, player_money)

            # Handle menu interactions
            if mouse_pressed[0]:  # Left click
                for option_rect, upgrade in options_rects:
                    if option_rect.collidepoint(mouse_pos):
                        # Apply upgrade logic here
                        if selected_entity.startswith("tower"):
                            tower_index = int(selected_entity[-1]) - 1
                            cost = player_towers[tower_index].apply_upgrade(upgrade["action"], player_money)
                            if cost > 0:
                                player_money -= cost
                        elif selected_entity == "troops":
                            if upgrade["action"] == "health" and player_money >= upgrade["cost"]:
                                TROOP_HEALTH += 10
                                player_money -= upgrade["cost"]
                            elif upgrade["action"] == "speed" and player_money >= upgrade["cost"]:
                                TROOP_SPEED += 0.1
                                player_money -= upgrade["cost"]
                            elif upgrade["action"] == "damage" and player_money >= upgrade["cost"]:
                                TROOP_DAMAGE += 1
                                player_money -= upgrade["cost"]

        for tower in player_towers:
            tower.spawn_troop(player_troops, current_time)  # Player troops spawn from player towers
        for tower in enemy_towers:
            tower.spawn_troop(enemy_troops, current_time)  # Enemy troops spawn from enemy towers


        # Move player troops, checking for collisions with enemy troops
        for player_troop in player_troops:
            player_troop.move(player_troops)

        # Move enemy troops, checking for collisions with player troops
        for enemy_troop in enemy_troops:
            enemy_troop.move(enemy_troops)

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
