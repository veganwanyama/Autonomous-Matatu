import pygame

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Matatu Simulator")

clock = pygame.time.Clock()

# Lane positions (x-coordinates for 3 lanes)
lane_positions = [200, 400, 600]
current_lane = 1  # start in middle lane

# Player (matatu) rectangle
player_width, player_height = 60, 100
player_color = (220, 30, 30)  # red
player_y = HEIGHT - 150  # near bottom of screen
player_x = lane_positions[current_lane]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and current_lane > 0:
                current_lane -= 1
            elif event.key == pygame.K_RIGHT and current_lane < 2:
                current_lane += 1

    # Smoothly move toward target lane
    target_x = lane_positions[current_lane]
    if player_x < target_x:
        player_x += 10
    elif player_x > target_x:
        player_x -= 10

    # Draw everything
    screen.fill((50, 50, 50))  # road background
    player_rect = pygame.Rect(player_x - player_width // 2, player_y, player_width, player_height)
    pygame.draw.rect(screen, player_color, player_rect)

    pygame.display.flip()
    clock.tick(60)  # 60 frames per second

pygame.quit()