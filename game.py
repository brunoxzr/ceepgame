import cv2
import numpy as np
import mediapipe as mp
import pygame
import sys
import random
import time
import os
import json

# ==========================
# CONFIGURAÇÃO DO MEDIAPIPE
# ==========================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.7
)

# --------------------------
# DETECÇÃO DE GESTOS
# --------------------------
def detectar_gesto(results):
    if not results or not results.multi_hand_landmarks:
        return None

    lm = results.multi_hand_landmarks[0].landmark
    tip_ids = [4, 8, 12, 16, 20]
    pip_ids = [3, 6, 10, 14, 18]

    fingers_up = [lm[tip].y < lm[pip].y for tip, pip in zip(tip_ids[1:], pip_ids[1:])]
    thumb_up = lm[tip_ids[0]].x > lm[pip_ids[0]].x

    total_up = sum(fingers_up) + (1 if thumb_up else 0)

    if total_up >= 3:
        return "JUMP"
    elif sum(fingers_up) == 1 and thumb_up:
        return "SHOT"
    elif total_up == 0:
        return "RUN"
    return None


# ==========================
# PERSISTÊNCIA DA WEBCAM
# ==========================
CONFIG_FILE = "config_cam.json"

def salvar_config_cam(rect):
    try:
        data = {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print("Aviso: não foi possível salvar config_cam.json:", e)

def carregar_config_cam(default_rect):
    if not os.path.exists(CONFIG_FILE):
        return default_rect
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return pygame.Rect(
            d.get("x", default_rect.x),
            d.get("y", default_rect.y),
            d.get("w", default_rect.w),
            d.get("h", default_rect.h),
        )
    except Exception as e:
        print("Aviso: não foi possível ler config_cam.json:", e)
        return default_rect


# ==========================
# INICIALIZAÇÃO DA CÂMERA
# ==========================
def inicializar_camera_logitech(start_id=0, max_checks=5):
    """
    Tenta inicializar a câmera forçando DirectShow e MJPG.
    """
    for idx in range(start_id, max_checks):
        print(f"🔎 Testando Câmera ID {idx}...")

        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ Câmera detectada no ID {idx}!")
                return cap
            else:
                print(f"❌ Câmera ID {idx} abriu mas retornou tela preta.")
                cap.release()
        else:
            print(f"❌ Falha ao abrir ID {idx}.")
    return None


# ==========================
# FUNÇÃO PRINCIPAL
# ==========================
def main():
    pygame.init()
    pygame.display.set_caption("CEEPGame 🧠 — IA Gestual v1.2 OTIMIZADO")

    WIDTH, HEIGHT = 960, 540
    original_size = (WIDTH, HEIGHT)
    screen = pygame.display.set_mode(original_size)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arialblack", 24)

    # --- CORES HUD ---
    TEXT_COLOR_PRIMARY = (255, 255, 255)   # Pontos
    TEXT_COLOR_SECONDARY = (255, 215, 0)   # Recorde
    TEXT_COLOR_SPEED = (0, 255, 255)       # Velocidade
    TEXT_COLOR_GESTURE = (100, 255, 100)   # Gesto

    # ===============================================
    # 🔄 INICIALIZAÇÃO DA CÂMERA
    # ===============================================
    cap = inicializar_camera_logitech(start_id=0, max_checks=5)

    if cap is None:
        print("🚨 ERRO CRÍTICO: Nenhuma câmera funcional encontrada.")
        pygame.quit()
        sys.exit()

    # ========= ÁUDIO =========
    try:
        pygame.mixer.init()
        theme_music = "theme.mp3"
        shoot_sound_file = "audio.mp3"

        if os.path.exists(theme_music):
            pygame.mixer.music.load(theme_music)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.25)

        shoot_sound = pygame.mixer.Sound(shoot_sound_file) if os.path.exists(shoot_sound_file) else None
        if shoot_sound:
            shoot_sound.set_volume(0.7)

        jump_sound = pygame.mixer.Sound("jump.wav") if os.path.exists("jump.wav") else None
        hit_sound = pygame.mixer.Sound("hit.wav") if os.path.exists("hit.wav") else None

    except Exception as e:
        print("Erro ao inicializar áudio:", e)
        jump_sound = hit_sound = shoot_sound = None

    # ========= IMAGENS =========
    def load_image_safe(name, size):
        if os.path.exists(name):
            img = pygame.image.load(name).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        return None

    walk_frames = []
    for fname in ["1.png", "2.png", "3.png"]:
        img = load_image_safe(fname, (60, 80))
        if img is not None:
            walk_frames.append(img)

    if not walk_frames:
        fallback = load_image_safe("player.png", (60, 80))
        if fallback:
            walk_frames = [fallback, fallback, fallback]
    
    ceep_logo = load_image_safe("logoceep.png", (220, 220))
    player_jump_img = load_image_safe("player_jump.png", (60, 80))
    player_shoot_img = load_image_safe("player_shoot.png", (60, 80))
    enemy_img = load_image_safe("enemy.png", (60, 80))
    obstacle_img = load_image_safe("obstacle.png", (60, 60))

    # ========= FUNDO SCROLLING E CHÃO =========
    background_image = load_image_safe("fundo2.jpg", (WIDTH, HEIGHT))
    background_x = 0

    if background_image:
        # altura proporcional da tua imagem (chão certinho)
        ground_y = int(HEIGHT * 0.8333)
    else:
        ground_y = HEIGHT - 60
        print("Aviso: fundo2.jpg não encontrado. Usando fundo padrão.")

    # ========= JOGADOR =========
    player_x = 120
    player_w, player_h = 60, 80
    player_y = ground_y - player_h

    vel_y = 0
    on_ground = True
    dust_particles = []
    shadow_radius = 35

    current_walk_frame = 0
    walk_frame_timer = 0
    walk_frame_interval = 110

    # ========= ENTIDADES =========
    bullets, obstacles, enemies = [], [], []
    spawn_timer = 0
    spawn_interval = 1200

    # ========= DIFICULDADE (IGUAL CÓDIGO ANTIGO) =========
    base_speed = 8
    game_speed = base_speed
    difficulty_increase = 0.0006        # igual ao código A
    score, record = 0, 0

    last_shot, last_jump = 0, 0
    shot_cd, jump_cd = 400, 600

    # ========= TELA / WEBCAM INTERATIVA =========
    is_fullscreen = False

    default_cam_rect = pygame.Rect(
        WIDTH - int(WIDTH * 0.22) - 20,
        20,
        int(WIDTH * 0.22),
        int(HEIGHT * 0.22),
    )
    cam_rect = carregar_config_cam(default_cam_rect)
    dragging = False
    drag_offset = (0, 0)
    MIN_CAM_W, MIN_CAM_H = 140, 100

    # ========= GESTOS / MEDIAPIPE =========
    last_gesture = None
    last_results = None
    last_gesture_update = 0
    GESTURE_UPDATE_INTERVAL = 180   # ~5.5 fps processamento de gesto

    def desenhar_faixa_lateral(screen, WIDTH, HEIGHT, background_image, ceep_logo):
        if background_image is None:
            return

        bg_w, bg_h = background_image.get_width(), background_image.get_height()

        # Se já preenche a tela, não precisa das faixas
        if bg_w == WIDTH and bg_h == HEIGHT:
            return

        # Definir áreas pretas
        screen_width, screen_height = WIDTH, HEIGHT

        # Caso existam barras laterais (modo widescreen)
        barra_esq_largura = (WIDTH - bg_w) // 2 if bg_w < WIDTH else 0
        barra_dir_largura = barra_esq_largura

        # Cor preta das barras
        if barra_esq_largura > 0:
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, barra_esq_largura, HEIGHT))
            pygame.draw.rect(screen, (0, 0, 0), (WIDTH - barra_dir_largura, 0, barra_dir_largura, HEIGHT))

            # Logo do lado esquerdo
            if ceep_logo:
                screen.blit(ceep_logo, (barra_esq_largura // 2 - ceep_logo.get_width() // 2,
                                        HEIGHT // 2 - ceep_logo.get_height() // 2))

            # Texto do lado direito
            font_big = pygame.font.SysFont("arialblack", 40)
            text_surface = font_big.render("VEM SER CEEP", True, (255, 0, 0))
            font_shadow = pygame.font.SysFont("arialblack", 40)

            # sombra amarela
            shadow_surface = font_shadow.render("VEM SER CEEP", True, (255, 255, 0))

            # posição central
            dx = WIDTH - barra_dir_largura // 2
            dy = HEIGHT // 2

            # sombra
            screen.blit(shadow_surface, (dx - text_surface.get_width() // 2 + 4,
                                        dy - text_surface.get_height() // 2 + 4))

            # texto principal
            screen.blit(text_surface, (dx - text_surface.get_width() // 2,
                                    dy - text_surface.get_height() // 2))

    running = True
    try:
        while running:
            dt = clock.tick(60)
            now = pygame.time.get_ticks()

            # ==================
            # EVENTOS DE SISTEMA
            # ==================
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

                if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    # Alterna fullscreen
                    is_fullscreen = not is_fullscreen

                    if is_fullscreen:
                        # pegar resolução REAL do monitor
                        info = pygame.display.Info()
                        WIDTH, HEIGHT = info.current_w, info.current_h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

                        # Reescala o fundo mantendo preenchimento
                        if background_image:
                            background_image = load_image_safe("fundo2.jpg", (WIDTH, HEIGHT))
                            background_x = 0

                            # chão proporcional ao fundo real
                            ground_y = int(HEIGHT * 0.8333)
                        else:
                            ground_y = HEIGHT - 60

                    else:
                        # voltar para janela normal
                        WIDTH, HEIGHT = original_size
                        screen = pygame.display.set_mode(original_size)

                        if background_image:
                            background_image = load_image_safe("fundo2.jpg", (WIDTH, HEIGHT))
                            background_x = 0
                            ground_y = int(HEIGHT * 0.8333)  # mantém proporção da imagem
                        else:
                            ground_y = HEIGHT - 60

                    # reposiciona player no chão correto
                    player_y = ground_y - player_h

                    # Ajusta webcam para continuar visível e proporcional
                    cam_rect.width = max(MIN_CAM_W, min(cam_rect.width, int(WIDTH * 0.8)))
                    cam_rect.height = max(MIN_CAM_H, min(cam_rect.height, int(HEIGHT * 0.8)))
                    cam_rect.x = max(0, min(cam_rect.x, WIDTH - cam_rect.width))
                    cam_rect.y = max(0, min(cam_rect.y, HEIGHT - cam_rect.height))

                    # Ajusta webcam
                    cam_rect.width = max(MIN_CAM_W, min(cam_rect.width, int(WIDTH * 0.8)))
                    cam_rect.height = max(MIN_CAM_H, min(cam_rect.height, int(HEIGHT * 0.8)))
                    cam_rect.x = max(0, min(cam_rect.x, WIDTH - cam_rect.width))
                    cam_rect.y = max(0, min(cam_rect.y, HEIGHT - cam_rect.height))

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1 and cam_rect.collidepoint(e.pos):
                        dragging = True
                        drag_offset = (cam_rect.x - e.pos[0], cam_rect.y - e.pos[1])

                    if e.button == 4:  # scroll up
                        cam_rect.width = int(cam_rect.width * 1.08)
                        cam_rect.height = int(cam_rect.height * 1.08)
                    if e.button == 5:  # scroll down
                        cam_rect.width = int(cam_rect.width * 0.92)
                        cam_rect.height = int(cam_rect.height * 0.92)

                    cam_rect.width = max(MIN_CAM_W, min(cam_rect.width, int(WIDTH * 0.9)))
                    cam_rect.height = max(MIN_CAM_H, min(cam_rect.height, int(HEIGHT * 0.9)))
                    cam_rect.x = max(0, min(cam_rect.x, WIDTH - cam_rect.width))
                    cam_rect.y = max(0, min(cam_rect.y, HEIGHT - cam_rect.height))

                if e.type == pygame.MOUSEBUTTONUP:
                    if e.button == 1 and dragging:
                        dragging = False
                        salvar_config_cam(cam_rect)

                if e.type == pygame.MOUSEMOTION and dragging:
                    cam_rect.x = e.pos[0] + drag_offset[0]
                    cam_rect.y = e.pos[1] + drag_offset[1]
                    cam_rect.x = max(0, min(cam_rect.x, WIDTH - cam_rect.width))
                    cam_rect.y = max(0, min(cam_rect.y, HEIGHT - cam_rect.height))

            # ==================
            # CAPTURA E GESTOS
            # ==================
            ret, frame = cap.read()
            if not ret:
                print("Falha na leitura do frame.")
                break

            frame = cv2.flip(frame, 1)

            # OTIMIZAÇÃO: processar gesto em 320x240 e com intervalo
            if now - last_gesture_update > GESTURE_UPDATE_INTERVAL:
                small = cv2.resize(frame, (320, 240))
                frame_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                last_results = hands.process(frame_rgb)
                last_gesture = detectar_gesto(last_results)
                last_gesture_update = now

            gesture = last_gesture

            # (desenhar landmarks na imagem original, só pra feedback visual)
            if last_results and last_results.multi_hand_landmarks:
                for hand_landmarks in last_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style(),
                    )

            # ==================
            # LÓGICA DO JOGO
            # =======

            # 🔹 MESMA LÓGICA DO CÓDIGO ANTIGO (A)
            # Aumenta a velocidade suavemente com o tempo
            game_speed += difficulty_increase * dt

            # Spawn depende da velocidade, com piso mínimo
            spawn_interval = max(550, 1200 - int(game_speed * 10))

            # Pontuação sobe continuamente em função da velocidade
            score += int(game_speed / 10)

            gravity = 0.9 + (game_speed / 20)
            jump_force = -18 - (game_speed / 5) * 0.5

            if gesture == "JUMP" and on_ground and now - last_jump > jump_cd:
                vel_y = jump_force
                on_ground = False
                last_jump = now
                if jump_sound:
                    try:
                        jump_sound.play()
                    except:
                        pass
                for i in range(10):
                    dust_particles.append({
                        "x": player_x + random.randint(-10, 40),
                        "y": ground_y - 5,
                        "vx": random.uniform(-1, 1),
                        "vy": random.uniform(-2, -0.5),
                        "life": random.randint(15, 25)
                    })

            if gesture == "SHOT" and now - last_shot > shot_cd:
                bullets.append({"x": player_x + player_w, "y": player_y + player_h // 2})
                last_shot = now
                if shoot_sound:
                    try:
                        if not pygame.mixer.Channel(1).get_busy():
                            pygame.mixer.Channel(1).play(shoot_sound)
                    except:
                        pass

            # física vertical
            vel_y += gravity
            player_y += vel_y

            if player_y + player_h >= ground_y:
                if not on_ground:
                    for i in range(12):
                        dust_particles.append({
                            "x": player_x + random.randint(-5, 40),
                            "y": ground_y - 5,
                            "vx": random.uniform(-1.5, 1.5),
                            "vy": random.uniform(-2, -0.2),
                            "life": random.randint(20, 30)
                        })
                player_y = ground_y - player_h
                vel_y = 0
                on_ground = True

            # animação de caminhada
            if on_ground and gesture != "SHOT" and walk_frames:
                walk_frame_timer += dt
                if walk_frame_timer >= walk_frame_interval:
                    walk_frame_timer = 0
                    current_walk_frame = (current_walk_frame + 1) % len(walk_frames)

            # Spawn de obstáculos/inimigos (sem ficar impossível)
            if now - spawn_timer > spawn_interval:
                min_gap = 250
                last_x = None

                if obstacles:
                    last_x = obstacles[-1]["x"]
                if enemies:
                    if last_x is None:
                        last_x = enemies[-1]["x"]
                    else:
                        last_x = max(last_x, enemies[-1]["x"])

                too_close = last_x is not None and (WIDTH - last_x) < min_gap
                too_many = (len(obstacles) + len(enemies)) >= 6

                if not too_close and not too_many:
                    if random.random() < 0.6:
                        h = random.randint(30, 70)
                        obstacles.append({"x": WIDTH, "y": ground_y - h, "w": 50, "h": h})
                    else:
                        enemies.append({"x": WIDTH, "y": ground_y - 80, "w": 60, "h": 80})

                spawn_timer = now

            # movimentação dos tiros e entidades
            for b in bullets:
                b["x"] += 15
            bullets = [b for b in bullets if b["x"] < WIDTH]

            for o in obstacles:
                o["x"] -= game_speed
            obstacles = [o for o in obstacles if o["x"] + o["w"] > 0]

            for en in enemies:
                en["x"] -= game_speed + 1
            enemies = [en for en in enemies if en["x"] + en["w"] > 0]

            # colisão tiros x inimigos
            player_rect = pygame.Rect(player_x, player_y, player_w, player_h)
            remove_b, remove_e = [], []

            for i, en in enumerate(enemies):
                er = pygame.Rect(en["x"], en["y"], en["w"], en["h"])
                for j, b in enumerate(bullets):
                    if er.colliderect(pygame.Rect(b["x"], b["y"], 10, 10)):
                        remove_b.append(j)
                        remove_e.append(i)
                        score += 50   # bônus por matar inimigo
                        if hit_sound:
                            try:
                                hit_sound.play()
                            except:
                                pass

            bullets = [b for idx, b in enumerate(bullets) if idx not in remove_b]
            enemies = [en for idx, en in enumerate(enemies) if idx not in remove_e]

            # colisão player x obstáculos / inimigos
            hit = any(
                player_rect.colliderect(pygame.Rect(o["x"], o["y"], o["w"], o["h"]))
                for o in obstacles
            ) or any(
                player_rect.colliderect(pygame.Rect(e["x"], e["y"], e["w"], e["h"]))
                for e in enemies
            )

            if hit:
                if hit_sound:
                    try:
                        hit_sound.play()
                    except:
                        pass
                record = max(record, score)
                score = 0
                game_speed = base_speed   # reseta dificuldade igual no antigo
                obstacles.clear()
                enemies.clear()
                bullets.clear()

            # ==================
            # DESENHO
            # ==================

            # Fundo
            if background_image:
                background_x -= game_speed * dt / 1000.0
                if background_x <= -WIDTH:
                    background_x = 0
                screen.blit(background_image, (background_x, 0))
                screen.blit(background_image, (background_x + WIDTH, 0))
            else:
                screen.fill((20, 22, 40))
                pygame.draw.rect(screen, (60, 65, 95), (0, ground_y, WIDTH, HEIGHT - ground_y))
            # Desenha faixas pretas laterais com logo e texto (se tiver espaço sobrando)
            desenhar_faixa_lateral(screen, WIDTH, HEIGHT, background_image, ceep_logo)

            # Player
            img_to_draw = None
            if gesture == "SHOT" and player_shoot_img:
                img_to_draw = player_shoot_img
            elif not on_ground and player_jump_img:
                img_to_draw = player_jump_img
            else:
                img_to_draw = walk_frames[current_walk_frame] if walk_frames else None

            if img_to_draw:
                screen.blit(img_to_draw, (player_x, player_y))
            else:
                color = (0, 200, 255) if gesture != "SHOT" else (255, 220, 0)
                pygame.draw.rect(screen, color, (player_x, player_y, player_w, player_h))

            # Partículas
            for p in dust_particles[:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["life"] -= 1
                if p["life"] <= 0:
                    dust_particles.remove(p)
                    continue
                pygame.draw.circle(screen, (200, 200, 200), (int(p["x"]), int(p["y"])), 3)

            # Tiros
            for b in bullets:
                pygame.draw.circle(screen, (255, 255, 0), (int(b["x"]), int(b["y"])), 5)

            # Obstáculos
            for o in obstacles:
                if obstacle_img:
                    screen.blit(obstacle_img, (o["x"], o["y"]))
                else:
                    pygame.draw.rect(screen, (0, 255, 100), (o["x"], o["y"], o["w"], o["h"]))

            # Inimigos
            for en in enemies:
                if enemy_img:
                    screen.blit(enemy_img, (en["x"], en["y"]))
                else:
                    pygame.draw.rect(screen, (255, 60, 60), (en["x"], en["y"], en["w"], en["h"]))

            # HUD
            screen.blit(font.render(f"Pontos: {score}", True, TEXT_COLOR_PRIMARY), (20, 20))
            screen.blit(font.render(f"Recorde: {record}", True, TEXT_COLOR_SECONDARY), (20, 50))
            screen.blit(font.render(f"Velocidade: {int(game_speed)}", True, TEXT_COLOR_SPEED), (20, 80))
            screen.blit(font.render(f"Gesto: {gesture if gesture else '-'}", True, TEXT_COLOR_GESTURE), (20, 110))

            # WEBCAM
            frame_h, frame_w = frame.shape[:2]
            target_w, target_h = cam_rect.width, cam_rect.height
            scale = min(target_w / frame_w, target_h / frame_h)
            draw_w = int(frame_w * scale)
            draw_h = int(frame_h * scale)
            frame_resized = cv2.resize(frame, (draw_w, draw_h))
            frame_rgb_small = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(frame_rgb_small.tobytes(), (draw_w, draw_h), "RGB")
            draw_x = cam_rect.x + (cam_rect.width - draw_w) // 2
            draw_y = cam_rect.y + (cam_rect.height - draw_h) // 2
            screen.blit(surf, (draw_x, draw_y))
            pygame.draw.rect(screen, (255, 255, 255), cam_rect, 2)

            pygame.display.flip()
    finally:
        try:
            salvar_config_cam(cam_rect)
        except:
            pass
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
