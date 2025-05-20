import pygame
import sys
import os
import random
import math
import pygame_gui as gui
from pygame.locals import *
import pygame.mask
import numpy

# 初始化Pygame
pygame.init()
pygame.mixer.init()

# 设置窗口大小
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Trump VS BOSS')

# 初始化UI管理器
ui_manager = gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT), 'data/themes/theme.json')

# 创建像素风按钮
start_button = gui.elements.UIButton(
    relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 200), (200, 50)),
    text='START',
    manager=ui_manager
)

exit_button = gui.elements.UIButton(
    relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 130), (200, 50)),
    text='EXIT',
    manager=ui_manager
)

# 颜色定义
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

# 物理参数
GRAVITY = 1.0  # 调整重力
JUMP_SPEED = -18  # 调整跳跃速度
GROUND_HEIGHT = WINDOW_HEIGHT - 100

# 游戏参数
CAMERA_THRESHOLD_X = WINDOW_WIDTH * 0.4  # 调整相机阈值
BOSS_APPEAR_DISTANCE = WINDOW_WIDTH * 1.5  # 再次提前BOSS出现时机

# 创建简单的音效
shoot_sound = pygame.mixer.Sound(pygame.sndarray.array(numpy.random.rand(4410).astype(numpy.float32)))
hit_sound = pygame.mixer.Sound(pygame.sndarray.array(numpy.random.rand(4410).astype(numpy.float32)))
jump_sound = pygame.mixer.Sound(pygame.sndarray.array(numpy.random.rand(4410).astype(numpy.float32)))
boss_sound = pygame.mixer.Sound(pygame.sndarray.array(numpy.random.rand(8820).astype(numpy.float32)))

# 调整音量
shoot_sound.set_volume(0.1)
hit_sound.set_volume(0.2)
jump_sound.set_volume(0.15)
boss_sound.set_volume(0.3)

# 加载图片资源
def load_sprite_sheet(filename, cols, rows, scale=1.0):
    image = pygame.image.load(filename).convert_alpha()
    # 缩放整个精灵表
    new_width = int(image.get_width() * scale)
    new_height = int(image.get_height() * scale)
    image = pygame.transform.scale(image, (new_width, new_height))
    
    total_width = image.get_width()
    total_height = image.get_height()
    frame_width = total_width // cols
    frame_height = total_height // rows
    frames = []
    
    for row in range(rows):
        for col in range(cols):
            frame = image.subsurface((col * frame_width, row * frame_height, 
                                    frame_width, frame_height))
            frames.append(frame)
    return frames

class PixelUI:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)  # 使用像素字体
        self.health_border_width = 2
        self.health_height = 20
        self.health_padding = 2
        
    def draw_health_bar(self, surface, x, y, width, current, maximum, color):
        # 绘制外边框
        border_rect = pygame.Rect(x, y, width, self.health_height)
        pygame.draw.rect(surface, WHITE, border_rect, self.health_border_width)
        
        # 绘制血量背景
        inner_rect = pygame.Rect(
            x + self.health_padding,
            y + self.health_padding,
            width - 2 * self.health_padding,
            self.health_height - 2 * self.health_padding
        )
        pygame.draw.rect(surface, BLACK, inner_rect)
        
        # 绘制当前血量
        health_width = (width - 2 * self.health_padding) * (current / maximum)
        health_rect = pygame.Rect(
            x + self.health_padding,
            y + self.health_padding,
            health_width,
            self.health_height - 2 * self.health_padding
        )
        pygame.draw.rect(surface, color, health_rect)
        
        # 绘制血量文字
        text = f"{current}/{maximum}"
        text_surface = self.font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=border_rect.center)
        surface.blit(text_surface, text_rect)

class Background:
    def __init__(self, image):
        # 保持宽高比缩放，垂直填满屏幕
        scale = WINDOW_HEIGHT / image.get_height()
        new_width = int(image.get_width() * scale)
        self.image = pygame.transform.scale(image, (new_width, WINDOW_HEIGHT))
        self.width = self.image.get_width()
        self.parallax_speed = 0.5
        self.x = 0  # 当前平移偏移
        
    def update(self, camera_x):
        # 背景应与相机同向移动（略慢），正向偏移
        self.x = int(camera_x * self.parallax_speed) % self.width
        
    def draw(self, screen):
        start_x = -self.x
        while start_x > -self.width:
            start_x -= self.width
        cur_x = start_x
        while cur_x < WINDOW_WIDTH:
            screen.blit(self.image, (cur_x, 0))
            cur_x += self.width

class Projectile:
    def __init__(self, x, y, speed_x, speed_y=0, size=10, color=RED, projectile_type="normal"):
        self.rect = pygame.Rect(x, y, size*2, size)  # 增大子弹尺寸
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.color = color
        self.type = projectile_type
        self.lifetime = 0
        self.max_lifetime = 180  # 3秒 (60帧/秒)
        
    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.type == "sine":
            self.rect.y += math.sin(self.lifetime * 0.1) * 3
        elif self.type == "homing":
            # 蓄力效果
            if self.lifetime < 30:
                self.speed_x *= 0.95
            else:
                self.speed_x *= 1.1
        self.lifetime += 1
        
    def draw(self, screen, rect_override=None):
        draw_rect = rect_override if rect_override is not None else self.rect
        if self.type == "normal":
            pygame.draw.ellipse(screen, (255, 50, 50), draw_rect)
            pygame.draw.ellipse(screen, (255, 200, 200), draw_rect, 2)
        elif self.type == "sine":
            glow_rect = draw_rect.inflate(8, 8)
            pygame.draw.ellipse(screen, (100, 100, 255, 128), glow_rect)
            pygame.draw.ellipse(screen, (50, 50, 255), draw_rect)
            pygame.draw.ellipse(screen, (150, 150, 255), draw_rect, 2)
        elif self.type == "homing":
            points = [
                (draw_rect.centerx, draw_rect.top),
                (draw_rect.right, draw_rect.centery),
                (draw_rect.centerx, draw_rect.bottom),
                (draw_rect.left, draw_rect.centery)
            ]
            pygame.draw.polygon(screen, (255, 255, 0), points)
            pygame.draw.polygon(screen, (255, 255, 150), points, 2)
            
    def is_expired(self):
        return self.lifetime >= self.max_lifetime

class GameAssets:
    def __init__(self):
        # 加载并等比例缩放开始界面
        original_start_ui = pygame.image.load('assets/UI start.png').convert_alpha()
        scale = WINDOW_HEIGHT / original_start_ui.get_height()
        start_ui_width = int(original_start_ui.get_width() * scale)
        self.start_ui = pygame.transform.scale(original_start_ui, 
                                             (start_ui_width, WINDOW_HEIGHT))
        
        # 加载背景
        self.bg = pygame.image.load('assets/BG_2.png').convert()  # 更新背景文件
        
        # Trump动画 - 缩小20%
        self.trump_idle = load_sprite_sheet('assets/Trump idle.png', 4, 1, 0.5)  # 从0.7改为0.5
        self.trump_run = load_sprite_sheet('assets/Trump run.png', 4, 1, 0.5)  # 从0.7改为0.5
        
        # BOSS动画
        self.boss_idle = load_sprite_sheet('assets/BOSS idle.png', 4, 1, 1.5)
        self.boss_walk = load_sprite_sheet('assets/boss walk.png', 4, 1, 1.5)
        
        # UI元素
        self.game_ui = pygame.image.load('assets/Game UI Design.png').convert_alpha()
        self.game_ui = pygame.transform.scale(self.game_ui, 
                                            (self.game_ui.get_width()//4, 
                                             self.game_ui.get_height()//4))
        
        # 水平翻转BOSS动画
        for i in range(len(self.boss_idle)):
            self.boss_idle[i] = pygame.transform.flip(self.boss_idle[i], True, False)
        for i in range(len(self.boss_walk)):
            self.boss_walk[i] = pygame.transform.flip(self.boss_walk[i], True, False)

class Bullet:
    def __init__(self, x, y, direction, speed):
        self.rect = pygame.Rect(x, y, 8, 4)
        self.direction = direction  # 1 for right, -1 for left
        self.speed = speed
        
    def update(self):
        self.rect.x += self.speed * self.direction
        
    def is_visible(self, camera_x):
        # 检查子弹是否在相机视野范围内（稍微扩大一些范围）
        bullet_screen_x = self.rect.x - camera_x
        return -100 < bullet_screen_x < WINDOW_WIDTH + 100

class Player:
    def __init__(self, assets):
        self.assets = assets
        self.idle_frames = assets.trump_idle
        self.run_frames = assets.trump_run
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_delay = 80
        self.is_running = False
        self.facing_left = False  # 新增：角色朝向
        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.bottom = GROUND_HEIGHT
        self.health = 100
        self.bullets = []  # 现在存储Bullet对象而不是Rect
        self.shoot_timer = 0
        self.shoot_delay = 300  # 提高射击频率
        self.speed = 12  # 提高移动速度
        self.bullet_speed = 25  # 提高子弹速度
        self.bullet_damage = 5
        
        self.velocity_y = 0
        self.is_jumping = False
        self.air_control = 0.8  # 空中移动控制

    def update(self, current_time):
        # 重力
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
        
        # 地面碰撞检测
        if self.rect.bottom > GROUND_HEIGHT:
            self.rect.bottom = GROUND_HEIGHT
            self.velocity_y = 0
            self.is_jumping = False

        # 动画更新
        if current_time - self.animation_timer > self.animation_delay:
            self.animation_timer = current_time
            self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
            if self.is_running:
                frame = self.run_frames[self.current_frame]
            else:
                frame = self.idle_frames[self.current_frame]
            # 根据朝向翻转图像
            if self.facing_left:
                self.image = pygame.transform.flip(frame, True, False)
            else:
                self.image = frame

        # 自动射击
        if current_time - self.shoot_timer > self.shoot_delay:
            self.shoot_timer = current_time
            self.shoot()

        # 更新子弹
        for bullet in self.bullets:
            bullet.update()

    def shoot(self):
        direction = -1 if self.facing_left else 1
        if self.facing_left:
            bullet = Bullet(self.rect.left, self.rect.centery, direction, self.bullet_speed)
        else:
            bullet = Bullet(self.rect.right, self.rect.centery, direction, self.bullet_speed)
        self.bullets.append(bullet)
        shoot_sound.play()

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = JUMP_SPEED
            self.is_jumping = True
            jump_sound.play()

class Boss:
    def __init__(self, assets):
        self.assets = assets
        self.idle_frames = assets.boss_idle
        self.walk_frames = assets.boss_walk
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_delay = 150
        self.is_walking = False
        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect()
        self.screen_offset = WINDOW_WIDTH - 350  # BOSS在屏幕上的固定x偏移
        self.rect.x = self.screen_offset  # 初始放在屏幕外，会在出现时调整
        self.rect.bottom = GROUND_HEIGHT
        self.health = 400
        self.max_health = 400
        self.projectiles = []
        self.attack_timer = 0
        self.attack_delay = 600  # 更快
        self.attack_pattern = -1
        self.pattern_timer = 0
        self.pattern_duration = 5000
        self.has_appeared = False
        self.entrance_speed = 6
        self.projectile_size = 15
        self.projectile_speed = 8  # 更快的子弹速度
        self.hit_effect_timer = 0
        self.hit_effect_duration = 100
        self.is_hit = False
        
        # 创建遮罩
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, current_time, player_x, camera_x):
        if not self.has_appeared:
            return

        # 始终根据相机位置更新世界坐标，使BOSS停留在屏幕右偏移
        self.rect.x = camera_x + self.screen_offset
        self.rect.bottom = GROUND_HEIGHT

        # 更新受击效果
        if self.is_hit:
            if current_time - self.hit_effect_timer > self.hit_effect_duration:
                self.is_hit = False

        # 更新动画
        if current_time - self.animation_timer > self.animation_delay:
            self.animation_timer = current_time
            self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
            self.image = self.idle_frames[self.current_frame]
            self.mask = pygame.mask.from_surface(self.image)

        # 攻击逻辑
        if current_time - self.attack_timer > self.attack_delay:
            self.attack_timer = current_time
            self.attack_pattern = (self.attack_pattern + 1) % 6
            self.shoot_projectiles()

        # 更新投射物并移除超出屏幕或已过期的
        for projectile in self.projectiles[:]:
            projectile.update()
            # 如果子弹超出了屏幕或者存活时间过长，移除它
            projectile_screen_x = projectile.rect.x - camera_x
            if (projectile_screen_x < -100 or 
                projectile_screen_x > WINDOW_WIDTH + 100 or
                projectile.rect.y < -100 or 
                projectile.rect.y > WINDOW_HEIGHT + 100 or
                projectile.is_expired()):
                self.projectiles.remove(projectile)

    def shoot_projectiles(self):
                # 循环切换弹幕模式
        self.attack_pattern = (self.attack_pattern + 1) % 6
        pattern = self.attack_pattern
        if pattern == 0:
            # 五连快速直线
            for i in range(7):
                self.projectiles.append(Projectile(
                    self.rect.centerx - i*18,
                    self.rect.centery,
                    -self.projectile_speed,
                    0,
                    self.projectile_size,
                    RED))
        elif pattern == 1:
            # 七发扇形
            for angle in range(-60, 61, 20):
                rad = math.radians(angle)
                self.projectiles.append(Projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    -self.projectile_speed*math.cos(rad),
                    self.projectile_speed*math.sin(rad),
                    self.projectile_size,
                    RED))
        elif pattern == 2:
            # 双相位正弦
            for phase in [0, math.pi/2, math.pi]:
                p = Projectile(self.rect.centerx,
                                self.rect.centery,
                                -self.projectile_speed,
                                0,
                                self.projectile_size,
                                BLUE,
                                "sine")
                p.lifetime = phase*30
                self.projectiles.append(p)
        elif pattern == 3:
            # 四颗追踪
            for _ in range(4):
                self.projectiles.append(Projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    -self.projectile_speed,
                    0,
                    int(self.projectile_size*1.2),
                    YELLOW,
                    "homing"))
        elif pattern == 4:
            # 24 向环形
            for angle in range(0,360,15):
                rad = math.radians(angle)
                self.projectiles.append(Projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    self.projectile_speed*0.8*math.cos(rad),
                    self.projectile_speed*0.8*math.sin(rad),
                    int(self.projectile_size*0.9)))
        else:
            # 旋转螺旋：发射12颗并在后续帧继续旋转（简化为不同初始角度）
            base_angle = (pygame.time.get_ticks()//10)%360
            for angle in range(base_angle, base_angle+360, 30):
                rad = math.radians(angle)
                self.projectiles.append(Projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    self.projectile_speed*math.cos(rad),
                    self.projectile_speed*math.sin(rad),
                    int(self.projectile_size*0.8)))

    def take_damage(self, damage, current_time):
        self.health -= damage
        self.is_hit = True
        self.hit_effect_timer = current_time

    def draw(self, screen, rect):
        if self.is_hit:
            # 创建一个暂时的表面来应用红色色调效果
            temp_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
            # 绘制原始图像
            temp_surface.blit(self.image, (0, 0))
            # 创建一个红色图层
            red_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
            red_surface.fill((255, 0, 0, 100))  # 半透明红色
            # 混合红色图层
            temp_surface.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # 绘制到屏幕
            screen.blit(temp_surface, rect)
        else:
            screen.blit(self.image, rect)

    def check_bullet_collision(self, bullet, camera_x):
        # 简化碰撞检测，提高命中率
        bullet_center_x = bullet.rect.centerx - self.rect.x
        bullet_center_y = bullet.rect.centery - self.rect.y
        
        # 检查点是否在BOSS图像区域内
        if (0 <= bullet_center_x < self.image.get_width() and 
            0 <= bullet_center_y < self.image.get_height()):
            # 放宽判定，只要在图像区域内就算命中
            return True
        return False

class Game:
    def __init__(self):
        self.assets = GameAssets()
        self.state = 'START'
        self.clock = pygame.time.Clock()
        self.player = None
        self.boss = None
        self.background = Background(self.assets.bg)
        self.camera_x = 0
        self.ui = PixelUI()
        self.total_distance = 0
        self.game_over_timer = 0
        self.debug = False  # 添加调试模式开关
        
    def reset_game(self):
        self.state = 'START'
        self.player = None
        self.boss = None
        self.camera_x = 0
        self.total_distance = 0
        self.game_over_timer = 0
        start_button.show()
        exit_button.show()

    def handle_events(self):
        time_delta = self.clock.tick(60)/1000.0
        
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
                
            if event.type == gui.UI_BUTTON_PRESSED:
                if event.ui_element == start_button:
                    self.state = 'PLAYING'
                    self.player = Player(self.assets)
                    self.boss = Boss(self.assets)
                    start_button.hide()
                    exit_button.hide()
                elif event.ui_element == exit_button:
                    return False
                    
            if self.state == 'PLAYING':
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        self.player.jump()
                        
            ui_manager.process_events(event)
            
        ui_manager.update(time_delta)
        return True

    def update(self):
        if self.state == 'PLAYING':
            current_time = pygame.time.get_ticks()
            
            # 更新玩家
            keys = pygame.key.get_pressed()
            
            # 移动和朝向控制
            moving = False
            if keys[K_LEFT]:
                move_amount = -self.player.speed
                self.player.facing_left = True
                moving = True
                if self.player.is_jumping:
                    move_amount *= self.player.air_control

                player_screen_x = self.player.rect.x - self.camera_x
                
                if player_screen_x < WINDOW_WIDTH * 0.3 and self.camera_x > 0:
                    camera_move = max(move_amount, -self.camera_x)
                    self.camera_x += camera_move
                    self.player.rect.x += move_amount
                else:
                    new_x = max(0, self.player.rect.x + move_amount)
                    self.player.rect.x = new_x
                    
            if keys[K_RIGHT]:
                move_amount = self.player.speed
                self.player.facing_left = False
                moving = True
                if self.player.is_jumping:
                    move_amount *= self.player.air_control
                    
                player_screen_x = self.player.rect.x - self.camera_x
                
                if player_screen_x > WINDOW_WIDTH * 0.4:
                    self.camera_x += move_amount
                    self.player.rect.x += move_amount
                else:
                    self.player.rect.x += move_amount

            self.player.is_running = moving

            # 跳跃控制
            if keys[K_SPACE] and not self.player.is_jumping:
                self.player.jump()

            if moving:
                self.total_distance += abs(move_amount)
            
            # 检查是否应该让BOSS出现
            if self.total_distance >= BOSS_APPEAR_DISTANCE and not self.boss.has_appeared:
                self.boss.has_appeared = True
                # 让Boss类自行根据camera_x定位
                self.boss.attack_timer = current_time
                boss_sound.play()

            # 更新玩家和子弹
            self.player.update(current_time)
            
            # 更新BOSS
            if self.boss.has_appeared:
                self.boss.update(current_time, self.player.rect.x, self.camera_x)
                self.background.update(self.camera_x)

            # 碰撞检测
            # 1. 玩家子弹和BOSS的碰撞
            for bullet in self.player.bullets[:]:
                if self.boss.has_appeared and self.boss.rect.colliderect(bullet.rect):
                    if self.boss.check_bullet_collision(bullet, self.camera_x):
                        self.boss.take_damage(self.player.bullet_damage, current_time)
                        self.player.bullets.remove(bullet)
                        hit_sound.play()
                        if self.boss.health <= 0:
                            self.state = 'GAME_OVER'
                            self.game_over_timer = current_time

            # 2. BOSS子弹和玩家的碰撞
            for projectile in self.boss.projectiles[:]:
                projectile_screen_x = projectile.rect.x - self.camera_x
                projectile_rect = projectile.rect.copy()
                projectile_rect.x = projectile_screen_x
                
                player_screen_x = self.player.rect.x - self.camera_x
                player_rect = self.player.rect.copy()
                player_rect.x = player_screen_x
                
                if projectile_rect.colliderect(player_rect):
                    self.player.health -= 10  # 减少伤害
                    self.boss.projectiles.remove(projectile)
                    hit_sound.play()
                    if self.player.health <= 0:
                        self.state = 'GAME_OVER'
                        self.game_over_timer = current_time

        elif self.state == 'GAME_OVER':
            current_time = pygame.time.get_ticks()
            # 3秒后返回主界面
            if current_time - self.game_over_timer > 3000:
                self.reset_game()

    def draw(self):
        # 清空屏幕
        screen.fill(BLACK)
        
        # 绘制背景
        self.background.draw(screen)
        
        if self.state == 'START':
            # 居中绘制开始界面
            start_x = (WINDOW_WIDTH - self.assets.start_ui.get_width()) // 2
            screen.blit(self.assets.start_ui, (start_x, 0))
            ui_manager.draw_ui(screen)
            
        elif self.state == 'PLAYING':
            # 计算所有游戏对象相对于相机的位置
            player_screen_x = self.player.rect.x - self.camera_x
            player_rect = self.player.rect.copy()
            player_rect.x = player_screen_x
            screen.blit(self.player.image, player_rect)
            
            # 绘制BOSS（如果出现）
            if self.boss.has_appeared:
                boss_screen_x = self.boss.rect.x - self.camera_x
                boss_rect = self.boss.rect.copy()
                boss_rect.x = boss_screen_x
                self.boss.draw(screen, boss_rect)
            
                # 调试模式 - 显示BOSS位置信息
                if self.debug:
                    font = pygame.font.Font(None, 24)
                    debug_text = f"BOSS: x={self.boss.rect.x}, screen_x={boss_screen_x}"
                    text_surf = font.render(debug_text, True, WHITE)
                    screen.blit(text_surf, (10, 40))
            
            # 绘制玩家子弹
            for bullet in self.player.bullets:
                bullet_screen_x = bullet.rect.x - self.camera_x
                bullet_rect = bullet.rect.copy()
                bullet_rect.x = bullet_screen_x
                pygame.draw.rect(screen, WHITE, bullet_rect)
            
            # 绘制BOSS的投射物 (使用相机偏移)
            if self.boss.has_appeared:
                for projectile in self.boss.projectiles:
                    projectile_screen_rect = projectile.rect.copy()
                    projectile_screen_rect.x -= self.camera_x
                    projectile.draw(screen, projectile_screen_rect)
            
            # UI元素不需要考虑相机位置
            self.ui.draw_health_bar(screen, 10, 10, 200, 
                                  self.player.health, 100, RED)
            if self.boss.has_appeared:
                boss_health_x = WINDOW_WIDTH - 210
                self.ui.draw_health_bar(screen, boss_health_x, 10, 200,
                                      self.boss.health, self.boss.max_health, RED)
            
            # 绘制地面
            pygame.draw.line(screen, WHITE, (0, GROUND_HEIGHT), 
                           (WINDOW_WIDTH, GROUND_HEIGHT), 2)
            
        elif self.state == 'GAME_OVER':
            # 继续绘制游戏画面
            if self.player:
                screen.blit(self.player.image, self.player.rect)
            if self.boss and self.boss.has_appeared:
                screen.blit(self.boss.image, self.boss.rect)
            
            # 绘制游戏结束文本
            font = pygame.font.Font(None, 74)
            if self.player.health <= 0:
                text = font.render('GAME OVER', True, RED)
            else:
                text = font.render('YOU WIN!', True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            screen.blit(text, text_rect)
            
            # 显示返回提示
            font_small = pygame.font.Font(None, 36)
            return_text = font_small.render('Returning to main menu...', True, WHITE)
            return_rect = return_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 50))
            screen.blit(return_text, return_rect)
        
        pygame.display.flip()
        self.clock.tick(60)

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit() 