import sys
import random
from pathlib import Path
import os

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

import json
import pygame
from os import path
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QTabWidget, QScrollArea
from PySide6.QtCore import Qt, QTimer, QSize, QMetaObject, Slot, QEvent, QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap
from pynput import keyboard
from PySide6.QtCore import QPropertyAnimation, QRect
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSpinBox, QCheckBox
from PySide6.QtGui import QCursor
from time import sleep
import math
from PySide6.QtGui import QRadialGradient
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "Entanglement.Control.Panel"
)

# =============================
# AUDIO
# =============================
SOUNDS = {}
ERRORSOUNDS = {}
AUDIO_AVAILABLE = False

try:
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except pygame.error as e:
    print(f"[Audio Disabled] {e}")
    AUDIO_AVAILABLE = False
    ctypes.windll.user32.MessageBoxW(0, "Audio driver not found, program won't be able to play any sound", "ERROR", 0)

try:
    entangle_music = resource_path("music\I_of_the_storm.ogg")
    if os.path.exists(entangle_music):
        if AUDIO_AVAILABLE and os.path.exists(entangle_music):
            pygame.mixer.music.load(entangle_music)
            pygame.mixer.music.set_volume(0.45)
except pygame.error as e:
    print(f"Audio warning: {e}")

def load_sound(name, volume=0.6):
    if not AUDIO_AVAILABLE:
        return None
    file_path = resource_path(os.path.join("sounds", name))
    if path.exists(file_path):
        snd = pygame.mixer.Sound(file_path)
        snd.set_volume(volume)
        return snd
    return None

SOUNDS["entangle"] = load_sound("entangle.wav", 0.7)
SOUNDS["close_popup"] = load_sound("click.mp3", 0.5)
SOUNDS["strong_popup_click"] = load_sound("daemonshankhit.mp3", 0.5)
SOUNDS["split_popup_click"] = load_sound("minionhit.mp3", 0.5)
ERRORSOUNDS["Error1"] = load_sound("error1.mp3", 0.5)
ERRORSOUNDS["Error2"] = load_sound("error2.mp3", 0.5)
ERRORSOUNDS["Error3"] = load_sound("error3.mp3", 0.5)
ERRORSOUNDS["Error4"] = load_sound("error4.mp3", 0.5)
ERRORSOUNDS["Error5"] = load_sound("error5.mp3", 0.5)
ERRORSOUNDS["Error6"] = load_sound("error6.mp3", 0.5)
ERRORSOUNDS["Error7"] = load_sound("error7.mp3", 0.5)
ERRORSOUNDS["Error8"] = load_sound("error8.mp3", 0.5)

# =============================
# LOADING SCREEN
# =============================
class LoadingPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window
        )
        self.setFixedSize(280, 90)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("INITIALIZING PROGRAM...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #00ff41;
            font-family: Consolas;
            font-size: 14px;
            font-weight: bold;
        """)

        layout.addWidget(label)

        self.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 220);
                border: 2px solid #00ff55;
            }
        """)

        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

# =============================
# CRT OVERLAY
# =============================
class CRTOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def animate(self):
        self.phase += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        jitter = int(2 * math.sin(self.phase / 6))
        painter.translate(jitter, 0)

        for y in range(0, h, 2):
            painter.fillRect(0, y, w, 1, QColor(0, 0, 0, 25))

        vignette = QRadialGradient(
            w // 2, h // 2,
            max(w, h) // 1.2
        )
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(1, QColor(0, 0, 0, 120))
        painter.fillRect(self.rect(), vignette)

        painter.end()


# =============================
# STATIC OVERLAY (child widget)
# =============================
class StaticOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.NoFocus)

        self.frames = []
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.next_frame)
        self.scroll_offset = 0
        self._frames_generated = False

    def generate_frames(self):
        w, h = self.width(), self.height()
        if w < 2 or h < 2:
            return

        self.frames.clear()
        frame_count = 12
        block = 3

        for _ in range(frame_count):
            pixmap = QPixmap(w, h)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            for y in range(0, h, block):
                for x in range(0, w, block):
                    if random.random() < 0.3:
                        continue
                    alpha = random.randint(60, 120)
                    brightness = random.randint(120, 255)

                    painter.fillRect(x, y, block, block, QColor(0, brightness, 0, alpha))
            painter.end()
            self.frames.append(pixmap)

        self._frames_generated = True
        self.current_frame = 0
        self.scroll_offset = 0
        self.update()
    
    def start(self):
        self.show()
        if self._frames_generated:
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()

    def next_frame(self):
        if not self.frames:
            return
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        if self.parent() and getattr(self.parent(), "vertical_static", False):
            self.scroll_offset = (self.scroll_offset + 4) % self.height()
        else:
            self.scroll_offset = 0

        self.update()

    def mousePressEvent(self, event):
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.frames:
            pixmap = self.frames[self.current_frame]
            y = self.scroll_offset
            painter.drawPixmap(0, y - self.height(), pixmap)
            painter.drawPixmap(0, y, pixmap)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 50))
        painter.end()

# =============================
# ERROR POPUP
# =============================
class ErrorPopup(QLabel):
    def __init__(self, image_path, close_callback, parent_overlay, red=False, split_depth=[0,None,None]):
        super().__init__(parent_overlay)
        self.close_callback = close_callback
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.red = red
        self.split_depth = split_depth[0]
        if not self.red:
            self.is_split = (
                parent_overlay.enable_splitting and
                random.random() < parent_overlay.split_chance and
                self.split_depth < self.parent().split_depth
            )
        else:
            self.is_split = False

        if self.is_split:
            image_path = random.choice(self.parent().split_error_images)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap)
            self.resize(pixmap.size())
        else:
            self.setText("ERROR\nIMAGE\nMISSING")
            self.setStyleSheet("background-color: white; border: 2px solid red; color: red; font-weight: bold;")
            self.setAlignment(Qt.AlignCenter)
            self.resize(240, 180)

        if self.split_depth == 0:
            self.place_randomly()
        else:
            self.move(split_depth[1])
        self.animate_in()
        self.show()
        self.raise_()

        self.moving = parent_overlay.moving_popups
        speed = parent_overlay.speed_multiplier
        base = random.choice([-2, -1, 1, 2])

        self.dx = int(base * speed)
        self.dy = int(base * speed)


        if self.moving:
            self.move_timer = QTimer(self)
            self.move_timer.timeout.connect(self.move_step)
            self.move_timer.start(16)

        self.strong = parent_overlay.strong_popups
        if self.strong:
            self.health = random.randint(
                parent_overlay.strong_min_hits,
                parent_overlay.strong_max_hits
            )
        else:
            self.health = 1

    def move_step(self):
        parent = self.parent()
        if not parent:
            return

        global_pos = self.mapToGlobal(QPoint(0, 0))
        rect = QRect(global_pos, self.size())

        screen = QApplication.screenAt(rect.center())
        if not screen:
            return

        bounds = screen.availableGeometry()

        if rect.left() <= bounds.left() or rect.right() >= bounds.right():
            self.dx *= -1

        if rect.top() <= bounds.top() or rect.bottom() >= bounds.bottom():
            self.dy *= -1

        self.move(self.x() + self.dx, self.y() + self.dy)


    def animate_in(self):
        start_rect = QRect(
            self.x() + self.width() // 2,
            self.y() + self.height() // 2,
            0,
            0
        )

        end_rect = self.geometry()

        self.setGeometry(start_rect)

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(50)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.start()

        ERRORSOUNDS["Error"+str(random.randint(1,8))].play()

    def place_randomly(self):
        parent = self.parent()
        if not parent:
            return

        if parent.multi_screen:
            geo = parent.geometry()
            offset_x = 0
            offset_y = 0
        else:
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            geo = screen.geometry()

            offset_x = geo.x() - parent.geometry().x()
            offset_y = geo.y() - parent.geometry().y()

        margin = 50
        x_max = max(margin, geo.width() - self.width() - margin)
        y_max = max(margin, geo.height() - self.height() - margin)

        x = random.randint(margin, x_max)
        y = random.randint(margin, y_max)

        self.move(x + offset_x, y + offset_y)

    def hit_feedback(self):
        rect = self.geometry()

        shake = QRect(
            rect.x() - 6,
            rect.y(),
            rect.width() + 12,
            rect.height()
        )

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(60)
        self.anim.setKeyValueAt(0, rect)
        self.anim.setKeyValueAt(0.5, shake)
        self.anim.setKeyValueAt(1, rect)
        self.anim.start()

        if SOUNDS["strong_popup_click"]:
            SOUNDS["strong_popup_click"].play()

    def spawn_chaos(self):
        for _ in range(5):
            img = random.choice(self.parent().error_images)
            popup = ErrorPopup(
                img,
                self.parent().on_popup_closed,
                self.parent(),
                False
            )
            self.parent().popups.append(popup)

            popup.show()

    def split(self):
        if SOUNDS["split_popup_click"]:
            SOUNDS["split_popup_click"].play()

        self.animate_out()

        for i in range(2):
            img = random.choice(self.parent().error_images)

            current_screen = QApplication.screenAt(self.mapToGlobal(self.rect().center()))
            if not current_screen:
                current_screen = QApplication.primaryScreen()
    
            geo = current_screen.geometry()

            local_screen_top_left = self.parent().mapFromGlobal(geo.topLeft())
            local_screen_bottom_right = self.parent().mapFromGlobal(geo.bottomRight())

            spawn_x = self.x() + random.randint(-200, 200)
            spawn_y = self.y() + random.randint(-200, 200)

            margin = 50
            child_w = int(self.width() * 0.7)
            child_h = int(self.height() * 0.7)

            final_x = max(local_screen_top_left.x() + margin, 
                          min(spawn_x, local_screen_bottom_right.x() - child_w - margin))
            final_y = max(local_screen_top_left.y() + margin, 
                          min(spawn_y, local_screen_bottom_right.y() - child_h - margin))

            random_offset_pos = QPoint(final_x, final_y)

            child = ErrorPopup(
                img,
                self.close_callback,
                self.parent(),
                0,
                [self.split_depth + 1, random_offset_pos, None]
            )

            child.resize(
                int(self.width() * 0.7),
                int(self.height() * 0.7)
            )

            self.parent().popups.append(child)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            
            if self.health > 1:
                self.health -= 1
                self.hit_feedback()
            else:
                if self.red:
                    self.spawn_chaos()
                elif self.is_split and self.split_depth < self.parent().split_depth:
                    self.split()
                    event.accept()
                    return
                
                self.animate_out()
            event.accept()

    def animate_out(self):
        end_rect = QRect(
            self.x() + self.width() // 2,
            self.y() + self.height() // 2,
            0,
            0
        )

        if SOUNDS["close_popup"]:
            SOUNDS["close_popup"].play()

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(40)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(end_rect)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def closeEvent(self, event):
        if callable(self.close_callback):
            self.close_callback(self)
        super().closeEvent(event)

# =============================
# SETTINGS WINDOW
# =============================
class SettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setObjectName("RootWindow")
        self.main_window = main_window

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setFixedSize(440, 650)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = None

        self._setup_tray()
        self._apply_global_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_status())

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self._build_control_tab()
        self._build_popups_tab()
        self._build_behavior_tab()
        self._build_challenge_tab()

    # ------------------------------------------------------------------
    # TRAY
    # ------------------------------------------------------------------

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(QIcon(resource_path("icon.ico")), self)
        self.tray.setToolTip("Entanglement Active")
        self.tray.activated.connect(self._tray_clicked)

        menu = QMenu()
        menu.addAction("Open Control Panel", self.show_panel)
        menu.addSeparator()
        menu.addAction("Quit", QApplication.quit)
        self.tray.setContextMenu(menu)

    # ------------------------------------------------------------------
    # STYLES
    # ------------------------------------------------------------------

    def _apply_global_style(self):
        self.setStyleSheet("""
            QWidget {
                background: #000;
                color: #00ff41;
                font-family: Consolas, monospace;
                font-size: 13px;
            }
                           
            QWidget#RootWindow {
                border: 2px solid #00ff55;
            }

            QTabWidget::pane {
                border: 1px solid #004d00;
                background: #000800;
            }

            QTabBar::tab {
                padding: 8px 16px;
                background: #000;
                border: 1px solid #004d00;
                color: #00aa44;
            }

            QTabBar::tab:selected {
                background: #001a00;
                color: #00ff41;
                border-bottom: 2px solid #00ff41;
            }

            QPushButton {
                border: 2px solid #00ff55;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #003300;
            }

            QSpinBox {
                background-color: #000800;
                color: #00ff41;
                border: 1px solid #00ff55;
                padding: 4px 6px;
                min-height: 24px;
            }

            QSpinBox::up-button,
            QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }

            QSpinBox::up-arrow,
            QSpinBox::down-arrow {
                image: none;
            }

            QCheckBox {
                spacing: 6px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #004d00;
                background: #000;
            }

            QCheckBox::indicator:checked {
                background: #003300;
            }
                           
            QScrollArea {
                background: #000000;
                border: 1px solid #004d00;
            }

            QScrollBar:vertical {
                background: #000;
                width: 12px;
                margin: 0px;
                border-left: 1px solid #004d00;
            }

            QScrollBar::handle:vertical {
                background: #00aa44;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #00ff41;
            }
                           
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
                           
            QToolTip {
        background-color: #000800;
                color: #00ff41;
                border: 1px solid #00ff55;
                padding: 6px 6px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("border-bottom: 1px solid #00ff55; font-weight: bold;")
        return lbl

    def _spinbox(self, minv, maxv, val):
        sb = QSpinBox()
        sb.setRange(minv, maxv)
        sb.setValue(val)
        sb.setToolTip(f"Range: {minv} – {maxv}")
        return sb

    def _button(self, text, callback, danger=False, height=32):
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.clicked.connect(callback)
        if danger:
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #ff3333;
                    color: #ff3333;
                    background: #100000;
                }
                QPushButton:hover {
                    background: #330000;
                }
            """)
        return btn

    # ------------------------------------------------------------------
    # TITLE BAR
    # ------------------------------------------------------------------

    def _build_title_bar(self):
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet("background: #000;")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 0, 8, 0)

        label = QLabel("ENTANGLEMENT CONTROL")
        label.setStyleSheet("font-weight: bold; letter-spacing: 1px;")

        min_btn = QPushButton("—")
        min_btn.setFixedSize(22, 22)
        min_btn.setStyleSheet("border: none;")
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(QApplication.quit)
        close_btn.setStyleSheet("border: none;")

        bar.mousePressEvent = self._mouse_press
        bar.mouseMoveEvent = self._mouse_move

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(min_btn)
        layout.addWidget(close_btn)
        return bar

    def _mouse_press(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def _mouse_move(self, e):
        if e.buttons() & Qt.LeftButton:
            self.move(self.pos() + e.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = e.globalPosition().toPoint()

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def _build_status(self):
        self.status = QLabel("STATUS: IDLE")
        self.status.setStyleSheet("border: 1px solid #00ff55; padding: 4px;")
        self.status.setAlignment(Qt.AlignCenter)
        return self.status

    # ------------------------------------------------------------------
    # CONTROL TAB
    # ------------------------------------------------------------------

    def _build_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.start_btn = self._button("INITIATE (F8)", self.start_entanglement, height=42)
        self.hide_btn = self._button("HIDE INTERFACE", self.hide_to_tray)
        quit_btn = self._button("TERMINATE PROGRAM", QApplication.quit, danger=True)

        layout.addWidget(self._section("SYSTEM"))
        layout.addWidget(self.start_btn)
        layout.addWidget(self.hide_btn)
        layout.addWidget(quit_btn)
        layout.addStretch()

        self.tabs.addTab(tab, "CONTROL")

    # ------------------------------------------------------------------
    # POPUPS TAB
    # ------------------------------------------------------------------

    def _build_popups_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.moving_cb = QCheckBox("MOVING POPUPS")
        self.strong_cb = QCheckBox("STRONG POPUPS")
        self.split_cb = QCheckBox("SPLITTING POPUPS")
        self.red_cb = QCheckBox("RED POPUPS")

        self.min_spin = self._spinbox(1, 100, 10)
        self.max_spin = self._spinbox(1, 100, 15)

        layout.addWidget(self._section("VARIANTS"))
        layout.addWidget(self.moving_cb)
        layout.addWidget(self.strong_cb)
        layout.addWidget(self.split_cb)
        layout.addWidget(self.red_cb)

        layout.addWidget(self._section("COUNT"))
        layout.addWidget(QLabel("MIN POPUPS"))
        layout.addWidget(self.min_spin)
        layout.addWidget(QLabel("MAX POPUPS"))
        layout.addWidget(self.max_spin)

        layout.addStretch()
        self.tabs.addTab(tab, "POPUPS")

    # ------------------------------------------------------------------
    # BEHAVIOR TAB
    # ------------------------------------------------------------------

    def _build_behavior_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)

        self.multi_screen = QCheckBox("POPUPS ON MULTIPLE SCREENS")
        self.vertical_cb = QCheckBox("VERTICAL STATIC SCROLL")
        self.speed_spin = self._spinbox(1, 1000, 100)
        self.speed_spin.setSuffix(" %")
        self.split_chance = self._spinbox(0, 100, 25)
        self.split_chance.setSuffix(" %")
        self.split_depth = self._spinbox(1, 10, 2)
        self.red_chance = self._spinbox(0, 100, 15)
        self.red_chance.setSuffix(" %")
        self.strong_min = self._spinbox(1, 20, 2)
        self.strong_max = self._spinbox(1, 20, 4)

        layout.addWidget(self._section("MINIGAME"))
        layout.addWidget(self.multi_screen)
        layout.addWidget(self.vertical_cb)

        layout.addWidget(self._section("MOVEMENT"))
        layout.addWidget(QLabel("SPEED"))
        layout.addWidget(self.speed_spin)

        layout.addWidget(self._section("SPLITTING"))
        layout.addWidget(QLabel("SPLITTING CHANCE"))
        layout.addWidget(self.split_chance)
        layout.addWidget(QLabel("SPLITTING DEPTH"))
        layout.addWidget(self.split_depth)

        layout.addWidget(self._section("RED POPUPS"))
        layout.addWidget(QLabel("RED POPUP CHANCE"))
        layout.addWidget(self.red_chance)

        layout.addWidget(self._section("STRONG POPUPS"))
        layout.addWidget(QLabel("MIN CLICKS"))
        layout.addWidget(self.strong_min)
        layout.addWidget(QLabel("MAX CLICKS"))
        layout.addWidget(self.strong_max)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        self.tabs.addTab(scroll, "BEHAVIOR")

    # ------------------------------------------------------------------
    # CHALLENGE TAB
    # ------------------------------------------------------------------

    def _build_challenge_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.challenge_btn = self._button(
            "START CHALLENGE MODE",
            self.toggle_challenge_mode,
            danger=True,
            height=48
        )

        self.challenge_min = self._spinbox(5, 36000, 30)
        self.challenge_max = self._spinbox(5, 36000, 90)

        self.challenge_strength = self._spinbox(1, 100, 35)
        self.challenge_strength.setSuffix(" %")
        self.challenge_rarity = self._spinbox(1, 100, 15)
        self.challenge_rarity.setSuffix(" %")

        warn = QLabel("⚠ Overrides manual control")
        warn.setAlignment(Qt.AlignCenter)
        warn.setStyleSheet("color: #ff4444; font-weight: bold;")

        layout.addWidget(self.challenge_btn)
        layout.addWidget(warn)
        layout.addWidget(QLabel("INTERVAL MIN (sec)"))
        layout.addWidget(self.challenge_min)
        layout.addWidget(QLabel("INTERVAL MAX (sec)"))
        layout.addWidget(self.challenge_max)
        layout.addWidget(QLabel("CHAOS STRENGTH"))
        layout.addWidget(self.challenge_strength)
        layout.addWidget(QLabel("MODIFIER RARITY"))
        layout.addWidget(self.challenge_rarity)
        layout.addStretch()

        self.tabs.addTab(tab, "CHALLENGE")

        self.load_settings()

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def load_settings(self):
        try:
            with open(resource_path("config.json"), "r") as f:
                data = json.load(f)
            self.min_spin.setValue(data.get("popup_min", 10))
            self.max_spin.setValue(data.get("popup_max", 15))
            self.vertical_cb.setChecked(data.get("vertical_static", True))
            self.moving_cb.setChecked(data.get("moving_popups", False))
            self.strong_cb.setChecked(data.get("strong_popups", False))
            self.split_cb.setChecked(data.get("enable_splitting", False))
            self.red_cb.setChecked(data.get("enable_red_popups", False))
            self.multi_screen.setChecked(data.get("multi_screen", False))
            self.speed_spin.setValue(data.get("speed_multiplier" * 100, 100))
            self.split_chance.setValue(data.get("split_chance" * 100, 25))
            self.split_depth.setValue(data.get("split_depth", 2))
            self.red_chance.setValue(data.get("red_chance" * 100, 15))
            self.strong_min.setValue(data.get("strong_min", 2))
            self.strong_max.setValue(data.get("strong_max", 4))
            self.challenge_min.setValue(data.get("challenge_min", 30))
            self.challenge_max.setValue(data.get("challenge_max", 90))
            self.challenge_strength.setValue(data.get("challenge_strength" * 100, 35))
            self.challenge_rarity.setValue(data.get("challenge_rarity" * 100, 15))
        except Exception:
            pass

    def apply_settings(self):
        mw = self.main_window
        mw.popup_min = self.min_spin.value()
        mw.popup_max = self.max_spin.value()
        mw.vertical_static = self.vertical_cb.isChecked()
        mw.moving_popups = self.moving_cb.isChecked()
        mw.strong_popups = self.strong_cb.isChecked()
        mw.enable_splitting = self.split_cb.isChecked()
        mw.enable_red_popups = self.red_cb.isChecked()
        mw.multi_screen = self.multi_screen.isChecked()
        mw.speed_multiplier = self.speed_spin.value() / 100
        mw.split_chance = self.split_chance.value() / 100
        mw.split_depth = self.split_depth.value()
        mw.red_popup_chance = self.red_chance.value() / 100
        mw.strong_min_hits = self.strong_min.value()
        mw.strong_max_hits = self.strong_max.value()
        mw.challenge_interval_min = self.challenge_min.value()
        mw.challenge_interval_max = self.challenge_max.value()
        mw.challenge_strength = self.challenge_strength.value() / 100
        mw.challenge_rarity = self.challenge_rarity.value() / 100

    def start_entanglement(self):
        if hasattr(self, "challenge_overrides") and self.challenge_overrides:
            print("CHAOS MODIFIERS ACTIVE")
            if hasattr(self, "settings_window"):
                self.settings_window.status.setText("STATUS: CHAOS")
        self.apply_settings()
        self.status.setText("STATUS: ENTANGLED")
        QMetaObject.invokeMethod(self.main_window, "start_entanglement", Qt.QueuedConnection)

    def toggle_challenge_mode(self):
        mw = self.main_window
        self.apply_settings()

        if not mw.challenge_mode:
            mw.start_challenge_mode()
            self.challenge_btn.setText("STOP CHALLENGE MODE")
            self.start_btn.setEnabled(False)
            self.status.setText("STATUS: CHALLENGE")
        else:
            mw.stop_challenge_mode()
            self.challenge_btn.setText("START CHALLENGE MODE")
            self.start_btn.setEnabled(True)
            self.status.setText("STATUS: IDLE")

    def hide_to_tray(self):
        self.tray.show()
        self.hide()

    def show_panel(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.tray.hide()

    def _tray_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_panel()

    def save_settings(self):
        data = {
            "popup_min": self.min_spin.value(),
            "popup_max": self.max_spin.value(),
            "vertical_static": self.vertical_cb.isChecked(),
            "moving_popups": self.moving_cb.isChecked(),
            "strong_popups": self.strong_cb.isChecked(),
            "enable_splitting": self.split_cb.isChecked(),
            "enable_red_popups": self.red_cb.isChecked(),
            "multi_screen": self.multi_screen.isChecked(),
            "speed_multiplier": self.speed_spin.value() / 100,
            "split_chance": self.split_chance.value() / 100,
            "split_depth": self.split_depth.value(),
            "red_popup_chance": self.red_chance.value() / 100,
            "strong_min_hits": self.strong_min.value(),
            "strong_max_hits": self.strong_max.value(),
            "challenge_interval_min": self.challenge_min.value(),
            "challenge_interval_max": self.challenge_max.value(),
            "challenge_strength": self.challenge_strength.value() / 100,
            "challenge_rarity": self.challenge_rarity.value() / 100,
        }
        with open(resource_path("config.json"), "w") as f:
            json.dump(data, f, indent=2)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()


# =============================
# MAIN WINDOW
# =============================
class MainWindow(QWidget):
    def __init__(self):
        self.ending_entanglement = False
        self.entanglement_active = False
        super().__init__()

        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.challenge_overrides = None

        self.vertical_static = True
        self.moving_popups = False
        self.strong_popups = False
        self.enable_splitting = False
        self.enable_red_popups = False

        self.challenge_mode = False
        self.challenge_interval_min = 30
        self.challenge_interval_max = 90
        self.challenge_strength = 0.35
        self.challenge_rarity = 0.15

        self.split_chance = 0.25
        self.split_depth = 2
        self.red_popup_chance = 0.15

        self.speed_multiplier = 1.0

        self.strong_min_hits = 2
        self.strong_max_hits = 4

        self.popup_min = 10
        self.popup_max = 15

        geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geo)

        self.static = StaticOverlay(self)
        self.static.setGeometry(self.rect())
        self.static.generate_frames()
        self.static.hide()

        self.crt = CRTOverlay(self)
        self.crt.setGeometry(self.rect())
        self.crt.hide()

        import os

        def list_images(folder):
            base = resource_path(folder)
            if not os.path.isdir(base):
                return []
            return [
                os.path.join(base, f)
                for f in os.listdir(base)
                if f.lower().endswith(".png")
            ]

        self.popups = []
        self.red_popups = []
        self.error_images = list_images("errors")
        self.red_error_images = list_images("rederrors")
        self.split_error_images = list_images("spliterrors")
        
        if not os.path.exists(resource_path("errors")):
            print("Creating 'errors' folder for testing...")
            Path("errors").mkdir()

    @Slot()
    def start_entanglement(self):
        print("start_entanglement called")
        self.entanglement_active = True

        self._base_settings = {
            key: getattr(self, key)
            for key in [
                "popup_min",
                "popup_max",
                "enable_red_popups",
                "red_popup_chance",
                "red_popup_chance",
                "enable_splitting",
                "split_chance",
                "split_depth",
                "moving_popups",
                "speed_multiplier",
                "strong_popups",
                "strong_min_hits",
                "strong_max_hits",
            ]
        }

        self.challenge_overrides = None
        if self.challenge_mode and random.random() < self.challenge_rarity:
            self.challenge_overrides = self.generate_challenge_override()
            if self.challenge_overrides:
                for key, value in self.challenge_overrides.items():
                    setattr(self, key, value)

                if self.popups:
                    return
        
        self.crt.show()

        if SOUNDS["entangle"]:
            SOUNDS["entangle"].play()
        sleep(0.7)
        self.static.start()
        self.crt.show()
        self.crt.raise_()
        
        if hasattr(self, "settings_window"):
            self.settings_window.status.setText("STATUS: ENTANGLED")
        
        self.activateWindow()
        self.raise_()

        try:
            count = random.randint(self.popup_min, self.popup_max)
        except Exception as e:
            print("Failed to start entanglement:", e)
            return
        print(f"Creating {count} popups")
        
        self.spawn_queue = count
        self.spawn_timer = QTimer(self)
        self.spawn_timer.setInterval(40)
        self.spawn_timer.timeout.connect(self.spawn_popup)
        self.spawn_timer.start()

        try:
            if pygame.mixer.music.get_busy() == False:
                if AUDIO_AVAILABLE:
                    pygame.mixer.music.play(fade_ms=400, loops=-1)
        except Exception:
            pass

        self.show()

    def generate_challenge_override(self):
        SETTING_LIMITS = {
            "popup_min": (1, 30),
            "popup_max": (5, 40),
            "red_popup_chance": (0.15, 0.75),
            "speed_multiplier": (0.5, 3.0),
            "strong_min_hits": (1, 3),
            "strong_max_hits": (3, 8),
            "split_chance": (0.15, 0.75),
            "split_depth": (1, 4),
        }
        overrides = {}

        if random.random() < self.challenge_strength:
            overrides["enable_red_popups"] = not self.enable_red_popups

        if random.random() < self.challenge_strength:
            overrides["moving_popups"] = not self.moving_popups

        if random.random() < self.challenge_strength:
            overrides["strong_popups"] = not self.strong_popups
            
        if random.random() < self.challenge_strength:
            overrides["enable_splitting"] = not self.enable_splitting

        def jitter(value, min_v, max_v, strength=None):
            if strength is None:
                strength = self.challenge_strength
            span = max_v - min_v
            delta = span * strength * random.uniform(-1, 1)
            return max(min_v, min(max_v, value + delta))
            
        for key, (min_v, max_v) in SETTING_LIMITS.items():
            if hasattr(self, key) and random.random() < self.challenge_strength:
                current = getattr(self, key)

                if isinstance(current, int):
                    new_val = int(round(jitter(current, min_v, max_v)))
                else:
                    new_val = jitter(current, min_v, max_v)

                overrides[key] = new_val

        if "popup_min" in overrides or "popup_max" in overrides:
            min_val = overrides.get("popup_min", self.popup_min)
            max_val = overrides.get("popup_max", self.popup_max)
            if min_val > max_val:
                overrides["popup_min"], overrides["popup_max"] = max_val, min_val

        return overrides if overrides else None

    def start_challenge_mode(self):
        if self.challenge_mode:
            return

        print("Challenge Mode enabled")
        self.challenge_mode = True
        self.schedule_next_challenge()

    def stop_challenge_mode(self):
        print("Challenge Mode disabled")
        self.challenge_mode = False

    def schedule_next_challenge(self):
        if not self.challenge_mode:
            return

        delay = random.randint(
            self.challenge_interval_min,
            self.challenge_interval_max
        )

        print(f"Next challenge entanglement in {delay}s")

        QTimer.singleShot(
            delay * 1000,
            self.trigger_challenge_entanglement
        )

    def trigger_challenge_entanglement(self):
        if not self.challenge_mode or self.entanglement_active:
            self.schedule_next_challenge()
            return

        QMetaObject.invokeMethod(
            self,
            "start_entanglement",
            Qt.QueuedConnection
        )

        self.schedule_next_challenge()

    def resizeEvent(self, event):
        self.static.setGeometry(self.rect())
        self.crt.setGeometry(self.rect())
        super().resizeEvent(event)

    def spawn_popup(self):
        if self.spawn_queue <= 0 or not self.entanglement_active:
            self.spawn_timer.stop()
            return
        
        is_red = (
            self.enable_red_popups and
            random.random() < self.red_popup_chance
        )

        if is_red:
            img = random.choice(self.red_error_images) if self.red_error_images else "dummy.png"
        else:
            img = random.choice(self.error_images) if self.error_images else "dummy.png"
        popup = ErrorPopup(img, self.on_popup_closed, self, red=is_red)
        if not is_red:
            self.popups.append(popup)
            self.spawn_queue -= 1
        else:
            self.red_popups.append(popup)

    def on_popup_closed(self, popup):
        if popup in self.popups:
            self.popups.remove(popup)
        
        if not self.popups:
            self.end_entanglement()

    def end_entanglement(self):
        print("Ending entanglement")

        if self.ending_entanglement:
            return
        self.ending_entanglement = True

        if hasattr(self, "settings_window"):
            self.settings_window.status.setText("STATUS: IDLE")
        if isinstance(self._base_settings, dict):
            for key, value in self._base_settings.items():
                setattr(self, key, value)

        self._base_settings = None
        
        self.entanglement_active = False
        for p in self.popups:
            p.close_callback = None
            p.close()
            p.blockSignals(True)
        self.popups.clear()
        for p in self.red_popups:
            p.close_callback = None
            p.close()
            p.blockSignals(True)
        self.red_popups.clear()
        self.hide()
        self.static.stop()
        self.crt.hide()
        try:
            pygame.mixer.music.fadeout(600)
        except:
            pass
        self.ending_entanglement = False

    def paintEvent(self, event):
        if not self.entanglement_active:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F4:
            print("F4 Kill Switch Activated")
            QApplication.quit()
        else:
            super().keyPressEvent(event)

# =============================
# GLOBAL HOTKEY (F9)
# =============================
def setup_global_hotkey(main_window):
    def on_activate_f9():
        if main_window.challenge_mode:
            return

        if hasattr(main_window, "settings_window"):
            main_window.settings_window.apply_settings()

        QMetaObject.invokeMethod(
            main_window,
            "start_entanglement",
            Qt.QueuedConnection
        )

    listener = keyboard.GlobalHotKeys({'<f8>': on_activate_f9})
    listener.start()
    return listener

# =============================
# ENTRY POINT
# =============================
if __name__ == "__main__":
    myappid = 'Entanglement.Control.Panel.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app_icon_path = resource_path("icon.ico")
    app.setWindowIcon(QIcon(app_icon_path))

    if not os.path.exists(app_icon_path):
        print(f"ERROR: Icon not found at {app_icon_path}")

    loading = LoadingPopup()
    loading.show()
    app.processEvents()

    window = MainWindow()
    settings = SettingsWindow(window)
    window.settings_window = settings

    settings.show()

    hotkey_listener = setup_global_hotkey(window)

    loading.close()

    print("Game overlay ready. Press F8 to start, F4 to stop.")

    try:
        sys.exit(app.exec())
    finally:
        hotkey_listener.stop()