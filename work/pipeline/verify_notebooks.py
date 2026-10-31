"""Audit saved notebook execution and test the input guards in isolated fixtures."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

import nbformat

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent.parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "work" / "build" / "jupyter_runtime" / "matplotlib"))


def check_input_guards(path: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    # Only setup/config/validation; never train or overwrite production data.
    setup_cells = [c.source for c in notebook.cells[:7] if c.cell_type == "code"]
    original_cwd = Path.cwd()
    for label, expected in [
        ("valid", None), ("missing_manifest", FileNotFoundError),
        ("missing_processed", FileNotFoundError), ("qa_changed", ValueError),
        ("raw_changed", ValueError), ("processed_changed", ValueError),
        ("not_passed", ValueError),
    ]:
        with tempfile.TemporaryDirectory(prefix="nb_guard_", dir=ROOT / "work" / "build") as directory:
            fixture = Path(directory)
            (fixture / "data").mkdir()
            (fixture / "work" / "pipeline").mkdir(parents=True)
            build = fixture / "work" / "build"
            build.mkdir()
            # Small raw is sufficient: guards check its hash, not raw content.
            source = fixture / "data" / "cell2celltrain.csv"
            source.write_text("fixture raw", encoding="utf-8")
            for name in ["processed_customers.parquet", "qa_report.json"]:
                (build / name).write_bytes((ROOT / "work" / "build" / name).read_bytes())
            manifest = json.loads((ROOT / "work" / "build" / "preparation_manifest.json").read_text(encoding="utf-8"))
            manifest["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            if label == "not_passed":
                manifest["status"] = "failed"
            if label != "missing_manifest":
                (build / "preparation_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            if label == "raw_changed":
                source.write_text("changed raw", encoding="utf-8")
            if label == "processed_changed":
                (build / "processed_customers.parquet").write_bytes(b"invalid")
            if label == "missing_processed":
                (build / "processed_customers.parquet").unlink()
            if label == "qa_changed":
                (build / "qa_report.json").write_text("{}", encoding="utf-8")
            caught = None
            try:
                os.chdir(fixture)
                namespace = {}
                with redirect_stdout(io.StringIO()):
                    for source_code in setup_cells:
                        exec(compile(source_code, path.name, "exec"), namespace)
            except Exception as error:
                caught = error
            finally:
                os.chdir(original_cwd)
            if expected is None and caught is not None:
                raise AssertionError(f"{path.name}/{label}: unexpected {caught}") from caught
            if expected is not None and not isinstance(caught, expected):
                raise AssertionError(f"{path.name}/{label}: expected {expected}, got {caught}")
            print(f"GUARD PASS {path.name}: {label}")


def main() -> None:
    for path in sorted(PIPELINE.glob("[0-9][0-9]_*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        cells = [c for c in notebook.cells if c.cell_type == "code"]
        counts = [c.execution_count for c in cells]
        if counts != list(range(1, len(cells) + 1)):
            raise AssertionError(f"{path.name}: missing/out-of-order execution evidence")
        errors = [o for c in cells for o in c.outputs if o.output_type == "error"]
        if errors:
            raise AssertionError(f"{path.name}: errors in saved outputs")
        plots = sum("image/png" in o.get("data", {}) for c in cells for o in c.outputs)
        tables = sum("text/html" in o.get("data", {}) for c in cells for o in c.outputs)
        if plots == 0 or tables == 0:
            raise AssertionError(f"{path.name}: missing saved plots or tables")
        print(f"AUDIT PASS {path.name}: {len(cells)} executed cells, {plots} plots, {tables} HTML tables")
        if path.name.startswith(("02", "03")):
            check_input_guards(path)


if __name__ == "__main__":
    main()
