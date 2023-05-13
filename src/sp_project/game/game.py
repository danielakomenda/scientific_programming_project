import pygame
import random


# Initialize Pygame
pygame.init()

# Set up the game window
window_width = 800
window_height = 600
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Thunderbolt Dodge")

# Load mountain image
mountain_image = pygame.image.load("mountain.jpeg")

# Set up character image
character_image = pygame.image.load("character.png")
character_rect = character_image.get_rect(center=(window_width // 2, window_height - character_image.get_height()))

# Set up thunderbolt image
thunderbolt_image = pygame.image.load("thunderbolt.png")
# Store thunderbolt positions
thunderbolts = []

# Set up game clock
clock = pygame.time.Clock()

# Set up game variables
score = 0
game_over = False

# Game loop
while not game_over:
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True

    # Update character position based on arrow key
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        character_rect.x -= 5
    elif keys[pygame.K_RIGHT]:
        character_rect.x += 5

    # Generate new thunderbolts
    if len(thunderbolts) < 10:
        thunderbolt_x = random.randint(0, window_width - thunderbolt_image.get_width())
        thunderbolt_y = 0
        thunderbolt_rect = thunderbolt_image.get_rect(topleft=(thunderbolt_x, thunderbolt_y))
        thunderbolts.append(thunderbolt_rect)

    # Update thunderbolt positions
    for thunderbolt in thunderbolts:
        thunderbolt.y += 5

        # Check if thunderbolt hits the character
        if thunderbolt.colliderect(character_rect):
            game_over = True

        # Check if thunderbolt is missed
        elif thunderbolt.y >= window_height:
            thunderbolts.remove(thunderbolt)
            score += 1

    # Blit mountain image onto the game window
    window.blit(mountain_image, (0, 0))

    # Blit character and thunderbolts onto the game window
    for thunderbolt in thunderbolts:
        window.blit(thunderbolt_image, thunderbolt)
    window.blit(character_image, character_rect)

    # Update game display
    pygame.display.update()

    # Set game frame rate
    clock.tick(30)  # 30 FPS

# Game over
pygame.quit()

