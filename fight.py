import sys
import os
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

# --- Optional Gemini import ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Using random scores instead.")

# --- Load API key if available ---
api_key = None
if GEMINI_AVAILABLE:
    try:
        with open("api_key.txt", "r") as f:
            api_key = f.read().strip()
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            print("⚠️ 'api_key.txt' is empty.")
            GEMINI_AVAILABLE = False
    except Exception as e:
        print(f"⚠️ Could not load API key: {e}")
        GEMINI_AVAILABLE = False


class InsultJudge(QWidget):
    def __init__(self):
        super().__init__()
        self.round = 1
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Insult Judge")
        self.setGeometry(200, 200, 800, 400)

        layout = QVBoxLayout()

        # --- Round label ---
        self.round_label = QLabel(f"Round {self.round}")
        self.round_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.round_label)

        # --- Player text boxes ---
        h_layout = QHBoxLayout()
        self.player1_box = QTextEdit()
        self.player1_box.setPlaceholderText("Player 1: Type your insult here...")
        self.player2_box = QTextEdit()
        self.player2_box.setPlaceholderText("Player 2: Type your insult here...")
        h_layout.addWidget(self.player1_box)
        h_layout.addWidget(self.player2_box)
        layout.addLayout(h_layout)

        # --- Judge button ---
        self.judge_button = QPushButton("Judge!")
        self.judge_button.clicked.connect(self.evaluate_insults)
        layout.addWidget(self.judge_button)

        # --- Result label ---
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def evaluate_insults(self):
        insult1 = self.player1_box.toPlainText().strip()
        insult2 = self.player2_box.toPlainText().strip()

        if not insult1 or not insult2:
            QMessageBox.warning(self, "Error", "Both players must enter an insult!")
            return

        # --- Call Gemini or use random fallback ---
        if GEMINI_AVAILABLE and api_key:
            try:
                prompt = f"""
                You are a judge in a humorous insult battle.
                Rate each insult from 1 to 10 based on wit, creativity, and humor.

                Player 1: "{insult1}"
                Player 2: "{insult2}"

                Return JSON only like this:
                {{"player1_score": 7, "player2_score": 4, "winner": "Player 1"}}
                """
                response = model.generate_content(prompt)
                data = json.loads(response.text)
                p1_score = data.get("player1_score", 0)
                p2_score = data.get("player2_score", 0)
                winner = data.get("winner", "Unknown")
            except Exception as e:
                print(f"⚠️ Gemini error: {e}")
                p1_score, p2_score = random.randint(1, 10), random.randint(1, 10)
                winner = "Player 1" if p1_score > p2_score else "Player 2"
        else:
            p1_score, p2_score = random.randint(1, 10), random.randint(1, 10)
            winner = "Player 1" if p1_score > p2_score else "Player 2"

        # --- Display and record result ---
        self.result_label.setText(
            f"Player 1: {p1_score} | Player 2: {p2_score} → Winner: {winner}"
        )

        self.save_results(insult1, insult2, p1_score, p2_score, winner)

        # --- Prepare for next round ---
        self.round += 1
        self.round_label.setText(f"Round {self.round}")
        self.player1_box.clear()
        self.player2_box.clear()

    def save_results(self, insult1, insult2, p1_score, p2_score, winner):
        """Appends results to results.txt in a readable format"""
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
