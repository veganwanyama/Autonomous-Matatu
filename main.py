import pygame
import random
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Matatu Simulator")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 60)
small_font = pygame.font.SysFont(None, 36)

# Lane positions
lane_positions = [200, 400, 600]
current_lane = 1

# Player setup
player_width, player_height = 60, 100
player_color = (220, 30, 30)
player_y = HEIGHT - 150
player_x = lane_positions[current_lane]

# Speed settings
base_speed = 6
braking = False
obstacle_speed = base_speed

# Vehicle obstacle setup
obstacle_width, obstacle_height = 60, 100
obstacle_color = (30, 30, 220)

# Zebra crossing setup (spans across all lanes, drawn differently)
zebra_height = 40
zebra_color = (255, 255, 255)
zebra_gap_color = (80, 80, 80)

obstacles = []  # each obstacle: {"type": "vehicle"/"zebra", "x":..., "y":...}
spawn_timer = 0
base_spawn_interval = 90
spawn_interval = base_spawn_interval

# Game state
game_over = False
score = 0

HIGHSCORE_FILE = "highscore.txt"

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def save_highscore(value):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(value))

highscore = load_highscore()

def reset_game():
    global current_lane, player_x, obstacles, obstacle_speed, score, game_over, spawn_timer, spawn_interval
    current_lane = 1
    player_x = lane_positions[current_lane]
    obstacles = []
    obstacle_speed = base_speed
    score = 0
    game_over = False
    spawn_timer = 0
    spawn_interval = base_spawn_interval

def spawn_obstacle():
    # Don't spawn a new obstacle too close to the last one
    if obstacles:
        last_obs = obstacles[-1]
        min_gap = 150
        if last_obs["y"] < min_gap - obstacle_height:
            return  # too soon, skip this spawn

    spawn_type = "vehicle" if random.random() < 0.7 else "zebra"

    if spawn_type == "vehicle":
        occupied_lanes = [obs["x"] for obs in obstacles if obs["y"] < obstacle_height * 2]
        available_lanes = [lane for lane in lane_positions if lane not in occupied_lanes]
        if available_lanes:
            lane_choice = random.choice(available_lanes)
            obstacles.append({"type": "vehicle", "x": lane_choice, "y": -obstacle_height})
    else:
        obstacles.append({"type": "zebra", "x": WIDTH // 2, "y": -zebra_height})
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if not game_over:
                if event.key == pygame.K_LEFT and current_lane > 0:
                    current_lane -= 1
                elif event.key == pygame.K_RIGHT and current_lane < 2:
                    current_lane += 1
                elif event.key == pygame.K_SPACE:
                    braking = True
            if game_over and event.key == pygame.K_r:
                reset_game()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                braking = False

    if not game_over:
        difficulty_speed_bonus = score * 0.15
        difficulty_spawn_reduction = score * 1.5
        current_base_speed = base_speed + difficulty_speed_bonus
        spawn_interval = max(30, base_spawn_interval - difficulty_spawn_reduction)

        target_speed = 1 if braking else current_base_speed
        if obstacle_speed < target_speed:
            obstacle_speed += 0.3
        elif obstacle_speed > target_speed:
            obstacle_speed -= 0.5

        target_x = lane_positions[current_lane]
        if player_x < target_x:
            player_x += 10
        elif player_x > target_x:
            player_x -= 10

        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            spawn_obstacle()

        for obs in obstacles:
            obs["y"] += obstacle_speed
        for obs in obstacles:
            if obs["y"] >= HEIGHT + 50 and not obs.get("scored"):
                score += 1
                obs["scored"] = True
        obstacles = [obs for obs in obstacles if obs["y"] < HEIGHT + 50]

       # Check collisions
        player_rect = pygame.Rect(player_x - player_width // 2, player_y, player_width, player_height)
        for obs in obstacles:
            if obs["type"] == "vehicle":
                obs_rect = pygame.Rect(obs["x"] - obstacle_width // 2, obs["y"], obstacle_width, obstacle_height)
                if player_rect.colliderect(obs_rect):
                    game_over = True
            else:  # zebra crossing spans full width
                obs_rect = pygame.Rect(0, obs["y"], WIDTH, zebra_height)
                if player_rect.colliderect(obs_rect):
                    # Only crash if still moving too fast (didn't brake enough)
                    safe_speed_threshold = 1.5
                    if obstacle_speed > safe_speed_threshold:
                        game_over = True

        if game_over and score > highscore:
            highscore = score
            save_highscore(highscore)

    # Draw everything
    screen.fill((50, 50, 50))

    for obs in obstacles:
        if obs["type"] == "vehicle":
            obs_rect = pygame.Rect(obs["x"] - obstacle_width // 2, obs["y"], obstacle_width, obstacle_height)
            pygame.draw.rect(screen, obstacle_color, obs_rect)
        else:
            # Draw zebra crossing as alternating stripes across the road
            stripe_width = 60
            for i, x in enumerate(range(0, WIDTH, stripe_width)):
                color = zebra_color if i % 2 == 0 else zebra_gap_color
                pygame.draw.rect(screen, color, (x, obs["y"], stripe_width, zebra_height))

            # Draw simple pedestrians standing near the crossing
            pedestrian_color = (255, 220, 150)
            pedestrian_positions = [120, 350, 580, 700]
            for px in pedestrian_positions:
                head_radius = 8
                body_width, body_height = 14, 22
                py = obs["y"] - body_height - head_radius
                pygame.draw.circle(screen, pedestrian_color, (px, py), head_radius)
                pygame.draw.rect(screen, pedestrian_color, (px - body_width // 2, py + head_radius, body_width, body_height))

    player_rect = pygame.Rect(player_x - player_width // 2, player_y, player_width, player_height)
    pygame.draw.rect(screen, player_color, player_rect)

    score_text = small_font.render(f"Score: {score}", True, (255, 255, 255))
    highscore_text = small_font.render(f"High Score: {highscore}", True, (255, 215, 0))
    screen.blit(score_text, (20, 20))
    screen.blit(highscore_text, (20, 55))

    if game_over:
        over_text = font.render("GAME OVER", True, (255, 0, 0))
        restart_text = small_font.render("Press R to restart", True, (255, 255, 255))
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()