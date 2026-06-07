# Python仮想環境の初期化タスク (Macローカルホスト側で実行)
init-env:
	uv venv --python 3.12
	uv pip install matplotlib japanize-matplotlib
	@echo "===================================================="
	@echo "ローカルPython仮想環境（.venv）の構築が完了しました。"
	@echo "グラフ描画を行うには 'make plot' を実行してください。"
	@echo "===================================================="

# ==============================================================================
# JRE / HPC Remote Synchronization (rsync) Settings
# ==============================================================================

# リモートサーバーの設定
REMOTE_USER := igarashi
REMOTE_HOST := ppxsvc.ccs.tsukuba.ac.jp
REMOTE_BASE_DIR := ~/dev/hpc_seminar

# Macローカルの現在のディレクトリ（Makefileがある場所）
LOCAL_BASE_DIR := .

# パターンルールを用いた汎用的な rsync ターゲット
# `.csv` と `.log` ファイルのみを対象に同期します
.PHONY: rsync-%
rsync-%:
	@echo "=> Syncing CSV and LOG files from remote: $* /out/..."
	@mkdir -p $(LOCAL_BASE_DIR)/$*/out
	rsync -avz --include="*/" --include="*.csv" --include="*.log" --exclude="*" \
		$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_BASE_DIR)/$*/out/ \
		$(LOCAL_BASE_DIR)/$*/out/
	@echo "=> Synchronization of $* completed successfully."
