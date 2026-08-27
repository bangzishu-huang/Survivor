from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from random import randint, choice
from groups import AllSprites

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 200

        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        self.max_lives = 3
        self.lives = self.max_lives
        self.hit_time = 0
        self.hit_cooldown = 1000
        self.score = 0
        self.overlay_alpha = 0
        self.overlay_speed = 300
        self.overlay_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.overlay_surf.fill('black')
        self.replay_button_rect = None
        self.button_font = pygame.font.Font(None, 44)
        self.score_font = pygame.font.Font(None, 42)
        self.game_over_font = pygame.font.Font(None, 90)
        self.game_describe = pygame.font.Font(None, 30)
        self.difficulty = None
        self.game_started = False
        self.game_over = False
        self.show_difficulty_select = False
        self.hit_sound = pygame.mixer.Sound(join('code', 'audio', 'hit.wav'))
        self.hit_sound.set_volume(0.65)
        self.hack_panel_open = False
        self.esp_enabled = False
        self.god_mode_enabled = False
        self.hack_toggle_font = pygame.font.Font(None, 30)
        self.hack_button_rect = pygame.FRect(0, 0, 180, 40)
        self.hack_button_rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 190)
        self.hack_panel_rect = pygame.FRect(WINDOW_WIDTH - 230, 20, 210, 200)
        self.master_toggle_rect = pygame.FRect(WINDOW_WIDTH - 220, 60, 24, 24)
        self.esp_toggle_rect = pygame.FRect(WINDOW_WIDTH - 220, 95, 24, 24)
        self.god_toggle_rect = pygame.FRect(WINDOW_WIDTH - 220, 130, 24, 24)
        self.extra_life_button_rect = pygame.FRect(WINDOW_WIDTH - 220, 165, 190, 30)

        self.button_scales = {
            'play': 1.0,
            'replay': 1.0,
            'easy': 1.0,
            'medium': 1.0,
            'hard': 1.0
        }

        self.high_score = {
            'easy': 0,
            'medium': 0,
            'hard': 0
        }

        self.difficulty_settings = {
            'easy': {
                'bullet_speed': 900,
                'enemy_speed': 250
            },

            'medium': {
                'bullet_speed': 1100,
                'enemy_speed': 350,
            },

            'hard': {
                'bullet_speed': 1400,
                'enemy_speed': 500
            }
        }

        self.difficulty_button_scales = {
            'easy': 1.0,
            'medium': 1.0,
            'hard': 1.0
        }

        self.difficulty_color = {
            'easy': (76, 187, 23),
            'medium': (255, 140, 0),
            'hard': (220, 20, 60)
        }

        self.difficulty_buttons = {
            'easy': pygame.FRect(0, 0, 180, 65),
            'medium': pygame.FRect(0, 0, 180, 65),
            'hard': pygame.FRect(0, 0, 180, 65)
        }

        button_x = WINDOW_WIDTH / 2

        self.difficulty_buttons['easy'].center = (button_x, WINDOW_HEIGHT / 2 - 100)
        self.difficulty_buttons['medium'].center = (button_x, WINDOW_HEIGHT / 2)
        self.difficulty_buttons['hard'].center = (button_x, WINDOW_HEIGHT / 2 + 100)

        self.play_button_rect = pygame.FRect(0, 0, 220, 70)
        self.play_button_rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 +60)

        self.shoot_sound = pygame.mixer.Sound(join('code', 'audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound = pygame.mixer.Sound(join('code', 'audio', 'impact.ogg'))
        self.music = pygame.mixer.Sound(join('code', 'audio', 'music.wav'))
        self.music.play(loops= -1)
        self.music.set_volume(0.2)
        self.load_images()
        self.setup()

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('code', 'images', 'weapon', 'bullet.png')).convert_alpha()

        folders = list(walk(join('code', 'images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('code', 'images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

        heart_scale = 0.05
        heart_raw = pygame.image.load(join('code', 'images', 'player', 'heart.png')).convert_alpha()
        size = (int(heart_raw.get_width() * heart_scale), int(heart_raw.get_height() * heart_scale))
        self.heart_surf = pygame.transform.smoothscale(heart_raw, size)
        self.heart_gray_surf = pygame.transform.grayscale(self.heart_surf)

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 40
            Bullet(self.bullet_surf, pos, self.gun.player_direction, self.difficulty_settings[self.difficulty]['bullet_speed'], (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()


    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True


    def setup(self):
        map = load_pygame(join('code', 'data', 'maps', 'world.tmx'))

        for x,y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
        for marker in map.get_layer_by_name('Entities'):
            if marker.name == 'Player':
                self.player = Player((marker.x, marker.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else: 
                self.spawn_positions.append((marker.x, marker.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                hit_enemies = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if hit_enemies:
                    self.impact_sound.play()
                    for sprite in hit_enemies:
                        if sprite.death_time == 0:
                            sprite.destroy()

                            self.score += 1
                            if self.score > self.high_score[self.difficulty]:
                                self.high_score[self.difficulty] = self.score
                    bullet.kill()                                  

    def draw_esp(self):
        if not self.esp_enabled:
            return

        offset = self.all_sprites.offset
        player_pos = pygame.Vector2(self.player.rect.center) + offset
        for enemy in self.enemy_sprites:
            if enemy.death_time != 0:
                continue
            enemy_pos = pygame.Vector2(enemy.rect.center) + offset
            pygame.draw.line(self.display_surface, (255, 0, 0), player_pos, enemy_pos, 1)
            pygame.draw.circle(self.display_surface, (255, 0, 0), enemy_pos, 22, 2)

    def player_collision(self):
        if self.god_mode_enabled:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.hit_time < self.hit_cooldown:
            return
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.hit_time = current_time
            self.lives -= 1
            self.hit_sound.play()
            if self.lives <= 0:
                self.trigger_game_over()

    def trigger_game_over(self):
        self.game_over = True
        self.overlay_alpha = 0
        self.replay_button_rect = None

    def reset(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()
        self.spawn_positions = []

        self.score = 0
        self.hit_time = 0
        self.can_shoot = True
        self.shoot_time = 0
        self.game_over = False
        self.game_started = False
        self.show_difficulty_select = True
        self.overlay_alpha = 0
        self.replay_button_rect = None

        self.setup()

    def draw_button(self, rect, text, button_id):
        mouse_pos = pygame.mouse.get_pos()
        hovering = rect.collidepoint(mouse_pos)

        current_scale = self.button_scales[button_id]

        target_scale = 1.05 if hovering else 1.0
        current_scale += (target_scale - current_scale) * 0.2
        self.button_scales[button_id] = current_scale

        scaled_rect = rect.copy()
        scaled_rect.width *= current_scale
        scaled_rect.height *= current_scale
        scaled_rect.center = rect.center

        button_color = (220, 220, 220) if hovering else (255, 255, 255)

        pygame.draw.rect(self.display_surface, button_color, scaled_rect, border_radius=10)

        text_surf = self.button_font.render(text, True, 'black')
        text_rect = text_surf.get_frect(center=scaled_rect.center)

        self.display_surface.blit(text_surf, text_rect)

    def draw_level_button(self, rect, text, level):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        base_color = self.difficulty_color[level]

        if hovered:
            color = tuple(int(c * 0.75) for c in base_color)
        else: 
            color = base_color

        pygame.draw.rect(self.display_surface, color, rect, border_radius=10)

        text_surf = self.button_font.render(text, True, 'white')
        text_rect = text_surf.get_frect(center=rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_heart(self):
        spacing = 10
        heart_w = self.heart_surf.get_width()
        total_width = self.max_lives * heart_w + (self.max_lives - 1) * spacing
        start_x = WINDOW_WIDTH / 2 - total_width / 2
        y = WINDOW_HEIGHT / 2 - 150

        for i in range(self.max_lives):
            x = start_x + i * (heart_w + spacing)
            surf = self.heart_surf if i < self.lives else self.heart_gray_surf
            self.display_surface.blit(surf, (x, y))

    def draw_score(self):
        high_score = self.high_score[self.difficulty]
        high_score_surf = self.score_font.render(f'HIGH SCORE: {high_score}', True, 'white')
        high_score_rect = high_score_surf.get_frect(center = (WINDOW_WIDTH / 2, 60))
        score_surf = self.score_font.render(f'SCORE: {self.score}', True, 'white')
        score_rect = score_surf.get_frect(center = (WINDOW_WIDTH / 2, 90))
        difficulty_surf = self.score_font.render(self.difficulty.upper(), True, self.difficulty_color[self.difficulty])
        difficulty_rect = difficulty_surf.get_frect(center=(WINDOW_WIDTH / 2, 25))
        self.display_surface.blit(difficulty_surf, difficulty_rect)
        self.display_surface.blit(high_score_surf, high_score_rect)
        self.display_surface.blit(score_surf, score_rect)

    def draw_start(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.display_surface.blit(overlay, (0, 0))
        title_surf = self.game_over_font.render('SURVIVOR', True, 'white')
        title_rect = title_surf.get_frect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 60))
        self.display_surface.blit(title_surf, title_rect)

        describe_surf = self.game_describe.render('Use keys "WASD" to move, and mouse to aim and shoot!', True, 'white')
        describe_rect = describe_surf.get_frect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 2))
        self.display_surface.blit(describe_surf, describe_rect)

        self.draw_button(self.play_button_rect, 'PLAY', 'play')

    def draw_game_over(self, dt):
        self.overlay_alpha = min(255, self.overlay_alpha + self.overlay_speed * dt)
        self.overlay_surf.set_alpha(self.overlay_alpha)
        self.display_surface.blit(self.overlay_surf, (0, 0))

        text_surf = self.game_over_font.render('GAME OVER', True, 'red')
        text_rect = text_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 85))
        self.display_surface.blit(text_surf, text_rect)

        score_surf = self.score_font.render(f'SCORE: {self.score}', True, 'white')
        score_rect = score_surf.get_frect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 15))
        self.display_surface.blit(score_surf, score_rect)

        high_score_surf = self.score_font.render(f'HIGH SCORE: {self.high_score[self.difficulty]}', True, 'white')
        high_score_rect = high_score_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 20))
        self.display_surface.blit(high_score_surf, high_score_rect)

        if self.overlay_alpha >= 255:
            self.replay_button_rect = pygame.FRect(0, 0, 220, 60)
            self.replay_button_rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 100)
            pygame.draw.rect(self.display_surface, 'white', self.replay_button_rect, border_radius=8)

            replay_text = self.button_font.render('PLAY AGAIN', True, 'black')
            replay_text_rect = replay_text.get_frect(center=self.replay_button_rect.center)
            self.display_surface.blit(replay_text, replay_text_rect)
        else:
            self.replay_button_rect = None

    def draw_hack_button(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.hack_button_rect.collidepoint(mouse_pos)
        color = (170, 170, 170) if hovered else (95, 95, 95)
        text_surf = self.hack_toggle_font.render('HACK MODE', True, 'darkgray')
        text_rect = text_surf.get_frect(center=self.hack_button_rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_toggle(self, rect, label, enabled):
        color = (0, 200, 0) if enabled else (90, 90, 90)
        pygame.draw.rect(self.display_surface, color, rect, border_radius=4)
        label_surf = self.hack_toggle_font.render(label, True, 'white')
        label_rect = label_surf.get_frect(midleft=(rect.right + 10, rect.centery))
        self.display_surface.blit(label_surf, label_rect)

    def draw_hack_panel(self):
        if not self.hack_panel_open:
            return

        pygame.draw.rect(self.display_surface, (25, 25, 25), self.hack_panel_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (90, 90, 90), self.hack_panel_rect, width=2, border_radius=8)

        title_surf = self.hack_toggle_font.render('HACK MENU', True, 'white')
        self.display_surface.blit(title_surf, (self.hack_panel_rect.x + 10, self.hack_panel_rect.y + 8))
        any_active = self.esp_enabled or self.god_mode_enabled
        self.draw_toggle(self.master_toggle_rect, 'TURN OFF ALL', not any_active)
        self.draw_toggle(self.esp_toggle_rect, 'ESP', self.esp_enabled)
        self.draw_toggle(self.god_toggle_rect, 'GOD MODE', self.god_mode_enabled)

        pygame.draw.rect(self.display_surface, (255, 255, 255), self.extra_life_button_rect, border_radius=6)
        life_text = self.hack_toggle_font.render('+1 LIFE', True, 'black')
        life_rect = life_text.get_frect(center=self.extra_life_button_rect.center)
        self.display_surface.blit(life_text, life_rect)

    def start_game(self, difficulty):
        self.difficulty = difficulty
        self.score = 0

        self.game_started = True
        self.show_difficulty_select = False
        self.game_over = False

        self.lives = self.max_lives
        self.hit_time = 0
        self.can_shoot = True
        self.shoot_time = 0 
        self.overlay_alpha = 0
        self.replay_button_rect = None

    def draw_difficulty_select(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.display_surface.blit(overlay, (0, 0))

        title_surf = self.game_over_font.render('SELECT DIFFICULTY', True, 'white')
        title_rect = title_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 180))
        self.display_surface.blit(title_surf, title_rect)

        for name, rect in self.difficulty_buttons.items():
            self.draw_level_button(rect, name.upper(), name)


        self.draw_hack_button()

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if self.game_started and not self.game_over and event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites, self.difficulty_settings[self.difficulty]['enemy_speed'])

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.hack_panel_open:
                        if self.master_toggle_rect.collidepoint(event.pos):
                            self.esp_enabled = False
                            self.god_mode_enabled = False
                        elif self.esp_toggle_rect.collidepoint(event.pos):
                            self.esp_enabled = not self.esp_enabled
                        elif self.god_toggle_rect.collidepoint(event.pos):
                            self.god_mode_enabled = not self.god_mode_enabled
                        elif self.extra_life_button_rect.collidepoint(event.pos):
                            if self.game_started and not self.game_over:
                                self.lives = min(self.lives + 1, self.max_lives)

                    if not self.game_started and not self.show_difficulty_select:
                        if self.play_button_rect.collidepoint(event.pos):
                            self.show_difficulty_select = True
                        
                    elif self.show_difficulty_select:
                        if self.difficulty_buttons['easy'].collidepoint(event.pos):
                            self.start_game('easy')
                        elif self.difficulty_buttons['medium'].collidepoint(event.pos):
                            self.start_game('medium')
                        elif self.difficulty_buttons['hard'].collidepoint(event.pos):
                            self.start_game('hard')
                        elif self.hack_button_rect.collidepoint(event.pos):
                            self.hack_panel_open = not self.hack_panel_open

                    elif self.game_over:
                        if self.game_over and self.replay_button_rect and self.replay_button_rect.collidepoint(event.pos):
                            self.reset()

            if self.game_started and not self.game_over:
                self.gun_timer()
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()

            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.draw_heart()
            self.draw_esp()

            if self.game_started:
                self.draw_score()

            if not self.game_started and not self.show_difficulty_select:
                self.draw_start()

            if self.show_difficulty_select:
                self.draw_difficulty_select()

            if self.game_over:
                self.draw_game_over(dt)

            self.draw_hack_panel()

            pygame.display.update()

        pygame.quit()




if __name__ == '__main__':
    game = Game()
    game.run()
