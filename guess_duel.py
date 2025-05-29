"""
Game title: Guess Duel
Developer: Shahriar
Description: A two-player turn-based number guessing game with difficulty modes, built with PyGame and Amazon Q CLI
"""

import pygame
import sys
import time
import math
import random
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer for sound effects

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MIN_WIDTH = 640
MIN_HEIGHT = 480

# Set up resizable window
flags = pygame.RESIZABLE | pygame.DOUBLEBUF
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
pygame.display.set_caption("Guess Duel")
clock = pygame.time.Clock()

# Modern color palette
BG_COLOR = (40, 44, 52)  # Dark blue-gray background
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (130, 130, 140)
LIGHT_GRAY = (180, 180, 190)
RED = (235, 83, 83)  # Softer red
LIGHT_RED = (255, 150, 150)
GREEN = (98, 209, 118)  # Softer green
BLUE = (83, 155, 235)  # Softer blue
YELLOW = (235, 198, 83)  # Softer yellow
PURPLE = (187, 134, 252)  # Modern purple
CYAN = (86, 235, 208)  # Modern cyan
TEXT_COLOR = (220, 220, 230)  # Light text for dark background
ACCENT_COLOR = (255, 149, 0)  # Orange accent

# Game states
STATE_MAIN_MENU = 0
STATE_INSTRUCTIONS = 1
STATE_MODE_SELECT = 2
STATE_ATTACKER_CHOOSE = 3  # Was STATE_DEFENDER_CHOOSE
STATE_DEFENDER_GUESS = 4   # Was STATE_ATTACKER_GUESS
STATE_RESULT = 5
STATE_GAME_OVER = 6
STATE_HISTORY = 7  # New state for viewing game history

# Load background music
try:
    pygame.mixer.music.load("background_music.mp3")
    has_background_music = True
except:
    has_background_music = False

# Load background image
background_image = None
try:
    background_image = pygame.image.load("background.jpg")
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    pass  # Will use plain background if image not found

# Sound effects
try:
    sound_correct = pygame.mixer.Sound("correct.wav")
    sound_wrong = pygame.mixer.Sound("wrong.wav")
    sound_click = pygame.mixer.Sound("click.wav")
    sound_game_over = pygame.mixer.Sound("game_over.wav")
except:
    # If sound files aren't available, create dummy sound objects
    class DummySound:
        def play(self): pass
    sound_correct = DummySound()
    sound_wrong = DummySound()
    sound_click = DummySound()
    sound_game_over = DummySound()

# Game settings
class GameSettings:
    def __init__(self):
        self.mode = None  # "easy", "medium", "hard"
        self.range_min = 1
        self.range_max = 9  # Default, will change based on mode and level
        self.defender_hp = 3  # Default, can be adjusted
        self.max_attempts = 6
        self.current_attempt = 0
        self.secret_number = None
        self.current_guess = None
        self.last_guess = None  # Store the last guess for display
        self.last_guess_correct = False  # Was the last guess correct?
        self.attacker_won = False  # Was defender_won
        self.show_secret = False  # Toggle for showing/hiding attacker input
        self.flash_time = 0  # For visual feedback when HP is lost
        self.last_invalid_input_time = 0  # For showing invalid input message
        self.transition_alpha = 255  # For screen transition effects
        self.fade_direction = -1  # -1 for fade in, 1 for fade out
        
        # Level system
        self.current_level = 1  # Current level (1-5)
        self.max_levels = 5  # Maximum levels per category
        self.current_hint = ""  # Current hint text
        # Multi-level system
        self.current_level = 1  # Current level (1-5)
        self.max_levels = 5  # Maximum levels per category
        self.levels_completed = 0  # Number of levels completed in current category
        
        # Hint system
        self.hint_shown = False  # Whether a hint has been shown
        self.current_hint = ""  # Current hint text

# Button class for reusable button functionality
class Button:
    def __init__(self, text, x, y, width, height, inactive_color, active_color, action=None):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.inactive_color = inactive_color
        self.active_color = active_color
        self.action = action
        self.is_hovered = False
        self.scale = 1.0  # For hover animation
        self.glow_size = 0  # For glow effect
        
        # Pre-render text to check dimensions
        font = pygame.font.SysFont(None, 32)  # Default font size
        text_obj = font.render(text, True, BLACK)
        text_rect = text_obj.get_rect()
        
        # Ensure button is wide enough for text
        self.width = max(self.width, text_rect.width + 40)  # Add padding
        
    def draw(self, surface, font):
        # Determine colors based on hover state
        current_color = self.active_color if self.is_hovered else self.inactive_color
        
        # Button animation on hover
        current_width = int(self.width * self.scale)
        current_height = int(self.height * self.scale)
        x_offset = (self.width - current_width) // 2
        y_offset = (self.height - current_height) // 2
        
        # Draw glow effect when hovered
        if self.is_hovered:
            glow_surface = pygame.Surface((current_width + self.glow_size*2, current_height + self.glow_size*2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.active_color[:3], 100), 
                            (0, 0, current_width + self.glow_size*2, current_height + self.glow_size*2), 
                            border_radius=10)
            surface.blit(glow_surface, (self.x + x_offset - self.glow_size, self.y + y_offset - self.glow_size))
        
        # Draw button with rounded corners
        button_rect = pygame.Rect(self.x + x_offset, self.y + y_offset, current_width, current_height)
        pygame.draw.rect(surface, current_color, button_rect, border_radius=8)
        
        # Add subtle gradient effect
        gradient_rect = pygame.Rect(self.x + x_offset, self.y + y_offset, current_width, current_height // 2)
        gradient_color = self.lighten_color(current_color, 30)
        pygame.draw.rect(surface, gradient_color, gradient_rect, border_radius=8)
        
        # Measure text to ensure it fits
        text_obj = font.render(self.text, True, BLACK if self.is_light_color(current_color) else WHITE)
        text_rect = text_obj.get_rect()
        
        # Check if text is too wide for button
        if text_rect.width > current_width - 20:  # Allow for padding
            # Reduce font size to fit
            new_font_size = int(font.get_height() * (current_width - 20) / text_rect.width)
            new_font = pygame.font.SysFont(None, max(12, new_font_size))  # Don't go below 12pt
            text_obj = new_font.render(self.text, True, BLACK if self.is_light_color(current_color) else WHITE)
            text_rect = text_obj.get_rect()
        
        # Center text in button
        text_rect.center = (self.x + self.width // 2, self.y + self.height // 2)
        
        # Draw subtle text shadow
        shadow_obj = font.render(self.text, True, (0, 0, 0, 100))
        shadow_rect = shadow_obj.get_rect()
        shadow_rect.center = (self.x + self.width // 2 + 2, self.y + self.height // 2 + 2)
        shadow_obj.set_alpha(100)
        surface.blit(shadow_obj, shadow_rect)
        
        # Draw text
        surface.blit(text_obj, text_rect)
    
    def update(self, mouse_pos, mouse_click):
        # Check if mouse is over button
        self.is_hovered = (self.x + self.width > mouse_pos[0] > self.x and 
                          self.y + self.height > mouse_pos[1] > self.y)
        
        # Animate button on hover
        target_scale = 1.05 if self.is_hovered else 1.0
        target_glow = 10 if self.is_hovered else 0
        self.scale += (target_scale - self.scale) * 0.2
        self.glow_size += (target_glow - self.glow_size) * 0.2
        
        # Handle click
        if self.is_hovered and mouse_click[0] == 1 and self.action is not None:
            sound_click.play()
            self.action()
            return True
        return False
    
    def set_position(self, x, y):
        """Update button position (for responsive UI)"""
        self.x = x
        self.y = y
    
    def lighten_color(self, color, amount=30):
        r = min(255, color[0] + amount)
        g = min(255, color[1] + amount)
        b = min(255, color[2] + amount)
        return (r, g, b)
    
    def is_light_color(self, color):
        # Check if a color is light (needs dark text) or dark (needs light text)
        return (color[0]*0.299 + color[1]*0.587 + color[2]*0.114) > 186
# Base screen class
class Screen:
    def __init__(self, game_settings):
        self.game_settings = game_settings
        self.transition_time = time.time()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
    
    def handle_event(self, event):
        pass
    
    def update(self):
        # Handle screen transition effects
        if self.game_settings.transition_alpha > 0 and self.game_settings.fade_direction < 0:
            self.game_settings.transition_alpha = max(0, self.game_settings.transition_alpha - 10)
        elif self.game_settings.transition_alpha < 255 and self.game_settings.fade_direction > 0:
            self.game_settings.transition_alpha = min(255, self.game_settings.transition_alpha + 10)
        
        # Update screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
    
    def draw(self, surface):
        # Draw background if available
        if background_image:
            # Scale background to fit window
            scaled_bg = pygame.transform.scale(background_image, (self.width, self.height))
            surface.blit(scaled_bg, (0, 0))
        else:
            # Create a gradient background
            for y in range(0, self.height, 2):
                # Calculate gradient color
                gradient_factor = y / self.height
                r = int(BG_COLOR[0] * (1 - gradient_factor * 0.3))
                g = int(BG_COLOR[1] * (1 - gradient_factor * 0.3))
                b = int(BG_COLOR[2] * (1 - gradient_factor * 0.3))
                pygame.draw.rect(surface, (r, g, b), (0, y, self.width, 2))
            
    def draw_transition_overlay(self, surface):
        # Draw transition overlay
        if self.game_settings.transition_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill(BLACK)
            overlay.set_alpha(self.game_settings.transition_alpha)
            surface.blit(overlay, (0, 0))
            
    def draw_panel(self, surface, x, y, width, height):
        """Draw a semi-transparent panel for content"""
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((30, 30, 40, 180))  # Semi-transparent dark panel
        pygame.draw.rect(panel, ACCENT_COLOR, (0, 0, width, height), 2, border_radius=10)
        surface.blit(panel, (x, y))
        
    def get_centered_position(self, width, height):
        """Get centered position for UI elements based on current screen size"""
        return (self.width // 2 - width // 2, self.height // 2 - height // 2)

# Main Menu Screen
class MainMenuScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        button_width = 250
        button_height = 60
        # Use self.width instead of SCREEN_WIDTH for responsive positioning
        button_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            Button("Play Game", button_x, 250, button_width, button_height, GREEN, CYAN, 
                  lambda: self.change_state(STATE_MODE_SELECT)),
            Button("Instructions", button_x, 350, button_width, button_height, BLUE, PURPLE, 
                  lambda: self.change_state(STATE_INSTRUCTIONS)),
            Button("View History", button_x, 450, button_width, button_height, YELLOW, ACCENT_COLOR, 
                  lambda: self.change_state(STATE_HISTORY))
        ]
        
        # Animation variables
        self.title_angle = 0
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(2, 5),
                'speed': random.uniform(0.5, 2.0),
                'color': random.choice([BLUE, GREEN, YELLOW, PURPLE, CYAN])
            })
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
        
        # Start background music when game starts
        if has_background_music and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        
        for button in self.buttons:
            button.update(mouse_pos, mouse_click)
    
    def update(self):
        super().update()
        self.title_angle += 0.02
        
        # Update particles
        for p in self.particles:
            p['y'] += p['speed']
            if p['y'] > self.height:
                p['y'] = 0
                p['x'] = random.randint(0, self.width)
                
        # Update button positions for responsive UI
        button_width = 250
        button_height = 60
        button_x = self.width // 2 - button_width // 2
        
        self.buttons[0].set_position(button_x, 250)
        self.buttons[1].set_position(button_x, 350)
        self.buttons[2].set_position(button_x, 450)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw particles
        for p in self.particles:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), p['size'])
        
        # Draw title with animation
        title_font = pygame.font.SysFont(None, 80)
        title_shadow = title_font.render("GUESS DUEL", True, BLACK)
        title_text = title_font.render("GUESS DUEL", True, ACCENT_COLOR)
        
        # Create a pulsing/glowing effect
        glow_factor = 0.5 + 0.5 * math.sin(self.title_angle * 2)
        glow_size = int(10 * glow_factor)
        
        # Draw title with shadow and glow - use self.width for responsive positioning
        shadow_rect = title_shadow.get_rect(center=(self.width // 2 + 3, 120 + 3))
        text_rect = title_text.get_rect(center=(self.width // 2, 120))
        
        # Draw glow
        glow_surface = pygame.Surface((text_rect.width + glow_size*2, text_rect.height + glow_size*2), pygame.SRCALPHA)
        glow_color = (*ACCENT_COLOR[:3], int(100 * glow_factor))
        pygame.draw.rect(glow_surface, glow_color, 
                        (0, 0, text_rect.width + glow_size*2, text_rect.height + glow_size*2), 
                        border_radius=15)
        surface.blit(glow_surface, (text_rect.x - glow_size, text_rect.y - glow_size))
        
        # Draw shadow and text
        title_shadow.set_alpha(150)
        surface.blit(title_shadow, shadow_rect)
        surface.blit(title_text, text_rect)
        
        # Draw subtitle - FIXED: Use self.width instead of SCREEN_WIDTH for responsive positioning
        subtitle_font = pygame.font.SysFont(None, 32)
        draw_text("A two-player number guessing game", subtitle_font, TEXT_COLOR, surface, 
                 self.width // 2, 180, True)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface, small_font)
            
        # Draw transition overlay
        self.draw_transition_overlay(surface)

# Instructions Screen
class InstructionsScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.back_button = Button("Back to Menu", self.width // 2 - 100, 500, 200, 50, BLUE, PURPLE, 
                                 lambda: self.change_state(STATE_MAIN_MENU))
        
        # Animation variables
        self.animation_time = 0
        self.icon_positions = [
            {'x': self.width * 0.2, 'y': 200, 'icon': '🎮', 'scale': 1.0, 'phase': 0},
            {'x': self.width * 0.8, 'y': 200, 'icon': '🎯', 'scale': 1.0, 'phase': 1},
            {'x': self.width * 0.2, 'y': 350, 'icon': '❤️', 'scale': 1.0, 'phase': 2},
            {'x': self.width * 0.8, 'y': 350, 'icon': '🔢', 'scale': 1.0, 'phase': 3},
        ]
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
    
    def handle_event(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.change_state(STATE_MAIN_MENU)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        self.back_button.update(mouse_pos, mouse_click)
    
    def update(self):
        super().update()
        self.animation_time += 0.05
        
        # Update icon animations
        for icon in self.icon_positions:
            icon['scale'] = 1.0 + 0.2 * math.sin(self.animation_time * 2 + icon['phase'])
        
        # Update button position for responsive UI
        self.back_button.set_position(self.width // 2 - 100, 500)
        
        # Update icon positions for responsive UI
        self.icon_positions[0]['x'] = self.width * 0.2
        self.icon_positions[1]['x'] = self.width * 0.8
        self.icon_positions[2]['x'] = self.width * 0.2
        self.icon_positions[3]['x'] = self.width * 0.8
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(650, self.width - 40)  # Make panel responsive to screen width
        panel_height = 450
        panel_x = self.width // 2 - panel_width // 2
        panel_y = 70
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw title with shadow
        draw_text("How to Play", font, ACCENT_COLOR, surface, self.width // 2, panel_y + 30, True, True)
        
        # Draw animated icons
        for icon in self.icon_positions:
            icon_font = pygame.font.SysFont(None, int(48 * icon['scale']))
            draw_text(icon['icon'], icon_font, TEXT_COLOR, surface, icon['x'], icon['y'], True)
        
        # Draw instructions with improved formatting - FIXED: Make text positions responsive
        instructions = [
            ("1. Attacker secretly chooses a number within the selected range", (self.width * 0.3, panel_y + 180)),
            ("2. Defender has 6 attempts to guess the number", (self.width * 0.3, panel_y + 220)),
            ("3. For each wrong guess, Defender loses 1 HP (starting with 3 HP)", (self.width * 0.3, panel_y + 260)),
            ("4. Game ends when Defender uses all attempts or loses all HP", (self.width * 0.3, panel_y + 300)),
            ("5. Complete all 5 levels to become a Category Champion!", (self.width * 0.3, panel_y + 340)),
        ]
        
        for text, pos in instructions:
            draw_text(text, small_font, TEXT_COLOR, surface, pos[0], pos[1], False)
        
        # Draw prompt with pulsing animation - FIXED: Use self.width for responsive positioning
        prompt_scale = 1.0 + 0.1 * abs(math.sin(self.animation_time * 3))
        prompt_font = pygame.font.SysFont(None, int(32 * prompt_scale))
        draw_text("Press SPACE to continue", prompt_font, CYAN, surface, 
                 self.width // 2, panel_y + 400, True)
        
        # Draw back button
        self.back_button.draw(surface, small_font)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
# Mode Select Screen
class ModeSelectScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        button_width = 250
        button_height = 70
        button_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            Button("Easy (1-9)", button_x, 180, button_width, button_height, GREEN, CYAN, self.set_mode_easy),
            Button("Medium (10-99)", button_x, 280, button_width, button_height, BLUE, PURPLE, self.set_mode_medium),
            Button("Hard (100-999)", button_x, 380, button_width, button_height, RED, ACCENT_COLOR, self.set_mode_hard),
            Button("Back", button_x, 480, button_width, button_height, GRAY, LIGHT_GRAY, 
                  lambda: self.change_state(STATE_MAIN_MENU))
        ]
        
        # Mode descriptions
        self.mode_descriptions = {
            "easy": "1-digit numbers - 5 levels with increasing challenge",
            "medium": "2-digit numbers - 5 levels with increasing challenge",
            "hard": "3-digit numbers - 5 levels with increasing challenge"
        }
        
        self.hovered_mode = None
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
    
    def set_mode_easy(self):
        self.game_settings.mode = "easy"
        self.game_settings.current_level = 1
        self.update_level_range("easy", 1)
        self.change_state(STATE_ATTACKER_CHOOSE)
    
    def set_mode_medium(self):
        self.game_settings.mode = "medium"
        self.game_settings.current_level = 1
        self.update_level_range("medium", 1)
        self.change_state(STATE_ATTACKER_CHOOSE)
    
    def set_mode_hard(self):
        self.game_settings.mode = "hard"
        self.game_settings.current_level = 1
        self.update_level_range("hard", 1)
        self.change_state(STATE_ATTACKER_CHOOSE)
        
    def update_level_range(self, mode, level):
        """Update number range and difficulty based on mode and level"""
        # Base ranges for each mode
        if mode == "easy":
            # Easy mode: 1-digit numbers
            base_min = 1
            base_max = 9
            self.game_settings.defender_hp = 3
            self.game_settings.max_attempts = 6
        elif mode == "medium":
            # Medium mode: 2-digit numbers
            base_min = 10
            base_max = 99
            self.game_settings.defender_hp = 3
            self.game_settings.max_attempts = 5
        elif mode == "hard":
            # Hard mode: 3-digit numbers
            base_min = 100
            base_max = 999
            self.game_settings.defender_hp = 2
            self.game_settings.max_attempts = 5
            
        # Adjust difficulty based on level
        if level == 1:
            # Level 1: Standard range
            self.game_settings.range_min = base_min
            self.game_settings.range_max = base_max
        elif level == 2:
            # Level 2: Slightly expanded range
            self.game_settings.range_min = base_min
            self.game_settings.range_max = int(base_max * 1.2)
        elif level == 3:
            # Level 3: Reduced attempts
            self.game_settings.range_min = base_min
            self.game_settings.range_max = base_max
            self.game_settings.max_attempts -= 1
        elif level == 4:
            # Level 4: Further expanded range
            self.game_settings.range_min = base_min
            self.game_settings.range_max = int(base_max * 1.5)
        elif level == 5:
            # Level 5: Maximum challenge
            self.game_settings.range_min = base_min
            self.game_settings.range_max = int(base_max * 2)
            self.game_settings.max_attempts -= 1
            
        # Reset attempts and other game state
        self.game_settings.current_attempt = 0
        self.game_settings.current_hint = ""
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        
        self.hovered_mode = None
        for i, button in enumerate(self.buttons):
            # Update button positions for responsive UI
            if i == 0:
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 - 150)
            elif i == 1:
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 - 50)
            elif i == 2:
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 + 50)
            elif i == 3:
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 + 150)
                
            button.update(mouse_pos, mouse_click)
            if button.is_hovered and i < 3:  # Only for the three difficulty modes
                self.hovered_mode = ["easy", "medium", "hard"][i]
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(600, self.width - 40)
        panel_height = min(450, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw title with shadow
        draw_text("Select Difficulty", font, ACCENT_COLOR, surface, self.width // 2, panel_y + 40, True, True)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface, small_font)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)

# Attacker Choose Screen (was Defender Choose Screen)
class DefenderScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.input_text = ""
        self.input_active = False
        self.input_box = pygame.Rect(self.width // 2 - 100, 200, 200, 50)
        
        # Toggle button for showing/hiding input
        self.toggle_button = Button("Show", self.width // 2 + 120, 200, 80, 50, BLUE, CYAN, self.toggle_show_secret)
        
        # Input cursor animation
        self.cursor_visible = True
        self.cursor_time = 0
    
    def toggle_show_secret(self):
        self.game_settings.show_secret = not self.game_settings.show_secret
        self.toggle_button.text = "Hide" if self.game_settings.show_secret else "Show"
    
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_RETURN:
                self.process_attacker_input()
            elif event.key == K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isdigit() and len(self.input_text) < 5:  # Limit input length
                self.input_text += event.unicode
        
        if event.type == MOUSEBUTTONDOWN:
            # Update input box position for responsive UI
            input_box = pygame.Rect(self.width // 2 - 100, self.height // 2 - 50, 200, 50)
            self.input_active = input_box.collidepoint(event.pos)
            
            # Check toggle button - FIXED: Properly handle button click
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = (1, 0, 0)  # Simulate left mouse button click
            
            # Update toggle button position
            self.toggle_button.set_position(self.width // 2 + 120, self.height // 2 - 50)
            if self.toggle_button.is_hovered and event.button == 1:
                self.toggle_show_secret()  # Directly call the toggle function on click
    
    def update(self):
        super().update()
        # Cursor blinking animation
        if time.time() - self.cursor_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_time = time.time()
            
        # Update toggle button hover state
        mouse_pos = pygame.mouse.get_pos()
        self.toggle_button.is_hovered = (self.toggle_button.x + self.toggle_button.width > mouse_pos[0] > self.toggle_button.x and 
                                        self.toggle_button.y + self.toggle_button.height > mouse_pos[1] > self.toggle_button.y)
    
    def process_attacker_input(self):
        global current_state
        try:
            num = int(self.input_text)
            # Check if number is within the current level's range
            if self.game_settings.range_min <= num <= self.game_settings.range_max:
                self.game_settings.secret_number = num
                self.input_text = ""
                self.game_settings.transition_alpha = 0
                self.game_settings.fade_direction = -1
                current_state = STATE_DEFENDER_GUESS
            else:
                # Invalid input - out of range
                self.game_settings.last_invalid_input_time = time.time()
                self.input_text = ""  # Clear invalid input
        except ValueError:
            # Invalid input - not a number
            self.game_settings.last_invalid_input_time = time.time()
            self.input_text = ""  # Clear invalid input
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(500, self.width - 40)
        panel_height = min(300, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw level indicator
        level_text = f"Level {self.game_settings.current_level} of {self.game_settings.max_levels}"
        level_font = pygame.font.SysFont(None, 28)
        draw_text(level_text, level_font, ACCENT_COLOR, surface, self.width // 2, panel_y + 30, True)
        
        # Draw title
        draw_text(f"Attacker: Choose a number", font, TEXT_COLOR, surface, self.width // 2, panel_y + 70, True)
        draw_text(f"Range: {self.game_settings.range_min}-{self.game_settings.range_max}", small_font, TEXT_COLOR, 
                 surface, self.width // 2, panel_y + 110, True)
        
        # Draw input box with modern styling - ensure it's properly sized for the content
        input_rect = pygame.Rect(self.width // 2 - 100, panel_y + 150, 200, 50)
        color = GREEN if self.input_active else GRAY
        
        # Draw input box background
        pygame.draw.rect(surface, (50, 50, 60), input_rect, border_radius=8)
        pygame.draw.rect(surface, color, input_rect, 2, border_radius=8)
        
        # Render the input text (masked or shown based on setting)
        display_text = self.input_text
        if not self.game_settings.show_secret and self.input_text:
            display_text = "●" * len(self.input_text)
        
        # Center the text in the input box
        if display_text:
            # Use a smaller font if the text is too long
            if len(display_text) > 3:
                input_font = pygame.font.SysFont(None, 28)  # Smaller font for longer numbers
            else:
                input_font = small_font
                
            text_surface = input_font.render(display_text, True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=input_rect.center)
            surface.blit(text_surface, text_rect)
            
            # Draw cursor if active
            if self.input_active and self.cursor_visible:
                cursor_x = text_rect.right + 2
                if cursor_x > input_rect.right - 5:
                    cursor_x = input_rect.right - 5
                pygame.draw.line(surface, TEXT_COLOR, 
                                (cursor_x, input_rect.y + 10), 
                                (cursor_x, input_rect.y + input_rect.height - 10), 2)
        elif self.input_active and self.cursor_visible:
            # Draw cursor at start position if no text
            pygame.draw.line(surface, TEXT_COLOR, 
                            (input_rect.x + 10, input_rect.y + 10), 
                            (input_rect.x + 10, input_rect.y + input_rect.height - 10), 2)
        
        # Reposition toggle button to align with input box
        self.toggle_button.set_position(input_rect.right + 20, input_rect.y)
        
        # Draw toggle button with current state
        button_color = CYAN if self.game_settings.show_secret else BLUE
        hover_color = BLUE if self.game_settings.show_secret else CYAN
        
        # Draw button with rounded corners
        button_rect = pygame.Rect(self.toggle_button.x, self.toggle_button.y, 
                                 self.toggle_button.width, self.toggle_button.height)
        pygame.draw.rect(surface, button_color if self.toggle_button.is_hovered else hover_color, 
                        button_rect, border_radius=8)
        
        # Draw button text
        button_text = "Hide" if self.game_settings.show_secret else "Show"
        button_font = pygame.font.SysFont(None, 28)
        text_obj = button_font.render(button_text, True, WHITE)
        text_rect = text_obj.get_rect(center=(self.toggle_button.x + self.toggle_button.width // 2, 
                                             self.toggle_button.y + self.toggle_button.height // 2))
        surface.blit(text_obj, text_rect)
        
        # Show invalid input message if needed
        if time.time() - self.game_settings.last_invalid_input_time < 2.0:
            error_font = pygame.font.SysFont(None, 24)
            error_alpha = min(255, int(255 * (2.0 - (time.time() - self.game_settings.last_invalid_input_time)) / 2.0))
            error_text = error_font.render("Invalid input! Enter a number in the valid range.", True, RED)
            error_text.set_alpha(error_alpha)
            error_rect = error_text.get_rect(center=(self.width // 2, panel_y + 220))
            surface.blit(error_text, error_rect)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
# Defender Guess Screen (was Attacker Guess Screen)
class AttackerScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.input_text = ""
        self.input_active = False
        self.input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, 300, 200, 50)
        
        # Input cursor animation
        self.cursor_visible = True
        self.cursor_time = 0
        
        # HP bar animation
        self.hp_animation = 0
    
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_RETURN:
                self.process_defender_input()
            elif event.key == K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isdigit() and len(self.input_text) < 5:  # Limit input length
                self.input_text += event.unicode
        
        if event.type == MOUSEBUTTONDOWN:
            # Update input box position for responsive UI
            input_box = pygame.Rect(self.width // 2 - 60, self.height // 2 + 60, 120, 50)
            self.input_active = input_box.collidepoint(event.pos)
    
    def generate_hint(self):
        """Generate a hint based on the secret number"""
        secret_str = str(self.game_settings.secret_number)
        hint_type = random.randint(1, 3)
        
        if hint_type == 1:
            # Hint about first digit
            return f"The number starts with {secret_str[0]}"
        elif hint_type == 2:
            # Hint about number being greater/less than midpoint
            midpoint = (self.game_settings.range_min + self.game_settings.range_max) // 2
            if self.game_settings.secret_number > midpoint:
                return f"The number is greater than {midpoint}"
            else:
                return f"The number is less than {midpoint}"
        else:
            # Hint about last digit
            return f"The number ends with {secret_str[-1]}"
    
    def process_defender_input(self):
        global current_state
        try:
            num = int(self.input_text)
            if self.game_settings.range_min <= num <= self.game_settings.range_max:
                self.game_settings.current_guess = num
                self.game_settings.current_attempt += 1
                
                # Store the guess for display
                self.game_settings.last_guess = num
                
                # Check if guess is correct
                if self.game_settings.current_guess == self.game_settings.secret_number:
                    sound_correct.play()
                    self.game_settings.last_guess_correct = True
                    
                    # Level completed - move to next level
                    self.game_settings.current_level += 1
                    if self.game_settings.current_level > self.game_settings.max_levels:
                        # All levels completed
                        self.game_settings.current_level = 1
                        self.game_settings.attacker_won = False
                        current_state = STATE_GAME_OVER
                        self.save_game_result(f"Defender wins - Completed all levels in {self.game_settings.mode} mode")
                    else:
                        # Update for next level
                        mode_select_screen = screens.get(STATE_MODE_SELECT)
                        if mode_select_screen:
                            mode_select_screen.update_level_range(self.game_settings.mode, self.game_settings.current_level)
                        current_state = STATE_ATTACKER_CHOOSE
                else:
                    sound_wrong.play()
                    self.game_settings.last_guess_correct = False
                    self.game_settings.defender_hp -= 1
                    self.game_settings.flash_time = time.time()  # Set flash time for visual feedback
                
                    self.input_text = ""
                    self.game_settings.transition_alpha = 0
                    self.game_settings.fade_direction = -1
                    current_state = STATE_RESULT
                    
                    # Check if we should show a hint (levels 3-5, after 2 incorrect guesses)
                    if (self.game_settings.current_level >= 3 and 
                        self.game_settings.current_attempt >= 2 and 
                        not self.game_settings.current_hint):
                        self.game_settings.current_hint = self.generate_hint()
                
                # Check game over conditions
                if self.game_settings.defender_hp <= 0:
                    sound_game_over.play()
                    if has_background_music:
                        pygame.mixer.music.stop()
                    self.game_settings.attacker_won = True  # Defender lost all HP, so Attacker wins
                    current_state = STATE_GAME_OVER
                    
                    # Save game result to history
                    self.save_game_result(f"Attacker wins - Level {self.game_settings.current_level}")
                    
                elif self.game_settings.current_attempt >= self.game_settings.max_attempts:
                    sound_game_over.play()
                    if has_background_music:
                        pygame.mixer.music.stop()
                    self.game_settings.attacker_won = False  # Attacker used all attempts, so Defender wins
                    current_state = STATE_GAME_OVER
                    
                    # Save game result to history
                    self.save_game_result(f"Defender wins - Level {self.game_settings.current_level}")
            else:
                # Invalid input - out of range
                self.game_settings.last_invalid_input_time = time.time()
                self.input_text = ""  # Clear invalid input
        except ValueError:
            # Invalid input - not a number
            self.game_settings.last_invalid_input_time = time.time()
            self.input_text = ""  # Clear invalid input
    
    def save_game_result(self, result):
        try:
            with open("scores.txt", "a") as f:
                f.write(f"{result} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except:
            pass  # Silently fail if file can't be written
    
    def update(self):
        super().update()
        # Update flash effect if active
        if time.time() - self.game_settings.flash_time < 0.3:
            # Flash is active
            pass
            
        # Cursor blinking animation
        if time.time() - self.cursor_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_time = time.time()
            
        # HP bar animation
        self.hp_animation += 0.05
    
    def draw(self, surface):
        # Determine background color based on flash state
        bg_color = None
        if time.time() - self.game_settings.flash_time < 0.3:
            # Flash red when HP is lost
            flash_intensity = max(0, 0.3 - (time.time() - self.game_settings.flash_time)) / 0.3
            bg_color = (min(255, BG_COLOR[0] + int(100 * flash_intensity)), 
                       max(0, BG_COLOR[1] - int(30 * flash_intensity)), 
                       max(0, BG_COLOR[2] - int(30 * flash_intensity)))
        
        if bg_color:
            # Create a gradient background with flash effect
            for y in range(0, self.height, 2):
                gradient_factor = y / self.height
                r = int(bg_color[0] * (1 - gradient_factor * 0.3))
                g = int(bg_color[1] * (1 - gradient_factor * 0.3))
                b = int(bg_color[2] * (1 - gradient_factor * 0.3))
                pygame.draw.rect(surface, (r, g, b), (0, y, self.width, 2))
        else:
            super().draw(surface)
        
        # Draw panel for content
        panel_width = min(600, self.width - 40)
        panel_height = min(400, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw level indicator
        level_text = f"Level {self.game_settings.current_level} of {self.game_settings.max_levels}"
        level_font = pygame.font.SysFont(None, 28)
        draw_text(level_text, level_font, ACCENT_COLOR, surface, self.width // 2, panel_y + 30, True)
        
        # Draw title
        draw_text(f"Defender: Guess the number", font, TEXT_COLOR, surface, self.width // 2, panel_y + 70, True)
        draw_text(f"Range: {self.game_settings.range_min}-{self.game_settings.range_max}", small_font, TEXT_COLOR, 
                 surface, self.width // 2, panel_y + 110, True)
        
        # Display attempts with clear formatting - FIXED
        attempts_text = f"Attempts: {self.game_settings.current_attempt}/{self.game_settings.max_attempts}"
        attempts_font = pygame.font.SysFont(None, 32)  # Use a specific font to avoid rendering issues
        draw_text(attempts_text, attempts_font, TEXT_COLOR, surface, self.width // 2, panel_y + 150, True)
        
        # Draw attempts progress bar - MOVED DOWN to avoid hiding the attempts text
        progress_width = min(300, panel_width - 100)
        progress_height = 15
        progress_x = self.width // 2 - progress_width // 2
        progress_y = panel_y + 180  # Moved down from 140 to 180 to avoid hiding the text
        
        # Background bar
        pygame.draw.rect(surface, GRAY, (progress_x, progress_y, progress_width, progress_height), border_radius=7)
        
        # Progress fill
        progress_fill = progress_width * (self.game_settings.current_attempt / self.game_settings.max_attempts)
        if progress_fill > 0:
            pygame.draw.rect(surface, YELLOW, 
                           (progress_x, progress_y, int(progress_fill), progress_height), 
                           border_radius=7)
        
        # Display defender HP
        draw_text(f"Defender HP: {self.game_settings.defender_hp}", small_font, TEXT_COLOR, surface, self.width // 2, panel_y + 180, True)
        
        # Draw HP bars with animation
        hp_bar_width = 60
        hp_bar_height = 25
        hp_bar_spacing = 15
        total_width = 3 * (hp_bar_width + hp_bar_spacing) - hp_bar_spacing  # Always show 3 slots
        start_x = self.width // 2 - total_width // 2
        
        # Draw empty HP slots first
        for i in range(3):  # Always show 3 slots
            pygame.draw.rect(surface, (80, 80, 80), 
                           (start_x + i * (hp_bar_width + hp_bar_spacing), panel_y + 210, hp_bar_width, hp_bar_height),
                           border_radius=5)
        
        # Draw filled HP bars with pulsing animation
        for i in range(self.game_settings.defender_hp):
            pulse = 0.8 + 0.2 * math.sin(self.hp_animation + i * 0.5)
            hp_color = (int(RED[0] * pulse), int(RED[1] * pulse), int(RED[2] * pulse))
            
            pygame.draw.rect(surface, hp_color, 
                           (start_x + i * (hp_bar_width + hp_bar_spacing), panel_y + 210, hp_bar_width, hp_bar_height),
                           border_radius=5)
            
            # Add highlight to top of bar
            highlight_height = 5
            highlight_color = (min(255, hp_color[0] + 50), min(255, hp_color[1] + 50), min(255, hp_color[2] + 50))
            pygame.draw.rect(surface, highlight_color, 
                           (start_x + i * (hp_bar_width + hp_bar_spacing), panel_y + 210, hp_bar_width, highlight_height),
                           border_radius=5)
        
        # Draw input box with modern styling
        input_rect = pygame.Rect(self.width // 2 - 60, panel_y + 260, 120, 50)
        color = BLUE if self.input_active else GRAY
        
        # Draw input box background
        pygame.draw.rect(surface, (50, 50, 60), input_rect, border_radius=8)
        pygame.draw.rect(surface, color, input_rect, 2, border_radius=8)
        
        # Render the input text
        if self.input_text:
            # Use a smaller font if the text is too long
            if len(self.input_text) > 3:
                input_font = pygame.font.SysFont(None, 28)  # Smaller font for longer numbers
            else:
                input_font = small_font
                
            text_surface = input_font.render(self.input_text, True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=input_rect.center)
            surface.blit(text_surface, text_rect)
            
            # Draw cursor if active
            if self.input_active and self.cursor_visible:
                cursor_x = text_rect.right + 2
                if cursor_x > input_rect.right - 5:
                    cursor_x = input_rect.right - 5
                pygame.draw.line(surface, TEXT_COLOR, 
                                (cursor_x, input_rect.y + 10), 
                                (cursor_x, input_rect.y + input_rect.height - 10), 2)
        elif self.input_active and self.cursor_visible:
            # Draw cursor at start position if no text
            pygame.draw.line(surface, TEXT_COLOR, 
                            (input_rect.x + 10, input_rect.y + 10), 
                            (input_rect.x + 10, input_rect.y + input_rect.height - 10), 2)
        
        # Display previous guess if available
        if self.game_settings.last_guess is not None:
            result_color = GREEN if self.game_settings.last_guess_correct else RED
            result_text = "Correct!" if self.game_settings.last_guess_correct else "Wrong!"
            
            # Create a small panel for the last guess
            last_guess_panel = pygame.Surface((220, 40), pygame.SRCALPHA)
            last_guess_panel.fill((50, 50, 60, 180))
            pygame.draw.rect(last_guess_panel, result_color, (0, 0, 220, 40), 2, border_radius=8)
            surface.blit(last_guess_panel, (self.width // 2 - 110, panel_y + 330))
            
            # Use a smaller font if needed
            guess_text = f"Last guess: {self.game_settings.last_guess} - {result_text}"
            guess_font = pygame.font.SysFont(None, 26)  # Smaller font to ensure it fits
            draw_text(guess_text, guess_font, result_color, surface, self.width // 2, panel_y + 350, True)
        
        # Show hint if available (for levels 3-5 after 2 incorrect guesses)
        if hasattr(self.game_settings, 'current_hint') and self.game_settings.current_hint:
            # Calculate the size needed for the hint text
            hint_font = pygame.font.SysFont(None, 24)
            hint_text = f"Hint: {self.game_settings.current_hint}"
            hint_text_surface = hint_font.render(hint_text, True, YELLOW)
            hint_text_width = hint_text_surface.get_width()
            
            # Make the panel width responsive to the text content
            hint_panel_width = max(panel_width - 80, hint_text_width + 40)  # Add padding
            hint_panel_height = 40  # Fixed height
            
            # Create the panel surface with the calculated size
            hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
            hint_panel.fill((60, 60, 80, 200))
            pygame.draw.rect(hint_panel, YELLOW, (0, 0, hint_panel_width, hint_panel_height), 2, border_radius=8)
            
            # Position the panel centered horizontally
            hint_panel_x = self.width // 2 - hint_panel_width // 2
            hint_panel_y = panel_y + panel_height - 60
            surface.blit(hint_panel, (hint_panel_x, hint_panel_y))
            
            # Draw the hint text
            draw_text(hint_text, hint_font, YELLOW, surface, self.width // 2, panel_y + panel_height - 40, True)
        
        # Show invalid input message if needed
        if time.time() - self.game_settings.last_invalid_input_time < 2.0:
            error_font = pygame.font.SysFont(None, 24)
            error_alpha = min(255, int(255 * (2.0 - (time.time() - self.game_settings.last_invalid_input_time)) / 2.0))
            error_text = error_font.render("Invalid input! Enter a number in the valid range.", True, RED)
            error_text.set_alpha(error_alpha)
            error_rect = error_text.get_rect(center=(self.width // 2, input_rect.y + 70))
            surface.blit(error_text, error_rect)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
# Result Screen
class ResultScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.particles = []
        self.generate_particles()
        self.show_secret = False  # Don't show secret number by default
    
    def generate_particles(self):
        self.particles = []
        color = GREEN if self.game_settings.current_guess == self.game_settings.secret_number else RED
        
        for _ in range(50):
            self.particles.append({
                'x': self.width // 2,
                'y': self.height // 2,
                'size': random.randint(3, 8),
                'speed_x': random.uniform(-3, 3),
                'speed_y': random.uniform(-3, 3),
                'color': color,
                'alpha': 255,
                'fade_speed': random.uniform(1, 3)
            })
    
    def handle_event(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            global current_state
            self.game_settings.transition_alpha = 0
            self.game_settings.fade_direction = -1
            current_state = STATE_DEFENDER_GUESS
    
    def update(self):
        super().update()
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['alpha'] -= p['fade_speed']
            
            if p['alpha'] <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(500, self.width - 40)
        panel_height = min(300, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw particles
        for p in self.particles:
            particle_surface = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*p['color'][:3], int(p['alpha'])), 
                             (p['size'], p['size']), p['size'])
            surface.blit(particle_surface, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        if self.game_settings.current_guess == self.game_settings.secret_number:
            result_text = "Correct guess!"
            sub_text = "Attacker survives this round."
            result_color = GREEN
        else:
            result_text = "Wrong!"
            # Only show the secret number when game is over
            if self.game_settings.defender_hp <= 0 or self.game_settings.current_attempt >= self.game_settings.max_attempts:
                sub_text = f"The number was {self.game_settings.secret_number}. Defender loses 1 HP!"
            else:
                sub_text = "Try again! Defender loses 1 HP!"
            result_color = RED
        
        # Animate the result text
        scale = 1.0 + 0.1 * abs(math.sin(time.time() * 5))
        result_font = pygame.font.SysFont(None, int(60 * scale))
        
        # Draw result with shadow and glow
        draw_text(result_text, result_font, result_color, surface, self.width // 2, panel_y + 80, True, True)
        
        # Use a smaller font if the sub-text is too long
        if len(sub_text) > 30:
            sub_font = pygame.font.SysFont(None, 24)  # Smaller font for longer text
        else:
            sub_font = small_font
            
        draw_text(sub_text, sub_font, TEXT_COLOR, surface, self.width // 2, panel_y + 150, True)
        
        # Draw continue prompt with animation
        prompt_scale = 1.0 + 0.05 * abs(math.sin(time.time() * 3))
        prompt_font = pygame.font.SysFont(None, int(32 * prompt_scale))
        draw_text("Press SPACE to continue", prompt_font, ACCENT_COLOR, surface, 
                 self.width // 2, panel_y + 220, True)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)

# Game Over Screen
class GameOverScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        button_width = 200
        button_height = 60
        button_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            Button("Play Again", button_x, 350, button_width, button_height, GREEN, CYAN, self.reset_game),
            Button("Main Menu", button_x, 430, button_width, button_height, BLUE, PURPLE, 
                  lambda: self.change_state(STATE_MAIN_MENU))
        ]
        
        self.animation_time = 0
        self.particles = []
        self.confetti_timer = 0
    
    def reset_game(self):
        global current_state
        self.game_settings.defender_hp = 3
        self.game_settings.current_attempt = 0
        self.game_settings.secret_number = None
        self.game_settings.current_guess = None
        self.game_settings.last_guess = None
        self.game_settings.attacker_won = False
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = STATE_MODE_SELECT
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        
        for button in self.buttons:
            button.update(mouse_pos, mouse_click)
    
    def update(self):
        super().update()
        self.animation_time += 0.05
        
        # Add confetti particles
        self.confetti_timer += 1
        if self.confetti_timer >= 5:  # Add new particles every 5 frames
            self.confetti_timer = 0
            
            # Choose colors based on winner
            colors = [GREEN, CYAN, BLUE] if not self.game_settings.attacker_won else [RED, YELLOW, ACCENT_COLOR]
            
            for _ in range(2):
                self.particles.append({
                    'x': random.randint(0, self.width),
                    'y': -10,
                    'size': random.randint(5, 15),
                    'speed_x': random.uniform(-1, 1),
                    'speed_y': random.uniform(2, 5),
                    'rotation': random.uniform(0, 360),
                    'rot_speed': random.uniform(-5, 5),
                    'color': random.choice(colors),
                    'alpha': 255,
                    'fade_speed': random.uniform(0.5, 1.5)
                })
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['rotation'] += p['rot_speed']
            
            if p['y'] > self.height:
                p['alpha'] -= p['fade_speed'] * 5
            
            if p['alpha'] <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw confetti particles
        for p in self.particles:
            particle_surface = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
            particle_surface.fill((*p['color'][:3], int(p['alpha'])))
            
            # Rotate the particle
            rotated_particle = pygame.transform.rotate(particle_surface, p['rotation'])
            rot_rect = rotated_particle.get_rect(center=(p['size']//2, p['size']//2))
            
            surface.blit(rotated_particle, (int(p['x'] - rot_rect.width//2), int(p['y'] - rot_rect.height//2)))
        
        # Draw panel for content
        panel_width = min(500, self.width - 40)
        panel_height = min(350, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw animated title with glow
        title_scale = 1.0 + 0.1 * abs(math.sin(self.animation_time * 3))
        title_font = pygame.font.SysFont(None, int(72 * title_scale))
        
        # Draw glow
        glow_size = int(15 * (0.8 + 0.2 * math.sin(self.animation_time * 2)))
        glow_surface = pygame.Surface((300 + glow_size*2, 80 + glow_size*2), pygame.SRCALPHA)
        glow_color = (*ACCENT_COLOR[:3], 100)
        pygame.draw.rect(glow_surface, glow_color, 
                        (0, 0, 300 + glow_size*2, 80 + glow_size*2), 
                        border_radius=20)
        surface.blit(glow_surface, (self.width//2 - 150 - glow_size, panel_y + 30 - glow_size))
        
        # Draw title text with shadow
        draw_text("Game Over", title_font, ACCENT_COLOR, surface, self.width // 2, panel_y + 70, True, True)
        
        # Draw result with animation
        if not self.game_settings.attacker_won:
            result_text = "Defender wins!"
            sub_text = "The Attacker ran out of attempts."
            emoji = "🛡️"  # Shield emoji for defender
            result_color = BLUE
        else:
            result_text = "Attacker wins!"
            sub_text = "The Defender ran out of HP."
            emoji = "⚔️"  # Sword emoji for attacker
            result_color = RED
        
        draw_text(result_text, font, result_color, surface, self.width // 2, panel_y + 150, True, True)
        draw_text(sub_text, small_font, TEXT_COLOR, surface, self.width // 2, panel_y + 190, True)
        
        # Draw animated emoji
        emoji_scale = 1.0 + 0.2 * abs(math.sin(self.animation_time * 2))
        emoji_font = pygame.font.SysFont(None, int(100 * emoji_scale))
        draw_text(emoji, emoji_font, TEXT_COLOR, surface, self.width // 2, panel_y + 250, True)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface, small_font)
            
        # Draw transition overlay
        self.draw_transition_overlay(surface)

# History Screen
class HistoryScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.history_lines = []
        self.load_history()
        
        self.back_button = Button("Back to Menu", self.width // 2 - 100, 500, 200, 50, BLUE, PURPLE, 
                                 lambda: self.change_state(STATE_MAIN_MENU))
        
        # Scroll animation
        self.scroll_offset = 0
        self.target_scroll = 0
        self.max_scroll = 0
    
    def load_history(self):
        try:
            with open("scores.txt", "r") as f:
                self.history_lines = f.readlines()
                # Limit to last 10 entries
                self.history_lines = self.history_lines[-10:]
                self.max_scroll = max(0, len(self.history_lines) * 30 - 300)
        except:
            self.history_lines = ["No game history found"]
            self.max_scroll = 0
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
    
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.change_state(STATE_MAIN_MENU)
            elif event.key == K_UP:
                self.target_scroll = max(0, self.target_scroll - 30)
            elif event.key == K_DOWN:
                self.target_scroll = min(self.max_scroll, self.target_scroll + 30)
        
        if event.type == MOUSEWHEEL:
            self.target_scroll = max(0, min(self.max_scroll, self.target_scroll - event.y * 20))
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        self.back_button.update(mouse_pos, mouse_click)
    
    def update(self):
        super().update()
        # Smooth scrolling
        self.scroll_offset += (self.target_scroll - self.scroll_offset) * 0.2
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(600, self.width - 40)
        panel_height = min(400, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw title with shadow
        draw_text("Game History", font, ACCENT_COLOR, surface, self.width // 2, panel_y + 30, True, True)
        
        # Create a clipping rect for scrolling content
        history_area = pygame.Rect(panel_x + 50, panel_y + 70, panel_width - 100, panel_height - 100)
        history_surface = pygame.Surface((history_area.width, history_area.height), pygame.SRCALPHA)
        history_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw history entries on the history surface
        if not self.history_lines:
            draw_text("No game history found", small_font, TEXT_COLOR, history_surface, 
                     history_area.width // 2, 50, True)
        else:
            for i, line in enumerate(self.history_lines):
                y_pos = i * 40 - int(self.scroll_offset)
                if -40 < y_pos < history_area.height:
                    # Determine color based on result
                    if "Attacker wins" in line:
                        color = RED
                    elif "Defender wins" in line:
                        color = BLUE
                    else:
                        color = TEXT_COLOR
                    
                    # Draw entry with alternating background
                    if i % 2 == 0:
                        pygame.draw.rect(history_surface, (60, 60, 70, 100), 
                                       (0, y_pos, history_area.width, 40), border_radius=5)
                    
                    draw_text(line.strip(), small_font, color, history_surface, 
                             history_area.width // 2, y_pos + 20, True)
        
        # Blit the history surface to the main surface
        surface.blit(history_surface, history_area)
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            if self.target_scroll > 0:
                # Draw up arrow
                pygame.draw.polygon(surface, TEXT_COLOR, [
                    (self.width // 2, panel_y + 60),
                    (self.width // 2 - 10, panel_y + 70),
                    (self.width // 2 + 10, panel_y + 70)
                ])
            
            if self.target_scroll < self.max_scroll:
                # Draw down arrow
                pygame.draw.polygon(surface, TEXT_COLOR, [
                    (self.width // 2, panel_y + panel_height - 60),
                    (self.width // 2 - 10, panel_y + panel_height - 70),
                    (self.width // 2 + 10, panel_y + panel_height - 70)
                ])
        
        # Draw back button
        self.back_button.draw(surface, small_font)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
# Initialize the screen
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)

# Game settings
game_settings = GameSettings()
current_state = STATE_MAIN_MENU

# Helper function for drawing text
def draw_text(text, font, color, surface, x, y, center=False, shadow=False, shadow_color=(0,0,0), shadow_offset=2):
    # First measure the text to ensure it fits in boxes
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    
    if shadow:
        shadow_obj = font.render(text, True, shadow_color)
        shadow_rect = shadow_obj.get_rect()
        if center:
            shadow_rect.center = (x + shadow_offset, y + shadow_offset)
        else:
            shadow_rect.topleft = (x + shadow_offset, y + shadow_offset)
        shadow_obj.set_alpha(150)
        surface.blit(shadow_obj, shadow_rect)
    
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)
    
    # Return the text dimensions for box sizing
    return text_rect.width, text_rect.height

# Create screen objects
screens = {
    STATE_MAIN_MENU: MainMenuScreen(game_settings),
    STATE_INSTRUCTIONS: InstructionsScreen(game_settings),
    STATE_MODE_SELECT: ModeSelectScreen(game_settings),
    STATE_ATTACKER_CHOOSE: DefenderScreen(game_settings),  # Renamed: Attacker chooses the number
    STATE_DEFENDER_GUESS: AttackerScreen(game_settings),   # Renamed: Defender guesses the number
    STATE_RESULT: ResultScreen(game_settings),
    STATE_GAME_OVER: GameOverScreen(game_settings),
    STATE_HISTORY: HistoryScreen(game_settings)
}

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == VIDEORESIZE:
            # Handle window resize
            width, height = event.size
            width = max(MIN_WIDTH, width)
            height = max(MIN_HEIGHT, height)
            screen = pygame.display.set_mode((width, height), flags)
        
        # Pass events to current screen
        screens[current_state].handle_event(event)
    
    # Update current screen
    screens[current_state].update()
    
    # Draw current screen
    screens[current_state].draw(screen)
    
    pygame.display.update()
    clock.tick(60)

# Clean up before exit
if has_background_music:
    pygame.mixer.music.stop()
pygame.quit()
sys.exit()
# Level Complete Screen
class LevelCompleteScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.animation_time = 0
        self.particles = []
        self.generate_particles()
    
    def generate_particles(self):
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(3, 8),
                'speed_x': random.uniform(-2, 2),
                'speed_y': random.uniform(-2, 2),
                'color': random.choice([GREEN, CYAN, YELLOW]),
                'alpha': 255,
                'fade_speed': random.uniform(0.5, 1.5)
            })
    
    def handle_event(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.next_level()
    
    def next_level(self):
        global current_state
        # Move to the next level
        self.game_settings.current_level += 1
        
        # Update range based on new level
        mode_select_screen = screens.get(STATE_MODE_SELECT)
        if mode_select_screen:
            mode_select_screen.update_level_range(self.game_settings.mode, self.game_settings.current_level)
        
        # Reset for next level
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = STATE_ATTACKER_CHOOSE
    
    def update(self):
        super().update()
        self.animation_time += 0.05
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['alpha'] -= p['fade_speed']
            
            if p['alpha'] <= 0:
                self.particles.remove(p)
                # Add a new particle to replace the removed one
                self.particles.append({
                    'x': random.randint(0, self.width),
                    'y': random.randint(0, self.height),
                    'size': random.randint(3, 8),
                    'speed_x': random.uniform(-2, 2),
                    'speed_y': random.uniform(-2, 2),
                    'color': random.choice([GREEN, CYAN, YELLOW]),
                    'alpha': 255,
                    'fade_speed': random.uniform(0.5, 1.5)
                })
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw particles
        for p in self.particles:
            particle_surface = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*p['color'][:3], int(p['alpha'])), 
                             (p['size'], p['size']), p['size'])
            surface.blit(particle_surface, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        # Draw panel for content
        panel_width = min(500, self.width - 40)
        panel_height = min(300, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw animated title
        scale = 1.0 + 0.1 * abs(math.sin(self.animation_time * 3))
        title_font = pygame.font.SysFont(None, int(60 * scale))
        draw_text("Level Complete!", title_font, GREEN, surface, self.width // 2, panel_y + 80, True, True)
        
        # Draw level info
        level_text = f"Level {self.game_settings.current_level - 1} Completed"
        draw_text(level_text, font, TEXT_COLOR, surface, self.width // 2, panel_y + 150, True)
        
        # Draw next level info
        if self.game_settings.current_level <= self.game_settings.max_levels:
            next_level_text = f"Get ready for Level {self.game_settings.current_level}!"
            draw_text(next_level_text, small_font, CYAN, surface, self.width // 2, panel_y + 200, True)
        
        # Draw continue prompt
        prompt_scale = 1.0 + 0.05 * abs(math.sin(self.animation_time * 5))
        prompt_font = pygame.font.SysFont(None, int(32 * prompt_scale))
        draw_text("Press SPACE to continue", prompt_font, ACCENT_COLOR, surface, 
                 self.width // 2, panel_y + 250, True)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)

# Category Complete Screen
class CategoryCompleteScreen(Screen):
    def __init__(self, game_settings):
        super().__init__(game_settings)
        self.animation_time = 0
        self.particles = []
        self.confetti_timer = 0
        
        button_width = 200
        button_height = 60
        button_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            Button("Main Menu", button_x, 400, button_width, button_height, BLUE, CYAN, 
                  lambda: self.change_state(STATE_MAIN_MENU)),
            Button("Try Another Category", button_x, 480, button_width, button_height, GREEN, YELLOW, 
                  lambda: self.change_state(STATE_MODE_SELECT))
        ]
    
    def change_state(self, new_state):
        global current_state
        self.game_settings.transition_alpha = 0
        self.game_settings.fade_direction = -1
        current_state = new_state
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        
        for button in self.buttons:
            # Update button positions for responsive UI
            if button.text == "Main Menu":
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 + 100)
            else:
                button.set_position(self.width // 2 - button.width // 2, self.height // 2 + 180)
                
            button.update(mouse_pos, mouse_click)
    
    def update(self):
        super().update()
        self.animation_time += 0.05
        
        # Add confetti particles
        self.confetti_timer += 1
        if self.confetti_timer >= 5:  # Add new particles every 5 frames
            self.confetti_timer = 0
            
            # Choose colors
            colors = [GREEN, CYAN, BLUE, YELLOW, PURPLE, ACCENT_COLOR]
            
            for _ in range(2):
                self.particles.append({
                    'x': random.randint(0, self.width),
                    'y': -10,
                    'size': random.randint(5, 15),
                    'speed_x': random.uniform(-1, 1),
                    'speed_y': random.uniform(2, 5),
                    'rotation': random.uniform(0, 360),
                    'rot_speed': random.uniform(-5, 5),
                    'color': random.choice(colors),
                    'alpha': 255,
                    'fade_speed': random.uniform(0.5, 1.5)
                })
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['rotation'] += p['rot_speed']
            
            if p['y'] > self.height:
                p['alpha'] -= p['fade_speed'] * 5
            
            if p['alpha'] <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw confetti particles
        for p in self.particles:
            particle_surface = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
            particle_surface.fill((*p['color'][:3], int(p['alpha'])))
            
            # Rotate the particle
            rotated_particle = pygame.transform.rotate(particle_surface, p['rotation'])
            rot_rect = rotated_particle.get_rect(center=(p['size']//2, p['size']//2))
            
            surface.blit(rotated_particle, (int(p['x'] - rot_rect.width//2), int(p['y'] - rot_rect.height//2)))
        
        # Draw panel for content
        panel_width = min(600, self.width - 40)
        panel_height = min(400, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw animated title with glow
        title_scale = 1.0 + 0.1 * abs(math.sin(self.animation_time * 3))
        title_font = pygame.font.SysFont(None, int(72 * title_scale))
        
        # Draw glow
        glow_size = int(15 * (0.8 + 0.2 * math.sin(self.animation_time * 2)))
        glow_surface = pygame.Surface((400 + glow_size*2, 80 + glow_size*2), pygame.SRCALPHA)
        glow_color = (*ACCENT_COLOR[:3], 100)
        pygame.draw.rect(glow_surface, glow_color, 
                        (0, 0, 400 + glow_size*2, 80 + glow_size*2), 
                        border_radius=20)
        surface.blit(glow_surface, (self.width//2 - 200 - glow_size, panel_y + 50 - glow_size))
        
        # Draw title text with shadow
        draw_text("Category Champion!", title_font, ACCENT_COLOR, surface, self.width // 2, panel_y + 80, True, True)
        
        # Draw category name
        category_text = f"{self.game_settings.mode.capitalize()} Mode Completed!"
        draw_text(category_text, font, GREEN, surface, self.width // 2, panel_y + 160, True)
        
        # Draw congratulations message
        congrats_text = "You've mastered all 5 levels!"
        draw_text(congrats_text, small_font, TEXT_COLOR, surface, self.width // 2, panel_y + 220, True)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface, small_font)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
    def draw(self, surface):
        super().draw(surface)
        
        # Draw panel for content
        panel_width = min(500, self.width - 40)
        panel_height = min(300, self.height - 40)
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        self.draw_panel(surface, panel_x, panel_y, panel_width, panel_height)
        
        # Draw particles
        for p in self.particles:
            particle_surface = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*p['color'][:3], int(p['alpha'])), 
                             (p['size'], p['size']), p['size'])
            surface.blit(particle_surface, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        if self.game_settings.current_guess == self.game_settings.secret_number:
            result_text = "Correct guess!"
            sub_text = "Attacker survives this round."
            result_color = GREEN
        else:
            result_text = "Wrong!"
            sub_text = f"The number was {self.game_settings.secret_number}. Defender loses 1 HP!"
            result_color = RED
        
        # Animate the result text
        scale = 1.0 + 0.1 * abs(math.sin(time.time() * 5))
        result_font = pygame.font.SysFont(None, int(60 * scale))
        
        # Draw result with shadow and glow
        draw_text(result_text, result_font, result_color, surface, self.width // 2, panel_y + 80, True, True)
        
        # Use a smaller font if the sub-text is too long
        if len(sub_text) > 30:
            sub_font = pygame.font.SysFont(None, 24)  # Smaller font for longer text
        else:
            sub_font = small_font
            
        draw_text(sub_text, sub_font, TEXT_COLOR, surface, self.width // 2, panel_y + 150, True)
        
        # Draw continue prompt with animation
        prompt_scale = 1.0 + 0.05 * abs(math.sin(time.time() * 3))
        prompt_font = pygame.font.SysFont(None, int(32 * prompt_scale))
        draw_text("Press SPACE to continue", prompt_font, ACCENT_COLOR, surface, 
                 self.width // 2, panel_y + 220, True)
        
        # Draw transition overlay
        self.draw_transition_overlay(surface)
    def generate_hint(self):
        """Generate a hint based on the secret number"""
        secret_str = str(self.game_settings.secret_number)
        hint_type = random.randint(1, 3)
        
        if hint_type == 1:
            # Hint about first digit
            return f"The number starts with {secret_str[0]}"
        elif hint_type == 2:
            # Hint about number being greater/less than midpoint
            midpoint = (self.game_settings.range_min + self.game_settings.range_max) // 2
            if self.game_settings.secret_number > midpoint:
                return f"The number is greater than {midpoint}"
            else:
                return f"The number is less than {midpoint}"
        else:
            # Hint about last digit
            return f"The number ends with {secret_str[-1]}"
