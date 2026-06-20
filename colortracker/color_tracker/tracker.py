"""
tracker.py
----------
Classe principal ColorTracker.

Responsabilidades:
  • Abrir a fonte de vídeo (arquivo ou webcam)
  • Gerenciar o histórico de trilhas por cor (deque)
  • Chamar o pipeline de P.I. a cada frame
  • Renderizar a janela principal e o painel de debug
  • Tratar teclas de atalho e gravar saída opcional
"""

import cv2
from collections import defaultdict, deque
from pathlib import Path
from typing import List, Union, Optional

from color_config import COLOR_PROFILES
from image_processing import process_frame, draw_detections


class ColorTracker:
    """
    Rastreador de objetos coloridos baseado em visão computacional.

    Parâmetros
    ----------
    source       : caminho para arquivo de vídeo ou índice da câmera (int)
    colors       : lista de nomes de cores a rastrear
    output_path  : caminho para salvar o vídeo processado (None = sem gravação)
    trail_length : número de frames que a trilha do centróide persiste
    min_area     : área mínima (px²) para considerar um contorno como objeto
    """

    WINDOW_MAIN  = "Rastreador de Objetos Coloridos"
    WINDOW_DEBUG = "Debug  |  HSV + Mascaras"

    def __init__(
        self,
        source      : Union[str, int],
        colors      : List[str],
        output_path : Optional[str] = None,
        trail_length: int = 40,
        min_area    : int = 800,
    ):
        self.source       = source
        self.colors       = colors
        self.output_path  = output_path
        self.trail_length = trail_length
        self.min_area     = min_area

        # Histórico de centróides por cor  →  {color_name: deque([(cx,cy), ...])}
        self.trails: dict = defaultdict(lambda: deque(maxlen=trail_length))

        # Escritor de vídeo (inicializado após abrir o cap)
        self.writer: Optional[cv2.VideoWriter] = None

        # Contadores para estatísticas na tela
        self.frame_count = 0

    # ─────────────────────────────────────────────────────────────────────
    # Loop principal
    # ─────────────────────────────────────────────────────────────────────

    def run(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a fonte de vídeo: {self.source}")

        fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 0 para webcam

        print(f"  Resolução : {width}×{height}  |  FPS : {fps:.1f}"
              f"  |  Total frames : {total if total > 0 else '∞'}")

        # Inicializar gravação de saída
        if self.output_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
            print(f"  Gravando em   : {self.output_path}")

        cv2.namedWindow(self.WINDOW_MAIN, cv2.WINDOW_NORMAL)

        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            self.frame_count += 1

            # ── Pipeline de Processamento de Imagens ──────────────────────
            hsv_frame, detections, masks = process_frame(
                frame, self.colors, self.min_area
            )

            # ── Atualizar trilhas ─────────────────────────────────────────
            # Registra centróide mais recente de cada cor detectada
            detected_colors = set()
            for obj in detections:
                self.trails[obj.color_name].append(obj.centroid)
                detected_colors.add(obj.color_name)

            # Cores não detectadas neste frame: insere None para "quebrar" trilha
            for color in self.colors:
                if color not in detected_colors:
                    if self.trails[color]:  # só insere se já teve histórico
                        self.trails[color].append(None)

            # ── Renderização ──────────────────────────────────────────────
            output = draw_detections(frame, detections, self.trails)
            output = self._draw_hud(output, detections, fps, total)
            cv2.imshow(self.WINDOW_MAIN, output)

            # ── Gravação do frame processado (sem painel de debug) ────────
            if self.writer:
                self.writer.write(output)

            # ── Teclas de controle ────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:          # Q / ESC → sair
                print("\n  Encerrado pelo usuário.")
                break
            elif key == ord("s"):                      # S → salvar frame
                name = f"frame_{self.frame_count:05d}.png"
                cv2.imwrite(name, output)
                saved_count += 1
                print(f"  Frame salvo: {name}")

        cap.release()
        if self.writer:
            self.writer.release()
        cv2.destroyAllWindows()

        print(f"\n  Frames processados : {self.frame_count}")
        if saved_count:
            print(f"  Frames salvos      : {saved_count}")

    # ─────────────────────────────────────────────────────────────────────
    # HUD (Heads-Up Display)
    # ─────────────────────────────────────────────────────────────────────

    def _draw_hud(
        self,
        frame      : np.ndarray,
        detections : list,
        fps        : float,
        total      : int,
    ) -> np.ndarray:
        """Desenha informações de telemetria no canto superior esquerdo."""
        h, w = frame.shape[:2]

        # Fundo semitransparente para o HUD
        hud_h = 22 + 20 * (len(self.colors) + 1)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (260, hud_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        y = 18
        progress = f"{self.frame_count}/{total}" if total > 0 else f"{self.frame_count}"
        cv2.putText(
            frame,
            f"Frame: {progress}   FPS: {fps:.0f}",
            (8, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA,
        )

        # Contagem de objetos por cor
        count_per_color = {c: 0 for c in self.colors}
        for obj in detections:
            count_per_color[obj.color_name] += 1

        for color_name in self.colors:
            y += 20
            bgr   = COLOR_PROFILES[color_name]["bgr"]
            label = COLOR_PROFILES[color_name]["label"]
            n     = count_per_color[color_name]
            dot_color = bgr if n > 0 else (60, 60, 60)
            cv2.circle(frame, (14, y - 4), 5, dot_color, -1)
            cv2.putText(
                frame,
                f"{label}: {n} objeto{'s' if n != 1 else ''}",
                (25, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                (220, 220, 220) if n > 0 else (90, 90, 90),
                1, cv2.LINE_AA,
            )

        # Legenda de teclas no canto inferior
        cv2.putText(
            frame,
            "Q/ESC: sair  |  S: salvar frame",
            (8, h - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1, cv2.LINE_AA,
        )

        return frame
