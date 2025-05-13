import cv2
import pygame
import mediapipe as mp
import sqlite3
import os
import random

# Initialize modules
pygame.init()
pygame.mixer.init()

# Set up display
width, height = 1280, 720
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pong 1v1")

# Load sounds
hit_sound = pygame.mixer.Sound("assets/ballhit.wav")
background_music = "assets/Fundal PONG.wav"
pygame.mixer.music.load(background_music)
pygame.mixer.music.play(-1)

# Ball and paddle properties
ball_radius = 20
ball_x, ball_y = width // 2, height // 2
ball_dx, ball_dy = 5, 5

paddle_width, paddle_height = 20, 150
left_paddle_y = right_paddle_y = height // 2 - paddle_height // 2
paddle_speed = 15

left_score = right_score = 0
theme = 0  # 0: dark, 1: light, 2: retro

# DB setup
db_file = "pong_highscore.db"
if not os.path.exists(db_file):
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE scores (left_score INTEGER, right_score INTEGER)")

def save_score(l, r):
    with sqlite3.connect(db_file) as conn:
        conn.execute("INSERT INTO scores (left_score, right_score) VALUES (?, ?)", (l, r))

def get_high_score():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.execute("SELECT MAX(left_score), MAX(right_score) FROM scores")
        return cursor.fetchone()

# Mediapipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
cap = cv2.VideoCapture(0)

# Bonus
bonus_active = False
bonus_timer = 0
bonus_x, bonus_y = random.randint(100, 1180), random.randint(100, 620)

def draw():
    if theme == 0:
        win.fill((0, 0, 0))
        paddle_color = (255, 255, 255)
        ball_color = (255, 255, 255)
    elif theme == 1:
        win.fill((255, 255, 255))
        paddle_color = (0, 0, 0)
        ball_color = (0, 0, 0)
    else:
        win.fill((0, 255, 0))
        paddle_color = (255, 0, 255)
        ball_color = (0, 0, 0)

    pygame.draw.rect(win, paddle_color, (20, left_paddle_y, paddle_width, paddle_height))
    pygame.draw.rect(win, paddle_color, (width - 40, right_paddle_y, paddle_width, paddle_height))
    pygame.draw.circle(win, ball_color, (ball_x, ball_y), ball_radius)
    
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"{left_score} : {right_score}", True, paddle_color)
    win.blit(score_text, (width // 2 - score_text.get_width() // 2, 20))

    if bonus_active:
        pygame.draw.circle(win, (255, 215, 0), (bonus_x, bonus_y), 15)

    pygame.display.update()

running = True
music_on = True

while running:
    pygame.time.delay(30)
    success, frame = cap.read()
    if not success:
        continue
    frame = cv2.flip(frame, 1)
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    h, w, _ = frame.shape

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * width
            y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y * height
            if x < width // 2:
                left_paddle_y = int(y) - paddle_height // 2
            else:
                right_paddle_y = int(y) - paddle_height // 2

    ball_x += ball_dx
    ball_y += ball_dy

    if ball_y <= 0 or ball_y >= height:
        ball_dy *= -1

    if (20 < ball_x - ball_radius < 40 and left_paddle_y < ball_y < left_paddle_y + paddle_height) or        (width - 40 < ball_x + ball_radius < width - 20 and right_paddle_y < ball_y < right_paddle_y + paddle_height):
        ball_dx *= -1
        hit_sound.play()

    if ball_x < 0:
        right_score += 1
        ball_x, ball_y = width // 2, height // 2
        ball_dx *= -1
        save_score(left_score, right_score)
    elif ball_x > width:
        left_score += 1
        ball_x, ball_y = width // 2, height // 2
        ball_dx *= -1
        save_score(left_score, right_score)

    if bonus_active:
        if abs(ball_x - bonus_x) < 20 and abs(ball_y - bonus_y) < 20:
            bonus_active = False
            paddle_height += 50

    if pygame.time.get_ticks() - bonus_timer > 10000:
        bonus_active = True
        bonus_x, bonus_y = random.randint(100, 1180), random.randint(100, 620)
        bonus_timer = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                theme = (theme + 1) % 3
            if event.key == pygame.K_m:
                music_on = not music_on
                pygame.mixer.music.set_volume(1.0 if music_on else 0.0)
            if event.key == pygame.K_r:
                left_score = right_score = 0

    draw()

cap.release()
pygame.quit()
