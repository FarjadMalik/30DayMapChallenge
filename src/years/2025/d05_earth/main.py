import fiona
import folium
import geopandas as gpd
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

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Convert date to string for tooltip display
    dataset["Sensor_Date"] = dataset["Sensor_Date"].astype(str)
    
    # TODO: join with admin boundaries to get names and areas for each admin unit
    # Add flood layer to map
    folium.GeoJson(
        dataset,
        name='Flood Extents 2025',
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': 'blue',
            'weight': 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['Area_ha', 'Area_m2', 'Sensor_ID', 'Sensor_Date'], 
            aliases=['Area in Hectares', 'Area in meters', 'Sensor', 'Date'],
            localize=True
            )
    ).add_to(basemap)

    # Add title — can be done via Html in map
    title_html = f"""
         <h3 align="center" style="font-size:20px"><b>Flooded Areas - Pakistan (Monsoon 2025)</b></h3>
         """
    basemap.get_root().html.add_child(folium.Element(title_html))

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
        color='white',
        edgecolor='black',
        linewidth=1
    )
    
    # plot polygons with colors
    dataset.plot(
        ax=ax,
        color='blue', 
        alpha=0.8
    )
    ax.set_xlim(center_lon - 9, center_lon + 9)
    ax.set_ylim(center_lat - 9, center_lat + 9)

    # Add title & legend
    ax.set_title(
        "Flooded Areas - Pakistan (Monsoon 2025)",
        fontsize=18,
        fontweight="bold",
        pad=20
    )
    
    # Beautify, add legend and save
    ax.legend(
        handles=[Patch(facecolor='blue', edgecolor='blue',
                                     label=f"Flood Extents")],
        title="Floods Pakistan 2025",
        loc="upper left",
        frameon=True
    )
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_earth_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'NAME_3','geometry']]

    # Geodatabase path
    gdb_path = "data/PAK_misc/FL20250818PAK.gdb"
    flood_layerlist = fiona.listlayers(gdb_path)
    logger.info(f"Layers in GDB: {flood_layerlist}")
    # Load the flood extent polygon layer
    flood_gdf = gpd.read_file(gdb_path, layer='VIIRS_20250826_20250907_FloodWaterExtent_PAK')
    
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if flood_gdf is not None and flood_gdf.crs.to_string() != "EPSG:4326":
        flood_gdf = flood_gdf.to_crs(epsg=4326)

    # Generate and Save the map
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(admin_gdf, flood_gdf, output_path)
    create_png(admin_gdf, flood_gdf, output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    filename = 'flood_pakistan_2025'
    generate_earth_map(path_dir=str(get_relative_path(__file__)), filename=filename)