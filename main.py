import pygame
import random
import math
import boto3
import os
import tempfile
from botocore.exceptions import ClientError
from dotenv import load_dotenv


# Initialize Pygame
pygame.init()
load_dotenv()


# Screen dimensions and settings
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
FPS = 60
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blue vs Red")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 26)


#Sounds
# hit_sound = pygame.mixer.Sound("./assets/sounds/hit_1.MP3")
# hit_sound2 = pygame.mixer.Sound("./assets/sounds/hit_2.MP3")
# hit_sound.set_volume(0.1)
# hit_sound2.set_volume(0.3)
aws_access_key = os.environ['AWS_ACCESS_KEY_ID']
aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
aws_region = os.environ['AWS_REGION']

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
MONEY_INCREMENT = 10

# Classes
class AudioManager:
    def __init__(self, bucket_name):
        """
        Initialize the AudioManager.
        - Connects to an AWS S3 bucket to download audio files.
        - Sets up Pygame's mixer for playing audio.
        - Creates a temporary directory to store downloaded files.
        """
        self.bucket_name = bucket_name  # Name of the S3 bucket to fetch audio from
        self.s3_client = boto3.client('s3',  # Initialize S3 client using boto3
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),  # AWS credentials from environment variables
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        self.audio_cache = {}  # Dictionary to cache loaded sounds

        self.temp_dir = os.path.join(os.path.dirname(__file__))
        os.makedirs(self.temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Initialize Pygame's mixer for audio playback
        pygame.mixer.init()

    def download_audio(self, s3_key):
        """
        Download an audio file from S3 and save it locally.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns the local file path or None if there's an error.
        """
        local_path = os.path.join(self.temp_dir, os.path.basename(s3_key))  # Define local save path

        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)  # Download file from S3
            return local_path  # Return the local file path
        except ClientError as e:  # Handle download errors
            print(f"Error downloading audio: {e}")
            return None  # Return None if download fails

    def load_sound(self, s3_key):
        """
        Load a sound effect from S3 into the Pygame mixer.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns the Pygame Sound object or None if there's an error.
        """
        if s3_key in self.audio_cache:  # Check if the sound is already cached
            return self.audio_cache[s3_key]

        local_path = self.download_audio(s3_key)  # Download the file if not cached
        if local_path:
            sound = pygame.mixer.Sound(local_path)  # Load the sound into Pygame
            self.audio_cache[s3_key] = sound  # Cache the loaded sound
            return sound
        return None  # Return None if loading fails

    def load_music(self, s3_key):
        """
        Load a background music file from S3 into the Pygame mixer.
        - s3_key: Path of the audio file in the S3 bucket.
        Returns True if the music is loaded successfully, False otherwise.
        """
        local_path = self.download_audio(s3_key)  # Download the file
        if local_path:
            pygame.mixer.music.load(local_path)  # Load the music into the mixer
            return True
        return False

    def play_music(self, loops=-1):
        """
        Play the loaded background music.
        - loops: Number of times to loop the music (-1 for infinite loop).
        """
        pygame.mixer.music.play(loops)

    def stop_music(self):
        """Stop the currently playing background music."""
        pygame.mixer.music.stop()

    def cleanup(self):
        """
        Clean up temporary files created during execution.
        - Deletes the temporary directory and all its contents.
        """
        import shutil

        # Stop and unload the music to release the file lock
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()  # Unloads the currently loaded music file

        shutil.rmtree(self.temp_dir)  # Remove the temporary directory and its contents


class Tower:
    def __init__(self, x, y, id=None, is_enemy=False):
        self.rect = pygame.Rect(x, y, TOWER_SIZE, TOWER_SIZE)
        self.health = 100
        self.max_health = 100  # For percentage calculation
        self.is_enemy = is_enemy
        self.id = id  # Unique identifier for the tower
        self.spawn_interval = 2000 # in milliseconds
        self.attack_power = 1
        self.last_spawn_time = pygame.time.get_ticks()  # Track last spawn time
        self.upgrades = {
            "health": {"value": 50, "cost": 50},
            "spawn_rate": {"value": -200, "cost": 100},
            "attack": {"value": 1, "cost": 75},
        }

    def apply_upgrade(self, upgrade, player_money):
        """Apply an upgrade to this specific tower."""
        if self.is_enemy:
            return 0  # Enemy towers cannot be upgraded

        if upgrade == "health" and player_money >= self.upgrades["health"]["cost"]:
            self.max_health += self.upgrades["health"]["value"]
            self.health = self.max_health  # Restore to max after upgrade
            return self.upgrades["health"]["cost"]

        elif upgrade == "spawn_rate" and player_money >= self.upgrades["spawn_rate"]["cost"]:
            self.spawn_interval = max(1000, self.spawn_interval + self.upgrades["spawn_rate"]["value"])
            return self.upgrades["spawn_rate"]["cost"]

        elif upgrade == "attack" and player_money >= self.upgrades["attack"]["cost"]:
            self.attack_power += self.upgrades["attack"]["value"]
            return self.upgrades["attack"]["cost"]

        return 0  # Return 0 if the upgrade can't be applied

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

        # Add the numerical health value
        font = pygame.font.Font(None, 15)  # Choose a font size
        health_text = f"{int(self.health)}"  # Format health as "current/max"
        text_surface = font.render(health_text, True, BLACK)  # Render text in white
        text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))  # Center text
        screen.blit(text_surface, text_rect)

    def shoot(self, troops):
        """Damage any troop within the tower's range."""
        for troop in troops:
            if self.rect.colliderect(troop.get_rect()):
                troop.health -= 1

    def spawn_troop(self, troops, current_time):
        """Spawn a troop at intervals specific to this tower."""
        if current_time - self.last_spawn_time > self.spawn_interval:
            x = self.rect.centerx
            y = self.rect.top if not self.is_enemy else self.rect.bottom - 10
            direction = -1 if self.is_enemy else 1
            troops.append(Troop(x, y, direction, self.is_enemy))
            self.last_spawn_time = current_time

    def draw(self):
        """Render the tower on the screen."""
        pygame.draw.rect(screen, RED if self.is_enemy else BLUE, self.rect)
        # Draw health bar
        self.draw_health_bar(screen)


class Base(Tower):  # Base extends Tower for simplicity
    def __init__(self, x, y, id=None, is_enemy=False):
        super().__init__(x, y, id=id, is_enemy=is_enemy)
        self.health = 200  # Bases have more health
        self.max_health = 200  # For percentage calculation
        self.id = id  # Unique identifier for the tower


class Troop:
    def __init__(self, x, y, direction, is_enemy=False, audio_manager=None):
        self.x = x
        self.y = y
        self.direction = direction
        self.is_enemy = is_enemy
        self.health = 10
        self.max_health = 10  # For calculating percentage
        self.size = 10
        self.speed = .5
        self.attack_power = .1  # Damage per attack
        self.attacking = False  # Whether the troop is attacking
        self.attack_timer = 20  # Timer for the attack animation
        self.attack_phase = "retreat"  # "back" for retreat, "forward" for attack
        self.target = None  # Current target (troop or structure)
        self.audio_manager = audio_manager  # Reference to the global audio manager
        self.hit_sound = None  # Cached sound
        self.upgrades = {
            "health": {"value": 5, "cost": 50},
            "speed": {"value": 0.1, "cost": 75},
            "attack": {"value": 1, "cost": 100},
        }

        if self.audio_manager:
            self.hit_sound = self.audio_manager.load_sound('hit_1.MP3')
            self.hit_sound.set_volume(0.7)  # Adjust volume level (0.0 to 1.0)

        # Cooldown management
        self.last_hit_sound_time = 0
        self.sound_cooldown = 500  # Cooldown in milliseconds

    def apply_upgrade(self, upgrade, player_money):
        """Apply an upgrade to this specific troop."""
        if self.is_enemy:
            return 0  # Enemy troops cannot be upgraded

        if upgrade == "health" and player_money >= self.upgrades["health"]["cost"]:
            self.max_health += self.upgrades["health"]["value"]
            self.health = self.max_health  # Restore to max after upgrade
            return self.upgrades["health"]["cost"]

        elif upgrade == "speed" and player_money >= self.upgrades["speed"]["cost"]:
            self.speed += self.upgrades["speed"]["value"]
            return self.upgrades["speed"]["cost"]

        elif upgrade == "attack" and player_money >= self.upgrades["attack"]["cost"]:
            self.attack_power += self.upgrades["attack"]["value"]
            return self.upgrades["attack"]["cost"]

        return 0  # Return 0 if the upgrade can't be applied

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

    def target_enemy(self, enemies):
        """
        Determine the nearest enemy troop within a reasonable range.
        """
        detection_radius = 50  # Increase detection radius

        for enemy in enemies:
            distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if distance <= detection_radius:
                return enemy  # Return the first enemy troop in range

        return None  # No valid troop targets

    def target_tower(self, enemy_towers):
        """
        Determine the nearest enemy tower within a certain range.
        """
        detection_radius = 200  # Adjust range for detecting towers
        nearest_tower = None
        min_distance = float('inf')

        for tower in enemy_towers:
            if tower.health > 0:  # Only consider alive towers
                distance = math.hypot(self.x - tower.rect.centerx, self.y - tower.rect.centery)
                if distance <= detection_radius and distance < min_distance:
                    nearest_tower = tower
                    min_distance = distance

        return nearest_tower  # Return the nearest valid tower or None


    def move(self, allies, enemies, enemy_towers):
        """
        Handle movement and attacking based on troop targeting, prioritizing enemy troops.

        """
        # Separate from allies
        self.avoid_allies(allies)

        # Retarget if the current target is invalid or destroyed
        if self.target and hasattr(self.target, "health") and self.target.health <= 0:
            self.target = None

        # Prioritize targeting enemy troops
        if not self.target or isinstance(self.target, Tower):
            troop_target = self.target_enemy(enemies)
            if troop_target:
                self.target = troop_target
            else:
                # If no enemy troops are in range, check for towers in range
                tower_target = self.target_tower(enemy_towers)
                if tower_target:
                    self.target = tower_target

        # Handle movement and attacking
        if self.target:
            if isinstance(self.target, Troop):  # If target is an enemy troop
                dx, dy = self.target.x - self.x, self.target.y - self.y
            elif isinstance(self.target, Tower):  # If target is a tower
                dx = self.target.rect.centerx - self.x
                dy = self.target.rect.centery - self.y
            else:
                dx, dy = 0, 0  # Fallback for safety

            distance_to_target = math.hypot(dx, dy)

            if distance_to_target > self.size:  # If not in range
                # Move closer to the target
                self.x += (dx / distance_to_target) * self.speed
                self.y += (dy / distance_to_target) * self.speed
                if self.attacking:  # Stop attacking if moving
                    self.stop_attack()
            else:
                # Attack the target when in range
                if not self.attacking:  # Start attacking if not already doing so
                    self.start_attack()
                self.animate_attack()  # Animate the attack
                self.target.health -= self.attack_power  # Reduce the target's health
                
            if self.hit_sound and self.target:
                # Play hit sound with a cooldown
                current_time = pygame.time.get_ticks()
                if current_time - self.last_hit_sound_time >= self.sound_cooldown and self.hit_sound:
                    print("Playing hit sound...")  # Debug log
                    self.hit_sound.play()
                    self.last_hit_sound_time = current_time  # Update the last play time
                else:
                    print("Hit sound on cooldown.")  # Debug log
            else:
                print("No target or hit sound not loaded.")  # Debug log
        else:
            # No valid target; move forward
            if self.attacking:
                self.stop_attack()
            self.y -= self.speed * self.direction  # Default movement


    def avoid_allies(self, allies):
        """Adjust horizontal position to avoid overlapping with allies."""
        for ally in allies:
            if ally != self and self.get_rect().colliderect(ally.get_rect()):
                dx = self.x - ally.x
                distance = abs(dx) if dx != 0 else 1
                push = 1 / distance

                if dx < 0:
                    self.x -= push
                else:
                    self.x += push

    def animate_attack(self):
        """
        Handle the attack animation by toggling between 'retreat' and 'advance' phases.
        """
        if self.attack_phase == "retreat":
            self.y += self.speed * self.direction  # Move backward slightly
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_phase = "advance"  # Switch to the 'advance' phase
                self.attack_timer = 20  # Reset timer for the next phase
        elif self.attack_phase == "advance":
            self.y -= self.speed * self.direction  # Move forward slightly
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_phase = "retreat"  # Switch to the 'retreat' phase
                self.attack_timer = 20  # Reset timer for the next phase

    def start_attack(self):
        """Start the attacking animation."""
        if not self.attacking:  # Prevent re-initializing
            self.attacking = True
            self.attack_phase = "retreat"
            self.attack_timer = 10  # Adjust for retreat duration

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
        rect = self.get_rect()

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


class Upgrade:
    def __init__(self, name, cost, effect, target, action):
        """
        Represents a single upgrade.
        :param name: Name of the upgrade (e.g., "Health +50").
        :param cost: Cost of the upgrade.
        :param effect: Effect description or value (for UI purposes).
        :param target: The entity this upgrade applies to (e.g., "Tower", "Troop").
        :param action: A callable function that implements the upgrade logic.
        """
        self.name = name
        self.cost = cost
        self.effect = effect
        self.target = target
        self.action = action  # A function to apply the upgrade


class UpgradeSystem:
    def __init__(self):
        self.upgrades = {}  # Dictionary of upgrades by entity

    def add_upgrade(self, entity_name, upgrade):
        """
        Add an upgrade to a specific entity.
        :param entity_name: The name of the entity (e.g., "Tower1", "Troops").
        :param upgrade: An Upgrade object to be added.
        """
        if entity_name not in self.upgrades:
            self.upgrades[entity_name] = []
        self.upgrades[entity_name].append(upgrade)

    def get_upgrades(self, entity_name):
        """
        Get all upgrades available for a specific entity.
        :param entity_name: The name of the entity.
        :return: List of upgrades for the entity.
        """
        return self.upgrades.get(entity_name, [])

    def apply_upgrade(self, upgrade, player_money):
        """
        Apply a selected upgrade if the player has enough money.
        :param upgrade: The selected Upgrade object.
        :param player_money: The player's current money.
        :return: Updated player money after applying the upgrade.
        """
        if player_money >= upgrade.cost:
            print(f"Applying upgrade: {upgrade.name}")
            upgrade.action()  # Execute the upgrade's logic (e.g., `tower.apply_upgrade`)
            return player_money - upgrade.cost  # Deduct the cost
        return player_money  # No deduction if insufficient funds


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
        upgrade_text = f"{upgrade.name} (${upgrade.cost})"
        text_surface = font.render(upgrade_text, True, BLACK)
        option_rect = pygame.Rect(menu_x + 10, menu_y + 10 + i * 40, menu_width - 20, 30)
        pygame.draw.rect(screen, GREEN if player_money >= upgrade.cost else RED, option_rect)
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
    # Initialize the audio manager
    audio_manager = AudioManager('bvr-game')

    # Preload hit sound
    audio_manager.load_sound('hit_1.MP3')

    # Load and play background music
    audio_manager.load_music('El Bosque Sombrío.mp3')
    audio_manager.play_music(-1)
    pygame.mixer.music.set_volume(0.5)

    # When quitting the game
    audio_manager.stop_music()
    pygame.mixer.stop()
    # audio_manager.cleanup()

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

    player_money = 5000
    enemy_money = 100

    buttons = [
        Button(10, 250, 30, 30, "T1", lambda: "tower1"),
        Button(10, 300, 30, 30, "T2", lambda: "tower2"),
        Button(10, 350, 30, 30, "Trp", lambda: "troops"),
        Button(10, 400, 30, 30, "B", lambda: "base"),
    ]

    # Initialize the UpgradeSystem
    upgrade_system = UpgradeSystem()

    # Add upgrades for entities
    # TOWER 1
    upgrade_system.add_upgrade("tower1", Upgrade(
        name="Health +50",
        cost=50,
        effect="Increases health by 50",
        target="T1",
        action=lambda: player_towers[0].apply_upgrade("health", player_money)
    ))
    upgrade_system.add_upgrade("tower1", Upgrade(
        name="AP +1",
        cost=75,
        effect="Increases attack power by 1",
        target="T1",
        action=lambda: player_towers[0].apply_upgrade("attack", player_money)
    ))
    upgrade_system.add_upgrade("tower1", Upgrade(
        name="SpR -200",
        cost=100,
        effect="Decrease Spawn Interval",
        target="T1",
        action=lambda: player_towers[0].apply_upgrade("spawn_rate", player_money)
    ))

    #TOWER 2
    upgrade_system.add_upgrade("tower2", Upgrade(
        name="Health +50",
        cost=50,
        effect="Increases health by 50",
        target="T2",
        action=lambda: player_towers[1].apply_upgrade("health", player_money)
    ))
    upgrade_system.add_upgrade("tower2", Upgrade(
        name="Attack Power +1",
        cost=75,
        effect="Increases attack power by 1",
        target="T2",
        action=lambda: player_towers[1].apply_upgrade("attack", player_money)
    ))
    upgrade_system.add_upgrade("tower2", Upgrade(
        name="SpR -200",
        cost=100,
        effect="Decrease Spawn Interval",
        target="T2",
        action=lambda: player_towers[1].apply_upgrade("spawn_rate", player_money)
    ))

    #MAIN BASE
    upgrade_system.add_upgrade("base", Upgrade(
        name="Health +50",
        cost=50,
        effect="Increases health by 50",
        target="B",
        action=lambda: player_towers[2].apply_upgrade("health", player_money)
    ))
    upgrade_system.add_upgrade("base", Upgrade(
        name="Attack Power +1",
        cost=75,
        effect="Increases attack power by 1",
        target="B",
        action=lambda: player_towers[2].apply_upgrade("attack", player_money)
    ))
    upgrade_system.add_upgrade("base", Upgrade(
        name="SpR -200",
        cost=100,
        effect="Decrease Spawn Interval",
        target="B",
        action=lambda: player_towers[2].apply_upgrade("spawn_rate", player_money)
    ))

    #TROOPS
    upgrade_system.add_upgrade("troops", Upgrade(
        name="Health +5",
        cost=50,
        effect="Increases troop health by 5",
        target="Trp",
        action=lambda: [troop.apply_upgrade("health", player_money) for troop in player_troops]
    ))
    upgrade_system.add_upgrade("troops", Upgrade(
        name="Speed +0.1",
        cost=75,
        effect="Increases troop speed by 0.1",
        target="Trp",
        action=lambda: [troop.apply_upgrade("speed", player_money) for troop in player_troops]
    ))
    upgrade_system.add_upgrade("troops", Upgrade(
        name="Attack +1",
        cost=100,
        effect="Increases troop attack power by 1",
        target="Trp",
        action=lambda: [troop.apply_upgrade("attack", player_money) for troop in player_troops]
    ))


    selected_entity = None  # Currently selected upgradeable entity
    menu_open = False  # Track whether the menu is currently open
    running = True
    while running:

        screen.fill(BROWN)
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle clicks on buttons
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left-click
                # Check if the menu is already open
                if menu_open:
                    # Check if the click is outside the menu to close it
                    menu_x, menu_y, menu_width, menu_height = 150, 350, 200, len(upgrade_system.get_upgrades(selected_entity)) * 40 + 20
                    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
                    if not menu_rect.collidepoint(event.pos):
                        menu_open = False
                        selected_entity = None
                        continue

                # Check for button clicks
                for button in buttons:
                    if button.is_clicked(event.pos, (True, False, False)):
                        selected_entity = button.callback()
                        menu_open = True  # Open the menu for the selected entity

                # Handle menu interactions
                if menu_open and selected_entity:
                    upgrades = upgrade_system.get_upgrades(selected_entity)
                    options_rects = upgrade_menu(screen, upgrades, player_money)
                    for option_rect, upgrade in options_rects:
                        if option_rect.collidepoint(event.pos):  # Clicked an upgrade
                            player_money = upgrade_system.apply_upgrade(upgrade, player_money)
                            break

        for tower in player_towers:
            tower.spawn_troop(player_troops, current_time)  # Player troops spawn from player towers
        for tower in enemy_towers:
            tower.spawn_troop(enemy_troops, current_time)  # Enemy troops spawn from enemy towers


        # Move player troops, checking for collisions with enemy troops and towers
        for i, player_troop in enumerate(player_troops):
            player_troop.move(
                allies=player_troops,
                enemies=enemy_troops,
                enemy_towers=enemy_towers
            )

        # Move enemy troops, checking for collisions with player troops and towers
        for i, enemy_troop in enumerate(enemy_troops):
            enemy_troop.move(
                allies=enemy_troops,
                enemies=player_troops,
                enemy_towers=player_towers
            )

        # Remove destroyed towers
        enemy_towers = [tower for tower in enemy_towers if tower.health > 0]
        player_towers = [tower for tower in player_towers if tower.health > 0]

        # Example collision handling in game loop
        for player_troop in player_troops:
            player_collision = False  # Tracks if this player troop is colliding with any enemy
            for enemy_troop in enemy_troops:
                if player_troop.get_rect().colliderect(enemy_troop.get_rect()):
                    player_collision = True

                    # Reduce health
                    player_troop.health -= enemy_troop.attack_power
                    enemy_troop.health -= player_troop.attack_power

                    # Stop movement and initiate attack
                    player_troop.start_attack()
                    enemy_troop.start_attack()



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
        player_base = next((base for base in player_towers if isinstance(base, Base)), None)
        enemy_base = next((base for base in enemy_towers if isinstance(base, Base)), None)

        if enemy_base is None or (enemy_base.health <= 0 if enemy_base else False):
            print("Victory! The enemy's base has been destroyed.")
            running = False  # End the game

        if player_base is None or (player_base.health <= 0 if player_base else False):
            print("Defeat! Your base has been destroyed.")
            running = False  # End the game


        # Draw buttons
        for button in buttons:
            button.draw(screen, font)

        # Draw upgrade menu if open
        if menu_open and selected_entity:
            upgrades = upgrade_system.get_upgrades(selected_entity)
            upgrade_menu(screen, upgrades, player_money)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
