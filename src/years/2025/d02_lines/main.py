import folium
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_html(admin, dataset, output_path):
    """
    """
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin is not None and admin.crs.to_string() != "EPSG:4326":
        admin = admin.to_crs(epsg=4326)
    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Add hydro/rivers layer to map
    folium.GeoJson(
        dataset,
        name='Railways and Highways - Pakistan',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'purple' if feature['properties']['type'] == 'rail' else 'red',
            'weight': 1,
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "red"
        }
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    basemap.save(f"{output_path}.html")
    

def create_png(admin, dataset, output_path):
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
        facecolor='white',
        edgecolor='black',
        linewidth=1
    )
    # Set map focus and limits
    ax.set_xlim(center_lon - 9, center_lon + 9)
    ax.set_ylim(center_lat - 9, center_lat + 9)

    # define colors for our rail and roads
    type_line = {
        'rail': 'red',
        'road': 'blue'
    }

    # plot dataset
    dataset.plot(
        ax=ax,
        color=[type_line.get(x) for x in dataset['type']]
    )
    
    # Add title & legend
    ax.set_title(
        "Railways and Highways - Pakistan",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    legend_elements = []
    for key, value in type_line.items():
        legend_elements.append(Patch(facecolor=value, edgecolor=value,
                                     label=f"{key}"))

    # Beautify, add legend and save
    ax.legend(
        handles=legend_elements,
        title="Type of Transport",
        loc="upper left",
        frameon=True
    )
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_lines_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

    # Load rails and roads layer from geopackage
    rail_gpkg_path = "data/PAK_misc/openstreetmap/openstreetmap_rail__PAK.gpkg"
    road_gpkg_path = "data/PAK_misc/openstreetmap/openstreetmap_roads-tertiary__PAK.gpkg"
    rail_gdf = gpd.read_file(rail_gpkg_path, layer='lines')
    road_gdf= gpd.read_file(road_gpkg_path, layer='lines')
    # Filter out roads and rails of importance to limit the dataset
    # Plus filter columns
    rail_gdf = rail_gdf.query("railway == 'rail' and usage == 'main'").loc[:, 
                                                            ['osm_id', 'name', 'other_tags', 'geometry']]
    highwaytype_list = ['primary', 'trunk', 'motorway'] 
    road_gdf = road_gdf.loc[road_gdf['highway'].isin(highwaytype_list), 
                            ['osm_id', 'name', 'surface', 'maxspeed', 'lanes', 'other_tags', 'geometry']]
    # Assign type
    rail_gdf["type"] = "rail"
    road_gdf["type"] = "road"
    # Check crs 
    if rail_gdf.crs != road_gdf.crs:
        rail_gdf = rail_gdf.to_crs(road_gdf.crs)
    # Combine rail and road dataframes with a new column indicating type
    railroad_gdf = gpd.GeoDataFrame(pd.concat([rail_gdf, road_gdf], ignore_index=True), geometry='geometry', 
                                    crs=rail_gdf.crs)
    logger.info(len(railroad_gdf))
    
    # Generate and save the maps
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(admin_gdf, railroad_gdf, output_path)
    create_png(admin_gdf, railroad_gdf, output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    filename = 'pakistan_railroad_map'
    generate_lines_map(path_dir=str(get_relative_path(__file__)), filename=filename)
