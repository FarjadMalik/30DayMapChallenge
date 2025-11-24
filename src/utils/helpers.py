import json
import pandas as pd
import geopandas as gpd

from typing import List
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


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

def load_and_flatten(json_path: str, data_column: str = 'data', meta: List = []) -> pd.DataFrame:
    """
    Load a JSON file in which a top-level DataFrame has a nested 'data' (by default) column,
    then flatten that column into its own DataFrame.

    Parameters
    ----------
    json_path : str
        Path to the JSON file (or a JSON string).
    data_column : str, optional
        The name of the column containing nested data to flatten, by default 'data'.
    meta : List, optional
        List of columns to include as metadata in the flattened DataFrame, by default [].

    Returns
    -------
    pd.DataFrame
        DataFrame containing only the flattened nested data.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        # Read the JSON into a pandas DataFrame
        json_data = json.load(f)

    # # Extract the 'data' column (which should be a list, or dicts)
    # # If it's a string, you may need to json.loads it
    # nested = df[data_column]

    # # If entries in nested are JSON strings, decode them
    # if nested.dtype == object and nested.apply(lambda x: isinstance(x, str)).all():
    #     nested = nested.apply(json.loads)

    # # Use json_normalize to flatten the nested column
    # # This will give you a new DataFrame with the keys inside each 'data' dict as columns
    # Flatten with json_normalize
    flat = pd.json_normalize(
        json_data,
        record_path=[data_column],               # the field that is a list of records
        meta=meta,  # metadata to keep per record
        meta_prefix="meta_"                 # optional prefix to avoid collisions
    )

    return flat