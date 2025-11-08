import sys
import os
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QColor

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


def load_sprite_transparent(path, size=(150, 150)):
    """Load an image and make magenta (255,0,255) transparent."""
    pix = QPixmap(path)
    img = pix.toImage().convertToFormat(QImage.Format_ARGB32)

    for x in range(img.width()):
        for y in range(img.height()):
            color = img.pixelColor(x, y)
            if color.red() == 255 and color.green() == 0 and color.blue() == 255:
                color.setAlpha(0)
                img.setPixelColor(x, y, color)

    pix = QPixmap.fromImage(img)
    pix = pix.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pix


class InsultJudge(QWidget):
    def __init__(self):
        super().__init__()
        self.round = 1
        self.max_health = 10
        self.player1_health = self.max_health
        self.player2_health = self.max_health
        self.game_number = 1
        self.initUI()

        # Event filter to handle red bar resizing
        self.p1_health_bar.installEventFilter(self)
        self.p2_health_bar.installEventFilter(self)

        # Show game instructions popup
        self.show_instructions()

        # Start a new game by wiping results.txt
        with open("results.txt", "w", encoding="utf-8") as f:
            f.write(f"--- Game {self.game_number} ---\n")

    def initUI(self):
        self.setWindowTitle("Ragebait Simulator")
        self.setGeometry(0, 0, 1300, 900)

        layout = QVBoxLayout()

        # Round label
        self.round_label = QLabel(f"Game {self.game_number} | Round {self.round}")
        self.round_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.round_label)

        # --- Player text boxes with referee in between ---
        h_layout = QHBoxLayout()

        # Player 1 box
        self.player1_box = QTextEdit()
        self.player1_box.setPlaceholderText("Player 1: Type your insult here...")
        self.player1_box.setFixedWidth(600)
        self.player1_box.setFixedHeight(300)

        # Player 2 box
        self.player2_box = QTextEdit()
        self.player2_box.setPlaceholderText("Player 2: Type your insult here...")
        self.player2_box.setFixedWidth(600)
        self.player2_box.setFixedHeight(300)

        # Referee sprite
        ref_pix = load_sprite_transparent(os.path.join("assets", "referee.png"), size=(200, 200))
        self.referee_sprite = QLabel()
        self.referee_sprite.setPixmap(ref_pix)
        self.referee_sprite.setAlignment(Qt.AlignCenter)

        # Winner label above referee as a speech bubble
        self.winner_label = QLabel("")
        self.winner_label.setAlignment(Qt.AlignCenter)
        self.winner_label.setStyleSheet(
            "background-color: #f5f5dc;"
            "border: 2px solid #555;"
            "border-radius: 15px;"
            "padding: 10px;"
            "font-size: 18px;"
            "font-weight: bold;"
            "color: darkblue;"
        )
        self.winner_label.setFixedWidth(180)
        self.winner_label.setWordWrap(True)

        # Referee layout (winner bubble + referee)
        referee_layout = QVBoxLayout()
        referee_layout.addWidget(self.winner_label)
        referee_layout.addWidget(self.referee_sprite)
        referee_layout.setAlignment(Qt.AlignCenter)

        # Add widgets to h_layout with reduced spacing
        h_layout.addWidget(self.player1_box)
        h_layout.addSpacing(20)
        h_layout.addLayout(referee_layout)
        h_layout.addSpacing(20)
        h_layout.addWidget(self.player2_box)

        layout.addLayout(h_layout)

        # --- Player sprites above health bars ---
        self.sprites_layout = QHBoxLayout()
        self.sprites_layout.setSpacing(50)

        # Player1 sprite
        player1_pix = load_sprite_transparent(os.path.join("assets", "player1.png"), size=(180, 180))
        self.player1_sprite = QLabel()
        self.player1_sprite.setPixmap(player1_pix)
        self.player1_sprite.setAlignment(Qt.AlignCenter)

        # Player2 sprite
        player2_pix = load_sprite_transparent(os.path.join("assets", "player2.png"), size=(180, 180))
        self.player2_sprite = QLabel()
        self.player2_sprite.setPixmap(player2_pix)
        self.player2_sprite.setAlignment(Qt.AlignCenter)

        self.sprites_layout.addWidget(self.player1_sprite)
        self.sprites_layout.addSpacing(50)
        self.sprites_layout.addWidget(self.player2_sprite)

        layout.addLayout(self.sprites_layout)

        # --- Health bars layout ---
        self.health_layout = QHBoxLayout()
        layout.addSpacing(20)

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
        self.update_health_bars()

    def show_instructions(self):
        instructions = (
            "Welcome to Ragebait Simulator!\n\n"
            "Players take turns typing insults in their respective text boxes. "
            "The AI judge will score each insult based on creativity and humor. "
            "The difference in scores will subtract health from the losing player. "
            "First player to lose all health loses the game.\n\n"
            "Good luck and have fun!"
        )
        QMessageBox.information(self, "Game Instructions", instructions)

    def eventFilter(self, source, event):
        if event.type() == event.Resize:
            self.update_health_bars()
        return super().eventFilter(source, event)

    def update_health_bars(self):
        p1_total_width = self.p1_health_bar.width()
        p2_total_width = self.p2_health_bar.width()

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

        # Update winner bubble above referee
        self.winner_label.setText(f"{winner} wins!")

        diff = abs(p1_score - p2_score)
        if p1_score > p2_score:
            self.player2_health = max(0, self.player2_health - diff)
        else:
            self.player1_health = max(0, self.player1_health - diff)

        self.update_health_bars()

        self.result_label.setText(f"Player 1: {p1_score} | Player 2: {p2_score}")
        self.save_results(insult1, insult2, p1_score, p2_score, winner)

        if self.player1_health <= 0 or self.player2_health <= 0:
            game_winner = "Player 1" if self.player1_health > 0 else "Player 2"
            play_again = QMessageBox.question(
                self,
                "Game Over",
                f"{game_winner} wins the game!\nDo you want to play again?",
                QMessageBox.Yes | QMessageBox.No
            )
            if play_again == QMessageBox.Yes:
                self.game_number += 1
                self.player1_health = self.max_health
                self.player2_health = self.max_health
                self.round = 1
                self.round_label.setText(f"Game {self.game_number} | Round {self.round}")
                self.winner_label.setText("")
                self.update_health_bars()
                with open("results.txt", "a", encoding="utf-8") as f:
                    f.write(f"--- Game {self.game_number} ---\n")
            else:
                QApplication.quit()
        else:
            self.round += 1
            self.round_label.setText(f"Game {self.game_number} | Round {self.round}")

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
