
import numpy as np
import cv2


TAMANHO_IMAGEM = (300, 300)


def _gerar_padrao_base(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)

    altura, largura = TAMANHO_IMAGEM
    y, x = np.mgrid[0:altura, 0:largura]

    # Parâmetros aleatórios (mas determinísticos por seed) que definem a "identidade" única do padrão de cristas.
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
    padrao = _gerar_padrao_base(seed)
    img = (padrao * 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return img


def simular_nova_captura(seed: int, ruido: float = 0.02) -> np.ndarray:
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
    return gerar_digital(seed_base + 12345)
