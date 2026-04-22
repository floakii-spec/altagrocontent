import os
from pathlib import Path
from typing import Dict


_DEFAULT_NOTE_PATHS = {
    "perfil_nathan": Path("meta/perfil-nathan.md"),
    "estrategia_conteudo": Path("03-estrategia/estrategia-conteudo.md"),
    "confraria": Path("03-estrategia/confraria.md"),
    "pautas": Path("01-ideias/pautas.md"),
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_vault_paths() -> list[Path]:
    env_path = os.getenv("OBSIDIAN_VAULT_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path).expanduser())

    repo_root = _repo_root()
    candidates.extend(
        [
            repo_root.parent / "agro-content-ob" / "agro-content",
            repo_root / "obsidian",
            repo_root / "vault",
        ]
    )
    return candidates


def _resolve_vault_path() -> Path | None:
    for candidate in _candidate_vault_paths():
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _read_note(vault_root: Path | None, relative_path: Path, max_chars: int = 1800) -> str:
    if not vault_root:
        return ""
    note_path = vault_root / relative_path
    if not note_path.exists():
        return ""
    text = note_path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncado]"


def load_studio_context() -> Dict[str, str]:
    vault_root = _resolve_vault_path()
    return {
        name: _read_note(vault_root, relative_path)
        for name, relative_path in _DEFAULT_NOTE_PATHS.items()
    }
