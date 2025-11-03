from pathlib import Path



def get_relative_path(filename: str) -> Path:
    """Get the relative path of the current file from the project root."""

    current_file = Path(filename).resolve()

    # Go up until you find your project root (e.g. contains .git or pyproject.toml)
    for parent in current_file.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            project_root = parent
            break
    else:
        project_root = current_file.parent  # fallback

    # relative_path = code_dir.relative_to(Path(__name__).resolve().parent)
    relative_path = current_file.relative_to(project_root)
    return relative_path