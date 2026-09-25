#!/usr/bin/env python3

import io
import random
import tkinter as tk
from pathlib import Path

import cairosvg
from PIL import Image, ImageTk
import pygame
#============================================================
#NIDIA'S SLOTS
#============================================================

PROJECT_DIR = Path.home() / "Code" / "nidias-slots"
ICON_DIR = Path("/usr/share/icons/Papirus/128x128/apps")
SOUND_DIR = Path("/usr/share/sounds")

SPIN_SOUND = SOUND_DIR / "Oxygen-Sys-Special.ogg"
REEL_STOP_SOUND = SOUND_DIR / "Oxygen-Sys-List-End.ogg"
WIN_SOUND = SOUND_DIR / "Oxygen-Sys-List-Match-Multiple.ogg"
LOSE_SOUND = SOUND_DIR / "Oxygen-Sys-App-Negative.ogg"

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 850

ROWS = 3
REELS = 5

STARTING_CREDITS = 100
MIN_BET = 1
MAX_BET = 10

ICON_SIZE = 128
#Time between reel animation frames.

ANIMATION_SPEED = 75
#Each reel stops slightly later than the previous reel.

REEL_STOP_DELAY = 550
#Number of animation cycles before a reel stops.

SPIN_FRAMES = 16
#============================================================
#ICONS
#============================================================

ICON_FILES = [
"gnome-weather.svg",
"bell.svg",
"clementine.svg",
"among-us.svg",
"annas-quest.svg",
"granatier.svg",
"badland.svg",
"bendy-and-the-ink-machine.svg",
"billard-gl.svg",
"element4l.svg",
"blobwars.svg",
"blush-blush.svg",
"cherrytree.svg",
"celeste.svg",
"chess.svg",
"crab-game.svg",
"crawl.svg",
"cuphead.svg",
"emerald-theme-manager-icon.svg",
"desura.svg",
"dont-starve-together.svg",
"fceux.svg",
]
#============================================================
#PAYLINES
#============================================================
#Each number represents the row used by that reel:
#0 = top
#1 = middle
#2 = bottom
#These give us five visually different lines.

PAYLINES = [
[0, 0, 0, 0, 0], # Top
[1, 1, 1, 1, 1], # Middle
[2, 2, 2, 2, 2], # Bottom
[0, 1, 2, 1, 0], # Down and up
[2, 1, 0, 1, 2], # Up and down
]
#============================================================
#PAYTABLE
#============================================================
#Number of consecutive matching symbols from the left.
#These are intentionally generous for the prototype.

PAYOUTS = {
2: 1,
3: 3,
4: 8,
5: 20,
}
#============================================================
#SLOT MACHINE ENGINE
#============================================================

class SlotMachine:

    def __init__(self):
        self.icons = self.load_icons()

        if not self.icons:
            raise RuntimeError(
                "No Papirus icons could be loaded.\n\n"
                f"Expected location:\n{ICON_DIR}"
            )

        self.credits = STARTING_CREDITS
        self.bet_per_line = MIN_BET

        self.reels = [
            [
                random.randrange(len(self.icons))
                for _ in range(ROWS)
            ]
            for _ in range(REELS)
        ]

    def load_icons(self):
        loaded = []

        for filename in ICON_FILES:
            path = ICON_DIR / filename

            if not path.exists():
                print(f"Warning: icon not found: {path}")
                continue

            try:
                png_data = cairosvg.svg2png(
                    url=str(path),
                    output_width=ICON_SIZE,
                    output_height=ICON_SIZE,
                )

                image = Image.open(
                    io.BytesIO(png_data)
                ).convert("RGBA")

                loaded.append({
                    "filename": filename,
                    "image": image,
                })

            except Exception as exc:
                print(f"Could not load {filename}: {exc}")

        return loaded

    def random_symbol(self):
        weights = [10] * min(8, len(self.icons))

        if len(self.icons) > 8:
            weights += [1] * (len(self.icons) - 8)

        return random.choices(
            range(len(self.icons)),
            weights=weights,
            k=1
        )[0]

    def generate_spin(self):
        return [
            [
                self.random_symbol()
                for _ in range(ROWS)
            ]
            for _ in range(REELS)
        ]

    def total_bet(self):
        return self.bet_per_line * len(PAYLINES)

    def evaluate_lines(self):
        wins = []

        for line_number, line in enumerate(PAYLINES, start=1):

            symbols = [
                self.reels[reel][line[reel]]
                for reel in range(REELS)
            ]

            first_symbol = symbols[0]
            count = 1

            for symbol in symbols[1:]:
                if symbol == first_symbol:
                    count += 1
                else:
                    break

            if count >= 2:

                if count == 2:
                    multiplier = PAYOUTS[2]
                if count == 3:
                    multiplier = PAYOUTS[3]
                elif count == 4:
                    multiplier = PAYOUTS[4]
                else:
                    multiplier = PAYOUTS[5]

                payout = self.bet_per_line * multiplier

                wins.append({
                    "line": line_number,
                    "count": count,
                    "symbol": first_symbol,
                    "payout": payout,
                    "positions": [
                        (reel, line[reel])
                        for reel in range(count)
                    ],
                })

        return wins

# --------------------------------------------------------

# Total wager

# --------------------------------------------------------

    def total_bet(self):
        return (
            self.bet_per_line
            * len(PAYLINES)
        )

#============================================================
#GUI
#============================================================

class NidiaSlotsApp:

    def __init__(self, root):

        self.root = root
        pygame.mixer.init()
        self.spin_sound = pygame.mixer.Sound(str(SPIN_SOUND))
        self.reel_stop_sound = pygame.mixer.Sound(str(REEL_STOP_SOUND))
        self.win_sound = pygame.mixer.Sound(str(LOSE_SOUND))
        self.lose_sound = pygame.mixer.Sound(str(WIN_SOUND))

        self.root.title(
            "Nidia's Slots"
        )

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.configure(
            bg="#35063E"
        )

        self.root.resizable(
            False,
            False
        )

        self.machine = SlotMachine()

        self.images = []

        self.spinning = False
        self.flash_state = False
        self.flash_job = None
        self.winning_positions = set()

        self.animation_frame = 0

        self.stop_after = [
            False
            for _ in range(REELS)
        ]

        self.build_interface()

        self.update_display()

# ========================================================

# INTERFACE

# ========================================================

    def build_interface(self):

        # ----------------------------------------------------

        # Title

        # ----------------------------------------------------

        title = tk.Label(
            self.root,
            text="NIDIA'S SLOTS",
            font=(
                "DejaVu Sans",
                34,
                "bold"
            ),
            fg="#ffd700",
            bg="#35063E",
        )

        title.pack(
            pady=(18, 5)
        )

        self.message_label = tk.Label(
            self.root,
            text="GOOD LUCK!",
            width=30,
            font=(
                "DejaVu Sans",
                16,
                "bold"
            ),
            fg="#ffffff",
            bg="#35063E",
        )

        self.message_label.pack(
            pady=(0, 10)
        )

        # ----------------------------------------------------

        # Machine

        # ----------------------------------------------------

        machine = tk.Frame(
            self.root,
            bg="#d4af37",
            bd=12,
            relief=tk.RIDGE,
        )

        machine.pack(
            padx=20,
            pady=10
        )

        # ----------------------------------------------------

        # Reel area

        # ----------------------------------------------------

        reel_frame = tk.Frame(
            machine,
            bg="#111111",
            bd=8,
            relief=tk.SUNKEN,
        )

        reel_frame.pack(
            padx=12,
            pady=12
        )

        self.reel_labels = []

        for reel in range(REELS):

            column = []

            for row in range(ROWS):

                label = tk.Label(
                    reel_frame,
                    width=ICON_SIZE,
                    height=ICON_SIZE,
                    bg="#ffffff",
                    bd=3,
                    relief=tk.RIDGE,
                )

                label.grid(
                    row=row,
                    column=reel,
                    padx=3,
                    pady=3,
                )

                column.append(label)

            self.reel_labels.append(column)

        # ----------------------------------------------------

        # Payline legend

        # ----------------------------------------------------

        legend = tk.Label(
            self.root,
            text=(
                "LINES: 1 TOP   2 CENTER   3 BOTTOM   "
                "4 ↓↑   5 ↑↓"
            ),
            font=(
                "DejaVu Sans",
                11
            ),
            fg="#aaaaaa",
            bg="#35063E",
        )

        legend.pack(
            pady=5
        )

        # ----------------------------------------------------

        # Information panel

        # ----------------------------------------------------

        info = tk.Frame(
            self.root,
            bg="#35063E"
        )

        info.pack(
            pady=10
        )

        self.credits_label = tk.Label(
            info,
            text="CREDITS: 100",
            font=(
                "DejaVu Sans",
                18,
                "bold"
            ),
            fg="#00ff66",
            bg="#35063E",
        )

        self.credits_label.grid(
            row=0,
            column=0,
            padx=35
        )

        self.bet_label = tk.Label(
            info,
            text="BET / LINE: 1",
            font=(
                "DejaVu Sans",
                18,
                "bold"
            ),
            fg="#ffffff",
            bg="#35063E",
        )

        self.bet_label.grid(
            row=0,
            column=1,
            padx=35
        )

        self.wager_label = tk.Label(
            info,
            text="TOTAL BET: 5",
            font=(
                "DejaVu Sans",
                18,
                "bold"
            ),
            fg="#ffaa00",
            bg="#35063E",
        )

        self.wager_label.grid(
            row=0,
            column=2,
            padx=35
        )

        # ----------------------------------------------------

        # Buttons

        # ----------------------------------------------------

        controls = tk.Frame(
            self.root,
            bg="#35063E"
        )

        controls.pack(
            pady=8
        )

        self.bet_down_button = tk.Button(
            controls,
            text="- BET",
            command=self.decrease_bet,
            font=(
                "DejaVu Sans",
                14,
                "bold"
            ),
            width=9,
            bg="#333333",
            fg="white",
        )

        self.bet_down_button.grid(
            row=0,
            column=0,
            padx=8
        )

        self.spin_button = tk.Button(
            controls,
            text="SPIN",
            command=self.start_spin,
            font=(
                "DejaVu Sans",
                22,
                "bold"
            ),
            width=12,
            height=2,
            bg="#cc0000",
            fg="white",
            activebackground="#ff3333",
            activeforeground="white",
        )

        self.spin_button.grid(
            row=0,
            column=1,
            padx=15
        )

        self.bet_up_button = tk.Button(
            controls,
            text="+ BET",
            command=self.increase_bet,
            font=(
                "DejaVu Sans",
                14,
                "bold"
            ),
            width=9,
            bg="#333333",
            fg="white",
        )

        self.bet_up_button.grid(
            row=0,
            column=2,
            padx=8
        )

        self.reset_button = tk.Button(
            self.root,
            text="RESET GAME",
            command=self.reset_game,
            font=(
                "DejaVu Sans",
                11
            ),
            width=14,
        )

        self.reset_button.pack(
            pady=5
        )

# ========================================================

# GAME CONTROL

# ========================================================

    def increase_bet(self):

        if self.spinning:
            return

        if (
            self.machine.bet_per_line
            < MAX_BET
        ):
            self.machine.bet_per_line += 1

        self.update_display()

    def decrease_bet(self):

        if self.spinning:
            return

        if (
            self.machine.bet_per_line
            > MIN_BET
        ):
            self.machine.bet_per_line -= 1

        self.update_display()

    def reset_game(self):

        if self.spinning:
            return

        self.machine.credits = (
            STARTING_CREDITS
        )

        self.machine.bet_per_line = (
            MIN_BET
        )

        self.message_label.config(
            text="GOOD LUCK!",
            fg="white"
        )

        self.clear_highlights()

        self.update_display()

# ========================================================

# SPIN

# ========================================================

    def start_spin(self):

        if self.spinning:
            return

        total_bet = (
            self.machine.total_bet()
        )

        if self.machine.credits < total_bet:

            self.message_label.config(
                text="NOT ENOUGH CREDITS!",
                fg="#ff3333"
            )

            return

        # Take the wager.

        self.machine.credits -= total_bet

        self.spinning = True
        self.spin_sound.play()

        self.spin_button.config(
            state=tk.DISABLED
        )

        self.bet_up_button.config(
            state=tk.DISABLED
        )

        self.bet_down_button.config(
            state=tk.DISABLED
        )

        self.message_label.config(
            text="SPINNING...",
            fg="#ffffff"
        )

        self.clear_highlights()

        # Generate final result.

        self.final_result = (
            self.machine.generate_spin()
        )

        self.animation_frame = 0

        self.stop_after = [
            False
            for _ in range(REELS)
        ]

        self.animate_reels()

# ========================================================

# REEL ANIMATION

# ========================================================

    def animate_reels(self):

        # Determine which reels are still spinning.

        active_reels = [
            reel
            for reel in range(REELS)
            if not self.stop_after[reel]
        ]

        if not active_reels:

            self.finish_spin()

            return

        # Advance animation.

        self.animation_frame += 1

        for reel in active_reels:

            # Once enough frames have passed,

            # stop this reel.

            stop_frame = (
                SPIN_FRAMES
                + reel * 5
            )

            if self.animation_frame >= stop_frame:

                self.stop_after[reel] = True
                self.reel_stop_sound.play()

                # Put final result onto reel.

                for row in range(ROWS):

                    self.machine.reels[
                        reel
                    ][row] = (
                        self.final_result[
                            reel
                        ][row]
                    )

            else:

                # Randomly cycle through symbols.

                for row in range(ROWS):

                    self.machine.reels[
                        reel
                    ][row] = (
                        self.machine.random_symbol()
                    )

        self.update_reels()

        self.root.after(
            ANIMATION_SPEED,
            self.animate_reels
        )

# ========================================================

# FINISH SPIN

# ========================================================

    def finish_spin(self):

        self.spinning = False

        wins = (
            self.machine.evaluate_lines()
        )

        total_winnings = sum(
            win["payout"]
            for win in wins
        )

        self.machine.credits += (
            total_winnings
        )

        self.spin_button.config(
            state=tk.NORMAL
        )

        self.bet_up_button.config(
            state=tk.NORMAL
        )

        self.bet_down_button.config(
            state=tk.NORMAL
        )

        if wins:
            self.win_sound.play()
            self.message_label.config(
                text=(
                    f"WIN! +{total_winnings} CREDITS"
                ),
                fg="#00ff66"
            )

            self.highlight_wins(wins)
            self.start_flash()
            self.root.after(3000, self.stop_flash)
        else:
            self.lose_sound.play()
            self.message_label.config(
                text="NO WIN — TRY AGAIN!",
                fg="#ffffff"
            )

        self.update_display()

# ========================================================

# DISPLAY

# ========================================================

    def update_reels(self):

        # Keep PhotoImage references alive.

        self.images = []

        for reel in range(REELS):

            for row in range(ROWS):

                symbol_index = (
                    self.machine.reels[
                        reel
                    ][row]
                )

                image = (
                    self.machine.icons[
                        symbol_index
                    ]["image"]
                )

                photo = ImageTk.PhotoImage(
                    image
                )

                self.images.append(photo)

                self.reel_labels[
                    reel
                ][row].config(
                    image=photo
                )

    def update_display(self):

        self.credits_label.config(
            text=(
                f"CREDITS: "
                f"{self.machine.credits}"
            )
        )

        self.bet_label.config(
            text=(
                f"BET / LINE: "
                f"{self.machine.bet_per_line}"
            )
        )

        self.wager_label.config(
            text=(
                f"TOTAL BET: "
                f"{self.machine.total_bet()}"
            )
        )

        self.update_reels()

# ========================================================

# PAYLINE HIGHLIGHTING

# ========================================================

    def clear_highlights(self):

        if self.flash_job is not None:
            self.root.after_cancel(self.flash_job)
            self.flash_job = None

        self.flash_state = False
        self.winning_positions = set()

        for reel in range(REELS):
            for row in range(ROWS):
                self.reel_labels[
                    reel
                ][row].config(
                    bg="#ffffff",
                    bd=3,
                    relief=tk.RIDGE
                )


    def highlight_wins(self, wins):

        self.clear_highlights()
        self.winning_positions = set()

        for win in wins:

            for reel, row in win["positions"]:
            
                self.winning_positions.add((reel, row))
                
                self.reel_labels[
                    reel
                ][row].config(
                    bg="#fff200",
                    bd=3,
                    relief=tk.RAISED
                )
    def start_flash(self):
        self.flash_state = not self.flash_state

        color = "#fff200" if self.flash_state else "#ffffff"

        for reel, row in self.winning_positions:
            self.reel_labels[
                reel
            ][row].config(bg=color)

        self.flash_job = self.root.after(
            250,
            self.start_flash
        )

    def stop_flash(self):
        if self.flash_job is not None:
            self.root.after_cancel(self.flash_job)
            self.flash_job = None

        for reel, row in self.winning_positions:
            self.reel_labels[
                reel
            ][row].config(
                bg="#fff200",
                bd=3,
                relief=tk.RIDGE
            )

#============================================================
#MAIN
#============================================================

def main():

    root = tk.Tk()

    try:

        NidiaSlotsApp(root)

    except RuntimeError as exc:

        error = tk.Label(
            root,
            text=str(exc),
            fg="#ff3333",
            bg="#35063E",
            font=(
                "DejaVu Sans",
                14
            ),
            wraplength=900
        )

        error.pack(
            expand=True,
            padx=30,
            pady=30
        )

    root.mainloop()

if __name__ == "__main__":
    main()
