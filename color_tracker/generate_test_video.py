"""
generate_test_video.py
-----------------------
Gera um vídeo de teste com bolas coloridas se movendo,
para demonstrar o rastreador sem precisar de câmera ou vídeo externo.

Uso:
    python generate_test_video.py              # gera 'teste.mp4'
    python generate_test_video.py -o meu.mp4  # nome customizado
"""

import cv2
import numpy as np
import argparse
import math


def generate(output: str = "teste.mp4", duration_sec: int = 15, fps: int = 30):
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output, fourcc, fps, (width, height))

    total_frames = duration_sec * fps

    # Definição das bolas: (cor_BGR, posição_inicial, velocidade, raio, nome)
    balls = [
        {"bgr": (0, 0, 220),    "pos": [200, 200], "vel": [4.0,  2.5],  "r": 45, "name": "Vermelho"},
        {"bgr": (0, 200, 0),    "pos": [600, 400], "vel": [-3.5, 3.0],  "r": 40, "name": "Verde"},
        {"bgr": (220, 60, 0),   "pos": [900, 150], "vel": [2.0, -4.0],  "r": 50, "name": "Azul"},
        {"bgr": (0, 230, 230),  "pos": [400, 550], "vel": [5.0,  1.5],  "r": 35, "name": "Amarelo"},
        {"bgr": (0, 128, 255),  "pos": [1050, 400],"vel": [-4.5,-2.0],  "r": 38, "name": "Laranja"},
        {"bgr": (200, 0, 160),  "pos": [700, 300], "vel": [3.0,  4.5],  "r": 42, "name": "Roxo"},
    ]

    print(f"Gerando vídeo de teste: {output}")
    print(f"  Resolução : {width}×{height}  |  FPS : {fps}  |  Duração : {duration_sec}s")
    print(f"  Total frames : {total_frames}")

    for f in range(total_frames):
        # Fundo gradiente cinza escuro
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (30, 30, 30)

        # Grade discreta para dar profundidade
        for gx in range(0, width, 80):
            cv2.line(frame, (gx, 0), (gx, height), (40, 40, 40), 1)
        for gy in range(0, height, 80):
            cv2.line(frame, (0, gy), (width, gy), (40, 40, 40), 1)

        for ball in balls:
            cx, cy = ball["pos"]
            r = ball["r"]

            # Movimento senoidal suave para tornar a trajetória interessante
            t = f / fps
            cx_draw = int(cx + 30 * math.sin(t * 1.3 + r))
            cy_draw = int(cy + 20 * math.cos(t * 0.9 + r))

            # Atualizar posição base
            ball["pos"][0] += ball["vel"][0]
            ball["pos"][1] += ball["vel"][1]

            # Ricochete nas bordas
            if ball["pos"][0] - r < 0 or ball["pos"][0] + r > width:
                ball["vel"][0] *= -1
            if ball["pos"][1] - r < 0 or ball["pos"][1] + r > height:
                ball["vel"][1] *= -1

            # Sombra suave
            cv2.circle(frame, (cx_draw + 4, cy_draw + 4), r, (0, 0, 0), -1)

            # Bola principal (preenchida)
            cv2.circle(frame, (cx_draw, cy_draw), r, ball["bgr"], -1)

            # Reflexo interno (brilho)
            highlight_color = tuple(min(255, int(c * 1.6)) for c in ball["bgr"])
            cv2.circle(frame, (cx_draw - r // 4, cy_draw - r // 4), r // 4, highlight_color, -1)

            # Borda branca leve
            cv2.circle(frame, (cx_draw, cy_draw), r, (200, 200, 200), 1)

        # Carimbo de tempo e frame no canto
        cv2.putText(
            frame,
            f"Frame {f+1:04d}/{total_frames}  |  {f/fps:.2f}s",
            (10, height - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1,
        )

        writer.write(frame)

        if (f + 1) % fps == 0:
            print(f"  {f+1}/{total_frames} frames gerados...")

    writer.release()
    print(f"\nVídeo salvo em: {output}")
    print("\nPara rastrear, execute:")
    print(f"  python main.py {output} -c vermelho verde azul amarelo laranja roxo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera vídeo de teste com bolas coloridas")
    parser.add_argument("-o", "--output",   default="teste.mp4",   help="Arquivo de saída")
    parser.add_argument("--duration",       type=int, default=15,  help="Duração em segundos")
    parser.add_argument("--fps",            type=int, default=30,  help="Frames por segundo")
    args = parser.parse_args()
    generate(args.output, args.duration, args.fps)
