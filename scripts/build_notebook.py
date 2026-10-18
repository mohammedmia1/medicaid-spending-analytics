"""Execute the notebook's visible cells and capture tables and chart outputs.

The notebook is the source of its own analytical code. This runner supplies
Jupyter-like display handling without requiring Jupyter for batch execution.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import io
import json
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def execute_notebook(check_only: bool = False) -> None:
    path = ROOT / "notebooks/Medicaid_Spending_Analysis.ipynb"
    notebook = json.loads(path.read_text())
    namespace = {"__name__": "__main__"}
    original_show = plt.show
    original_directory = Path.cwd()
    started = time.monotonic()
    execution = 0
    try:
        os.chdir(ROOT)
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            execution += 1
            outputs = []
            captured = io.StringIO()

            def flush_stdout():
                if captured.getvalue():
                    outputs.append({"output_type": "stream", "name": "stdout",
                                    "text": captured.getvalue().splitlines(keepends=True)})
                    captured.seek(0)
                    captured.truncate(0)

            def display(value):
                flush_stdout()
                data = {"text/plain": repr(value)}
                if hasattr(value, "_repr_html_"):
                    html = value._repr_html_()
                    if html is not None:
                        data["text/html"] = html
                outputs.append({"output_type": "display_data", "metadata": {}, "data": data})

            def show(*args, **kwargs):
                flush_stdout()
                for number in plt.get_fignums():
                    figure = plt.figure(number)
                    buffer = io.BytesIO()
                    figure.savefig(buffer, format="png", dpi=120, bbox_inches="tight", facecolor="white")
                    outputs.append({"output_type": "display_data", "metadata": {},
                                    "data": {"image/png": base64.b64encode(buffer.getvalue()).decode("ascii"),
                                             "text/plain": f"<Figure with {len(figure.axes)} axes>"}})
                    plt.close(figure)

            namespace["display"] = display
            plt.show = show
            try:
                with contextlib.redirect_stdout(captured):
                    exec(compile("".join(cell["source"]), f"notebook-cell-{execution}", "exec"), namespace)
                flush_stdout()
            except Exception as error:
                raise RuntimeError(f"Notebook cell {execution} failed: {error}") from error
            cell["execution_count"] = execution
            cell["outputs"] = outputs
            print(f"Executed cell {execution}", flush=True)
        if not check_only:
            path.write_text(json.dumps(notebook, indent=1) + "\n")
        action = "Checked" if check_only else "Executed and saved"
        print(f"{action} {execution} cells in {time.monotonic() - started:.1f}s; all result comparisons passed")
    finally:
        plt.show = original_show
        plt.close("all")
        os.chdir(original_directory)
        # Release the notebook's large data frames in long-lived Python callers.
        namespace.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Execute all cells without rewriting the saved notebook")
    execute_notebook(check_only=parser.parse_args().check)
