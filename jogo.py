import pygame
import random
import sys
import json
import os

# =============================================================================
# 1. INICIALIZAÇÃO E CONFIGURAÇÕES GERAIS
# =============================================================================

pygame.init()
pygame.mixer.init()

# Configurações da tela
largura, altura = 800, 700
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Corrida Urbana")

# Paleta de Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (50, 50, 50)
AMARELO = (255, 255, 0)
VERMELHO = (200, 0, 0)
FAIXA_CLARA = (255, 255, 150)
VERDE_ATIVO = (100, 255, 100)
AZUL_BOTAO = (0, 150, 255)
AZUL_BOTAO_HOVER = (0, 180, 255)
VERMELHO_BOTAO = (255, 50, 50)
VERMELHO_BOTAO_HOVER = (255, 80, 80)
LARANJA_BOTAO = (255, 165, 0)
LARANJA_BOTAO_HOVER = (255, 200, 0)

# Fontes (com fallback para a fonte padrão)
try:
    fonte = pygame.font.SysFont("Verdana", 30)
    fonte_titulo = pygame.font.SysFont("Verdana", 60, bold=True)
    fonte_botao = pygame.font.SysFont("Verdana", 35, bold=True)
    fonte_input = pygame.font.SysFont("Verdana", 30)
    fonte_ranking = pygame.font.SysFont("Verdana", 20)
except pygame.error:
    fonte = pygame.font.Font(None, 40)
    fonte_titulo = pygame.font.Font(None, 70)
    fonte_botao = pygame.font.Font(None, 45)
    fonte_input = pygame.font.Font(None, 40)
    fonte_ranking = pygame.font.Font(None, 30)

# =============================================================================
# 2. FUNÇÕES AUXILIARES (CARREGAMENTO DE ARQUIVOS, ETC.)
# =============================================================================

def carregar_imagem(caminho, dimensoes=None):
    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        if dimensoes:
            imagem = pygame.transform.scale(imagem, dimensoes)
        return imagem
    except pygame.error as e:
        print(f"Erro ao carregar imagem: {caminho} - {e}")
        superficie_erro = pygame.Surface(dimensoes if dimensoes else (50, 50))
        superficie_erro.fill(VERMELHO)
        return superficie_erro

def carregar_som(caminho):
    try:
        return pygame.mixer.Sound(caminho)
    except pygame.error as e:
        print(f"Erro ao carregar som: {caminho} - {e}")
        return None

# =============================================================================
# 3. CARREGAMENTO DOS RECURSOS DO JOGO (ASSETS)
# =============================================================================

moto_largura, moto_altura = 80, 200
moto_img = carregar_imagem("imagens/moto.png", (moto_largura, moto_altura))

fundo_menu = carregar_imagem("imagens/fundo_menu.png", (largura, altura))
moeda_img = carregar_imagem("imagens/moeda.png", (50, 50))
cidade_esq = carregar_imagem("imagens/cidade_esq.png", (120, altura))
cidade_dir = carregar_imagem("imagens/cidade_dir.png", (120, altura))

obstaculo_tipos = {
    "carro_azul_corrida": {"img": carregar_imagem("imagens/carro_azul_corrida.png", (180, 130))},
    "carro_policia": {"img": carregar_imagem("imagens/carro_policia.png", (180, 130))},
    "carro_verde_agua_aberto": {"img": carregar_imagem("imagens/carro_verde_agua_aberto.png", (180, 130))},
    "carro_verde_agua_fechado": {"img": carregar_imagem("imagens/carro_verde_agua_fechado.png", (180, 130))},
    "carro_vermelho": {"img": carregar_imagem("imagens/carro_vermelho.png", (180, 130))},
    "carro_amarelo": {"img": carregar_imagem("imagens/carro_amarelo.png", (180, 130))},
    "cone": {"img": carregar_imagem("imagens/cone.png", (80, 100))},
    "buraco": {"img": carregar_imagem("imagens/buraco.png", (100, 100))},
}

buzina_som = carregar_som("sons/buzina.wav")
crash_som = carregar_som("sons/crash.wav")
coin_som = carregar_som("sons/coin.wav")
musica_menu = "sons/musica_menu.mp3"
musica_fundo = "sons/musica_fundo.mp3"

# =============================================================================
# 4. CLASSES E LÓGICA DO JOGO
# =============================================================================

ranking = []
def carregar_ranking():
    global ranking
    try:
        with open("ranking.json", "r") as f:
            ranking = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ranking = []

def salvar_ranking():
    with open("ranking.json", "w") as f:
        json.dump(ranking, f)

def mostrar_texto(texto, fonte_obj, cor, x, y, centralizar=True):
    render = fonte_obj.render(texto, True, cor)
    rect = render.get_rect(center=(x, y)) if centralizar else render.get_rect(topleft=(x, y))
    tela.blit(render, rect)
    return rect

def tocar_musica(caminho_musica):
    try:
        pygame.mixer.music.load(caminho_musica)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.5)
    except pygame.error as e:
        print(f"Erro ao tocar música {caminho_musica}: {e}")

class Obstaculo:
    def __init__(self, tipo):
        propriedades = obstaculo_tipos[tipo]
        self.img = propriedades["img"]
        self.largura = self.img.get_width()
        self.altura = self.img.get_height()
        self.x = random.randint(120, largura - 120 - self.largura)
        self.y = -self.altura

    def desenhar(self):
        tela.blit(self.img, (self.x, self.y))

    def colidiu_com(self, moto_rect):
        obstaculo_hitbox = pygame.Rect(self.x + 45, self.y, self.largura - 90, self.altura)
        return moto_rect.colliderect(obstaculo_hitbox)

class PowerUp:
    def __init__(self):
        self.img = moeda_img
        self.largura = self.img.get_width()
        self.altura = self.img.get_height()
        self.x = random.randint(120, largura - 120 - self.largura)
        self.y = -self.altura
        self.valor = 50

    def desenhar(self):
        tela.blit(self.img, (self.x, self.y))
        
    def colidiu_com(self, moto_rect):
        powerup_rect = pygame.Rect(self.x, self.y, self.largura, self.altura)
        return moto_rect.colliderect(powerup_rect)

# =============================================================================
# 5. TELAS DO JOGO (MENUS)
# =============================================================================

def tela_gameover(nome, pontuacao):
    global ranking
    ranking.append({"nome": nome, "pontos": pontuacao})
    ranking = sorted(ranking, key=lambda x: x["pontos"], reverse=True)[:5]
    salvar_ranking()
    pygame.mixer.music.stop()
    if crash_som: crash_som.play()
    esperando = True
    while esperando:
        tela.fill(PRETO)
        mostrar_texto("GAME OVER", fonte_titulo, VERMELHO, largura//2, 150)
        mostrar_texto(f"{nome}: {pontuacao} pontos", fonte, BRANCO, largura//2, 250)
        mostrar_texto("Pressione R para Reiniciar", fonte, AMARELO, largura//2, 350)
        mostrar_texto("Pressione M para voltar ao Menu", fonte, AMARELO, largura//2, 400)
        mostrar_texto("RANKING TOP 5", fonte_titulo, AMARELO, largura//2, 500)
        for i, jogador in enumerate(ranking):
            mostrar_texto(f"{i+1}. {jogador['nome']} - {jogador['pontos']}", fonte_ranking, BRANCO, largura//2, 560 + i*30)
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_r:
                    main_loop(nome)
                if evento.key == pygame.K_m:
                    tela_inicial()

def tela_tutorial():
    rodando = True
    while rodando:
        tela.blit(fundo_menu, (0,0))
        mostrar_texto("TUTORIAL", fonte_titulo, BRANCO, largura//2, 100)
        mostrar_texto("Use SETAS ou A/D para mover a moto", fonte, BRANCO, largura//2, 250)
        mostrar_texto("Desvie dos obstáculos para sobreviver", fonte, BRANCO, largura//2, 300)
        mostrar_texto("Colete moedas para pontos extras!", fonte, AMARELO, largura//2, 350)
        mostrar_texto("Pressione P para pausar o jogo", fonte, BRANCO, largura//2, 400)
        mostrar_texto("Pressione ESC para voltar ao menu", fonte, BRANCO, largura//2, 500)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
        pygame.display.update()

def tela_pausa():
    pygame.mixer.music.pause()
    pausado = True
    while pausado:
        tela.fill(PRETO)
        mostrar_texto("JOGO PAUSADO", fonte_titulo, AMARELO, largura // 2, altura // 2 - 50)
        mostrar_texto("Pressione P para continuar", fonte, BRANCO, largura // 2, altura // 2 + 50)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_p:
                    pausado = False
        pygame.display.update()
    pygame.mixer.music.unpause()

def tela_inicial():
    carregar_ranking()
    tocar_musica(musica_menu)
    rodando = True
    nome_jogador = ""
    input_ativo = False
    while rodando:
        tela.blit(fundo_menu, (0,0))
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mostrar_texto("CORRIDA URBANA", fonte_titulo, AMARELO, largura//2, 80)
        input_rect = pygame.Rect(largura//2 - 150, 180, 300, 50)
        cor_input = VERDE_ATIVO if input_ativo else BRANCO
        pygame.draw.rect(tela, CINZA, input_rect, border_radius=5)
        pygame.draw.rect(tela, cor_input, input_rect, 2, border_radius=5)
        mostrar_texto(nome_jogador, fonte_input, BRANCO, largura//2, 205)
        if not nome_jogador and not input_ativo:
            mostrar_texto("Digite seu nome", fonte_input, (150, 150, 150), largura//2, 205)
        botoes = [
            {"texto": "INICIAR JOGO", "y": 260, "acao": "iniciar", "cor_normal": AZUL_BOTAO, "cor_hover": AZUL_BOTAO_HOVER},
            {"texto": "COMO JOGAR", "y": 330, "acao": "tutorial", "cor_normal": LARANJA_BOTAO, "cor_hover": LARANJA_BOTAO_HOVER},
            {"texto": "SAIR", "y": 400, "acao": "sair", "cor_normal": VERMELHO_BOTAO, "cor_hover": VERMELHO_BOTAO_HOVER}
        ]
        for botao in botoes:
            rect = pygame.Rect(largura//2 - 135, botao["y"], 270, 60)
            cor = botao["cor_hover"] if rect.collidepoint(mouse_x, mouse_y) else botao["cor_normal"]
            pygame.draw.rect(tela, cor, rect, border_radius=15)
            mostrar_texto(botao["texto"], fonte_botao, PRETO, largura//2, botao["y"] + 30)
        mostrar_texto("RANKING TOP 5", fonte, AMARELO, largura//2, 530)
        for i, jogador in enumerate(ranking):
            mostrar_texto(f"{i+1}. {jogador['nome']} - {jogador['pontos']}", fonte_ranking, BRANCO, largura//2, 570 + i*30)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                input_ativo = input_rect.collidepoint(evento.pos)
                for botao in botoes:
                    rect = pygame.Rect(largura//2 - 135, botao["y"], 270, 60)
                    if rect.collidepoint(evento.pos):
                        if botao["acao"] == "iniciar" and nome_jogador.strip() != "":
                            main_loop(nome_jogador.strip())
                        elif botao["acao"] == "tutorial":
                            tela_tutorial()
                        elif botao["acao"] == "sair":
                            pygame.quit()
                            sys.exit()
            if evento.type == pygame.KEYDOWN and input_ativo:
                if evento.key == pygame.K_BACKSPACE:
                    nome_jogador = nome_jogador[:-1]
                elif evento.key == pygame.K_RETURN and nome_jogador.strip() != "":
                    main_loop(nome_jogador.strip())
                else:
                    if len(nome_jogador) < 12:
                        nome_jogador += evento.unicode
        pygame.display.update()

# =============================================================================
# 6. LOOP PRINCIPAL DO JOGO
# =============================================================================

def main_loop(nome):
    tocar_musica(musica_fundo)
    moto_x = largura // 2 - moto_largura // 2
    moto_y = altura - moto_altura - 10
    velocidade_moto = 5
    pontuacao = 0
    dificuldade = 0
    obstaculos = []
    powerups = []
    derrapadas = []
    clock = pygame.time.Clock()
    tempo_ultimo_obstaculo = pygame.time.get_ticks()
    tempo_ultimo_powerup = pygame.time.get_ticks()
    intervalo_obstaculo = 1200
    intervalo_powerup = 5000
    faixa_offset = 0
    rodando = True
    while rodando:
        tela.fill(CINZA)
        tela.blit(cidade_esq, (0, 0))
        tela.blit(cidade_dir, (largura - 120, 0))
        road_speed = 5 + dificuldade
        faixa_altura, faixa_espaco = 60, 40
        faixa_offset = (faixa_offset + road_speed) % (faixa_altura + faixa_espaco)
        for i in range(-faixa_altura, altura, faixa_altura + faixa_espaco):
            pygame.draw.rect(tela, FAIXA_CLARA, (largura//2 - 5, i - faixa_offset, 10, faixa_altura))
        for x, y in derrapadas:
            pygame.draw.rect(tela, PRETO, (x, y, 5, 15))

        # --- Ordem de Desenho (do fundo para a frente) ---
        for powerup in powerups:
            powerup.desenhar()

        for obstaculo in obstaculos:
            obstaculo.desenhar()

        tela.blit(moto_img, (moto_x, moto_y))
        
        # --- Loop de Eventos (input do jogador) ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE and buzina_som:
                    buzina_som.play()
                if evento.key == pygame.K_p:
                    tela_pausa()
        
        # --- Lógica de Movimento do Jogador ---
        teclas = pygame.key.get_pressed()
        moto_movida = False
        if (teclas[pygame.K_LEFT] or teclas[pygame.K_a]) and moto_x > 120:
            moto_x -= velocidade_moto
            moto_movida = True
        if (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) and moto_x < largura - 120 - moto_largura:
            moto_x += velocidade_moto
            moto_movida = True
        if moto_movida:
            derrapadas.append((moto_x + moto_largura // 2, moto_y + moto_altura - 20))
            derrapadas = derrapadas[-50:]
        derrapadas = [(x, y + road_speed) for x, y in derrapadas if y < altura]

        # --- Geração de Obstáculos e Power-ups ---
        agora = pygame.time.get_ticks()
        if agora - tempo_ultimo_obstaculo > intervalo_obstaculo:
            tipos_disponiveis = list(obstaculo_tipos.keys())
            if tipos_disponiveis:
                tipo_escolhido = random.choice(tipos_disponiveis)
                obstaculos.append(Obstaculo(tipo_escolhido))
            tempo_ultimo_obstaculo = agora
        if agora - tempo_ultimo_powerup > intervalo_powerup:
            powerups.append(PowerUp())
            tempo_ultimo_powerup = agora
        
        # --- Lógica de Colisão e Atualização dos Objetos ---
        # Hitbox da moto SUPER FINA, focada apenas no centro.
        moto_hitbox = pygame.Rect(moto_x + 30, moto_y + 30, moto_largura - 60, moto_altura - 60)
        
        # Atualiza a posição de cada obstáculo
        for obstaculo in obstaculos[:]:
            obstaculo.y += road_speed
            if obstaculo.y > altura:
                obstaculos.remove(obstaculo)
                pontuacao += 10
            if obstaculo.colidiu_com(moto_hitbox):
                tela_gameover(nome, pontuacao)
                return

        # Atualiza a posição de cada power-up
        for powerup in powerups[:]:
            powerup.y += road_speed
            if powerup.y > altura:
                powerups.remove(powerup)
            if powerup.colidiu_com(moto_hitbox):
                if coin_som: coin_som.play()
                pontuacao += powerup.valor
                powerups.remove(powerup)

        # --- Sistema de Pontuação e Dificuldade ---
        pontuacao += 1
        if pontuacao > 0 and pontuacao % 1000 == 0:
            dificuldade += 1
            intervalo_obstaculo = max(400, intervalo_obstaculo - 100)
            velocidade_moto = min(10, velocidade_moto + 1)
        
        # --- Exibição de Informações (HUD) ---
        mostrar_texto(f"Pontos: {pontuacao}", fonte, BRANCO, 10, 10, centralizar=False)
        mostrar_texto(f"Nível: {dificuldade + 1}", fonte, BRANCO, largura - 150, 10, centralizar=False)

        # --- Atualização Final da Tela ---
        pygame.display.update()
        clock.tick(60)

# =============================================================================
# 7. PONTO DE ENTRADA DO PROGRAMA
# =============================================================================

if __name__ == "__main__":
    tela_inicial()