import geopandas as gpd

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

def clip_geo_dataset(dataset: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame, out_file: str = ''):
    """
    Clip a geodataframe based on a boundary file
    """ 
    if dataset.crs != boundary.crs:
        boundary = boundary.to_crs(dataset.crs)
    dataset = dataset.clip(boundary)
    if out_file or out_file == '':
        dataset.to_file(out_file)
        return
    return dataset