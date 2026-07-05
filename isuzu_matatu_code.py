import pygame
import random
import os
import sys

pygame.init()

WIDTH, HEIGHT = 420, 680
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ISUZU AUTONOMOUS MATATU")

#Road and lane settings
ROAD_MARGIN = 40                       # grass/shoulder width on each side
ROAD_LEFT = ROAD_MARGIN
ROAD_RIGHT = WIDTH - ROAD_MARGIN
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

#Car dimensions
CAR_W, CAR_H = 46, 78

# Colors
GRASS = (34, 120, 60)
ROAD = (55, 55, 60)
LANE_LINE = (230, 230, 230)
ZEBRA_LIGHT = (240, 240, 240)
ZEBRA_DARK = (40, 40, 40)
MATATU_BODY = (240, 195, 25)      # matatu yellow colour
MATATU_STRIPE = (200, 30, 30)     # red stripe
MATATU_STRIPE2 = (25, 90, 200)    # blue stripe
WINDOW_TINT = (140, 200, 230)
OTHER_CAR_COLORS = [(180, 40, 40), (40, 90, 180), (90, 170, 90), (150, 90, 200), (230, 140, 30)]
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
SCORE_COLOR = (255, 255, 255)
GAMEOVER_RED = (220, 40, 40)

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 60)
small_font = pygame.font.SysFont(None, 36)

# Lane positions
def lane_center_x(lane_index: int) -> int:
    """Return the x pixel center of a given lane index (0, 1, 2)."""
    return ROAD_LEFT + lane_index * LANE_WIDTH + LANE_WIDTH // 2

lane_positions = [200, 400, 600]
current_lane = 1

# Matatu setup
player_width, player_height = 60, 100
player_color = (220, 30, 30)
player_y = HEIGHT - 150
player_x = lane_positions[current_lane]

class Matatu:
    def __init__(self):
        self.lane = 1  # start in middle lane
        self.width = CAR_W
        self.height = CAR_H
        self.y = HEIGHT - self.height - 30
        self.x = lane_center_x(self.lane) - self.width // 2
        self.target_x = self.x
        self.slide_speed = 14

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.target_x = lane_center_x(self.lane) - self.width // 2

    def move_right(self):
        if self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.target_x = lane_center_x(self.lane) - self.width // 2

    def update(self):
        if self.x < self.target_x:
            self.x = min(self.x + self.slide_speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.slide_speed, self.target_x)

    def draw(self, surf):
        x, y, w, h = int(self.x), int(self.y), self.width, self.height

        # body
        body_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, MATATU_BODY, body_rect, border_radius=8)

        # racing stripes (classic matatu decoration)
        stripe_w = w // 6
        pygame.draw.rect(surf, MATATU_STRIPE, (x + w // 2 - stripe_w - 2, y, stripe_w, h))
        pygame.draw.rect(surf, MATATU_STRIPE2, (x + w // 2 + 2, y, stripe_w, h))

        # wheels
        pygame.draw.rect(surf, BLACK, (x - 3, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x - 3, y + h - 26, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + h - 26, 5, 16))

        # label
        font = pygame.font.SysFont("arial", 13, bold=True)
        text = font.render("MATATU", True, BLACK)
        trect = text.get_rect(center=(x + w // 2, y + h // 2 + 2))
        surf.blit(text, trect)

# Speed settings
base_speed = 6
braking = True
obstacle_speed = base_speed

# Vehicle obstacle setup
class OtherCar:
    def __init__(self, lane, speed):
        self.lane = lane
        self.width = CAR_W
        self.height = CAR_H
        self.x = lane_center_x(lane) - self.width // 2
        self.y = -self.height
        self.speed = speed
        self.color = random.choice(OTHER_CAR_COLORS)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):
        self.y += self.speed

    def off_screen(self):
        return self.y > HEIGHT

    def draw(self, surf):
        x, y, w, h = int(self.x), int(self.y), self.width, self.height
        pygame.draw.rect(surf, self.color, (x, y, w, h), border_radius=8)
        pygame.draw.rect(surf, WINDOW_TINT, (x + 6, y + 8, w - 12, 16), border_radius=3)
        pygame.draw.rect(surf, WINDOW_TINT, (x + 6, y + h - 26, w - 12, 16), border_radius=3)
        pygame.draw.rect(surf, BLACK, (x - 3, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x - 3, y + h - 26, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + h - 26, 5, 16))

#Road setup
class Road:
    def __init__(self):
        self.scroll = 0
        self.dash_len = 30
        self.gap_len = 24
        self.zebra_timer = 0
        self.zebra_interval = random.randint(260, 420)  # distance between crossings
        self.zebra_stripes = []  # list of y positions (top) of active zebra crossings

    def update(self, speed):
        self.scroll = (self.scroll + speed) % (self.dash_len + self.gap_len)
        self.zebra_timer += speed
        for z in self.zebra_stripes:
            z["y"] += speed
        self.zebra_stripes = [z for z in self.zebra_stripes if z["y"] < HEIGHT + 60]

        if self.zebra_timer >= self.zebra_interval:
            self.zebra_timer = 0
            self.zebra_interval = random.randint(260, 420)
            self.zebra_stripes.append({"y": -80})

    def draw(self, surf):
        # grass shoulders
        surf.fill(GRASS)
        # road surface
        pygame.draw.rect(surf, ROAD, (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))

        # lane dividing lines (dashed), 2 internal dividers for 3 lanes
        for lane_i in range(1, LANE_COUNT):
            x = ROAD_LEFT + lane_i * LANE_WIDTH
            y = -self.dash_len + self.scroll
            while y < HEIGHT:
                pygame.draw.rect(surf, LANE_LINE, (x - 2, y, 4, self.dash_len))
                y += self.dash_len + self.gap_len

        # road edge lines
        pygame.draw.rect(surf, LANE_LINE, (ROAD_LEFT - 4, 0, 4, HEIGHT))
        pygame.draw.rect(surf, LANE_LINE, (ROAD_RIGHT, 0, 4, HEIGHT))

        # zebra crossings
        for z in self.zebra_stripes:
            top = z["y"]
            stripe_h = 8
            gap = 8
            y = top
            while y < top + 60:
                color = ZEBRA_LIGHT
                pygame.draw.rect(surf, color, (ROAD_LEFT, int(y), ROAD_WIDTH, stripe_h))
                y += stripe_h + gap


# Game state
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ISUZU AUTONOMOUS MATATU")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("arial", 42, bold=True)
    font_mid = pygame.font.SysFont("arial", 22, bold=True)
    font_small = pygame.font.SysFont("arial", 16)

    def new_game():
        return {
            "player": Matatu(),
            "road": Road(),
            "cars": [],
            "peds": [],
            "speed": 5.0,
            "score": 0,
            "car_timer": 0,
            "car_interval": 70,
            "ped_timer": 0,
            "ped_interval": 130,
            "game_over": False,
        }

    state = new_game()

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif not state["game_over"]:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        state["player"].move_left()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        state["player"].move_right()
                else:
                    if event.key == pygame.K_r:
                        state = new_game()

        if not state["game_over"]:
            speed = state["speed"]

            # difficulty ramps up slowly with score
            state["speed"] = min(12.0, 5.0 + state["score"] / 300.0)

            state["player"].update()
            state["road"].update(speed)

            # spawn other cars
            state["car_timer"] += 1
            if state["car_timer"] >= state["car_interval"]:
                state["car_timer"] = 0
                state["car_interval"] = random.randint(50, 100)
                lane = random.randint(0, LANE_COUNT - 1)
                state["cars"].append(OtherCar(lane, speed + random.uniform(-1, 2)))

            # update obstacles
            for c in state["cars"]:
                c.update()
            state["cars"] = [c for c in state["cars"] if not c.off_screen()]


            # score by distance survived
            state["score"] += 1

            # collision detection
            player_rect = state["player"].rect
            for c in state["cars"]:
                if player_rect.colliderect(c.rect):
                    state["game_over"] = True

        # ---------------- DRAW ----------------
        state["road"].draw(screen)

        for p in state["peds"]:
            p.draw(screen)
        for c in state["cars"]:
            c.draw(screen)
        state["player"].draw(screen)

        # HUD
        score_text = font_mid.render(f"Score: {state['score']}", True, SCORE_COLOR)
        screen.blit(score_text, (10, 10))

        if state["game_over"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            go_text = font_big.render("GAME OVER", True, GAMEOVER_RED)
            screen.blit(go_text, go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

            final_score = font_mid.render(f"Final Score: {state['score']}", True, WHITE)
            screen.blit(final_score, final_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))

            restart_text = font_small.render("Press R to restart, ESC to quit", True, WHITE)
            screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()