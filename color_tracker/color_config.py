"""
color_config.py
---------------
Perfis de cor no espaço HSV para rastreamento.

OpenCV usa HSV com:
  H : 0–179
  S : 0–255
  V : 0–255

Cada perfil contém:
  - ranges  : lista de [(lower, upper), ...] — suporta cores que "envolvem"
              o cilindro HSV (ex.: vermelho passa por H=0 e H=179)
  - bgr     : cor BGR para desenho dos contornos/texto
  - label   : nome exibido na tela
"""

import numpy as np

# Estrutura de cada perfil:
# "nome": {
#     "ranges": [( np.array([H, S, V]), np.array([H, S, V]) ), ...],
#     "bgr"   : (B, G, R),
#     "label" : "Rótulo",
# }

COLOR_PROFILES = {
    # ── Vermelho (dois intervalos: perto de 0° e de 180°) ──────────────────
    "vermelho": {
        "ranges": [
            (np.array([0,   120, 70]),  np.array([10,  255, 255])),
            (np.array([165, 120, 70]),  np.array([179, 255, 255])),
        ],
        "bgr"  : (0, 0, 220),
        "label": "Vermelho",
    },

    # ── Laranja ────────────────────────────────────────────────────────────
    "laranja": {
        "ranges": [
            (np.array([10, 150, 100]), np.array([25, 255, 255])),
        ],
        "bgr"  : (0, 128, 255),
        "label": "Laranja",
    },

    # ── Amarelo ────────────────────────────────────────────────────────────
    "amarelo": {
        "ranges": [
            (np.array([22, 130, 100]), np.array([38, 255, 255])),
        ],
        "bgr"  : (0, 230, 230),
        "label": "Amarelo",
    },

    # ── Verde ──────────────────────────────────────────────────────────────
    "verde": {
        "ranges": [
            (np.array([38, 80, 60]),  np.array([85, 255, 255])),
        ],
        "bgr"  : (0, 200, 0),
        "label": "Verde",
    },

    # ── Ciano / Turquesa ───────────────────────────────────────────────────
    "ciano": {
        "ranges": [
            (np.array([85,  80, 60]),  np.array([100, 255, 255])),
        ],
        "bgr"  : (200, 200, 0),
        "label": "Ciano",
    },

    # ── Azul ───────────────────────────────────────────────────────────────
    "azul": {
        "ranges": [
            (np.array([100, 100, 60]),  np.array([130, 255, 255])),
        ],
        "bgr"  : (220, 60, 0),
        "label": "Azul",
    },

    # ── Roxo / Violeta ─────────────────────────────────────────────────────
    "roxo": {
        "ranges": [
            (np.array([130, 80, 50]),  np.array([155, 255, 255])),
        ],
        "bgr"  : (200, 0, 160),
        "label": "Roxo",
    },

    # ── Rosa / Magenta ─────────────────────────────────────────────────────
    "rosa": {
        "ranges": [
            (np.array([155, 80, 60]),  np.array([170, 255, 255])),
        ],
        "bgr"  : (180, 60, 220),
        "label": "Rosa",
    },

    # ── Branco ─────────────────────────────────────────────────────────────
    "branco": {
        "ranges": [
            (np.array([0,   0,  200]), np.array([179, 40, 255])),
        ],
        "bgr"  : (200, 200, 200),
        "label": "Branco",
    },

    # ── Preto ──────────────────────────────────────────────────────────────
    "preto": {
        "ranges": [
            (np.array([0, 0, 0]),  np.array([179, 255, 50])),
        ],
        "bgr"  : (60, 60, 60),
        "label": "Preto",
    },
}


def list_colors():
    """Imprime no terminal as cores disponíveis de forma formatada."""
    print("\n  Cores disponíveis para rastreamento:")
    print("  " + "─" * 38)
    for key, profile in COLOR_PROFILES.items():
        b, g, r = profile["bgr"]
        print(f"   • {key:<12}  ({profile['label']})")
    print("  " + "─" * 38)


def build_mask(hsv_frame: "np.ndarray", color_name: str) -> "np.ndarray":
    """
    Retorna a máscara binária combinada para a cor solicitada,
    aplicando todos os sub-intervalos HSV do perfil.
    """
    import cv2
    profile = COLOR_PROFILES[color_name]
    mask = None
    for lower, upper in profile["ranges"]:
        m = cv2.inRange(hsv_frame, lower, upper)
        mask = m if mask is None else cv2.bitwise_or(mask, m)
    return mask
