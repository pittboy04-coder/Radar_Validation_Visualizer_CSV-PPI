"""Top-down geographic scene view for accumulated radar echo visualization."""
import math
import pygame
from typing import List, Tuple, Optional

NM_TO_M = 1852.0

COLORS = {
    'water': (20, 40, 80),
    'own_ship': (255, 255, 0),
    'range_ring': (60, 80, 120),
    'echo': (0, 200, 0),
    'title': (180, 200, 220),
    'north_arrow': (255, 255, 255),
}


class SceneView:
    """Accumulated radar echo view — builds up a persistent picture from sweep data."""

    def __init__(self, size: int = 600):
        self.size = size
        self.center = (size // 2, size // 2)
        self.radius = size // 2 - 20
        self.surface = pygame.Surface((size, size))
        self.echo_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self.echo_surface.fill((0, 0, 0, 0))
        self._font = None
        self._small_font = None

    def _get_font(self, size: int = 16):
        if self._font is None:
            self._font = pygame.font.SysFont('consolas', 16)
            self._small_font = pygame.font.SysFont('consolas', 12)
        return self._small_font if size <= 12 else self._font

    def render(self, sweep_pairs: List[Tuple[float, List[float]]],
               range_nm: float = 6.0) -> pygame.Surface:
        """Render accumulated radar echoes."""
        max_range_m = range_nm * NM_TO_M
        zoom = self.radius / max_range_m if max_range_m > 0 else 1.0

        for bearing, data in sweep_pairs:
            bearing_rad = math.radians(bearing)
            num_bins = len(data)
            for i, intensity in enumerate(data):
                if intensity < 0.05:
                    continue
                dist_m = (i + 0.5) / num_bins * max_range_m
                dx = dist_m * math.sin(bearing_rad)
                dy = dist_m * math.cos(bearing_rad)
                sx = self.center[0] + dx * zoom
                sy = self.center[1] - dy * zoom
                if 0 <= sx < self.size and 0 <= sy < self.size:
                    green = int(min(255, intensity * 255 * 1.5))
                    alpha = int(min(255, intensity * 255))
                    pygame.draw.circle(self.echo_surface, (0, green, 0, alpha),
                                       (int(sx), int(sy)), 2)

        # Compose
        self.surface.fill(COLORS['water'])
        self.surface.blit(self.echo_surface, (0, 0))
        self._draw_range_rings(range_nm)
        self._draw_north_arrow()

        # Center marker
        pygame.draw.circle(self.surface, COLORS['own_ship'], self.center, 4)

        font = self._get_font()
        label = font.render("SCENE VIEW", True, COLORS['title'])
        self.surface.blit(label, (self.size // 2 - label.get_width() // 2, 5))

        return self.surface

    def clear_echoes(self):
        self.echo_surface.fill((0, 0, 0, 0))

    def _draw_range_rings(self, range_nm: float):
        num_rings = 4
        font = self._get_font(12)
        for i in range(1, num_rings + 1):
            r = int(self.radius * i / num_rings)
            pygame.draw.circle(self.surface, COLORS['range_ring'], self.center, r, 1)
            ring_nm = range_nm * i / num_rings
            label = font.render(f"{ring_nm:.1f}nm", True, COLORS['range_ring'])
            self.surface.blit(label, (self.center[0] + 4, self.center[1] - r + 2))

    def _draw_north_arrow(self):
        ax, ay = self.size - 30, 30
        pygame.draw.line(self.surface, COLORS['north_arrow'],
                         (ax, ay + 15), (ax, ay - 15), 2)
        pygame.draw.polygon(self.surface, COLORS['north_arrow'],
                            [(ax, ay - 15), (ax - 5, ay - 5), (ax + 5, ay - 5)])
        font = self._get_font(12)
        n_label = font.render("N", True, COLORS['north_arrow'])
        self.surface.blit(n_label, (ax - n_label.get_width() // 2, ay - 30))
