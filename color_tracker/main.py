"""
============================================================
  Rastreador de Objetos Coloridos em Vídeo
  Processamento de Imagens - Projeto Final
============================================================
  Pipeline:
    1. Transformação de Cor  (BGR → HSV)
    2. Limiarização          (inRange por faixa HSV)
    3. Filtragem Morfológica (abertura + fechamento)
    4. Rastreamento de Centróide
============================================================
"""

import argparse
import sys
from pathlib import Path

from tracker import ColorTracker
from color_config import COLOR_PROFILES, list_colors
from utils import banner


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rastreador de Objetos Coloridos em Vídeo",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "video",
        nargs="?",
        default=None,
        help="Caminho para o vídeo de entrada (omita para usar webcam)",
    )
    parser.add_argument(
        "-c",
        "--colors",
        nargs="+",
        metavar="COR",
        help=(
            "Cores a rastrear. Disponíveis:\n"
            + ", ".join(COLOR_PROFILES.keys())
            + "\nExemplo: -c vermelho azul amarelo"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="ARQUIVO",
        help="Salvar vídeo processado neste caminho (ex: resultado.mp4)",
    )
    parser.add_argument(
        "--trail",
        type=int,
        default=40,
        metavar="N",
        help="Comprimento da trilha do centróide em frames (padrão: 40)",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=800,
        metavar="PX²",
        help="Área mínima do contorno para ser considerado objeto (padrão: 800)",
    )
    parser.add_argument(
        "--list-colors",
        action="store_true",
        help="Listar todas as cores disponíveis e sair",
    )
    return parser.parse_args()


def interactive_color_selection():
    """Permite ao usuário escolher cores interativamente no terminal."""
    print("\n" + "═" * 50)
    print("  SELEÇÃO INTERATIVA DE CORES")
    print("═" * 50)
    list_colors()
    print("\nDigite as cores separadas por espaço:")
    print("Exemplo: vermelho azul amarelo")
    raw = input("→ ").strip().lower()
    chosen = [c.strip() for c in raw.split() if c.strip()]
    return chosen


def main():
    banner()
    args = parse_args()

    if args.list_colors:
        list_colors()
        sys.exit(0)

    # ---------- Seleção de cores ----------
    if args.colors:
        chosen_colors = [c.lower() for c in args.colors]
    else:
        chosen_colors = interactive_color_selection()

    # Validar cores escolhidas
    invalid = [c for c in chosen_colors if c not in COLOR_PROFILES]
    if invalid:
        print(f"\n[ERRO] Cores não reconhecidas: {', '.join(invalid)}")
        print("Use --list-colors para ver as opções disponíveis.")
        sys.exit(1)

    if not chosen_colors:
        print("[ERRO] Nenhuma cor selecionada.")
        sys.exit(1)

    # ---------- Fonte de vídeo ----------
    if args.video:
        source_path = Path(args.video)
        if not source_path.exists():
            print(f"[ERRO] Arquivo não encontrado: {args.video}")
            sys.exit(1)
        source = str(source_path)
    else:
        source = 0  # webcam

    print(f"\n{'═'*50}")
    print(f"  Cores selecionadas : {', '.join(chosen_colors)}")
    print(f"  Fonte              : {'webcam' if source == 0 else source}")
    print(f"  Saída              : {args.output or 'apenas exibição'}")
    print(f"  Trilha (frames)    : {args.trail}")
    print(f"  Área mínima        : {args.min_area} px²")
    print(f"{'═'*50}\n")
    print("Pressione  Q  para encerrar | S  para salvar frame")

    # ---------- Iniciar rastreador ----------
    tracker = ColorTracker(
        source=source,
        colors=chosen_colors,
        output_path=args.output,
        trail_length=args.trail,
        min_area=args.min_area,
    )
    tracker.run()


if __name__ == "__main__":
    main()
