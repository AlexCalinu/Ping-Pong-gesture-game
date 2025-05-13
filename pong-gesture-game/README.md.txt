# Pong 1v1 – Gesture-Controlled Game

This is a modern version of the classic Pong game, enhanced with gesture control via webcam using **MediaPipe** and **OpenCV**. The game also includes dynamic difficulty, power-up bonuses, a scoring system with persistent high scores using SQLite, and multiple visual themes.

## 🎮 Features

- 🖐️ Gesture-Based Control via webcam
- 🧠 Adaptive Difficulty
- 🟡 Bonus System
- 🏆 High Score Tracking
- 🎨 Theme Switching (press `T`)
- 🔇 Music Toggle (press `M`)
- 🧹 Reset Score (press `R`)

## 🚀 How to Run

```bash
pip install -r requirements.txt
python main.py
```

> ⚠️ Requires a working webcam

## 🧩 Technologies Used

- Python
- Pygame
- OpenCV
- MediaPipe
- SQLite

## 📄 Disclaimer

This project is a result of the PA Lab course at the Faculty of Computer Automation and Electronics (FACE) University of Craiova (http://ace.ucv.ro/)
It demonstrates the application of computer vision techniques for real-time hand tracking, using MediaPipe, combined with a simple physics engine for paddle-ball interactions.
The game also integrates database management to track high scores, creating an interactive and engaging gameplay experience

Functionalities:

Two-player mode with hand tracking for paddle control.

Ball movement and bouncing with increasing speed.

Score tracking and display.

Bonus ball that grows paddles when collected.

Difficulty settings (Easy, Medium, Hard).


Known Issues & Limitations

Hand tracking accuracy may be affected by poor lighting or camera quality.

Hand-paddle assignments may occasionally be incorrect.

Performance depends on webcam quality and system specifications.

Ball speed increases significantly as the score increases, making the game too difficult.

The bonus ball may be hard to see depending on the selected theme.

Hand detection may fail in certain hand positions or when hands overlap.
