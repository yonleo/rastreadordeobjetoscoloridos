"""
image_processing.py
--------------------
Módulo de Processamento de Imagens (P.I.)

Implementa o pipeline completo frame a frame:

  Etapa 1 – Transformação de Cor   : BGR → HSV
  Etapa 2 – Limiarização           : máscara binária via inRange
  Etapa 3 – Filtragem Morfológica  : abertura (remove ruído) +
                                     fechamento (preenche buracos)
  Etapa 4 – Detecção de Contornos  : findContours
  Etapa 5 – Cálculo de Centróide   : momentos de imagem (M10/M00, M01/M00)
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from color_config import build_mask, COLOR_PROFILES


# ─────────────────────────────────────────────────────────────────────────────
# Kernels morfológicos (pré-calculados uma vez)
# ─────────────────────────────────────────────────────────────────────────────
_KERNEL_OPEN  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
_KERNEL_CLOSE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))


@dataclass
class DetectedObject:
    """Representa um objeto detectado em um único frame."""
    color_name : str
    contour    : np.ndarray
    centroid   : Tuple[int, int]      # (cx, cy)
    bbox       : Tuple[int, int, int, int]  # (x, y, w, h)
    area       : float


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────────────────────────────────────────

def process_frame(
    frame      : np.ndarray,
    colors     : List[str],
    min_area   : int = 800,
) -> Tuple[np.ndarray, List[DetectedObject], dict]:
    """
    Processa um único frame e retorna:
      - hsv_frame   : frame no espaço HSV (para debug/exibição)
      - detections  : lista de DetectedObject encontrados
      - masks       : dict {color_name: mask_binaria} (para debug/exibição)

    Pipeline de P.I.:
      1. BGR → HSV        (cv2.cvtColor)
      2. Limiarização     (cv2.inRange para cada cor selecionada)
      3. Filtragem morfo  (abertura → fechamento)
      4. Contornos        (cv2.findContours)
      5. Centróide        (cv2.moments)
    """

    # ── ETAPA 1: Transformação de Cor ─────────────────────────────────────
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    detections: List[DetectedObject] = []
    masks: dict = {}

    for color_name in colors:
        # ── ETAPA 2: Limiarização ─────────────────────────────────────────
        raw_mask = build_mask(hsv_frame, color_name)

        # ── ETAPA 3: Filtragem Morfológica ────────────────────────────────
        #   Abertura  = erosão  → dilatação  (elimina ruído de pequenos pontos)
        opened = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN,  _KERNEL_OPEN)
        #   Fechamento = dilatação → erosão  (preenche buracos internos)
        cleaned = cv2.morphologyEx(opened,   cv2.MORPH_CLOSE, _KERNEL_CLOSE)

        masks[color_name] = cleaned

        # ── ETAPA 4: Detecção de Contornos ────────────────────────────────
        contours, _ = cv2.findContours(
            cleaned,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue  # descarta regiões muito pequenas (ruído residual)

            # ── ETAPA 5: Cálculo de Centróide via Momentos ────────────────
            M  = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            x, y, w, h = cv2.boundingRect(cnt)

            detections.append(DetectedObject(
                color_name = color_name,
                contour    = cnt,
                centroid   = (cx, cy),
                bbox       = (x, y, w, h),
                area       = area,
            ))

    return hsv_frame, detections, masks


# ─────────────────────────────────────────────────────────────────────────────
# Funções de desenho
# ─────────────────────────────────────────────────────────────────────────────

def draw_detections(
    frame      : np.ndarray,
    detections : List[DetectedObject],
    trails     : dict,
) -> np.ndarray:
    """
    Desenha sobre o frame:
      • Contorno externo cheio na cor do objeto
      • Bounding box retangular
      • Ponto central (centróide)
      • Trilha histórica de posições do centróide
      • Rótulo com nome da cor e área
    """
    output = frame.copy()

    for obj in detections:
        bgr   = COLOR_PROFILES[obj.color_name]["bgr"]
        label = COLOR_PROFILES[obj.color_name]["label"]
        cx, cy = obj.centroid
        x, y, w, h = obj.bbox

        # — Contorno externo (cor correspondente ao objeto) —
        cv2.drawContours(output, [obj.contour], -1, bgr, 2)

        # — Preenchimento semi-transparente —
        overlay = output.copy()
        cv2.drawContours(overlay, [obj.contour], -1, bgr, -1)
        cv2.addWeighted(overlay, 0.18, output, 0.82, 0, output)

        # — Bounding box —
        cv2.rectangle(output, (x, y), (x + w, y + h), bgr, 1)

        # — Centróide —
        cv2.circle(output, (cx, cy), 6, bgr, -1)
        cv2.circle(output, (cx, cy), 8, (255, 255, 255), 1)

        # — Rótulo —
        text = f"{label}  {obj.area:.0f}px²"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        tx, ty = x, y - 8
        cv2.rectangle(output, (tx - 2, ty - th - 4), (tx + tw + 4, ty + 2), bgr, -1)
        cv2.putText(
            output, text, (tx, ty),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
        )

    # — Trilhas de centróide —
    for color_name, trail in trails.items():
        bgr = COLOR_PROFILES[color_name]["bgr"]
        pts = list(trail)
        for i in range(1, len(pts)):
            if pts[i - 1] is None or pts[i] is None:
                continue
            # Espessura e opacidade crescem em direção ao ponto mais recente
            thickness = max(1, int(3 * i / len(pts)))
            alpha     = i / len(pts)
            color_faded = tuple(int(c * alpha) for c in bgr)
            cv2.line(output, pts[i - 1], pts[i], color_faded, thickness)

    return output


def build_debug_panel(
    hsv_frame : np.ndarray,
    masks     : dict,
    panel_w   : int = 200,
) -> np.ndarray:
    """
    Monta um painel lateral de debug com:
      - Thumbnail do frame HSV
      - Máscara binária de cada cor rastreada
    """
    panels = []

    # Thumbnail HSV
    hsv_thumb = cv2.resize(hsv_frame, (panel_w, int(panel_w * hsv_frame.shape[0] / hsv_frame.shape[1])))
    label_bg  = np.zeros((18, panel_w, 3), dtype=np.uint8)
    cv2.putText(label_bg, "HSV", (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    panels.append(np.vstack([label_bg, hsv_thumb]))

    for color_name, mask in masks.items():
        h_thumb = int(panel_w * mask.shape[0] / mask.shape[1])
        thumb   = cv2.resize(mask, (panel_w, h_thumb))
        thumb3  = cv2.cvtColor(thumb, cv2.COLOR_GRAY2BGR)

        # Colorir máscara com a cor do perfil
        bgr = COLOR_PROFILES[color_name]["bgr"]
        colored = np.zeros_like(thumb3)
        colored[thumb > 0] = bgr
        thumb3 = cv2.addWeighted(thumb3, 0.4, colored, 0.6, 0)

        label_bg = np.zeros((18, panel_w, 3), dtype=np.uint8)
        cv2.putText(
            label_bg,
            COLOR_PROFILES[color_name]["label"],
            (4, 13),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, bgr, 1,
        )
        panels.append(np.vstack([label_bg, thumb3]))

    # Juntar todos os painéis verticalmente
    if not panels:
        return np.zeros((1, panel_w, 3), dtype=np.uint8)

    # Igualar larguras (pode haver diferença de 1px por arredondamento)
    max_w = max(p.shape[1] for p in panels)
    panels = [
        cv2.copyMakeBorder(p, 0, 0, 0, max_w - p.shape[1], cv2.BORDER_CONSTANT)
        for p in panels
    ]
    return np.vstack(panels)
