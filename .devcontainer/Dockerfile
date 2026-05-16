FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gdb \
    make \
    openmpi-bin \
    libopenmpi-dev \
    libomp-dev \
    htop \
    git \
    openssh-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Starshipのインストール
RUN curl -sS https://starship.rs/install.sh | sh -s -- -y

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash

# ユーザーをvscodeに切り替え
USER $USERNAME

# Starshipの初期化設定
RUN echo 'eval "$(starship init bash)"' >> ~/.bashrc

# 視覚的ノイズのパージ（設定ファイルの自動生成）
RUN mkdir -p ~/.config && \
    echo '[container]' > ~/.config/starship.toml && \
    echo 'disabled = true' >> ~/.config/starship.toml && \
    echo '' >> ~/.config/starship.toml && \
    echo '[nodejs]' >> ~/.config/starship.toml && \
    echo 'disabled = true' >> ~/.config/starship.toml && \
    echo '' >> ~/.config/starship.toml && \
    echo '[python]' >> ~/.config/starship.toml && \
    echo 'symbol = "🐍 "' >> ~/.config/starship.toml