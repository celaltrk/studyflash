import yaml
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent
_cache: dict[str, dict] = {}


def load_prompt(name: str) -> dict:
    """Load a prompt YAML file by name (without extension). Results are cached."""
    if name not in _cache:
        path = _PROMPTS_DIR / f"{name}.yaml"
        with open(path) as f:
            _cache[name] = yaml.safe_load(f)
    return _cache[name]
