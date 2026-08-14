"""
biometria.py

Núcleo do sistema de reconhecimento biométrico.

Algoritmo utilizado: ORB (Oriented FAST and Rotated BRIEF)
- FAST: detecta pontos-chave (keypoints) de interesse em regiões de variação
  local de intensidade. Neste projeto, esses pontos são usados como
  características visuais genéricas; não se trata de um extrator dedicado de
  minúcias de sistemas AFIS.
- BRIEF: gera um descritor binário compacto para cada keypoint, permitindo
  comparação rápida.
- BFMatcher (Brute-Force Matcher) com distância de Hamming: compara os
  descritores de duas imagens e conta quantos pontos correspondem entre si.

ORB foi escolhido por sua eficiência computacional, pelo uso de descritores
binários e pela integração direta com o OpenCV. No contexto acadêmico deste
projeto, ele atua como um método de comparação de características locais em
imagens de alto contraste.

O grau de similaridade entre duas digitais é calculado como a proporção
de "bons matches" (distância de Hamming abaixo de um limiar) em relação
ao número de keypoints detectados. Um limiar (THRESHOLD_AUTENTICACAO)
decide se a autenticação é aceita ou rejeitada.
"""

import cv2
import numpy as np

THRESHOLD_AUTENTICACAO = 0.35  # proporção mínima de matches para aceitar
DISTANCIA_MAXIMA_MATCH = 40    # distância de Hamming máxima p/ considerar bom match

_orb = cv2.ORB_create(nfeatures=500)
_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


class DigitalInvalidaError(Exception):
    """Levantada quando não é possível extrair características da imagem."""


def extrair_caracteristicas(imagem: np.ndarray):
    """Extrai keypoints e descritores ORB de uma imagem de digital."""
    if imagem is None or imagem.size == 0:
        raise DigitalInvalidaError("Imagem de digital vazia ou inválida.")

    if len(imagem.shape) == 3:
        imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    keypoints, descritores = _orb.detectAndCompute(imagem, None)

    if descritores is None or len(keypoints) < 8:
        raise DigitalInvalidaError(
            "Não foi possível extrair características suficientes da digital "
            "(imagem com pouco contraste ou de baixa qualidade)."
        )
    return keypoints, descritores


def comparar_digitais(img_cadastrada: np.ndarray, img_tentativa: np.ndarray) -> float:
    """
    Compara duas imagens de digital e retorna um score de similaridade
    entre 0.0 (nenhuma semelhança) e 1.0 (idêntica).
    """
    try:
        kp1, desc1 = extrair_caracteristicas(img_cadastrada)
        kp2, desc2 = extrair_caracteristicas(img_tentativa)
    except DigitalInvalidaError:
        return 0.0

    matches = _matcher.match(desc1, desc2)
    if not matches:
        return 0.0

    bons_matches = [m for m in matches if m.distance < DISTANCIA_MAXIMA_MATCH]

    menor_n_keypoints = min(len(kp1), len(kp2))
    if menor_n_keypoints == 0:
        return 0.0

    score = len(bons_matches) / menor_n_keypoints
    return min(score, 1.0)


def autenticar(imagem_tentativa: np.ndarray, candidatos: list):
    """
    Compara a imagem de tentativa contra uma lista de candidatos cadastrados.

    candidatos: lista de tuplas (usuario_id, nome, imagem_cadastrada)

    Retorna (usuario_id, nome, score) do melhor candidato SE o score
    ultrapassar o THRESHOLD_AUTENTICACAO; caso contrário retorna None.
    """
    melhor = None
    melhor_score = 0.0

    for usuario_id, nome, img_cadastrada in candidatos:
        score = comparar_digitais(img_cadastrada, imagem_tentativa)
        if score > melhor_score:
            melhor_score = score
            melhor = (usuario_id, nome, score)

    if melhor and melhor_score >= THRESHOLD_AUTENTICACAO:
        return melhor
    return None
