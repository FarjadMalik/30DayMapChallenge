import folium
import rasterio
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from rasterio.plot import reshape_as_image

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_html(admin, maps_info, output_path):
    """
    """
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin is not None and admin.crs.to_string() != "EPSG:4326":
        admin = admin.to_crs(epsg=4326)
        
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create base folium map 
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')
      
    # Add each map one by one
    for map in maps_info: 
        # Load land cover land use layer 
        
        with rasterio.open(map['path']) as src:
            bounds = src.bounds
            img = src.read()
            crs = src.crs
        
        # logger.info(f"Raster CRS: {crs}")
        # logger.info(f"Raster bounds: {bounds}")
        # logger.info(f"Raster img shape: {img.shape}")
        
        # Reshape the image for proper display (bands, rows, cols) -> (rows, cols, bands)
        img = reshape_as_image(img)
        # logger.info(f"Raster reshaped shape: {img.shape}")

        # Normalize image values to 0–1 for display
        img = img.astype(float)
        img = (img - np.nanmin(img)) / (np.nanmax(img) - np.nanmin(img))

        folium.raster_layers.ImageOverlay(
            name="Ancient India Map",
            image=img,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],  # [[lat_min, lon_min], [lat_max, lon_max]]
            opacity=0.7,
            interactive=True,
            cross_origin=False,
            zindex=1
        ).add_to(basemap)

    # Add the administrative boundaries layer
    folium.GeoJson(
        admin,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 1,
            'dashArray': '5, 5'
        }
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save and exit
    basemap.save(f"{output_path}.html")

def create_png(admin, raster_map, output_path):
    """
    """
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # create fig and axis
    _, ax = plt.subplots(figsize=(12, 10))

    # plot admin boundaries
    admin.plot(
        ax=ax,
        color='white',
        edgecolor='black',
        linewidth=1
    )
    # TODO: fix the limits based on raster
    ax.set_xlim(center_lon - 11, center_lon + 11)
    ax.set_ylim(center_lat - 11, center_lat + 11)

    # plot raster image    
    

    # Add title & legend
    ax.set_title(
        "Analog Map",
        fontsize=18,
        fontweight="bold",
        pad=20
    )
    
    # Beautify, add legend and save
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_analog_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

    # List of analog maps with approximate name/time label
    # if the maps are not georeferenced then define boundingbbox
    # the given map was georeferenced manually in QGIS
    maps_info = [
        {
            "path": "data/PAK_misc/analog_maps/ancientindia_modified.tif",
            # "bounds": [68, 6, 97, 36],  # [min_lon, min_lat, max_lon, max_lat]
            "year": 1850
        },
        # {
        #     "path": "british_india_map_1900.png",
        #     "bounds": [68, 6, 97, 36],
        #     "year": 1900
        # },
        # {
        #     "path": "british_india_map_1940.png",
        #     "bounds": [68, 6, 97, 36],
        #     "year": 1940
        # },
    ]

    # Generate and save maps
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(admin_gdf, maps_info, output_path)
    # TODO: Add png maps
    # for map in maps_info:
    #     create_png(admin_gdf, maps_info, f"{output_path}_{map['year']}")

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Draw one of the maps from analog folder
    # Maps have been georeferenced using QGIS
    filename = 'analog_map'
    generate_analog_map(path_dir=str(get_relative_path(__file__)), filename=filename)
