import json
from pathlib import Path

from app.main import create_app


def main() -> None:
    output_path = Path(__file__).resolve().parents[3] / "frontend" / "openapi.json"
    output_path.write_text(json.dumps(create_app().openapi(), indent=2) + "\n")
    print(f"Exported OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
