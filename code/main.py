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
        self.game_over = False
        self.overlay_alpha = 0
        self.overlay_speed = 300
        self.overlay_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.overlay_surf.fill('black')
        self.replay_button_rect = None
        self.game_over_font = pygame.font.Font(None, 90)
        self.button_font = pygame.font.Font(None, 44)

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
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            print('shoot')
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
                self.collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if self.collision_sprites:
                    self.impact_sound.play()
                    for sprite in self.collision_sprites:
                        sprite.destroy()
                    bullet.kill()                                  

    def player_collision(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.hit_time < self.hit_cooldown:
            return
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.hit_time = current_time
            self.lives -= 1
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
        self.spawn_positions = []

        self.lives = self.max_lives
        self.hit_time = 0
        self.can_shoot = True
        self.shoot_time = 0
        self.game_over = False
        self.overlay_alpha = 0
        self.replay_button_rect = None

        self.setup()

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

    def draw_game_over(self, dt):
        self.overlay_alpha = min(255, self.overlay_alpha + self.overlay_speed * dt)
        self.overlay_surf.set_alpha(self.overlay_alpha)
        self.display_surface.blit(self.overlay_surf, (0, 0))

        text_surf = self.game_over_font.render('GAME OVER', True, 'white')
        text_rect = text_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 40))
        self.display_surface.blit(text_surf, text_rect)

        if self.overlay_alpha >= 255:
            self.replay_button_rect = pygame.FRect(0, 0, 220, 60)
            self.replay_button_rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50)
            pygame.draw.rect(self.display_surface, 'white', self.replay_button_rect, border_radius=8)

            replay_text = self.button_font.render('Play Again', True, 'black')
            replay_text_rect = replay_text.get_frect(center=self.replay_button_rect.center)
            self.display_surface.blit(replay_text, replay_text_rect)
        else:
            self.replay_button_rect = None

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if not self.game_over and event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.game_over and self.replay_button_rect and self.replay_button_rect.collidepoint(event.pos):
                        self.reset()

            if not self.game_over:
                self.gun_timer()
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()

            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.draw_heart()

            if self.game_over:
                self.draw_game_over(dt)

            pygame.display.update()

        pygame.quit()




if __name__ == '__main__':
    game = Game()
    game.run()

# then afterwards i should also start to include