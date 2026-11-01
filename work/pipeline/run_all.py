"""Execute notebooks in fresh Jupyter kernels and save their real outputs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent.parent
NOTEBOOKS = [
    PIPELINE_DIR / "01_data_preparation_and_eda.ipynb",
    PIPELINE_DIR / "02_analysis_and_visualization.ipynb",
    PIPELINE_DIR / "03_model_training_and_evaluation.ipynb",
]


def run_notebook(path: Path, working_directory: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    manager = KernelManager(kernel_name="python3")
    # Always use this interpreter, not a globally installed Python kernel.
    manager.kernel_spec.argv = [
        sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}",
    ]
    client = NotebookClient(
        notebook,
        km=manager,
        timeout=1800,
        resources={"metadata": {"path": str(working_directory)}},
        allow_errors=False,
    )
    client.on_cell_start = lambda cell, cell_index, **kwargs: print(
        f"  cell {cell_index + 1}: {cell.get('id', '')}", flush=True,
    ) if cell.cell_type == "code" else None
    print(f"RUN {path.name} | cwd={working_directory}", flush=True)
    try:
        client.execute()
    finally:
        # Persist execution evidence, including an error at the failed cell.
        nbformat.write(notebook, path)
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        manager.cleanup_resources()
    print(f"PASS {path.name} — outputs saved", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["01", "02", "03", "04"])
    parser.add_argument("--cwd", choices=["project", "notebook"], default="notebook")
    args = parser.parse_args()
    runtime_dir = PROJECT_ROOT / "work" / "build" / "jupyter_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.environ["IPYTHONDIR"] = str(runtime_dir / "ipython")
    os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime_dir)
    os.environ["MPLCONFIGDIR"] = str(runtime_dir / "matplotlib")
    selected = [p for p in NOTEBOOKS if args.only is None or p.name.startswith(args.only)]
    if args.only == "04":
        selected = [PROJECT_ROOT / "work" / "viz" / "04_eda_truc_quan.ipynb"]
    missing = [str(path) for path in selected if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing pipeline notebooks: {missing}")
    for notebook in selected:
        working_directory = PROJECT_ROOT if args.cwd == "project" else notebook.parent
        run_notebook(notebook, working_directory)
    print("PIPELINE PASS — selected notebooks completed", flush=True)


if __name__ == "__main__":
    main()
