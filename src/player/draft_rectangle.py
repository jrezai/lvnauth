import pygame
from typing import List


class DraftRectangle:
    """
    This class is used for drawing a small rounded rectangle at the top
    center of a visual story to show the mouse pointer x/y coordinates.
    It's used when creating a visual novel (draft-mode).
    """
    def __init__(self,
                 main_surface: pygame.Surface):

        # The visual novel's main surface.
        self.main_surface = main_surface

        # The size of the surface we're going to create.
        self.width, self.height = (125, 25)

        # Create an alpha-supporting surface that will contain the rectangle.
        self.rect_surface = pygame.Surface((self.width, self.height),
                                           pygame.SRCALPHA).convert_alpha()

    def draw(self, display_text: str) -> List[pygame.Rect]:
        """
        Draw a small rectangle at the top center of the main surface.
        
        Arguments:
        
        - display_text: (str) the text to show in the draft rectangle.
        """

        update_rect = []

        # left, top, width, height
        # This rect will be used for drawing on the main story's surface.
        rect_main_dimensions = (0, 0, self.width, self.height)

        # left, top, width, height
        # This rect will be used for drawing in a surface here that
        # can accept alpha transparency.
        rect_shape = pygame.Rect(0, 0, self.width, self.height)

        # Center of where the rect needs to be drawn on the main surface.
        center = (self.main_surface.get_width() // 2, 15)

        # Create the draft rectangle
        rect_main_location = pygame.Rect(rect_main_dimensions)
        rect_main_location.center = center

        # Blue with 200 alpha
        color = (100, 100, 200, 200)

        # Draw the rectangle on a surface that can accept alpha transparency.
        pygame.draw.rect(surface=self.rect_surface,
                         color=color,
                         rect=rect_shape,
                         border_radius=8)

        # Draw text on a new font surface
        font = pygame.font.SysFont("pygame", 22)
        font_surface = font.render(display_text, True, (255, 255, 255)).convert_alpha()
        
        # The center of the draft rectangle
        center_text_rect = (self.rect_surface.get_width() // 2,
                       self.rect_surface.get_height() // 2)
        
        # left, top, width, height
        # Get the rect of the font surface so we can alter it by centering it.
        rect_text = font_surface.get_rect()
        rect_text.center = center_text_rect
        
        # Blit the coordinates on to the font surface.
        self.rect_surface.blit(font_surface, rect_text)
        
        # Blit the surface that the draft rectangle is on
        # to the main surface.
        self.main_surface.blit(self.rect_surface, rect_main_location)

        # The rect area that will be used for updating the main surface.
        update_rect.append(rect_main_location)

        # The caller of this method will want a rect as a list so it knows
        # where to update the screen.
        return update_rect
