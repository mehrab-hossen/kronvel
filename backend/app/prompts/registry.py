"""
Loads versioned prompt templates. Every agent decision traces back to an
exact prompt file — the relative path IS the version identifier. Bump the
filename (system_v2.jinja2) to introduce a new version rather than editing
v1 in place, so old audit records referencing "system_v1" stay meaningful.
"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_PROMPTS_DIR = Path(__file__).parent
_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=select_autoescape(disabled_extensions=("jinja2",)),
)


def load_prompt(relative_path: str, **context) -> str:
    """relative_path example: 'copilot/system_v1.jinja2'"""
    template = _env.get_template(relative_path)
    return template.render(**context)
