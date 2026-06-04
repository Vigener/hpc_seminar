# GitHub Copilot Instructions for HPC Project

## 1. System Architecture & Development Flow

You are an expert AI assistant helping an HPC (High-Performance Computing) developer.
The project uses a hybrid engineering workflow across three environments:

- **Host OS (macOS / ARM)**: Used for code editing, Python runtime, and generating graphics/plots.
- **Local Container (Ubuntu via OrbStack)**: Used strictly for C/C++ compiler checks (syntax validation) and lightweight execution sanity tests.
- **Production (PPX Cluster / Linux x86_64)**: Used for actual heavy performance evaluations.

## 2. Environment-Specific Execution Rules

### C/C++ Code & Job Scripts (PPX Target)

- **DO NOT** attempt to compile or execute C/C++ binaries directly on the host macOS.
- When compilation or testing commands are requested, **ALWAYS** suggest running them inside the local Docker/OrbStack container terminal (assume the project root is mounted to `/workspace`).
- Treat C/C++ execution as targeted for the PPX cluster using the Slurm workload manager via `sbatch`.
- When modifying or writing PPX job scripts, make them straightforward, explicit, and readable. Keep functions and variables minimal, and include helpful comments.
- Prefer absolute path building derived from the script's directory location over relying on explicit `cd` state changes.
- Assume existing pre-compiled binaries on the shared filesystem are prioritized; do not add unnecessary build overhead into job scripts.

### Python & Data Plotting (Host macOS via `uv`)

- Python runtime, virtual environments (`.venv`), and dependencies are managed **strictly via `uv`** on the local host macOS. (Mise is used only to install `uv`, not Python itself).
- **DO NOT** execute Python scripts on the PPX production nodes or inside the local container unless explicitly asked.
- You **MAY** suggest or automatically trigger host-level Python commands (always using the project's `.venv/bin/python`) to process results or render graphs.
- When generating plots, ensure dependencies like `matplotlib` or `pandas` are managed via `uv` (e.g., referenced via `uv.lock` or `pyproject.toml`).

## 3. Directory Structure & Artifact Management

Follow these standardized structural rules strictly for all file placements and references:

- **Source Files**: Place all `.c` (or `.cpp`) and `.sh` (job scripts) directly in the project root directory.
- **Python Scripts**: Place all Python code inside the `scripts/` directory.
- **Binaries**: Standardize all compiled binary outputs into the `bin/` directory. Reference them via `./bin/...` or `"$SCRIPT_DIR/bin/..."`.
- **Artifacts (Data & Plots)**: Standardize all experimental outputs (raw CSVs, logs, images, and plots) into the `out/` directory.
- **CSV Formatting**: Output all data from C/C++ in a clean, tabular CSV layout optimized for Python parsing. Ensure column names and structures are streamlined within the C layer where possible.
- **Directory Creation**: Job scripts on the PPX side may safely include `mkdir -p out` before execution. Explicitly assign CSV paths to variables (e.g., `RAWCSV`) and stream output directly (e.g., `./bin/... > "$RAWCSV"`).

## 4. Automation via Makefiles

- Every compilation task or script execution must be easily triggered using a clean, minimal `Makefile` configured for the respective directory or workflow.
- Ensure tasks like compiling inside the container or plotting via the host's Python environment are clearly decoupled into appropriate `make` targets for perfect reproducibility.

## 5. Coding Standards & Consistency

- **ALWAYS** prioritize maintaining consistency with the existing architecture, file layout, and naming conventions present in the repository.
