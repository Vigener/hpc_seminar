# Python仮想環境の初期化タスク (Macローカルホスト側で実行)
init-env:
	uv venv --python 3.12
	uv pip install matplotlib japanize-matplotlib
	@echo "===================================================="
	@echo "ローカルPython仮想環境（.venv）の構築が完了しました。"
	@echo "グラフ描画を行うには 'make plot' を実行してください。"
	@echo "===================================================="