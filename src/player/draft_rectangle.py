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
        self.width, self.height = (200, 25)

        # left, top, width, height
        # This rect will be used for drawing on the main story's surface.
        self.rect_main_dimensions = (0, 0, self.width, self.height)

        # Create an alpha-supporting surface that will contain the rectangle.
        self.rect_surface = pygame.Surface((self.width, self.height),
                                           pygame.SRCALPHA).convert_alpha()

        # Any text here will show up in the draft rectangle
        # for only 2 seconds (120 frames).
        # Purpose: for when sprite data has been copied to the clipboard with the 'i' key.
        self.temporary_text = None

        self._temporary_text_frame_counter = 0

        self.pending_show = False
        self.pending_hide = False
        self.visible = True

    def toggle_visibility(self):
        """
        Hide or show the draft rectangle.
        """

        # So the update rect gets populated for refreshing
        if self.visible:
            self.start_hide()
        else:
            self.start_show()

        self.visible = not self.visible

    def get_temporary_text(self) -> str | None:
        """
        Return any temporary text that should be shown
        in the draft rectangle for 2 seconds (120 frames).

        Purpose: used for showing text such as 'Copied to clipboard'.
        """

        if self.temporary_text:
            if self._temporary_text_frame_counter < 120:  # 2 seconds
                self._temporary_text_frame_counter += 1
                return self.temporary_text
            else:
                self._temporary_text_frame_counter = 0
                self.temporary_text = None

    def start_hide(self):
        """
        Hide the draft rectangle in the next frame.
        """
        # So the update rect will get populated
        self.pending_hide = True
        self.pending_show = False

    def start_show(self):
        """
        Show the draft rectangle in the next frame.
        """
        # So the update rect will get populated
        self.pending_hide = False
        self.pending_show = True

    def update(self) -> List[pygame.Rect]:
        """
        Return the update rect as a list, unless the draft rectangle is not visible.
        """
        update_rect = []
        if any([self.pending_show, self.pending_hide, self.visible]):
            update_rect.append(pygame.Rect(self.rect_main_dimensions))
            self.pending_show = False
            self.pending_hide = False

        return update_rect

    def draw(self, display_text: str):
        """
        Draw a small rectangle at the top center of the main surface.
        
        Arguments:
        
        - display_text: (str) the text to show in the draft rectangle.
        """

        if not self.visible:
            return

        # left, top, width, height
        # This rect will be used for drawing in a surface here that
        # can accept alpha transparency.
        rect_shape = pygame.Rect(0, 0, self.width, self.height)

        # Center of where the rect needs to be drawn on the main surface.
        center = (self.main_surface.get_width() // 2, 15)

        # Create the draft rectangle
        rect_main_location = pygame.Rect(self.rect_main_dimensions)
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
        self.update()
