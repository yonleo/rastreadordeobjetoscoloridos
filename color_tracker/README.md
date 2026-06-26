#  Rastreador de Objetos Coloridos em Vídeo

Projeto de **Processamento de Imagens** que detecta e rastreia objetos coloridos
em tempo real — em vídeos gravados ou diretamente pela webcam.

---

##  Pipeline de Processamento de Imagens

```
Frame BGR
    │
    ▼
[1] Transformação de Cor ──── BGR → HSV (cv2.cvtColor)
    │
    ▼
[2] Limiarização ─────────── Máscara binária por faixa HSV (cv2.inRange)
    │                         (uma máscara por cor selecionada)
    ▼
[3] Filtragem Morfológica ── Abertura  = erosão  → dilatação  (remove ruído)
    │                         Fechamento = dilatação → erosão  (fecha buracos)
    ▼
[4] Detecção de Contornos ── cv2.findContours → RETR_EXTERNAL
    │
    ▼
[5] Rastreamento de Centróide ── Momentos de imagem M10/M00, M01/M00
    │
    ▼
Desenho: contorno colorido + bbox + centróide + trilha histórica
```

### Por que HSV?

O espaço **BGR** mistura cor e brilho em três canais, tornando a segmentação
frágil a variações de iluminação. O **HSV** separa:
- **H**ue (matiz) — a cor em si (0–179 no OpenCV)
- **S**aturation — intensidade da cor
- **V**alue — brilho

Com isso, basta definir um intervalo de H para isolar cada cor
independentemente das condições de luz.

---

##  Estrutura do Projeto

```
color_tracker/
├── main.py                  # Ponto de entrada; CLI + seleção interativa
├── tracker.py               # Classe ColorTracker (loop de vídeo, HUD, gravação)
├── image_processing.py      # Pipeline de P.I. (etapas 1–5)
├── color_config.py          # Perfis HSV de cada cor + função build_mask
├── utils.py                 # Banner e utilitários
├── generate_test_video.py   # Gerador de vídeo de teste (bolas coloridas)
└── requirements.txt
```

---

##  Instalação

```bash
# 1. Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 2. Instalar dependências
pip install -r requirements.txt
```

---

##  Uso

### Gerar vídeo de teste (opcional)
```bash
python generate_test_video.py
# Gera teste.mp4 com 6 bolas coloridas se movendo por 15 segundos
```

### Rastrear com vídeo
```bash
# Rastrear vermelho e azul em um vídeo
python main.py teste.mp4 -c vermelho azul

# Rastrear múltiplas cores e salvar resultado
python main.py teste.mp4 -c vermelho verde azul amarelo laranja roxo -o resultado.mp4

# Seleção interativa de cores (sem -c)
python main.py teste.mp4
```

### Rastrear pela webcam
```bash
python main.py -c verde vermelho
# (sem argumento de vídeo = usa câmera padrão)
```

### Parâmetros disponíveis

| Argumento        | Padrão    | Descrição                                          |
|------------------|-----------|----------------------------------------------------|
| `video`          | —         | Caminho do vídeo (omita para webcam)               |
| `-c / --colors`  | interativo| Cores a rastrear                                   |
| `-o / --output`  | nenhum    | Salvar vídeo processado                            |
| `--trail`        | 40        | Tamanho da trilha do centróide (em frames)         |
| `--min-area`     | 800       | Área mínima do contorno (px²) para ser detectado  |
| `--list-colors`  | —         | Lista as cores disponíveis                         |

### Teclas durante a execução

| Tecla | Ação                              |
|-------|-----------------------------------|
| `Q`   | Encerrar o programa               |
| `ESC` | Encerrar o programa               |
| `S`   | Salvar frame atual como PNG       |
| `D`   | Ativar/desativar painel de debug  |

---

##  Cores disponíveis

| Nome        | Cor          |
|-------------|--------------|
| `vermelho`  | 🔴 Vermelho  |
| `laranja`   | 🟠 Laranja   |
| `amarelo`   | 🟡 Amarelo   |
| `verde`     | 🟢 Verde     |
| `ciano`     | 🩵 Ciano     |
| `azul`      | 🔵 Azul      |
| `roxo`      | 🟣 Roxo      |
| `rosa`      | 🩷 Rosa      |
| `branco`    | ⚪ Branco    |
| `preto`     | ⚫ Preto     |

```bash
python main.py --list-colors   # exibe todas com exemplos
```

---

##  Detalhes do Pipeline de P.I.

### Etapa 1 — Transformação de Cor
```python
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
```
Converte cada frame de BGR para HSV antes de qualquer análise.

### Etapa 2 — Limiarização
```python
mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
```
Gera uma imagem binária (0 ou 255) onde os pixels dentro do intervalo HSV
da cor alvo ficam brancos. Cores como **vermelho** requerem dois intervalos
(H≈0° e H≈180°), combinados com `bitwise_or`.

### Etapa 3 — Filtragem Morfológica
```python
# Abertura: elimina pequenos pontos de ruído
opened  = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel_5x5)
# Fechamento: preenche buracos internos
cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_9x9)
```
Usa **elemento estruturante elíptico** para respeitar a forma circular
dos objetos rastreados.

### Etapa 4 — Detecção de Contornos
```python
contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```
Extrai apenas os contornos externos. Contornos com área < `min_area` são
descartados (ruído residual).

### Etapa 5 — Rastreamento de Centróide
```python
M  = cv2.moments(contour)
cx = int(M["m10"] / M["m00"])   # centróide X
cy = int(M["m01"] / M["m00"])   # centróide Y
```
O centróide de cada objeto é armazenado em um `deque` de tamanho fixo
(`trail_length`), gerando a trilha histórica desenhada no vídeo.



---

##  Referências

- Bradski, G. & Kaehler, A. — *Learning OpenCV 3* (O'Reilly, 2016)
- Gonzalez, R. C. & Woods, R. E. — *Digital Image Processing* (Pearson, 2018)
- Documentação OpenCV — https://docs.opencv.org
