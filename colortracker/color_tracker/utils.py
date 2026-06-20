"""
utils.py
--------
Funções utilitárias do projeto.
"""


def banner():
    print("""
╔══════════════════════════════════════════════════════╗
║      RASTREADOR DE OBJETOS COLORIDOS EM VÍDEO        ║
║      Processamento de Imagens                        ║
╠══════════════════════════════════════════════════════╣
║  Pipeline de P.I.                                    ║
║    1. Transformação de Cor   BGR → HSV               ║
║    2. Limiarização           inRange (máscara binária)║
║    3. Filtragem Morfológica  Abertura + Fechamento    ║
║    4. Rastreamento de Centróide via Momentos          ║
╚══════════════════════════════════════════════════════╝
""")
