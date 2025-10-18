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
MAX_ENTITY_DISTANCE = 15  # Максимальная дистанция отрисовки ентитей

# Создание экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Foxen3D - v0.4")
clock = pygame.time.Clock()

# Состояния игры
MAIN_MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3

game_state = MAIN_MENU

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

# Генерация процедурной музыки для меню
def generate_menu_music():
    melody = []
    notes = [262, 294, 330, 349, 392, 440, 494, 523]  # C major scale

    for i in range(16):
        note = random.choice(notes)
        duration = random.uniform(0.3, 0.6)
        sound = generate_sound(note, duration, wave_type='sine')
        melody.append((sound, duration))

    return melody

# Генерация процедурной музыки для игры
def generate_game_music():
    chords = [
        [220, 277, 329],  # A minor
        [196, 247, 294],  # G
        [247, 294, 370],  # B
        [165, 208, 247]   # E
    ]

    melody = []
    for i in range(4):
        chord = random.choice(chords)
        for note in chord:
            duration = random.uniform(0.2, 0.4)
            freq = note * random.uniform(0.98, 1.02)
            sound = generate_sound(freq, duration, wave_type='sine')
            melody.append((sound, duration))

    return melody

# Создаем звуки
sounds = {
    'shot': generate_sound(100, 0.2, wave_type='square'),
    'step': generate_sound(50, 0.1, wave_type='noise'),
    'hit': generate_sound(300, 0.15, wave_type='sine'),
    'pickup': generate_sound(400, 0.3, wave_type='sine'),
    'level_up': generate_sound(600, 0.5, wave_type='sine'),
    'enemy_hit': generate_sound(150, 0.2, wave_type='square'),
    'bullet_shot': generate_sound(80, 0.15, wave_type='square')
}

# Генерируем музыку
menu_music = generate_menu_music()
game_music = generate_game_music()
current_music_pattern = menu_music
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

    elif entity_type == "pluyabob":  # Новый тип врага
        # Создаем плюябоба с другой текстуркой
        center_x, center_y = size // 2, size // 2

        # Синее тело
        for y in range(size):
            for x in range(size):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < 20:
                    # Синий градиент
                    blue = int(200 - dist * 2)
                    green = int(max(50, 100 - dist * 2))
                    red = int(max(50, 100 - dist * 3))
                    texture.set_at((x, y), (red, green, blue))

                # Голова
                head_dist = math.sqrt((x - center_x)**2 + (y - center_y + 8)**2)
                if head_dist < 12:
                    texture.set_at((x, y), (100, 100, 150))

        # Добавляем детали (глаза побольше)
        pygame.draw.circle(texture, (255, 255, 255), (center_x - 6, center_y - 8), 4)
        pygame.draw.circle(texture, (255, 255, 255), (center_x + 6, center_y - 8), 4)
        pygame.draw.circle(texture, (0, 0, 0), (center_x - 6, center_y - 8), 2)
        pygame.draw.circle(texture, (0, 0, 0), (center_x + 6, center_y - 8), 2)

        # Рот
        pygame.draw.arc(texture, (0, 0, 0), (center_x - 8, center_y, 16, 10), 0, math.pi, 2)

    elif entity_type == "bullet":
        # Текстура для пули
        center_x, center_y = size // 2, size // 2

        # Оранжевая пуля
        for y in range(size):
            for x in range(size):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < 8:
                    # Оранжевый градиент
                    red = int(255 - dist * 5)
                    green = int(150 - dist * 5)
                    blue = int(50 - dist * 3)
                    texture.set_at((x, y), (red, green, blue))

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
def generate_procedural_map(width, height, seed, level):
    random.seed(seed + level * 1000)  # Разные сиды для разных уровней
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
                room_size = random.randint(1, min(3, 2 + level // 2))  # Комнаты увеличиваются с уровнем
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

# Глобальные переменные для уровня и состояния игры
current_level = 1
MAP_SIZE = 15
MAP = None
player_pos = np.array([1.5, 1.5], dtype=float)
player_angle = 0.0
player_health = 100
player_score = 0
player_ammo = 30
enemies_killed = 0
total_enemies = 0
sky_type = "SKY"  # По умолчанию небо

# Z-буфер для правильного рендеринга
z_buffer = np.full(SCREEN_WIDTH, float('inf'))

# Entity система с улучшенной логикой
class Entity:
    def __init__(self, x, y, entity_type, texture, damage=0, health=1):
        self.pos = np.array([x, y], dtype=float)
        self.type = entity_type
        self.texture = texture
        self.active = True
        self.animation_frame = 0
        self.damage = damage
        self.health = health
        self.last_attack_time = 0
        self.attack_cooldown = 1000  # 1 секунда для обычных врагов
        self.last_shot_time = 0
        self.shot_cooldown = 2000  # 2 секунды для плюябобов

    def update(self, player_pos, current_time, bullets, entities):
        if self.type == "enemy" and self.active:
            # Простая ИИ: следует за игроком
            direction = player_pos - self.pos
            distance = np.linalg.norm(direction)

            if distance > 0.5 and distance < 5.0:
                direction_normalized = direction / distance
                self.pos += direction_normalized * 0.02

            # Атака игрока при близком расстоянии
            if distance < 1.5 and current_time - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = current_time
                return True  # Возвращаем True если атаковал

            # Анимация
            self.animation_frame = (self.animation_frame + 1) % 60

        elif self.type == "pluyabob" and self.active:
            # Плюябоб стреляет пулями
            direction = player_pos - self.pos
            distance = np.linalg.norm(direction)

            if distance < 8.0 and current_time - self.last_shot_time > self.shot_cooldown:
                self.last_shot_time = current_time
                # Создаем пулю
                if distance > 0:
                    bullet_dir = direction / distance
                    bullet_texture = generate_entity_texture(entity_type="bullet")
                    bullet = Entity(self.pos[0], self.pos[1], "bullet", bullet_texture, damage=10)
                    bullet.velocity = bullet_dir * 0.1
                    bullets.append(bullet)
                    sounds['bullet_shot'].play()

            # Анимация
            self.animation_frame = (self.animation_frame + 1) % 60

        elif self.type == "bullet" and self.active:
            # Движение пули
            self.pos += self.velocity

            # Проверка столкновения со стенами
            map_x, map_y = int(self.pos[0]), int(self.pos[1])
            if 0 <= map_x < MAP.shape[0] and 0 <= map_y < MAP.shape[1]:
                if MAP[map_x, map_y] > 0:
                    self.active = False
                    return False

            # Проверка столкновения с игроком (для вражеских пуль)
            if self.damage > 0:  # Это вражеская пуля
                dist_to_player = np.linalg.norm(self.pos - player_pos)
                if dist_to_player < 0.5:
                    self.active = False
                    return "player_hit"

            # Проверка столкновения с врагами (для пуль игрока)
            else:
                for entity in entities:
                    if entity.type in ["enemy", "pluyabob"] and entity.active:
                        dist_to_entity = np.linalg.norm(self.pos - entity.pos)
                        if dist_to_entity < 0.5:
                            entity.health -= 10  # Урон от пули игрока
                            self.active = False
                            if entity.health <= 0:
                                entity.active = False
                                return entity
                            else:
                                sounds['enemy_hit'].play()
                            break

        return False

    def distance_to_player(self, player_pos):
        return np.linalg.norm(self.pos - player_pos)

# Процедурная генерация ентитей
def generate_entities(map_data, count=10, level=1):
    entities = []
    enemy_count = 0

    # Увеличиваем количество врагов с уровнем
    enemy_target = min(count // 2 + level, count - 2)

    for _ in range(count):
        while True:
            x, y = random.randint(1, map_data.shape[0]-2), random.randint(1, map_data.shape[1]-2)
            if map_data[x, y] == 0:
                if enemy_count < enemy_target:
                    # Случайно выбираем между обычным врагом и плюябобом
                    if random.random() < 0.7 or level < 3:  # Первые уровни - больше обычных врагов
                        entity_type = "enemy"
                        health = 30 + level * 5
                        damage = 10
                    else:
                        entity_type = "pluyabob"
                        health = 20 + level * 3
                        damage = 0  # Плюябобы не наносят урон при близкой атаке

                    enemy_count += 1
                else:
                    entity_type = random.choice(["item", "decor", "item"])
                    health = 1
                    damage = 0

                texture = generate_entity_texture(entity_type=entity_type)
                entities.append(Entity(x + 0.5, y + 0.5, entity_type, texture, damage, health))
                break

    return entities, enemy_count

# Инициализация ентитей
entities = []
bullets = []  # Список пуль

# Создаем текстуры - убедимся, что у нас достаточно текстур для всех возможных ID
wall_textures = [
    generate_wall_texture(style='brick'),
    generate_wall_texture(style='brick'),
    generate_wall_texture(style='metal'),
    generate_wall_texture(style='brick')  # Добавим дополнительную текстуру на всякий случай
]

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
    all_entities = entities + bullets
    sorted_entities = sorted(all_entities,
                           key=lambda e: e.distance_to_player(player_pos),
                           reverse=True)

    for entity in sorted_entities:
        if not entity.active:
            continue

        if entity.type == "bullet" and entity.damage > 0:  # Вражеские пули всегда видны
            pass
        elif not is_entity_visible(entity.pos):
            continue

        entity_dir = entity.pos - player_pos
        entity_angle = math.atan2(entity_dir[1], entity_dir[0]) - player_angle
        entity_angle = (entity_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(entity_angle) < HALF_FOV + 0.2 or entity.type == "bullet":
            dist = np.linalg.norm(entity_dir)

            # ИСПРАВЛЕНИЕ: Проверяем дистанцию и избегаем бесконечных значений
            if not math.isfinite(dist) or dist > MAX_ENTITY_DISTANCE or dist < 0.1:
                continue

            if entity.type != "bullet":  # Для пуль не применяем коррекцию искажения
                dist *= math.cos(entity_angle)

            # Исправление: проверяем границы индекса
            screen_x = int((SCREEN_WIDTH / 2) * (1 + entity_angle / HALF_FOV))
            if screen_x < 0 or screen_x >= SCREEN_WIDTH:
                continue

            # Улучшенная проверка Z-буфера с учетом размера ентити
            sprite_height = min(int(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2)
            sprite_width = sprite_height

            # Для пуль делаем меньше размер
            if entity.type == "bullet":
                sprite_height = max(10, sprite_height // 3)
                sprite_width = sprite_height

            # Проверяем Z-буфер для всей ширины спрайта
            z_check_pass = True
            start_x = max(0, screen_x - sprite_width // 2)
            end_x = min(SCREEN_WIDTH, screen_x + sprite_width // 2)

            for x in range(start_x, end_x):
                if dist > z_buffer[x] + 0.1:  # Небольшой зазор для предотвращения мерцания
                    z_check_pass = False
                    break

            if z_check_pass and dist > 0.1:
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
    # Разные типы неба в зависимости от уровня
    if sky_type == "SKY":
        ceiling_color = (120, 120, 200)  # Голубое небо
        # Облака
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, HALF_HEIGHT // 3)
            size = random.randint(10, 30)
            pygame.draw.circle(screen, (200, 200, 220), (x, y), size)
            pygame.draw.circle(screen, (200, 200, 220), (x + 15, y - 5), size - 5)
            pygame.draw.circle(screen, (200, 200, 220), (x - 15, y + 5), size - 5)
    else:  # COSMOS
        ceiling_color = (10, 10, 40)  # Темно-синее небо
        # Звезды
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, HALF_HEIGHT // 2)
            size = random.randint(1, 3)
            brightness = random.randint(150, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)

    # Пол
    floor_color = (80, 80, 80)

    # Шахматный паттерн для пола
    for y in range(HALF_HEIGHT, SCREEN_HEIGHT, 20):
        for x in range(0, SCREEN_WIDTH, 20):
            if (x // 20 + y // 20) % 2 == 0:
                pygame.draw.rect(screen, (70, 70, 70), (x, y, 20, 20))
            else:
                pygame.draw.rect(screen, (90, 90, 90), (x, y, 20, 20))

    # Рисуем потолок
    pygame.draw.rect(screen, ceiling_color, (0, 0, SCREEN_WIDTH, HALF_HEIGHT))

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
    level_text = font.render(f"Level: {current_level}", True, (255, 255, 255))
    enemies_text = font.render(f"Enemies: {total_enemies - enemies_killed}/{total_enemies}", True, (255, 255, 255))
    sky_text = font.render(f"Sky: {sky_type}", True, (255, 255, 255))

    screen.blit(score_text, (SCREEN_WIDTH - 150, 10))
    screen.blit(ammo_text, (SCREEN_WIDTH - 150, 40))
    screen.blit(level_text, (SCREEN_WIDTH - 150, 70))
    screen.blit(enemies_text, (SCREEN_WIDTH - 150, 100))
    screen.blit(sky_text, (SCREEN_WIDTH - 150, 130))

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

    # ИСПРАВЛЕНИЕ: Направление игрока (правильный расчет)
    # Учитываем, что на миникарте Y увеличивается вниз, а в игровом мире - вверх
    direction_length = 10
    end_x = player_map_x + math.cos(player_angle) * direction_length
    end_y = player_map_y - math.sin(player_angle) * direction_length  # Инвертируем Y

    pygame.draw.line(map_surface, (255, 0, 0), (player_map_x, player_map_y), (end_x, end_y), 2)

    # Рисуем ентити на миникарте
    for entity in entities + bullets:
        if entity.active:
            entity_map_x = int(entity.pos[1] * cell_size)
            entity_map_y = int(entity.pos[0] * cell_size)

            if entity.type == "enemy":
                color = (255, 0, 0)  # Красный для врагов
            elif entity.type == "pluyabob":
                color = (0, 0, 255)  # Синий для плюябобов
            elif entity.type == "bullet":
                if entity.damage > 0:
                    color = (255, 100, 0)  # Оранжевый для вражеских пуль
                else:
                    color = (255, 255, 0)  # Желтый для пуль игрока
            elif entity.type == "item":
                color = (0, 255, 0)  # Зеленый для предметов
            else:
                color = (200, 200, 0)  # Желтый для декора

            size = 2
            if entity.type == "bullet":
                size = 1
            pygame.draw.circle(map_surface, color, (entity_map_x, entity_map_y), size)

    screen.blit(map_surface, (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 160))

def render_level_complete():
    # Отрисовка сообщения о завершении уровня
    font_large = pygame.font.SysFont(None, 72)
    font_small = pygame.font.SysFont(None, 36)

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    level_text = font_large.render(f"LEVEL {current_level} COMPLETE!", True, (255, 215, 0))
    continue_text = font_small.render("Press SPACE to continue", True, (255, 255, 255))

    screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
    screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 + 50))

def render_main_menu():
    screen.fill((0, 0, 0))

    # Заголовок
    font_title = pygame.font.SysFont(None, 80)
    font_button = pygame.font.SysFont(None, 50)

    title_text = font_title.render("FOXENSTEIN 3D", True, (255, 100, 100))
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))

    # Кнопки
    play_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 250, 200, 60)
    exit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 350, 200, 60)

    pygame.draw.rect(screen, (50, 50, 50), play_button)
    pygame.draw.rect(screen, (50, 50, 50), exit_button)

    play_text = font_button.render("PLAY", True, (255, 255, 255))
    exit_text = font_button.render("EXIT", True, (255, 255, 255))

    screen.blit(play_text, (SCREEN_WIDTH//2 - play_text.get_width()//2, 265))
    screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, 365))

    return play_button, exit_button

def render_pause_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font_title = pygame.font.SysFont(None, 72)
    font_button = pygame.font.SysFont(None, 50)

    title_text = font_title.render("PAUSED", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))

    # Кнопки
    resume_button = pygame.Rect(SCREEN_WIDTH//2 - 150, 200, 300, 60)
    restart_button = pygame.Rect(SCREEN_WIDTH//2 - 150, 280, 300, 60)
    main_menu_button = pygame.Rect(SCREEN_WIDTH//2 - 150, 360, 300, 60)

    pygame.draw.rect(screen, (50, 50, 50), resume_button)
    pygame.draw.rect(screen, (50, 50, 50), restart_button)
    pygame.draw.rect(screen, (50, 50, 50), main_menu_button)

    resume_text = font_button.render("RESUME", True, (255, 255, 255))
    restart_text = font_button.render("RESTART LEVEL", True, (255, 255, 255))
    main_menu_text = font_button.render("MAIN MENU", True, (255, 255, 255))

    screen.blit(resume_text, (SCREEN_WIDTH//2 - resume_text.get_width()//2, 215))
    screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 295))
    screen.blit(main_menu_text, (SCREEN_WIDTH//2 - main_menu_text.get_width()//2, 375))

    return resume_button, restart_button, main_menu_button

def next_level():
    global current_level, MAP, entities, player_pos, player_angle, player_ammo, enemies_killed, total_enemies, sky_type, bullets

    current_level += 1
    enemies_killed = 0
    bullets = []  # Очищаем пули

    # Определяем тип неба (каждые 5 уровней меняется)
    if current_level % 5 == 0:
        sky_type = "COSMOS" if sky_type == "SKY" else "SKY"
    elif current_level == 1:
        sky_type = "SKY"  # Первый уровень - небо

    # Генерация новой карты
    MAP = generate_procedural_map(MAP_SIZE, MAP_SIZE, random.randint(0, 1000), current_level)

    # Поиск безопасной стартовой позиции
    while True:
        start_x, start_y = random.randint(1, MAP.shape[0]-2), random.randint(1, MAP.shape[1]-2)
        if MAP[start_x, start_y] == 0:
            player_pos = np.array([start_x + 0.5, start_y + 0.5], dtype=float)
            break

    player_angle = 0.0
    player_ammo = 30
    player_health = 100  # Восстанавливаем здоровье

    # Генерация новых ентитей
    entities, total_enemies = generate_entities(MAP, 8 + current_level * 2, current_level)

    # Воспроизведение звука перехода на новый уровень
    sounds['level_up'].play()

def restart_game():
    global current_level, MAP, entities, player_pos, player_angle, player_health, player_score, player_ammo, enemies_killed, total_enemies, sky_type, bullets

    current_level = 1
    enemies_killed = 0
    player_health = 100
    player_score = 0
    player_ammo = 30
    bullets = []
    sky_type = "SKY"

    # Генерация новой карты
    MAP = generate_procedural_map(MAP_SIZE, MAP_SIZE, random.randint(0, 1000), current_level)

    # Поиск безопасной стартовой позиции
    while True:
        start_x, start_y = random.randint(1, MAP.shape[0]-2), random.randint(1, MAP.shape[1]-2)
        if MAP[start_x, start_y] == 0:
            player_pos = np.array([start_x + 0.5, start_y + 0.5], dtype=float)
            break

    player_angle = 0.0

    # Генерация новых ентитей
    entities, total_enemies = generate_entities(MAP, 8 + current_level * 2, current_level)

def restart_level():
    global MAP, entities, player_pos, player_angle, player_ammo, enemies_killed, total_enemies, bullets

    enemies_killed = 0
    bullets = []

    # Генерация новой карты для текущего уровня
    MAP = generate_procedural_map(MAP_SIZE, MAP_SIZE, random.randint(0, 1000), current_level)

    # Поиск безопасной стартовой позиции
    while True:
        start_x, start_y = random.randint(1, MAP.shape[0]-2), random.randint(1, MAP.shape[1]-2)
        if MAP[start_x, start_y] == 0:
            player_pos = np.array([start_x + 0.5, start_y + 0.5], dtype=float)
            break

    player_angle = 0.0
    player_ammo = 30

    # Генерация новых ентитей
    entities, total_enemies = generate_entities(MAP, 8 + current_level * 2, current_level)

def check_level_complete():
    # Проверяем, все ли враги убиты
    active_enemies = sum(1 for entity in entities if entity.type in ["enemy", "pluyabob"] and entity.active)
    return active_enemies == 0

def shoot_bullet():
    global player_ammo, bullets

    if player_ammo > 0:
        player_ammo -= 1
        sounds['shot'].play()

        # Создаем пулю
        bullet_dir = np.array([math.cos(player_angle), math.sin(player_angle)])
        bullet_texture = generate_entity_texture(entity_type="bullet")
        bullet = Entity(player_pos[0], player_pos[1], "bullet", bullet_texture)
        bullet.velocity = bullet_dir * 0.2
        bullets.append(bullet)

def render_game():
    screen.fill((0, 0, 0))

    render_floor_ceiling()
    render_walls()
    render_entities()
    render_hud()
    render_minimap()

    # Если уровень завершен, показываем сообщение
    if check_level_complete():
        render_level_complete()
        return True  # Уровень завершен
    return False  # Уровень не завершен

# Главный цикл с улучшенной логикой
running = True
last_step_time = 0
step_interval = 500  # мс между звуками шагов
level_complete = False
last_enemy_attack_time = 0
enemy_attack_cooldown = 1000  # 1 секунда

# Инициализация игры
restart_game()

while running:
    current_time = pygame.time.get_ticks()

    # Воспроизведение процедурной музыки (с проверкой)
    if len(current_music_pattern) > 0:
        if current_time - last_note_time > current_music_pattern[current_note][1] * 1000:
            current_music_pattern[current_note][0].play()
            current_note = (current_note + 1) % len(current_music_pattern)
            last_note_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if game_state == MAIN_MENU:
                # В главном меню ESC ничего не делает
                pass

            elif game_state == PLAYING:
                if level_complete:
                    if event.key == pygame.K_SPACE:
                        next_level()
                        level_complete = False
                else:
                    if event.key == pygame.K_SPACE:
                        shoot_bullet()
                    elif event.key == pygame.K_r:
                        # Перезарядка
                        if player_ammo < 30:
                            player_ammo = 30
                            sounds['pickup'].play()
                    elif event.key == pygame.K_ESCAPE:
                        game_state = PAUSED

            elif game_state == PAUSED:
                if event.key == pygame.K_ESCAPE:
                    game_state = PLAYING

            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    game_state = PLAYING
                    restart_game()
                elif event.key == pygame.K_ESCAPE:
                    game_state = MAIN_MENU
                    current_music_pattern = menu_music

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if game_state == MAIN_MENU:
                play_button, exit_button = render_main_menu()
                if play_button.collidepoint(mouse_pos):
                    game_state = PLAYING
                    current_music_pattern = game_music
                    current_note = 0
                    last_note_time = current_time
                    restart_game()
                elif exit_button.collidepoint(mouse_pos):
                    running = False

            elif game_state == PAUSED:
                resume_button, restart_button, main_menu_button = render_pause_menu()
                if resume_button.collidepoint(mouse_pos):
                    game_state = PLAYING
                elif restart_button.collidepoint(mouse_pos):
                    game_state = PLAYING
                    restart_level()
                elif main_menu_button.collidepoint(mouse_pos):
                    game_state = MAIN_MENU
                    current_music_pattern = menu_music
                    current_note = 0
                    last_note_time = current_time

    # Отрисовка в зависимости от состояния игры
    if game_state == MAIN_MENU:
        play_button, exit_button = render_main_menu()

    elif game_state == PLAYING:
        if not level_complete:
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
            for entity in entities + bullets:
                result = entity.update(player_pos, current_time, bullets, entities)

                if result == True and entity.type == "enemy":  # Враг атаковал
                    if current_time - last_enemy_attack_time > enemy_attack_cooldown:
                        player_health -= entity.damage
                        last_enemy_attack_time = current_time
                        sounds['hit'].play()

                elif result == "player_hit":  # Пуля попала в игрока
                    player_health -= 10
                    sounds['hit'].play()

                elif isinstance(result, Entity):  # Пуля попала во врага
                    if result.type in ["enemy", "pluyabob"]:
                        enemies_killed += 1
                        player_score += 100
                        sounds['hit'].play()

                # Подбор предметов
                if entity.active and entity.type == "item" and entity.distance_to_player(player_pos) < 1.0:
                    entity.active = False
                    player_score += 50
                    player_health = min(100, player_health + 20)
                    player_ammo = min(30, player_ammo + 10)
                    sounds['pickup'].play()

            # Удаляем неактивные пули
            bullets = [bullet for bullet in bullets if bullet.active]

            # Проверяем смерть игрока
            if player_health <= 0:
                game_state = GAME_OVER

        # Рендеринг игры
        level_complete = render_game()

    elif game_state == PAUSED:
        # Рендерим игру под меню паузы
        render_game()
        render_pause_menu()

    elif game_state == GAME_OVER:
        # Экран Game Over
        screen.fill((0, 0, 0))
        font_large = pygame.font.SysFont(None, 72)
        font_small = pygame.font.SysFont(None, 36)

        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        score_text = font_small.render(f"Final Score: {player_score}", True, (255, 255, 255))
        restart_text = font_small.render("Press R to restart or ESC for main menu", True, (255, 255, 255))

        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
