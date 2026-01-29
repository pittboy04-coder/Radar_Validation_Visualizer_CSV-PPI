#!/usr/bin/env python3
"""Radar Validation Visualizer — CSV-to-PPI viewer."""
import sys
import os
import platform
import pygame
from data_import import CsvPlayer
from ppi_display import PPIDisplay
from scene_view import SceneView

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 700
DISPLAY_SIZE = 600
FPS = 60

# Colors
BG_COLOR = (20, 20, 30)
BUTTON_COLOR = (40, 50, 60)
BUTTON_HOVER = (50, 65, 80)
BUTTON_ACTIVE = (0, 100, 0)
TEXT_COLOR = (0, 200, 0)
BORDER_COLOR = (60, 70, 80)
HIGHLIGHT = (0, 255, 0)


def get_default_dir():
    if platform.system() == 'Windows':
        d = r"C:\Users\Noah\OneDrive - Strategy Communications\Desktop\maritime_radar_sim"
    else:
        d = os.path.expanduser("~/maritime_radar_sim")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def open_file_dialog():
    """Open file/folder dialog, return path or None."""
    import tkinter as tk
    from tkinter import filedialog
    initial = get_default_dir()
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select CSV File (or Cancel for folder)",
        initialdir=initial,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if not path:
        path = filedialog.askdirectory(
            title="Select CSV Data Folder",
            initialdir=initial)
    root.destroy()
    return path if path else None


def main():
    pygame.init()
    pygame.display.set_caption("Radar Validation Visualizer (CSV-PPI)")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas', 18)
    small_font = pygame.font.SysFont('consolas', 14)

    # State
    csv_player = None
    range_nm = 6.0
    range_scales = [0.25, 0.5, 0.75, 1.5, 3, 6, 12, 24, 48, 96]
    range_idx = 5
    status_text = "No data loaded"
    file_text = ""

    # Layout calculation
    PANEL_WIDTH = 200
    MIN_DISPLAY = 250

    def calc_layout(w, h):
        avail = w - PANEL_WIDTH - 20
        ds = min(h - 20, (avail - 20) // 2)
        ds = max(MIN_DISPLAY, ds)
        px, py = 10, (h - ds) // 2
        sx, sy = ds + 20, py
        return ds, px, py, sx, sy

    display_size, ppi_x, ppi_y, scene_x, scene_y = calc_layout(WINDOW_WIDTH, WINDOW_HEIGHT)

    ppi = PPIDisplay(size=display_size)
    ppi.initialize()
    ppi.set_ppi_offset(ppi_x, ppi_y)

    scene = SceneView(size=display_size)

    # Button rects (relative to panel area)
    def get_buttons(w, h):
        panel_x = w - PANEL_WIDTH - 5
        return {
            'load_file': pygame.Rect(panel_x, 40, PANEL_WIDTH - 10, 35),
            'stop': pygame.Rect(panel_x, 85, PANEL_WIDTH - 10, 35),
            'clear': pygame.Rect(panel_x, 130, PANEL_WIDTH - 10, 35),
        }

    buttons = get_buttons(WINDOW_WIDTH, WINDOW_HEIGHT)
    hover_btn = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.VIDEORESIZE:
                w, h = event.w, event.h
                if w < 100 or h < 100:
                    continue
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                display_size, ppi_x, ppi_y, scene_x, scene_y = calc_layout(w, h)
                ppi = PPIDisplay(size=display_size)
                ppi.initialize()
                ppi.set_ppi_offset(ppi_x, ppi_y)
                scene = SceneView(size=display_size)
                buttons = get_buttons(w, h)

            elif event.type == pygame.MOUSEMOTION:
                ppi.handle_mouse_motion(event.pos[0], event.pos[1])
                hover_btn = None
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        hover_btn = name

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if name == 'load_file':
                            path = open_file_dialog()
                            if path:
                                csv_player = CsvPlayer(path)
                                if csv_player.active:
                                    status_text = "Playing"
                                    file_text = os.path.basename(path)
                                    scene.clear_echoes()
                                else:
                                    csv_player = None
                                    status_text = "No CSV data found"
                                    file_text = ""
                        elif name == 'stop':
                            if csv_player:
                                csv_player.stop()
                                csv_player = None
                                status_text = "Stopped"
                        elif name == 'clear':
                            scene.clear_echoes()
                            ppi = PPIDisplay(size=display_size)
                            ppi.initialize()
                            ppi.set_ppi_offset(ppi_x, ppi_y)
                            status_text = "Cleared"

            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if ppi.screen_to_polar(mouse_pos[0], mouse_pos[1]) is not None:
                    if event.y > 0 and range_idx > 0:
                        range_idx -= 1
                    elif event.y < 0 and range_idx < len(range_scales) - 1:
                        range_idx += 1
                    range_nm = range_scales[range_idx]
                    ppi.set_range(range_nm)

        # Skip render when minimized
        if pygame.display.get_surface().get_size()[0] == 0:
            clock.tick(FPS)
            continue

        # Get sweep data
        sweep_pairs = []
        if csv_player and csv_player.active:
            sweep_pairs = csv_player.get_next_sweeps()
            for bearing, data in sweep_pairs:
                ppi.draw_sweep_data(bearing, data)

        # Render
        screen.fill(BG_COLOR)

        # PPI
        ppi_surface = ppi.render()
        screen.blit(ppi_surface, (ppi_x, ppi_y))

        # Scene view
        scene_surface = scene.render(sweep_pairs, range_nm)
        screen.blit(scene_surface, (scene_x, scene_y))

        # Cursor info
        ppi.draw_cursor_info(screen, ppi_x, ppi_y + display_size + 5)

        # Control panel
        win_w, win_h = screen.get_size()
        panel_x = win_w - PANEL_WIDTH - 5

        # Panel background
        panel_rect = pygame.Rect(panel_x - 5, 5, PANEL_WIDTH + 10, win_h - 10)
        pygame.draw.rect(screen, (30, 35, 40), panel_rect)
        pygame.draw.rect(screen, BORDER_COLOR, panel_rect, 1)

        # Title
        title = font.render("CSV VIEWER", True, HIGHLIGHT)
        screen.blit(title, (panel_x + (PANEL_WIDTH - title.get_width()) // 2, 12))

        # Buttons
        btn_labels = {'load_file': 'LOAD FILE', 'stop': 'STOP', 'clear': 'CLEAR'}
        for name, rect in buttons.items():
            # Update rect position for current window size
            rect.x = panel_x
            if name == 'stop':
                rect.y = 85
            elif name == 'clear':
                rect.y = 130

            if hover_btn == name:
                color = BUTTON_HOVER
            elif name == 'stop' and csv_player and csv_player.active:
                color = BUTTON_ACTIVE
            else:
                color = BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)
            label = font.render(btn_labels[name], True, TEXT_COLOR)
            screen.blit(label, (rect.centerx - label.get_width() // 2,
                                rect.centery - label.get_height() // 2))

        # Status info
        y_info = 180
        status_label = small_font.render(f"Status: {status_text}", True, TEXT_COLOR)
        screen.blit(status_label, (panel_x + 5, y_info))

        if file_text:
            file_label = small_font.render(f"File: {file_text}", True, TEXT_COLOR)
            screen.blit(file_label, (panel_x + 5, y_info + 20))

        range_label = small_font.render(f"Range: {range_nm} nm", True, TEXT_COLOR)
        screen.blit(range_label, (panel_x + 5, y_info + 45))

        if csv_player and csv_player.active:
            files_label = small_font.render(
                f"Files: {csv_player._current_rotation_idx + 1}/{len(csv_player._rotations)}",
                True, TEXT_COLOR)
            screen.blit(files_label, (panel_x + 5, y_info + 65))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
