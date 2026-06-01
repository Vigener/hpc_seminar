FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gdb \
    make \
    clangd \
    openmpi-bin \
    libopenmpi-dev \
    libomp-dev \
    htop \
    git \
    openssh-client \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    python-is-python3 \
    python3-numpy \
    python3-pandas \
    python3-matplotlib \
    fonts-noto-cjk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python packages that are better installed via pip
RUN python3 -m pip install --no-cache-dir japanize-matplotlib

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

# 視覚的ノイズにならないよう、絵文字1文字だけですっきり識別させる設定
RUN mkdir -p ~/.config && \
    echo '[container]' > ~/.config/starship.toml && \
    echo 'disabled = false' >> ~/.config/starship.toml && \
    echo 'format = "[$symbol ]($style)"' >> ~/.config/starship.toml && \
    echo 'symbol = "📦"' >> ~/.config/starship.toml && \
    echo 'style = "bold blue"' >> ~/.config/starship.toml && \
    echo '' >> ~/.config/starship.toml && \
    echo '[nodejs]' >> ~/.config/starship.toml && \
    echo 'disabled = true' >> ~/.config/starship.toml && \
    echo '' >> ~/.config/starship.toml && \
    echo '[python]' >> ~/.config/starship.toml && \
    echo 'symbol = "🐍 "' >> ~/.config/starship.toml
