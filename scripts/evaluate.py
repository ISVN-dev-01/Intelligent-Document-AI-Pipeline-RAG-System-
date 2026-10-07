import argparse
import json
from pathlib import Path

from _common import ROOT, authenticated_app, cli_error

from evaluation.evaluator import evaluate


def main():
    parser = argparse.ArgumentParser(description="Evaluate the supplied synthetic corpus; Google mode makes paid API requests.")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation" / "results.json")
    args = parser.parse_args()
    app, principal = authenticated_app()
    try:
        dataset = json.loads((ROOT / "evaluation" / "evaluation_dataset.json").read_text())
        result = evaluate(app, principal, dataset)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items() if key != "cases"}, indent=2))
        print(f"Detailed measurements: {args.output}")
    finally:
        app.engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        cli_error(exc)
