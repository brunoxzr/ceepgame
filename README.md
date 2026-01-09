# 🎮 CEEPGame — Jogo Educacional com IA Gestual

<p align="center">
  <img src="logoceep.png" alt="CEEP" width="160">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Ativo-success?style=for-the-badge">
  <img src="https://img.shields.io/badge/Python-Game-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/MediaPipe-Gestos-FF6F00?style=for-the-badge">
  <img src="https://img.shields.io/badge/Pygame-Engine-00C853?style=for-the-badge">
</p>

<p align="center">
  <strong>Jogo 2D controlado por gestos com visão computacional</strong><br>
  Desenvolvido no CEEP Assaí como projeto educacional de IA aplicada.
</p>

---

## 🧠 Visão Geral

O **CEEPGame** é um jogo 2D em Python controlado **exclusivamente por gestos da mão**, detectados em tempo real via **webcam** usando **MediaPipe**. O projeto une **jogos, inteligência artificial e visão computacional**, promovendo aprendizado prático e engajamento.

O jogador corre automaticamente e interage com o ambiente por meio de gestos naturais:

* ✋ **Pular** obstáculos
* 👉 **Atirar** em inimigos
* 🏃 **Correr** continuamente

---

## ✋ Gestos Reconhecidos

| Gesto               | Ação   |
| ------------------- | ------ |
| 3+ dedos levantados | Pular  |
| Polegar + 1 dedo    | Atirar |
| Mão fechada         | Correr |

A detecção é otimizada para baixo consumo de CPU, processando gestos em resolução reduzida e com *intervalo inteligente*.

---

## 🛠️ Tecnologias Utilizadas

| Camada              | Tecnologia               |
| ------------------- | ------------------------ |
| Linguagem           | Python 3                 |
| Engine de Jogo      | Pygame                   |
| Visão Computacional | OpenCV                   |
| IA Gestual          | MediaPipe Hands          |
| Áudio               | Pygame Mixer             |
| Persistência        | JSON (posição da webcam) |

---

## 🧩 Arquitetura do Sistema

```text
Webcam
  │
  ▼
OpenCV
  │
  ▼
MediaPipe Hands
  │
  ▼
Reconhecimento de Gestos
  │
  ▼
Lógica do Jogo (Pygame)
```

---

## 🎮 Mecânicas do Jogo

* Velocidade aumenta progressivamente (dificuldade dinâmica)
* Spawn inteligente de obstáculos e inimigos
* Sistema de pontuação e recorde
* Partículas visuais e efeitos sonoros
* Detecção de colisão com reinício suave

---

## 🖥️ Interface & Controles

* 🎥 **Webcam flutuante** (arrastável e redimensionável)
* 🖥️ **Modo tela cheia** (`F11`)
* 📊 HUD com pontuação, recorde, velocidade e gesto atual

A posição da webcam é salva automaticamente em `config_cam.json`.

---

## 📂 Estrutura do Projeto

```text
CEEPGame/
├── main.py
├── logoceep.png
├── fundo2.jpg
├── player.png / 1.png / 2.png / 3.png
├── enemy.png
├── obstacle.png
├── theme.mp3
├── jump.wav
├── hit.wav
├── audio.mp3
├── config_cam.json
```

---

## ⚙️ Requisitos

* Python 3.9+
* Webcam funcional
* Sistema operacional: Windows / Linux

### Bibliotecas

```bash
pip install opencv-python mediapipe pygame numpy
```

---

## ▶️ Como Executar

```bash
python main.py
```

Ao iniciar:

1. A câmera será detectada automaticamente
2. Escure a mão em frente à webcam
3. Controle o jogo apenas com gestos ✋

---

## 🧪 Objetivo Educacional

Este projeto foi desenvolvido no **CEEP Assaí** para demonstrar:

* Aplicação real de IA em tempo real
* Integração entre visão computacional e jogos
* Lógica de física, eventos e renderização
* Otimização de performance em Python

---

## 🏫 Instituição

* **Centro:** CEEP Assaí
* **Curso:** Desenvolvimento de Sistemas
* **Projeto:** IA + Jogos Educacionais

---


> *VEM SER CEEP 🚀*
