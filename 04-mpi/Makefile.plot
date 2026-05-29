.PHONY: plot

PYTHON ?= python3
OUT_DIR ?= out
INPUT_CSV ?= $(shell ls -1t $(OUT_DIR)/laplace_ppx_raw_*.csv 2>/dev/null | head -n 1)
SUMMARY_CSV ?= $(OUT_DIR)/laplace_ppx_summary.csv
FIGURE_OUT ?= $(OUT_DIR)/laplace_ppx_time.png
PLOT_TITLE ?= Laplace MPI: Mean time vs process count
SHOW_ERROR_BARS ?= 0

plot:
	@if [ -z "$(INPUT_CSV)" ]; then \
		echo "INPUT_CSV is empty. Put CSV in $(OUT_DIR)/ and set INPUT_CSV=..."; \
		exit 1; \
	fi
	@mkdir -p $(OUT_DIR)
	@$(PYTHON) scripts/plot_ppx_time.py \
		--input "$(INPUT_CSV)" \
		--summary-output "$(SUMMARY_CSV)" \
		--figure-output "$(FIGURE_OUT)" \
		--title "$(PLOT_TITLE)" \
		$(if $(filter 1,$(SHOW_ERROR_BARS)),--show-error-bars,)
	@echo "summary: $(SUMMARY_CSV)"
	@echo "figure : $(FIGURE_OUT)"
