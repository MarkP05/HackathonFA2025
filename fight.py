import sys
import os
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt

# --- Try importing Gemini SDK ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("google-generativeai not installed. Using random scores instead.")

# --- Load API Key ---
api_key = None
if GEMINI_AVAILABLE:
    try:
        with open("api_key.txt", "r") as f:
            api_key = f.read().strip()
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            print("'api_key.txt' is empty.")
            GEMINI_AVAILABLE = False
    except Exception as e:
        print(f"Could not load API key: {e}")
        GEMINI_AVAILABLE = False


class InsultJudge(QWidget):
    def __init__(self):
        super().__init__()
        self.round = 1
        self.max_health = 10
        self.player1_health = self.max_health
        self.player2_health = self.max_health
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Insult Judge")
        self.setGeometry(200, 200, 800, 500)

        layout = QVBoxLayout()

        # Round label
        self.round_label = QLabel(f"Round {self.round}")
        self.round_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.round_label)

        # Player text boxes
        h_layout = QHBoxLayout()
        self.player1_box = QTextEdit()
        self.player1_box.setPlaceholderText("Player 1: Type your insult here...")
        self.player2_box = QTextEdit()
        self.player2_box.setPlaceholderText("Player 2: Type your insult here...")
        h_layout.addWidget(self.player1_box)
        h_layout.addWidget(self.player2_box)
        layout.addLayout(h_layout)

        # Health bars below each text box
        self.health_layout = QHBoxLayout()

        # Player 1 red background
        self.p1_health_bar = QFrame()
        self.p1_health_bar.setFrameShape(QFrame.StyledPanel)
        self.p1_health_bar.setStyleSheet("background-color: red;")
        self.p1_health_bar.setFixedHeight(30)

        # Player 2 red background
        self.p2_health_bar = QFrame()
        self.p2_health_bar.setFrameShape(QFrame.StyledPanel)
        self.p2_health_bar.setStyleSheet("background-color: red;")
        self.p2_health_bar.setFixedHeight(30)

        # Add red bars to layout
        self.health_layout.addWidget(self.p1_health_bar)
        self.health_layout.addWidget(self.p2_health_bar)
        layout.addLayout(self.health_layout)

        # Foreground green bars (children of red bars)
        self.p1_health_fore = QFrame(self.p1_health_bar)
        self.p1_health_fore.setStyleSheet("background-color: green;")
        self.p1_health_fore.setFixedHeight(30)

        self.p2_health_fore = QFrame(self.p2_health_bar)
        self.p2_health_fore.setStyleSheet("background-color: green;")
        self.p2_health_fore.setFixedHeight(30)

        # Judge button
        self.judge_button = QPushButton("Judge!")
        self.judge_button.clicked.connect(self.evaluate_insults)
        layout.addWidget(self.judge_button)

        # Result label
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

        # Initial health display
        self.update_health_bars()

    # --- Fixed update_health_bars() as a proper class method ---
    def update_health_bars(self):
        # Get current width of the red bar (parent)
        p1_total_width = self.p1_health_bar.width()
        p2_total_width = self.p2_health_bar.width()

        # Set green bar width as fraction of health
        p1_width = int((self.player1_health / self.max_health) * p1_total_width)
        p2_width = int((self.player2_health / self.max_health) * p2_total_width)

        self.p1_health_fore.setFixedWidth(p1_width)
        self.p2_health_fore.setFixedWidth(p2_width)

    def evaluate_insults(self):
        insult1 = self.player1_box.toPlainText().strip()
        insult2 = self.player2_box.toPlainText().strip()

        if not insult1 or not insult2:
            QMessageBox.warning(self, "Error", "Both players must enter an insult!")
            return

        # Call Gemini or use random fallback
        if GEMINI_AVAILABLE and api_key:
            try:
                prompt = f"""
                You are the judge in a fun, creative insult battle.

                Rate each insult from 1–10 for wit, creativity, and humor.
                Then decide which insult wins.
                Don't let the users input profanity or vulgar language.
                Be lenient and creative in your scoring, don't grade them in the eyes of an older person. 
                This game will be played by college students, ages 18-22, so be mature and flexible with the results.
                Don't make scores impossible to obtain, don't be stingy, but also don't hand out perfect tens unless the insult truly deserves it.

                Return *only* valid JSON in this exact format:
                {{
                    "player1_score": <number>,
                    "player2_score": <number>,
                    "winner": "Player 1" or "Player 2"
                }}

                Player 1: "{insult1}"
                Player 2: "{insult2}"
                """
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.strip("`").replace("json", "").strip()
                data = json.loads(text)
                p1_score = int(data.get("player1_score", random.randint(1, 10)))
                p2_score = int(data.get("player2_score", random.randint(1, 10)))
                winner = data.get("winner", "Unknown")
            except Exception as e:
                print(f"Gemini error: {e}")
                p1_score, p2_score = random.randint(1, 10), random.randint(1, 10)
                winner = "Player 1" if p1_score > p2_score else "Player 2"
        else:
            p1_score, p2_score = random.randint(1, 10), random.randint(1, 10)
            winner = "Player 1" if p1_score > p2_score else "Player 2"

        # Subtract health based on score difference
        diff = abs(p1_score - p2_score)
        if p1_score > p2_score:
            self.player2_health -= diff
            if self.player2_health < 0:
                self.player2_health = 0
        else:
            self.player1_health -= diff
            if self.player1_health < 0:
                self.player1_health = 0

        # Update health bars
        self.update_health_bars()

        # Display and record result
        self.result_label.setText(
            f"Player 1: {p1_score} | Player 2: {p2_score} → Winner: {winner}"
        )
        self.save_results(insult1, insult2, p1_score, p2_score, winner)

        # Check for game over
        if self.player1_health <= 0 or self.player2_health <= 0:
            game_winner = "Player 1" if self.player1_health > 0 else "Player 2"
            QMessageBox.information(self, "Game Over", f"{game_winner} wins the game!")
            # Reset health and round
            self.player1_health = self.max_health
            self.player2_health = self.max_health
            self.update_health_bars()
            self.round = 1
            self.round_label.setText(f"Round {self.round}")

        # Prepare for next round
        self.round += 1
        self.round_label.setText(f"Round {self.round}")
        self.player1_box.clear()
        self.player2_box.clear()

    def save_results(self, insult1, insult2, p1_score, p2_score, winner):
        with open("results.txt", "a", encoding="utf-8") as f:
            f.write(f"Round {self.round}\n")
            f.write(f"Player 1: {insult1}\n")
            f.write(f"Player 2: {insult2}\n")
            f.write(f"Scores: {p1_score} : {p2_score} | Winner: {winner}\n\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InsultJudge()
    window.show()
    sys.exit(app.exec_())
