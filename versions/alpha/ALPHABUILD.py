import pygame
import numpy as np
import math
import random

# Инициализация Pygame
pygame.init()

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
pygame.display.set_caption("Foxen3D ALPHABUILD")
clock = pygame.time.Clock()

# Генерация текстур стен (в стиле оригинального Wolfenstein)
def generate_wall_texture(size=64, color_variation=30):
    texture = pygame.Surface((size, size))
    base_color = (random.randint(150, 200), random.randint(100, 150), random.randint(50, 100))

    for y in range(size):
        for x in range(size):
            # Создаем кирпичный паттерн
            brick_x = x % 16
            brick_y = y % 16

            # Границы кирпичей
            if brick_x == 0 or brick_y == 0 or brick_x == 15 or brick_y == 15:
                color = (max(0, base_color[0] - 50), max(0, base_color[1] - 50), max(0, base_color[2] - 50))
            else:
                # Вариация цвета внутри кирпича
                variation = random.randint(-color_variation, color_variation)
                color = (
                    max(0, min(255, base_color[0] + variation)),
                    max(0, min(255, base_color[1] + variation)),
                    max(0, min(255, base_color[2] + variation))
                )

            # Добавляем шум
            if random.random() < 0.1:
                noise = random.randint(-20, 20)
                color = (
                    max(0, min(255, color[0] + noise)),
                    max(0, min(255, color[1] + noise)),
                    max(0, min(255, color[2] + noise))
                )

            texture.set_at((x, y), color)

    return texture

# Генерация текстур для ентитей (враги, предметы)
def generate_entity_texture(size=64, entity_type="enemy"):
    texture = pygame.Surface((size, size), pygame.SRCALPHA)

    if entity_type == "enemy":
        # Простой спрайт врага
        center_x, center_y = size // 2, size // 2

        # Тело
        body_color = (200, 50, 50)
        pygame.draw.circle(texture, body_color, (center_x, center_y), 20)

        # Голова
        head_color = (150, 100, 100)
        pygame.draw.circle(texture, head_color, (center_x, center_y - 10), 12)

        # Глаза
        pygame.draw.circle(texture, (255, 255, 255), (center_x - 5, center_y - 12), 4)
        pygame.draw.circle(texture, (255, 255, 255), (center_x + 5, center_y - 12), 4)
        pygame.draw.circle(texture, (0, 0, 0), (center_x - 5, center_y - 12), 2)
        pygame.draw.circle(texture, (0, 0, 0), (center_x + 5, center_y - 12), 2)

        # Руки/ноги
        pygame.draw.rect(texture, body_color, (center_x - 25, center_y, 50, 15))

    elif entity_type == "item":
        # Предмет (аптечка или патроны)
        if random.choice([True, False]):
            # Аптечка
            pygame.draw.rect(texture, (255, 50, 50), (20, 10, 24, 44))
            pygame.draw.rect(texture, (255, 255, 255), (24, 14, 16, 36))
            pygame.draw.rect(texture, (255, 50, 50), (28, 18, 8, 28))
        else:
            # Патроны
            pygame.draw.rect(texture, (200, 200, 50), (15, 10, 34, 44))
            for i in range(3):
                pygame.draw.rect(texture, (100, 100, 100), (20, 15 + i * 12, 24, 8))

    elif entity_type == "decor":
        # Декоративный объект (столб, бочка)
        pygame.draw.rect(texture, (150, 100, 50), (20, 10, 24, 54))
        for i in range(3):
            pygame.draw.rect(texture, (100, 70, 30), (22, 15 + i * 15, 20, 5))

    return texture

# Создаем текстуры
wall_textures = [generate_wall_texture() for _ in range(3)]
entity_textures = {
    "enemy": generate_entity_texture(entity_type="enemy"),
    "item": generate_entity_texture(entity_type="item"),
    "decor": generate_entity_texture(entity_type="decor")
}

# Карта (0 - пустота, 1-3 - стены с разными текстурами)
MAP = np.array([
    [1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 2, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1]
])

# Entity система
class Entity:
    def __init__(self, x, y, entity_type, texture):
        self.pos = np.array([x, y], dtype=float)
        self.type = entity_type
        self.texture = texture
        self.active = True

    def update(self, player_pos):
        # Простая логика для врагов
        if self.type == "enemy" and self.active:
            # Враги просто стоят на месте в этой демке
            pass

    def distance_to_player(self, player_pos):
        return np.linalg.norm(self.pos - player_pos)

# Создаем ентити
entities = [
    Entity(2.5, 2.5, "enemy", entity_textures["enemy"]),
    Entity(1.5, 1.5, "item", entity_textures["item"]),
    Entity(4.5, 3.5, "item", entity_textures["item"]),
    Entity(3.5, 5.5, "decor", entity_textures["decor"]),
    Entity(5.5, 1.5, "decor", entity_textures["decor"])
]

# Параметры игрока
player_pos = np.array([1.5, 1.5], dtype=float)
player_angle = 0.0
player_health = 100
player_score = 0

def cast_ray(angle):
    angle %= 2 * math.pi

    ray_dir = np.array([math.cos(angle), math.sin(angle)])
    map_pos = np.floor(player_pos).astype(int)

    delta_dist = np.abs(1 / ray_dir)

    step = np.zeros(2, dtype=int)
    side_dist = np.zeros(2)

    for i in range(2):
        if ray_dir[i] < 0:
            step[i] = -1
            side_dist[i] = (player_pos[i] - map_pos[i]) * delta_dist[i]
        else:
            step[i] = 1
            side_dist[i] = (map_pos[i] + 1 - player_pos[i]) * delta_dist[i]

    hit = False
    side = 0
    texture_id = 0

    while not hit and np.max(np.abs(map_pos - np.floor(player_pos))) < MAX_DEPTH:
        if side_dist[0] < side_dist[1]:
            side_dist[0] += delta_dist[0]
            map_pos[0] += step[0]
            side = 0
        else:
            side_dist[1] += delta_dist[1]
            map_pos[1] += step[1]
            side = 1

        if 0 <= map_pos[0] < MAP.shape[0] and 0 <= map_pos[1] < MAP.shape[1]:
            if MAP[map_pos[0], map_pos[1]] > 0:
                hit = True
                texture_id = MAP[map_pos[0], map_pos[1]] - 1

    if hit:
        if side == 0:
            perp_dist = (map_pos[0] - player_pos[0] + (1 - step[0]) / 2) / ray_dir[0]
        else:
            perp_dist = (map_pos[1] - player_pos[1] + (1 - step[1]) / 2) / ray_dir[1]
        return perp_dist, side, texture_id, map_pos
    return None, None, None, None

# Функция для проверки видимости ентити
def is_entity_visible(entity_pos):
    # Бросаем луч к ентити
    dx = entity_pos[0] - player_pos[0]
    dy = entity_pos[1] - player_pos[1]
    dist_to_entity = math.sqrt(dx*dx + dy*dy)

    # Нормализуем направление
    if dist_to_entity > 0:
        dx /= dist_to_entity
        dy /= dist_to_entity
    else:
        return True

    # Используем DDA для проверки видимости
    map_x, map_y = int(player_pos[0]), int(player_pos[1])
    ray_x, ray_y = player_pos[0], player_pos[1]

    # Длина луча от текущей позиции до следующей границы
    delta_dist_x = abs(1 / dx) if dx != 0 else float('inf')
    delta_dist_y = abs(1 / dy) if dy != 0 else float('inf')

    # Направление шага и начальная длина луча
    step_x = 1 if dx >= 0 else -1
    step_y = 1 if dy >= 0 else -1

    if dx < 0:
        side_dist_x = (ray_x - map_x) * delta_dist_x
    else:
        side_dist_x = (map_x + 1 - ray_x) * delta_dist_x

    if dy < 0:
        side_dist_y = (ray_y - map_y) * delta_dist_y
    else:
        side_dist_y = (map_y + 1 - ray_y) * delta_dist_y

    # DDA-алгоритм
    hit = False
    while not hit and (abs(ray_x - player_pos[0]) + abs(ray_y - player_pos[1])) < dist_to_entity:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
        else:
            side_dist_y += delta_dist_y
            map_y += step_y

        # Проверяем, не достигли ли мы ентити
        if (abs(ray_x - entity_pos[0]) < 0.5 and abs(ray_y - entity_pos[1]) < 0.5):
            return True

        # Проверяем, не попали ли в стену
        if 0 <= map_x < MAP.shape[0] and 0 <= map_y < MAP.shape[1]:
            if MAP[map_x, map_y] > 0:
                return False

        # Обновляем позицию луча
        if side_dist_x < side_dist_y:
            ray_x = map_x if step_x == -1 else map_x + 1
        else:
            ray_y = map_y if step_y == -1 else map_y + 1

    return True

def render_entities():
    # Сортируем ентити по расстоянию (от дальних к ближним)
    sorted_entities = sorted(entities,
                           key=lambda e: e.distance_to_player(player_pos),
                           reverse=True)

    for entity in sorted_entities:
        if not entity.active:
            continue

        # Проверяем видимость ентити
        if not is_entity_visible(entity.pos):
            continue

        # Вектор от игрока к ентити
        entity_dir = entity.pos - player_pos

        # Угол к ентити относительно направления игрока
        entity_angle = math.atan2(entity_dir[1], entity_dir[0]) - player_angle
        entity_angle = (entity_angle + math.pi) % (2 * math.pi) - math.pi

        # Если ентити в поле зрения
        if abs(entity_angle) < HALF_FOV + 0.2:
            # Дистанция до ентити
            dist = np.linalg.norm(entity_dir)

            # Коррекция искажения
            dist *= math.cos(entity_angle)

            if dist > 0.5:  # Не рисуем слишком близкие ентити
                # Размер спрайта на экране
                sprite_height = min(int(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2)
                sprite_width = sprite_height

                # Позиция на экране
                sprite_screen_x = int((SCREEN_WIDTH / 2) * (1 + entity_angle / HALF_FOV)) - sprite_width // 2
                sprite_screen_y = (SCREEN_HEIGHT - sprite_height) // 2

                # Масштабируем текстуру с фильтрацией (улучшает качество при приближении)
                if sprite_width > 0 and sprite_height > 0:
                    sprite_surface = pygame.transform.smoothscale(entity.texture, (sprite_width, sprite_height))
                    screen.blit(sprite_surface, (sprite_screen_x, sprite_screen_y))

def render_walls():
    for x in range(SCREEN_WIDTH):
        ray_angle = player_angle + math.atan2(x - SCREEN_WIDTH / 2, SCREEN_WIDTH / (2 * math.tan(HALF_FOV)))

        dist, side, texture_id, map_pos = cast_ray(ray_angle)

        if dist is not None:
            # Коррекция искажения
            dist *= math.cos(player_angle - ray_angle)

            # Высота стены
            wall_height = min(int(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2)

            # Расчет координат текстуры
            if side == 0:
                wall_x = player_pos[1] + dist * math.sin(ray_angle)
            else:
                wall_x = player_pos[0] + dist * math.cos(ray_angle)
            wall_x %= 1

            # Выбор текстуры
            texture = wall_textures[texture_id]

            # Отрисовка текстурированного столбца с улучшенным масштабированием
            tex_x = int(wall_x * 64)
            if wall_height > 0:
                # Используем smoothscale для улучшения качества при увеличении
                wall_slice = texture.subsurface(tex_x, 0, 1, 64)
                wall_slice = pygame.transform.smoothscale(wall_slice, (1, wall_height))
                screen.blit(wall_slice, (x, (SCREEN_HEIGHT - wall_height) // 2))

            # Добавляем тень для создания глубины
            if side == 1:
                shadow = pygame.Surface((1, wall_height))
                shadow.set_alpha(100)
                shadow.fill((0, 0, 0))
                screen.blit(shadow, (x, (SCREEN_HEIGHT - wall_height) // 2))

def render_floor_ceiling():
    # Простой пол и потолок
    floor_color = (80, 80, 80)
    ceiling_color = (120, 120, 200)

    pygame.draw.rect(screen, ceiling_color, (0, 0, SCREEN_WIDTH, HALF_HEIGHT))
    pygame.draw.rect(screen, floor_color, (0, HALF_HEIGHT, SCREEN_WIDTH, HALF_HEIGHT))

def render_hud():
    # Здоровье
    health_color = (255, 0, 0) if player_health < 30 else (0, 255, 0)
    pygame.draw.rect(screen, (50, 50, 50), (10, 10, 204, 24))
    pygame.draw.rect(screen, health_color, (12, 12, 2 * player_health, 20))

    # Счет
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {player_score}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH - 150, 10))

    # Компас/направление
    pygame.draw.circle(screen, (255, 255, 255), (SCREEN_WIDTH // 2, 30), 15, 1)
    angle_x = 15 * math.cos(player_angle)
    angle_y = 15 * math.sin(player_angle)
    pygame.draw.line(screen, (255, 0, 0),
                    (SCREEN_WIDTH // 2, 30),
                    (SCREEN_WIDTH // 2 + angle_x, 30 + angle_y), 2)

def render():
    screen.fill((0, 0, 0))

    render_floor_ceiling()
    render_walls()
    render_entities()
    render_hud()

# Главный цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Выстрел/взаимодействие
                for entity in entities:
                    if entity.type == "enemy" and entity.active:
                        dist = entity.distance_to_player(player_pos)
                        if dist < 2.0:  # Если враг близко
                            entity.active = False
                            player_score += 100

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

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        new_pos = player_pos + move_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        new_pos = player_pos - move_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos

    if keys[pygame.K_a]:
        new_pos = player_pos - strafe_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos

    if keys[pygame.K_d]:
        new_pos = player_pos + strafe_vec
        if 0 <= int(new_pos[0]) < MAP.shape[0] and 0 <= int(new_pos[1]) < MAP.shape[1]:
            if MAP[int(new_pos[0]), int(new_pos[1])] == 0:
                player_pos = new_pos

    # Обновление ентитей
    for entity in entities:
        entity.update(player_pos)

    render()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
