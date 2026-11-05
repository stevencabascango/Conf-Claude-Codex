"""A separately executed reference worker. It makes no model calls."""
import json
import sys

from .io import read_json


def main():
    from .benchmark import execute
    task = read_json(sys.argv[1])
    if task.get("reference_case") != "hodge-r4":
        raise ValueError("Reference worker is limited to the documented hodge-r4 benchmark")
    print(json.dumps(execute(task), ensure_ascii=False))


if __name__ == "__main__":
    main()
