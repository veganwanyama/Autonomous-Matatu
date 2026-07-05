import pygame
import random
import sys

pygame.init()

# screen size - went with portrait since it feels more like a phone monitor app
WIDTH = 420
HEIGHT = 680
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ISUZU AUTONOMOUS MATATU")

# road doesnt take the whole screen, leave some grass on sides
road_start = 40
road_end = WIDTH - 40
road_w = road_end - road_start

# 3 lanes across the road
num_lanes = 3
lane_w = road_w // num_lanes

# car size - tweaked this a few times to look right
CAR_W = 46
CAR_H = 78

# --- colours ---
GRASS = (34, 120, 60)
ROAD = (55, 55, 60)
LANE_LINE = (230, 230, 230)
ZEBRA_WHITE = (240, 240, 240)
ZEBRA_DARK = (40, 40, 40)
FENCE_POSTS = (255,255,208)
FENCE_NET = (255,255,0)

# matatu is yellow with red and blue stripes (classic kenya colours)
MATATU_YELLOW = (240, 195, 25)
STRIPE_RED = (200, 30, 30)
STRIPE_BLUE = (25, 90, 200)
WINDOW_COLOR = (140, 200, 230)

# other cars get random colors from this list
CAR_COLORS = [
    (180, 40, 40),
    (40, 90, 180),
    (90, 170, 90),
    (150, 90, 200),
    (230, 140, 30)
]

WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (220, 40, 40)
GOLD = (255, 215, 0)
SKIN = (255, 220, 150)  # pedestrian colour

clock = pygame.time.Clock()

# fonts
big_font = pygame.font.SysFont("arial", 42, bold=True)
mid_font = pygame.font.SysFont("arial", 22, bold=True)
small_font = pygame.font.SysFont("arial", 16)


# gives back the x position of the center of a lane
# lane 0 = leftmost, lane 2 = rightmost
def lane_x(lane_num):
    return road_start + lane_num * lane_w + lane_w // 2


# ---- MATATU (player car) ----
class Matatu:
    def __init__(self):
        self.lane = 1  # start in middle
        self.w = CAR_W
        self.h = CAR_H
        self.y = HEIGHT - self.h - 30
        self.x = lane_x(self.lane) - self.w // 2
        self.target_x = self.x
        self.move_spd = 14  # how fast it slides between lanes

    # collision box
    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def go_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.target_x = lane_x(self.lane) - self.w // 2

    def go_right(self):
        if self.lane < num_lanes - 1:
            self.lane += 1
            self.target_x = lane_x(self.lane) - self.w // 2

    def update(self):
        # slide smoothly toward target lane
        if self.x < self.target_x:
            self.x = min(self.x + self.move_spd, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.move_spd, self.target_x)

    def draw(self, surf):
        x = int(self.x)
        y = int(self.y)
        w = self.w
        h = self.h

        # yellow body
        pygame.draw.rect(surf, MATATU_YELLOW, (x, y, w, h), border_radius=8)

        # the two racing stripes down the middle
        sw = w // 6
        pygame.draw.rect(surf, STRIPE_RED, (x + w//2 - sw - 2, y, sw, h))
        pygame.draw.rect(surf, STRIPE_BLUE, (x + w//2 + 2, y, sw, h))

        # 4 wheels
        pygame.draw.rect(surf, BLACK, (x - 3, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + 10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x - 3, y + h - 26, 5, 16))
        pygame.draw.rect(surf, BLACK, (x + w - 2, y + h - 26, 5, 16))

        # matatu label in the middle
        lbl = pygame.font.SysFont("arial", 13, bold=True)
        txt = lbl.render("MATATU", True, BLACK)
        surf.blit(txt, txt.get_rect(center=(x + w//2, y + h//2 + 2)))


# ---- OTHER CARS (obstacles) ----
class Car:
    def __init__(self, lane, spd):
        self.lane = lane
        self.w = CAR_W
        self.h = CAR_H
        self.x = lane_x(lane) - self.w // 2
        self.y = -self.h  # start just above screen
        self.spd = spd
        self.color = random.choice(CAR_COLORS)
        self.counted = False  # so we only add score once

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, spd):
        self.y += spd

    def gone(self):
        return self.y > HEIGHT

    def draw(self, surf):
        x = int(self.x)
        y = int(self.y)
        w = self.w
        h = self.h

        pygame.draw.rect(surf, self.color, (x, y, w, h), border_radius=8)

        # windshields front and back
        pygame.draw.rect(surf, WINDOW_COLOR, (x+6, y+8, w-12, 16), border_radius=3)
        pygame.draw.rect(surf, WINDOW_COLOR, (x+6, y+h-26, w-12, 16), border_radius=3)

        # wheels same as matatu
        pygame.draw.rect(surf, BLACK, (x-3, y+10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x+w-2, y+10, 5, 16))
        pygame.draw.rect(surf, BLACK, (x-3, y+h-26, 5, 16))
        pygame.draw.rect(surf, BLACK, (x+w-2, y+h-26, 5, 16))


# ---- ZEBRA CROSSING ----
class ZebraCrossing:
    def __init__(self):
        self.y = -80
        self.h = 60
        self.stripe = 8
        self.gap = 8
        self.counted = False

        # pedestrians stand on the grass shoulders, not in the road
        # so they dont block lanes
        self.ped_xs = [
            road_start - 25,        # left side grass
            road_end + 10,          # right side grass
        ]

    def get_rect(self):
        return pygame.Rect(road_start, int(self.y), road_w, self.h)

    def update(self, spd):
        self.y += spd

    def gone(self):
        return self.y > HEIGHT + 60

    def draw(self, surf):
        # alternating white and dark stripes
        y = self.y
        light = True
        while y < self.y + self.h:
            c = ZEBRA_WHITE if light else ZEBRA_DARK
            pygame.draw.rect(surf, c, (road_start, int(y), road_w, self.stripe))
            y += self.stripe + self.gap
            light = not light

        # little pedestrian figures on each side
        for px in self.ped_xs:
            head_r = 6
            bw = 10
            bh = 18
            # position them just above the crossing
            py = int(self.y) - bh - head_r - 2
            pygame.draw.circle(surf, SKIN, (int(px), py), head_r)
            pygame.draw.rect(surf, SKIN, (int(px) - bw//2, py + head_r, bw, bh))


# ---- ROAD (scrolling background) ----
class Road:
    def __init__(self):
        self.scroll = 0
        self.dash = 30   # length of each dashed line
        self.gap = 24    # gap between dashes

    def update(self, spd):
        # keep scroll looping so dashes animate continuously
        self.scroll = (self.scroll + spd) % (self.dash + self.gap)

    def draw(self, surf):
        # grass on both sides
        surf.fill(GRASS)

        #fence bodering both sides of the road
        fence_gap = 34
        post_w = 6 
        post_h = 24

        left_fence_x = road_start - 20
        right_fence_x = road_end + 18

        pygame.draw.rect(surf, FENCE_NET, (left_fence_x -6, 0, 4, HEIGHT))
        pygame.draw.rect(surf, FENCE_NET, (right_fence_x -6, 0, 4, HEIGHT))

        y = -fence_gap + self.scroll
        while y < HEIGHT:
            pygame.draw.rect(surf, FENCE_POSTS, (left_fence_x, int(y), post_w, post_h))
            pygame.draw.rect(surf, FENCE_POSTS, (right_fence_x, int(y), post_w, post_h))
            y += post_h + fence_gap 


        # main road surface
        pygame.draw.rect(surf, ROAD, (road_start, 0, road_w, HEIGHT))

        # dashed lane dividers
        for i in range(1, num_lanes):
            x = road_start + i * lane_w
            y = -self.dash + self.scroll
            while y < HEIGHT:
                pygame.draw.rect(surf, LANE_LINE, (x-2, int(y), 4, self.dash))
                y += self.dash + self.gap

        # solid edge lines on both sides of road
        pygame.draw.rect(surf, LANE_LINE, (road_start - 4, 0, 4, HEIGHT))
        pygame.draw.rect(surf, LANE_LINE, (road_end, 0, 4, HEIGHT))


# ---- MAIN GAME LOOP ----
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ISUZU AUTONOMOUS MATATU")
    clock = pygame.time.Clock()

    def fresh_game():
        return {
            "matatu": Matatu(),
            "road": Road(),
            "cars": [],
            "zebras": [],
            "spd": 5.0,
            "score": 0,
            "car_timer": 0,
            "next_car": 70,       # frames until next car spawns
            "zebra_timer": 0,
            "next_zebra": random.randint(500, 800),
            "braking": False,
            "dead": False,        # game over flag
        }

    g = fresh_game()
    running = True

    while running:
        clock.tick(FPS)

        # --- handle input ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif not g["dead"]:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        g["matatu"].go_left()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        g["matatu"].go_right()
                    elif event.key == pygame.K_SPACE:
                        g["braking"] = True

                elif event.key == pygame.K_r:
                    g = fresh_game()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    g["braking"] = False

        # --- update game if still alive ---
        if not g["dead"]:

            # speed increases slowly as score goes up
            # max speed capped at 12 so it doesnt get ridiculous
            top_spd = min(12.0, 5.0 + g["score"] / 300.0)

            # braking slows everything to 1, releasing speeds back up
            want_spd = 1.0 if g["braking"] else top_spd
            if g["spd"] < want_spd:
                g["spd"] = min(g["spd"] + 0.3, want_spd)
            elif g["spd"] > want_spd:
                g["spd"] = max(g["spd"] - 0.8, want_spd)

            spd = g["spd"]

            g["matatu"].update()
            g["road"].update(spd)

            # spawn a new car every so often
            g["car_timer"] += 1
            if g["car_timer"] >= g["next_car"]:
                g["car_timer"] = 0
                g["next_car"] = random.randint(50, 110)

                # check which lanes already have cars near the top
                # always keep at least 2 lanes free so its not impossible
                busy = [c.lane for c in g["cars"] if c.y < CAR_H * 4]
                free = [l for l in range(num_lanes) if l not in busy]
                if len(free) >= 2:
                    g["cars"].append(Car(random.choice(free), spd))

            # spawn zebra crossings less often than cars
            g["zebra_timer"] += spd
            if g["zebra_timer"] >= g["next_zebra"]:
                g["zebra_timer"] = 0
                g["next_zebra"] = random.randint(500, 800)
                g["zebras"].append(ZebraCrossing())

            # move everything
            for c in g["cars"]:
                c.update(spd)
            for z in g["zebras"]:
                z.update(spd)

            # remove anything that went off screen
            g["cars"] = [c for c in g["cars"] if not c.gone()]
            g["zebras"] = [z for z in g["zebras"] if not z.gone()]

            # score - add points for each obstacle that passed safely
            for c in g["cars"]:
                if c.y > HEIGHT and not c.counted:
                    c.counted = True
                    g["score"] += 1
            for z in g["zebras"]:
                if z.y > HEIGHT and not z.counted:
                    z.counted = True
                    g["score"] += 2  # zebra worth more since you have to brake

            # check collisions
            prect = g["matatu"].get_rect()

            for c in g["cars"]:
                if prect.colliderect(c.get_rect()):
                    g["dead"] = True

            for z in g["zebras"]:
                if prect.colliderect(z.get_rect()):
                    # only die if still going fast
                    # braking enough = safe to cross
                    if spd > 1.5:
                        g["dead"] = True

        # --- draw everything ---
        g["road"].draw(screen)

        for z in g["zebras"]:
            z.draw(screen)
        for c in g["cars"]:
            c.draw(screen)
        g["matatu"].draw(screen)

        # score top left
        screen.blit(mid_font.render(f"Score: {g['score']}", True, WHITE), (10, 10))
        screen.blit(small_font.render("BRAKE [SPACE]", True, (200, 200, 200)), (10, 35))

        # shows braking warning at the bottom
        if g["braking"]:
            brake_txt = mid_font.render("!! BRAKING !!", True, (255, 80, 80))
            screen.blit(brake_txt, brake_txt.get_rect(center=(WIDTH//2, HEIGHT - 30)))

        # game over overlay
        if g["dead"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            screen.blit(
                big_font.render("GAME OVER", True, RED),
                big_font.render("GAME OVER", True, RED).get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
            )
            screen.blit(
                mid_font.render(f"Final Score: {g['score']}", True, WHITE),
                mid_font.render(f"Final Score: {g['score']}", True, WHITE).get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            )
            screen.blit(
                small_font.render("R to restart  |  ESC to quit", True, WHITE),
                small_font.render("R to restart  |  ESC to quit", True, WHITE).get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            )
            

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()