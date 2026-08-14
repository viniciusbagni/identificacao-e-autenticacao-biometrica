"""
gerador_digitais.py

Este módulo é responsável por SIMULAR a captura de uma impressão digital.

Justificativa (ver relatório, seção de Aportes Teóricos):
Por não haver leitor biométrico físico disponível para o desenvolvimento
deste trabalho, optou-se por gerar imagens sintéticas que reproduzem o
padrão visual simplificado de cristas, inspirado em impressões digitais,
por meio da sobreposição de funções senoidais moduladas em
frequência e fase, com ruído gaussiano para simular variações de pressão
e textura de pele.

Cada usuário possui uma "semente" (seed) única, que gera um padrão de
cristas exclusivo e determinístico para fins de simulação. Esse padrão não
representa a unicidade biométrica de uma impressão digital humana real. O módulo também simula uma NOVA CAPTURA da
mesma digital (por exemplo, no momento da autenticação), aplicando
pequenas distorções geométricas e ruído, assim como aconteceria em
capturas reais consecutivas do mesmo dedo em um leitor óptico.

A arquitetura foi desenhada de forma que a troca por imagens reais
(arquivos de um dataset público, ou capturadas por scanner/câmera) exija
apenas substituir a origem da imagem -- o restante do pipeline
(pré-processamento, extração de características e comparação, em
biometria.py) permanece o mesmo.
"""

import numpy as np
import cv2


TAMANHO_IMAGEM = (300, 300)


def _gerar_padrao_base(seed: int) -> np.ndarray:
    """Gera o padrão de cristas papilares determinístico para uma seed."""
    rng = np.random.default_rng(seed)

    altura, largura = TAMANHO_IMAGEM
    y, x = np.mgrid[0:altura, 0:largura]

    # Parâmetros aleatórios (mas determinísticos por seed) que definem
    # a "identidade" única do padrão de cristas.
    freq_x = rng.uniform(0.08, 0.16)
    freq_y = rng.uniform(0.08, 0.16)
    fase = rng.uniform(0, 2 * np.pi)
    angulo = rng.uniform(0, np.pi)

    # Rotaciona o sistema de coordenadas para variar a orientação das cristas
    xr = x * np.cos(angulo) - y * np.sin(angulo)
    yr = x * np.sin(angulo) + y * np.cos(angulo)

    # Combinação de senoides simulando cristas + pequenas "minúcias"
    padrao = np.sin(freq_x * xr + fase) + np.sin(freq_y * yr + fase * 0.5)

    # Adiciona pontos de "singularidade" (simulando núcleos/deltas da digital)
    n_singularidades = rng.integers(3, 7)
    for _ in range(n_singularidades):
        cx, cy = rng.uniform(40, largura - 40), rng.uniform(40, altura - 40)
        raio = rng.uniform(20, 45)
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        padrao += 0.6 * np.sin(dist / raio * np.pi)

    padrao = (padrao - padrao.min()) / (padrao.max() - padrao.min())
    return padrao


def gerar_digital(seed: int) -> np.ndarray:
    """Gera a imagem 'original' cadastrada para um usuário (enrollment)."""
    padrao = _gerar_padrao_base(seed)
    img = (padrao * 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return img


def simular_nova_captura(seed: int, ruido: float = 0.02) -> np.ndarray:
    """
    Simula uma NOVA captura da mesma digital (ex: no momento do login),
    aplicando pequena rotação/translação e ruído -- assim como aconteceria
    numa leitura real do mesmo dedo em momentos diferentes.
    """
    padrao = _gerar_padrao_base(seed)
    img = (padrao * 255).astype(np.uint8)

    altura, largura = img.shape
    rng = np.random.default_rng(seed + 999)

    # pequena rotação/translação para simular reposicionamento do dedo
    angulo_graus = rng.uniform(-4, 4)
    dx, dy = rng.uniform(-4, 4), rng.uniform(-4, 4)
    M = cv2.getRotationMatrix2D((largura / 2, altura / 2), angulo_graus, 1.0)
    M[0, 2] += dx
    M[1, 2] += dy
    img = cv2.warpAffine(img, M, (largura, altura), borderValue=255)

    ruido_arr = rng.normal(0, ruido * 255, img.shape)
    img = np.clip(img.astype(np.float32) + ruido_arr, 0, 255).astype(np.uint8)

    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return img


def gerar_digital_impostor(seed_base: int) -> np.ndarray:
    """Gera uma digital de outra 'pessoa' qualquer, para testes de rejeição."""
    return gerar_digital(seed_base + 12345)
