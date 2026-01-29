"""PPI (Plan Position Indicator) radar display for CSV viewer."""
import math
import pygame
from typing import List, Tuple, Optional


class PPIDisplay:
    """Renders radar data in classic PPI format."""

    def __init__(self, size: int = 600):
        self.size = size
        self.radius = size // 2 - 20
        self.center = (size // 2, size // 2)

        # Colors (Furuno-style green phosphor)
        self.bg_color = (0, 10, 0)
        self.grid_color = (0, 60, 0)
        self.sweep_color = (0, 255, 0)
        self.text_color = (0, 200, 0)

        self.num_range_rings = 4
        self.trail_persistence = 0.95
        self.range_nm = 6.0

        self.surface: Optional[pygame.Surface] = None
        self.echo_surface: Optional[pygame.Surface] = None
        self.font: Optional[pygame.font.Font] = None
        self.ppi_offset = (0, 0)

        # Cursor state
        self.cursor_range_nm: Optional[float] = None
        self.cursor_bearing: Optional[float] = None

    def initialize(self) -> None:
        self.surface = pygame.Surface((self.size, self.size))
        self.echo_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.echo_surface.fill((0, 0, 0, 0))
        self.font = pygame.font.SysFont('consolas', 14)

    def set_range(self, range_nm: float) -> None:
        self.range_nm = range_nm

    def set_ppi_offset(self, x: int, y: int) -> None:
        self.ppi_offset = (x, y)

    def draw_sweep_data(self, bearing: float, data: List[float],
                        fade_old: bool = True) -> None:
        if fade_old:
            fade_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, int(255 * (1 - self.trail_persistence))))
            self.echo_surface.blit(fade_surface, (0, 0),
                                   special_flags=pygame.BLEND_RGBA_SUB)

        num_bins = len(data)
        bearing_rad = math.radians(bearing - 90)

        for i, intensity in enumerate(data):
            if intensity < 0.05:
                continue
            range_ratio = (i + 0.5) / num_bins
            r = range_ratio * self.radius
            x = self.center[0] + r * math.cos(bearing_rad)
            y = self.center[1] + r * math.sin(bearing_rad)

            green = int(min(255, intensity * 255 * 1.5))
            alpha = int(min(255, intensity * 255))
            pygame.draw.circle(self.echo_surface, (0, green, 0, alpha),
                               (int(x), int(y)), 2)

    def handle_mouse_motion(self, mx: int, my: int) -> None:
        result = self.screen_to_polar(mx, my)
        if result:
            self.cursor_range_nm, self.cursor_bearing = result
        else:
            self.cursor_range_nm = None
            self.cursor_bearing = None

    def screen_to_polar(self, mx: int, my: int) -> Optional[Tuple[float, float]]:
        lx = mx - self.ppi_offset[0] - self.center[0]
        ly = my - self.ppi_offset[1] - self.center[1]
        dist = math.sqrt(lx * lx + ly * ly)
        if dist > self.radius:
            return None
        range_nm = (dist / self.radius) * self.range_nm
        bearing = math.degrees(math.atan2(lx, -ly)) % 360
        return range_nm, bearing

    def render(self) -> pygame.Surface:
        self.surface.fill(self.bg_color)

        # Range rings
        for i in range(1, self.num_range_rings + 1):
            r = int(self.radius * i / self.num_range_rings)
            pygame.draw.circle(self.surface, self.grid_color, self.center, r, 1)
            ring_nm = self.range_nm * i / self.num_range_rings
            if self.font:
                label = self.font.render(f"{ring_nm:.1f}nm", True, self.text_color)
                self.surface.blit(label, (self.center[0] + 4, self.center[1] + r - 14))

        # Bearing lines every 30 degrees
        for deg in range(0, 360, 30):
            rad = math.radians(deg - 90)
            ex = self.center[0] + self.radius * math.cos(rad)
            ey = self.center[1] + self.radius * math.sin(rad)
            pygame.draw.line(self.surface, self.grid_color, self.center, (int(ex), int(ey)), 1)

        # Echo data
        self.surface.blit(self.echo_surface, (0, 0))

        # Center dot
        pygame.draw.circle(self.surface, self.sweep_color, self.center, 3)

        # Cursor crosshairs
        if self.cursor_range_nm is not None:
            r = int((self.cursor_range_nm / self.range_nm) * self.radius)
            bearing_rad = math.radians(self.cursor_bearing - 90)
            cx = self.center[0] + r * math.cos(bearing_rad)
            cy = self.center[1] + r * math.sin(bearing_rad)
            pygame.draw.line(self.surface, (0, 255, 255),
                             (int(cx) - 10, int(cy)), (int(cx) + 10, int(cy)), 1)
            pygame.draw.line(self.surface, (0, 255, 255),
                             (int(cx), int(cy) - 10), (int(cx), int(cy) + 10), 1)

        return self.surface

    def draw_cursor_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        if self.font and self.cursor_range_nm is not None:
            text = f"R: {self.cursor_range_nm:.2f}nm  B: {self.cursor_bearing:.1f}\u00b0"
            label = self.font.render(text, True, self.text_color)
            surface.blit(label, (x, y))
