import folium
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio

from pathlib import Path
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_hydro_map(path_dir: str, file_html: str):
    """
    Creates hydro map using hydro geopackage
    
    """
    logger.info(f"Hello from {path_dir}")
    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[0.0, 0.0], zoom_start=6, tiles='OpenStreetMap')

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'pk_hydro_map'
    create_hydro_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)