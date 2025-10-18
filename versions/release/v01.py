import pygame
import numpy as np
import math
import random
from numba import jit

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
HALF_HEIGHT = SCREEN_HEIGHT // 2
FOV = math.pi / 3
HALF_FOV = FOV / 2
MAX_DEPTH = 20
MOVE_SPEED = 0.1
ROTATION_SPEED = 0.1

# Создание экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Foxen3D - v0.1")
clock = pygame.time.Clock()

# Генерация процедурных звуков
def generate_sound(frequency, duration, sample_rate=22050, wave_type='sine'):
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)

    if wave_type == 'sine':
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    elif wave_type == 'square':
        wave = 0.3 * np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave_type == 'sawtooth':
        wave = 0.4 * (2 * (t * frequency - np.floor(0.5 + t * frequency)))
    elif wave_type == 'noise':
        wave = 0.2 * np.random.random(samples) - 0.1

    # Apply envelope
    envelope = np.ones(samples)
    attack = int(0.1 * samples)
    decay = int(0.2 * samples)
    release = int(0.3 * samples)

    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[attack:attack+decay] = np.linspace(1, 0.7, decay)
    envelope[-release:] = np.linspace(0.7, 0, release)

    wave *= envelope

    # Convert to pygame sound
    stereo = np.column_stack((wave, wave))
    stereo = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(stereo)

# Генерация процедурной музыки
def generate_music():
    chords = [
        [220, 277, 329],  # A minor
        [196, 247, 294],  # G
        [247, 294, 370],  # B
        [165, 208, 247]   # E
    ]

    melody = []
    for i in range(4):  # Уменьшил количество нот для производительности
        chord = random.choice(chords)
        for note in chord:
            duration = random.uniform(0.2, 0.4)  # Увеличил длительность
            freq = note * random.uniform(0.98, 1.02)
            sound = generate_sound(freq, duration, wave_type='sine')
            melody.append((sound, duration))

    return melody

# Создаем звуки
sounds = {
    'shot': generate_sound(100, 0.2, wave_type='square'),
    'step': generate_sound(50, 0.1, wave_type='noise'),
    'hit': generate_sound(300, 0.15, wave_type='sine'),
    'pickup': generate_sound(400, 0.3, wave_type='sine')
}

# Генерируем музыку
music_pattern = generate_music()
current_note = 0
last_note_time = 0

# Генерация текстур стен с улучшенной процедурной генерацией
def generate_wall_texture(size=64, color_variation=30, style='brick'):
    texture = pygame.Surface((size, size))

    if style == 'brick':
        base_color = (random.randint(150, 200), random.randint(100, 150), random.randint(50, 100))

        for y in range(size):
            for x in range(size):
                brick_x = x % 16
                brick_y = y % 16

                if brick_x == 0 or brick_y == 0 or brick_x == 15 or brick_y == 15:
                    color = (max(0, base_color[0] - 50), max(0, base_color[1] - 50), max(0, base_color[2] - 50))
                else:
                    variation = random.randint(-color_variation, color_variation)
                    color = (
                        max(0, min(255, base_color[0] + variation)),
                        max(0, min(255, base_color[1] + variation)),
                        max(0, min(255, base_color[2] + variation))
                    )

                if random.random() < 0.05:
                    noise = random.randint(-20, 20)
                    color = (
                        max(0, min(255, color[0] + noise)),
                        max(0, min(255, color[1] + noise)),
                        max(0, min(255, color[2] + noise))
                    )

                texture.set_at((x, y), color)

    elif style == 'metal':
        base_color = (random.randint(100, 150), random.randint(100, 150), random.randint(120, 180))

        for y in range(size):
            for x in range(size):
                # Металлическая текстура с полосами
                stripe = (x + y) % 8
                if stripe < 2:
                    color = (max(0, base_color[0] - 50), max(0, base_color[1] - 50), max(0, base_color[2] - 50))
                else:
                    color = base_color

                # Добавляем зернистость
                if random.random() < 0.3:
                    noise = random.randint(-10, 10)
                    color = (
                        max(0, min(255, color[0] + noise)),
                        max(0, min(255, color[1] + noise)),
                        max(0, min(255, color[2] + noise))
                    )

                texture.set_at((x, y), color)

    return texture

# Генерация текстур для ентитей с улучшенной графикой
def generate_entity_texture(size=64, entity_type="enemy"):
    texture = pygame.Surface((size, size), pygame.SRCALPHA)

    if entity_type == "enemy":
        # Создаем врага с более детальной графикой
        center_x, center_y = size // 2, size // 2

        # Градиентное тело
        for y in range(size):
            for x in range(size):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < 20:
                    # Красный градиент
                    red = int(200 - dist * 2)
                    green = int(max(50, 100 - dist * 2))
                    blue = int(max(50, 100 - dist * 3))
                    texture.set_at((x, y), (red, green, blue))

                # Голова
                head_dist = math.sqrt((x - center_x)**2 + (y - center_y + 8)**2)
                if head_dist < 12:
                    texture.set_at((x, y), (150, 100, 100))

        # Добавляем детали
        pygame.draw.circle(texture, (255, 255, 255), (center_x - 5, center_y - 6), 3)
        pygame.draw.circle(texture, (255, 255, 255), (center_x + 5, center_y - 6), 3)
        pygame.draw.circle(texture, (0, 0, 0), (center_x - 5, center_y - 6), 1)
        pygame.draw.circle(texture, (0, 0, 0), (center_x + 5, center_y - 6), 1)

    elif entity_type == "item":
        # Улучшенные предметы
        if random.choice([True, False]):
            # Аптечка с градиентом
            for y in range(10, 54):
                for x in range(20, 44):
                    red = 255 - abs(y - 32) * 3
                    green_blue = 50 + abs(y - 32) * 2
                    texture.set_at((x, y), (red, green_blue, green_blue))

            pygame.draw.rect(texture, (255, 255, 255), (24, 14, 16, 36))
            pygame.draw.rect(texture, (255, 100, 100), (28, 18, 8, 28))
        else:
            # Патроны с металлическим эффектом
            for y in range(10, 54):
                for x in range(15, 49):
                    gold = 200 + (x + y) % 3 * 20
                    texture.set_at((x, y), (gold, gold, 50))

            for i in range(3):
                pygame.draw.rect(texture, (150, 150, 150), (20, 15 + i * 12, 24, 8))

    return texture

# GPU-ускоренная процедурная генерация карты
def generate_procedural_map(width, height, seed):
    random.seed(seed)
    map_data = np.zeros((width, height), dtype=np.int32)

    # Внешние стены
    map_data[0, :] = 1
    map_data[-1, :] = 1
    map_data[:, 0] = 1
    map_data[:, -1] = 1

    # Процедурные комнаты и коридоры
    for i in range(2, width-2, 3):
        for j in range(2, height-2, 3):
            if random.random() > 0.4:
                room_size = random.randint(1, 3)
                for x in range(room_size):
                    for y in range(room_size):
                        if i+x < width-1 and j+y < height-1:
                            map_data[i+x, j+y] = 0

                            # Добавляем стены вокруг комнат
                            if x == 0 or x == room_size-1 or y == 0 or y == room_size-1:
                                if random.random() > 0.3:
                                    # Используем только 1, 2, 3 для текстур
                                    map_data[i+x, j+y] = random.randint(1, 3)

    # Соединяем комнаты коридорами
    for i in range(3, width-3, 3):
        for j in range(3, height-3, 3):
            if random.random() > 0.5:
                # Горизонтальный коридор
                length = random.randint(1, 4)
                for x in range(length):
                    if i+x < width-1:
                        map_data[i+x, j] = 0
            else:
                # Вертикальный коридор
                length = random.randint(1, 4)
                for y in range(length):
                    if j+y < height-1:
                        map_data[i, j+y] = 0

    return map_data

# Генерация карты
MAP_SIZE = 15
MAP = generate_procedural_map(MAP_SIZE, MAP_SIZE, random.randint(0, 1000))

# Z-буфер для правильного рендеринга
z_buffer = np.full(SCREEN_WIDTH, float('inf'))

# Entity система с улучшенной логикой
class Entity:
    def __init__(self, x, y, entity_type, texture):
        self.pos = np.array([x, y], dtype=float)
        self.type = entity_type
        self.texture = texture
        self.active = True
        self.animation_frame = 0

    def update(self, player_pos):
        if self.type == "enemy" and self.active:
            # Простая ИИ: следует за игроком
            direction = player_pos - self.pos
            distance = np.linalg.norm(direction)

            if distance > 0.5 and distance < 5.0:
                direction_normalized = direction / distance
                self.pos += direction_normalized * 0.02

            # Анимация
            self.animation_frame = (self.animation_frame + 1) % 60

    def distance_to_player(self, player_pos):
        return np.linalg.norm(self.pos - player_pos)

# Процедурная генерация ентитей
def generate_entities(map_data, count=10):
    entities = []
    for _ in range(count):
        while True:
            x, y = random.randint(1, map_data.shape[0]-2), random.randint(1, map_data.shape[1]-2)
            if map_data[x, y] == 0:
                entity_type = random.choice(["enemy", "item", "decor"])
                texture = generate_entity_texture(entity_type=entity_type)
                entities.append(Entity(x + 0.5, y + 0.5, entity_type, texture))
                break
    return entities

# Создаем ентити
entities = generate_entities(MAP, 8)

# Создаем текстуры - убедимся, что у нас достаточно текстур для всех возможных ID
wall_textures = [
    generate_wall_texture(style='brick'),
    generate_wall_texture(style='brick'),
    generate_wall_texture(style='metal'),
    generate_wall_texture(style='brick')  # Добавим дополнительную текстуру на всякий случай
]

# Параметры игрока
player_pos = np.array([1.5, 1.5], dtype=float)
player_angle = 0.0
player_health = 100
player_score = 0
player_ammo = 30

# GPU-ускоренный raycasting
@jit(nopython=True)
def cast_ray_gpu(player_pos, player_angle, map_data, max_depth):
    ray_dir_x = math.cos(player_angle)
    ray_dir_y = math.sin(player_angle)

    map_x = int(player_pos[0])
    map_y = int(player_pos[1])

    delta_dist_x = abs(1.0 / (ray_dir_x + 1e-8))
    delta_dist_y = abs(1.0 / (ray_dir_y + 1e-8))

    if ray_dir_x < 0:
        step_x = -1
        side_dist_x = (player_pos[0] - map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1.0 - player_pos[0]) * delta_dist_x

    if ray_dir_y < 0:
        step_y = -1
        side_dist_y = (player_pos[1] - map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1.0 - player_pos[1]) * delta_dist_y

    hit = False
    side = 0
    texture_id = 0

    for _ in range(max_depth):
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1

        if 0 <= map_x < map_data.shape[0] and 0 <= map_y < map_data.shape[1]:
            if map_data[map_x, map_y] > 0:
                hit = True
                # Ограничиваем texture_id диапазоном 0-2
                texture_id = min(max(0, map_data[map_x, map_y] - 1), 2)
                break

    if hit:
        if side == 0:
            perp_dist = (map_x - player_pos[0] + (1 - step_x) / 2.0) / ray_dir_x
        else:
            perp_dist = (map_y - player_pos[1] + (1 - step_y) / 2.0) / ray_dir_y

        # Вычисление координаты текстуры
        if side == 0:
            wall_x = player_pos[1] + perp_dist * ray_dir_y
        else:
            wall_x = player_pos[0] + perp_dist * ray_dir_x
        wall_x -= math.floor(wall_x)

        return perp_dist, side, texture_id, wall_x

    return float('inf'), 0, 0, 0.0

def cast_ray(angle):
    return cast_ray_gpu(player_pos, angle, MAP, MAX_DEPTH)

# GPU-ускоренная проверка видимости ентити
@jit(nopython=True)
def is_entity_visible_gpu(player_pos, entity_pos, map_data, max_depth):
    dx = entity_pos[0] - player_pos[0]
    dy = entity_pos[1] - player_pos[1]
    dist_to_entity = math.sqrt(dx*dx + dy*dy)

    if dist_to_entity <= 0:
        return True

    dx /= dist_to_entity
    dy /= dist_to_entity

    map_x, map_y = int(player_pos[0]), int(player_pos[1])
    ray_x, ray_y = player_pos[0], player_pos[1]

    delta_dist_x = abs(1.0 / (dx + 1e-8))
    delta_dist_y = abs(1.0 / (dy + 1e-8))

    step_x = 1 if dx >= 0 else -1
    step_y = 1 if dy >= 0 else -1

    if dx < 0:
        side_dist_x = (ray_x - map_x) * delta_dist_x
    else:
        side_dist_x = (map_x + 1.0 - ray_x) * delta_dist_x

    if dy < 0:
        side_dist_y = (ray_y - map_y) * delta_dist_y
    else:
        side_dist_y = (map_y + 1.0 - ray_y) * delta_dist_y

    current_dist = 0.0
    while current_dist < dist_to_entity and current_dist < max_depth:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            current_dist = (map_x - ray_x + (1 - step_x) / 2.0) / dx if dx != 0 else float('inf')
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            current_dist = (map_y - ray_y + (1 - step_y) / 2.0) / dy if dy != 0 else float('inf')

        # Проверяем достижение ентити
        if abs(ray_x + dx * current_dist - entity_pos[0]) < 0.5 and abs(ray_y + dy * current_dist - entity_pos[1]) < 0.5:
            return True

        # Проверяем столкновение со стеной
        if 0 <= map_x < map_data.shape[0] and 0 <= map_y < map_data.shape[1]:
            if map_data[map_x, map_y] > 0:
                return False

    return True

def is_entity_visible(entity_pos):
    return is_entity_visible_gpu(player_pos, entity_pos, MAP, MAX_DEPTH)

def render_entities():
    global z_buffer

    # Сортируем ентити по расстоянию (от дальних к ближним)
    sorted_entities = sorted(entities,
                           key=lambda e: e.distance_to_player(player_pos),
                           reverse=True)

    for entity in sorted_entities:
        if not entity.active:
            continue

        if not is_entity_visible(entity.pos):
            continue

        entity_dir = entity.pos - player_pos
        entity_angle = math.atan2(entity_dir[1], entity_dir[0]) - player_angle
        entity_angle = (entity_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(entity_angle) < HALF_FOV + 0.2:
            dist = np.linalg.norm(entity_dir)
            dist *= math.cos(entity_angle)

            # Исправление: проверяем границы индекса
            screen_x = int((SCREEN_WIDTH / 2) * (1 + entity_angle / HALF_FOV))
            if screen_x < 0 or screen_x >= SCREEN_WIDTH:
                continue

            if dist > 0.5 and dist < z_buffer[screen_x]:
                sprite_height = min(int(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2)
                sprite_width = sprite_height

                sprite_screen_x = screen_x - sprite_width // 2
                sprite_screen_y = (SCREEN_HEIGHT - sprite_height) // 2

                # Проверяем, чтобы спрайт не выходил за границы экрана
                if sprite_width > 0 and sprite_height > 0:
                    # Анимация ентити
                    if entity.type == "enemy" and entity.animation_frame > 30:
                        scaled_texture = pygame.transform.scale(entity.texture, (sprite_width, sprite_height))
                    else:
                        scaled_texture = pygame.transform.smoothscale(entity.texture, (sprite_width, sprite_height))

                    # Ограничиваем позицию спрайта
                    draw_x = max(0, min(SCREEN_WIDTH - sprite_width, sprite_screen_x))
                    draw_y = max(0, min(SCREEN_HEIGHT - sprite_height, sprite_screen_y))

                    screen.blit(scaled_texture, (draw_x, draw_y))

                    # Обновляем Z-буфер только для видимой части
                    start_x = max(0, sprite_screen_x)
                    end_x = min(SCREEN_WIDTH, sprite_screen_x + sprite_width)
                    for x in range(start_x, end_x):
                        if 0 <= x < SCREEN_WIDTH:
                            z_buffer[x] = min(z_buffer[x], dist)

def render_walls():
    global z_buffer
    z_buffer.fill(float('inf'))

    for x in range(SCREEN_WIDTH):
        ray_angle = player_angle + math.atan2(x - SCREEN_WIDTH / 2, SCREEN_WIDTH / (2 * math.tan(HALF_FOV)))

        dist, side, texture_id, wall_x = cast_ray(ray_angle)

        if dist < MAX_DEPTH:
            dist *= math.cos(player_angle - ray_angle)

            wall_height = min(int(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2)

            # ИСПРАВЛЕНИЕ: Проверяем границы texture_id
            if texture_id < 0 or texture_id >= len(wall_textures):
                texture_id = 0  # Используем текстуру по умолчанию

            texture = wall_textures[texture_id]
            tex_x = int(wall_x * 64)

            if wall_height > 0 and 0 <= tex_x < 64:
                wall_slice = texture.subsurface(tex_x, 0, 1, 64)
                wall_slice = pygame.transform.smoothscale(wall_slice, (1, wall_height))
                screen.blit(wall_slice, (x, (SCREEN_HEIGHT - wall_height) // 2))

                # Обновляем Z-буфер для стен
                if 0 <= x < SCREEN_WIDTH:
                    z_buffer[x] = dist

            if side == 1:
                shadow = pygame.Surface((1, wall_height))
                shadow.set_alpha(100)
                shadow.fill((0, 0, 0))
                screen.blit(shadow, (x, (SCREEN_HEIGHT - wall_height) // 2))

def render_floor_ceiling():
    # Улучшенный пол и потолок с текстурами
    floor_color = (80, 80, 80)
    ceiling_color = (120, 120, 200)

    # Шахматный паттерн для пола
    for y in range(HALF_HEIGHT, SCREEN_HEIGHT, 20):
        for x in range(0, SCREEN_WIDTH, 20):
            if (x // 20 + y // 20) % 2 == 0:
                pygame.draw.rect(screen, (70, 70, 70), (x, y, 20, 20))
            else:
                pygame.draw.rect(screen, (90, 90, 90), (x, y, 20, 20))

    # Звезды на потолке
    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, HALF_HEIGHT // 2)
        size = random.randint(1, 3)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), size)

def render_hud():
    # Улучшенный HUD
    font = pygame.font.SysFont(None, 24)

    # Здоровье
    health_color = (255, 0, 0) if player_health < 30 else (0, 255, 0)
    pygame.draw.rect(screen, (50, 50, 50), (10, 10, 204, 24))
    pygame.draw.rect(screen, health_color, (12, 12, 2 * player_health, 20))
    health_text = font.render(f"HP: {player_health}", True, (255, 255, 255))
    screen.blit(health_text, (220, 12))

    # Счет и патроны
    score_text = font.render(f"Score: {player_score}", True, (255, 255, 255))
    ammo_text = font.render(f"Ammo: {player_ammo}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH - 150, 10))
    screen.blit(ammo_text, (SCREEN_WIDTH - 150, 40))

    # Прицел
    pygame.draw.line(screen, (255, 0, 0), (SCREEN_WIDTH//2 - 10, SCREEN_HEIGHT//2),
                    (SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2), 2)
    pygame.draw.line(screen, (255, 0, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10),
                    (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10), 2)

def render_minimap():
    # Миникарта
    map_surface = pygame.Surface((150, 150))
    map_surface.set_alpha(128)
    map_surface.fill((0, 0, 0))

    cell_size = 10
    for x in range(MAP.shape[0]):
        for y in range(MAP.shape[1]):
            if MAP[x, y] > 0:
                pygame.draw.rect(map_surface, (100, 100, 100),
                               (y * cell_size, x * cell_size, cell_size, cell_size))

    # Игрок на миникарте
    player_map_x = int(player_pos[1] * cell_size)
    player_map_y = int(player_pos[0] * cell_size)
    pygame.draw.circle(map_surface, (0, 255, 0), (player_map_x, player_map_y), 3)

    # Направление игрока
    end_x = player_map_x + math.cos(player_angle) * 10
    end_y = player_map_y + math.sin(player_angle) * 10
    pygame.draw.line(map_surface, (255, 0, 0), (player_map_x, player_map_y), (end_x, end_y), 2)

    screen.blit(map_surface, (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 160))

def render():
    screen.fill((0, 0, 0))

    render_floor_ceiling()
    render_walls()
    render_entities()
    render_hud()
    render_minimap()

# Главный цикл с улучшенной логикой
running = True
last_step_time = 0
step_interval = 500  # мс между звуками шагов

while running:
    current_time = pygame.time.get_ticks()

    # Воспроизведение процедурной музыки (с проверкой)
    if len(music_pattern) > 0:
        if current_time - last_note_time > music_pattern[current_note][1] * 1000:
            music_pattern[current_note][0].play()
            current_note = (current_note + 1) % len(music_pattern)
            last_note_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and player_ammo > 0:
                # Выстрел
                sounds['shot'].play()
                player_ammo -= 1

                # Проверка попадания
                for entity in entities:
                    if entity.type == "enemy" and entity.active:
                        dist = entity.distance_to_player(player_pos)
                        if dist < 2.0:
                            entity.active = False
                            player_score += 100
                            sounds['hit'].play()

            elif event.key == pygame.K_r:
                # Перезарядка
                if player_ammo < 30:
                    player_ammo = 30
                    sounds['pickup'].play()

    # Обработка управления
    keys = pygame.key.get_pressed()

    # Вращение
    if keys[pygame.K_LEFT]:
        player_angle -= ROTATION_SPEED
    if keys[pygame.K_RIGHT]:
        player_angle += ROTATION_SPEED

    # Движение
    move_vec = np.array([math.cos(player_angle), math.sin(player_angle)]) * MOVE_SPEED
    strafe_vec = np.array([math.cos(player_angle + math.pi/2), math.sin(player_angle + math.pi/2)]) * MOVE_SPEED

    moved = False

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        new_pos = player_pos + move_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos
                moved = True

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        new_pos = player_pos - move_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos
                moved = True

    if keys[pygame.K_a]:
        new_pos = player_pos - strafe_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos
                moved = True

    if keys[pygame.K_d]:
        new_pos = player_pos + strafe_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos
                moved = True

    # Воспроизведение звуков шагов
    if moved and current_time - last_step_time > step_interval:
        sounds['step'].play()
        last_step_time = current_time

    # Обновление ентитей
    for entity in entities:
        entity.update(player_pos)

        # Подбор предметов
        if entity.active and entity.type == "item" and entity.distance_to_player(player_pos) < 1.0:
            entity.active = False
            player_score += 50
            player_health = min(100, player_health + 20)
            player_ammo = min(30, player_ammo + 10)
            sounds['pickup'].play()

    render()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
