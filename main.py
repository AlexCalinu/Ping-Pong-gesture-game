import pygame
import sys
import os
import random
import cv2
import mediapipe as mp
import sqlite3

# Cai relative la folderul scriptului, ca jocul sa porneasca din orice director
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

pygame.init()

WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ping Pong 1v1")
MAX_PADDLE_HEIGHT = 200
BONUS_GROWTH = 1.3

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

THEMES = {
    "dark": {
        "bg": (0, 0, 0),
        "fg": (255, 255, 255)
    },
    "light": {
        "bg": (255, 255, 255),
        "fg": (0, 0, 0)
    },
    "retro": {
        "bg": (20, 20, 50),
        "fg": (0, 255, 0)
    }
}
current_theme = "dark"

pygame.mixer.init()

pygame.mixer.music.load(os.path.join(ASSETS_DIR, "background.ogg"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0)

hit_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "ballhit.wav"))
score_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "points.wav"))
hit_sound.set_volume(0.3)
score_sound.set_volume(0.5)

INITIAL_BALL_SPEED_X = 5
INITIAL_BALL_SPEED_Y = 5
ball_speed_x = INITIAL_BALL_SPEED_X
ball_speed_y = INITIAL_BALL_SPEED_Y
paddle_speed = 6

PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
left_paddle = pygame.Rect(20, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 35, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

ball = pygame.Rect(WIDTH // 2 - 15, HEIGHT // 2 - 15, 30, 30)

score_left = 0
score_right = 0


DB_FILE = os.path.join(BASE_DIR, "pong_highscore.db")

def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS highscores (
                mode TEXT PRIMARY KEY,
                score INTEGER
            )
        ''')
        cursor.execute('INSERT OR IGNORE INTO highscores (mode, score) VALUES (?, ?)', ('infinite', 0))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare baza de date la initializare: {e}")
    finally:
        if conn:
            conn.close()

def load_highscore():
    highscore_val = 0
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM highscores WHERE mode = ?', ('infinite',))
        row = cursor.fetchone()
        if row:
            highscore_val = row[0]
    except sqlite3.Error as e:
        print(f"Eroare baza de date la incarcare highscore: {e}")
        # Daca apare eroare, highscore-ul ramane 0
    finally:
        if conn:
            conn.close()
    return highscore_val

def save_highscore(score_val):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('UPDATE highscores SET score = ? WHERE mode = ?', (score_val, 'infinite'))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare baza de date la salvare highscore: {e}")
    finally:
        if conn:
            conn.close()


init_db()
highscore = load_highscore()


font = pygame.font.SysFont("consolas", 30)

clock = pygame.time.Clock()
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Nu am gasit o camera web. Jocul porneste, dar paletele nu pot fi controlate.")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

MAX_BALL_SPEED = 12

bonus_ball = None
BONUS_BALL_SIZE = 20
bonus_spawn_time = 0
BONUS_INTERVAL = 10000
bonus_active_time = 5000
bonus_collected = False

def spawn_bonus_ball():
    global bonus_ball, bonus_spawn_time, bonus_collected
    x = random.randint(100, WIDTH - 100)
    y = random.randint(100, HEIGHT - 100)
    bonus_ball = pygame.Rect(x, y, BONUS_BALL_SIZE, BONUS_BALL_SIZE)
    bonus_spawn_time = pygame.time.get_ticks()
    bonus_collected = False

def set_difficulty(level):
    global ball_speed_x, ball_speed_y, paddle_speed
    if level == "easy":
        ball_speed_x = 4
        ball_speed_y = 4
        paddle_speed = 4
    elif level == "medium":
        ball_speed_x = 5
        ball_speed_y = 5
        paddle_speed = 6
    elif level == "hard":
        ball_speed_x = 6
        ball_speed_y = 6
        paddle_speed = 8

def show_start_screen():
    global difficulty
    run = True
    while run:
        WIN.fill(WHITE)
        font = pygame.font.SysFont("consolas", 50)
        title = font.render("Select Difficulty", True, BLACK)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        easy_button = pygame.Rect(WIDTH // 4 - 100, HEIGHT // 2, 200, 50)
        medium_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
        hard_button = pygame.Rect(WIDTH * 3 // 4 - 100, HEIGHT // 2, 200, 50)

        pygame.draw.rect(WIN, BLACK, easy_button)
        pygame.draw.rect(WIN, BLACK, medium_button)
        pygame.draw.rect(WIN, BLACK, hard_button)

        easy_text = font.render("Easy", True, WHITE)
        medium_text = font.render("Medium", True, WHITE)
        hard_text = font.render("Hard", True, WHITE)

        WIN.blit(easy_text, (WIDTH // 4 - easy_text.get_width() // 2, HEIGHT // 2 + 10))
        WIN.blit(medium_text, (WIDTH // 2 - medium_text.get_width() // 2, HEIGHT // 2 + 10))
        WIN.blit(hard_text, (WIDTH * 3 // 4 - hard_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.collidepoint(event.pos):
                    difficulty = "easy"
                    set_difficulty(difficulty)
                    return
                if medium_button.collidepoint(event.pos):
                    difficulty = "medium"
                    set_difficulty(difficulty)
                    return
                if hard_button.collidepoint(event.pos):
                    difficulty = "hard"
                    set_difficulty(difficulty)
                    return

    pygame.quit()
    sys.exit()

def increase_difficulty():
    global ball_speed_x, ball_speed_y

    def set_speed(target_speed):
        new_speed_x = target_speed if ball_speed_x > 0 else -target_speed
        new_speed_y = target_speed if ball_speed_y > 0 else -target_speed
        return new_speed_x, new_speed_y

    if 3 <= max(score_left, score_right) < 6:
        ball_speed_x, ball_speed_y = set_speed(7)
    elif 6 <= max(score_left, score_right) < 10:
        ball_speed_x, ball_speed_y = set_speed(8)
    elif 10 <= max(score_left, score_right) < 15:
        ball_speed_x, ball_speed_y = set_speed(9)
    elif max(score_left, score_right) >= 15:
        ball_speed_x, ball_speed_y = set_speed(10)



def update_highscore():
    global highscore
    current_game_score = max(score_left, score_right)
    if current_game_score > highscore:
        highscore = current_game_score
        save_highscore(highscore)



def reset_highscore():
    global score_left, score_right, highscore
    score_left = 0
    score_right = 0
    highscore = 0
    save_highscore(0)


def draw():
    colors = THEMES[current_theme]
    WIN.fill(colors["bg"])
    pygame.draw.rect(WIN, colors["fg"], left_paddle)
    pygame.draw.rect(WIN, colors["fg"], right_paddle)
    pygame.draw.ellipse(WIN, colors["fg"], ball)
    pygame.draw.aaline(WIN, colors["fg"], (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

    if bonus_ball and not bonus_collected:
        pygame.draw.ellipse(WIN, (255, 215, 0), bonus_ball)

    left_text = font.render(f"{score_left}", True, colors["fg"])
    right_text = font.render(f"{score_right}", True, colors["fg"])
    highscore_text = font.render(f"Highscore: {highscore}", True, colors["fg"])

    WIN.blit(left_text, (WIDTH // 4, 20))
    WIN.blit(right_text, (WIDTH * 3 // 4, 20))
    WIN.blit(highscore_text, (WIDTH // 2 - 80, HEIGHT - 40))

    pygame.display.update()

def reset_ball():
    global ball_speed_x, ball_speed_y
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_speed_x = INITIAL_BALL_SPEED_X * (-1 if ball_speed_x > 0 else 1)
    ball_speed_y = INITIAL_BALL_SPEED_Y

def handle_paddle_collision():
    global ball_speed_x, ball_speed_y

    if ball.colliderect(left_paddle):
        ball.left = left_paddle.right
        ball_speed_x *= -1

        hit_pos = (ball.centery - left_paddle.centery) / (left_paddle.height / 2)
        ball_speed_y = hit_pos * 6

        if abs(ball_speed_y) < 2:
            ball_speed_y = random.choice([-1, 1]) * 3

        hit_sound.play()

    elif ball.colliderect(right_paddle):
        ball.right = right_paddle.left
        ball_speed_x *= -1

        hit_pos = (ball.centery - right_paddle.centery) / (right_paddle.height / 2)
        ball_speed_y = hit_pos * 6

        if abs(ball_speed_y) < 2:
            ball_speed_y = random.choice([-1, 1]) * 3

        hit_sound.play()

def grow_paddle(paddle):
    if paddle.height < MAX_PADDLE_HEIGHT:
        new_height = int(paddle.height * BONUS_GROWTH)
        if new_height > MAX_PADDLE_HEIGHT:
            new_height = MAX_PADDLE_HEIGHT
        paddle.height = new_height

running = True
difficulty = "medium"
show_start_screen()

cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while running:
    clock.tick(60)
    current_time = pygame.time.get_ticks()

    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                lm = hand_landmarks.landmark[9]

                hand_y_scaled = int(lm.y * HEIGHT)

                hand_label = handedness.classification[0].label

                target_paddle = None

                if hand_label == "Left":
                    target_paddle = left_paddle
                elif hand_label == "Right":
                    target_paddle = right_paddle

                if target_paddle:

                    target_paddle.centery = max(PADDLE_HEIGHT // 2, min(HEIGHT - PADDLE_HEIGHT // 2, hand_y_scaled))




    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                if current_theme == "dark":
                    current_theme = "light"
                elif current_theme == "light":
                    current_theme = "retro"
                else:
                    current_theme = "dark"

            if event.key == pygame.K_m:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                else:
                    pygame.mixer.music.play(-1, 0.0)

            if event.key == pygame.K_r:
                reset_highscore()

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_speed_y *= -1

    handle_paddle_collision()

    if ball.left <= 0:
        score_right += 1
        score_sound.play()
        reset_ball()
    elif ball.right >= WIDTH:
        score_left += 1
        score_sound.play()
        reset_ball()

    increase_difficulty()

    if bonus_ball is None and current_time - bonus_spawn_time > BONUS_INTERVAL:
        spawn_bonus_ball()

    if bonus_ball and current_time > bonus_spawn_time + bonus_active_time:
         bonus_ball = None

    if bonus_ball and ball.colliderect(bonus_ball):
        bonus_collected = True
        bonus_ball = None
        if ball.centerx < WIDTH // 2:
            grow_paddle(left_paddle)
        else:
            grow_paddle(right_paddle)

    update_highscore()

    draw()

cap.release()
pygame.quit()
sys.exit()