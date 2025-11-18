import fiona
import folium
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch
from branca.element import Template, MacroElement
from shapely.geometry import MultiPolygon, GeometryCollection, Polygon

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_folium_map(dataset, output_path):
    
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = dataset.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Add IPC polygons to the map
    folium.GeoJson(
        dataset,
        name='Acute Food Insecurity Areas Pakistan',
        style_function=lambda feature: {
            'fillColor': feature['properties']['color'],
            'color': feature['properties']['color'],
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['Area', 'Level 1', 'overall_phase', 'estimated_population', 'Percentage', 
                    'confidence_level', 'Date of analysis',],
            aliases=['District:', 'Province:',  'Overall Level:', 'Number Affected:', 'Percentage Affected:', 
                    'Confidence Level:', 'Date of Analysis:'],
            localize=True
        )
    ).add_to(basemap)

    # Add legend for phases/colors
    title_html = '''
    <h3 align="center" style="font-size:20px; font-weight:bold; margin-top:10px">
        IPC Acute Food Insecurity Levels - Pakistan
    </h3>
    '''
    basemap.get_root().html.add_child(folium.Element(title_html))

    # Define your color mapping for phases, e.g.:
    # phase_color_dict = {
    #     1: '#fae61e', # Phase 1 color
    #     2: '#e67800', # Phase 2 color
    #     3: '#c80000', # Phase 3 color
    #     4: '#640000', # Phase 4 color
    #     5: '#000000', # Phase 5 color
    # }

    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
    position: fixed; 
    bottom: 50px; left: 50px; width: 180px; height: 150px; 
    border:2px solid grey; z-index:9999; font-size:14px;
    background-color: white;
    opacity: 0.8;
    padding: 10px;
    ">
    <b>Level Legend</b><br>
    <i style="background:#fae61e;width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;"></i>Level 1<br>
    <i style="background:#e67800;width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;"></i>Level 2<br>
    <i style="background:#c80000;width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;"></i>Level 3<br>
    <i style="background:#640000;width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;"></i>Level 4<br>
    <i style="background:#000000;width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;"></i>Level 5<br>
    </div>
    {% endmacro %}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)

    # Add legend to your map
    basemap.get_root().add_child(legend)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(output_path)    

def create_png_map(dataset, output_path):
    
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = dataset.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # create fig and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # plot polygons with colors
    dataset.plot(
        ax=ax,
        color=dataset['color'], # fill
        edgecolor=dataset['color'], # outline
        linewidth=1,
        alpha=0.7
    )
    lat_range = 6
    lon_range =6
    ax.set_xlim(center_lon - lon_range, center_lon + lon_range)
    ax.set_ylim(center_lat - lat_range, center_lat + lat_range)

    # Add title & legend
    ax.set_title(
        "IPC Acute Food Insecurity Levels - Pakistan",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    legend_elements = []
    for phase, color in dataset[['overall_phase', 'color']].drop_duplicates().values:
        legend_elements.append(Patch(facecolor=color, edgecolor=color,
                                     label=f"Level {phase}"))
    ax.legend(
        handles=legend_elements,
        title="IPC Food Phases",
        loc="lower left",
        frameon=True
    )

    # Beautify and save
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_polygon_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load IPC Acute Food Insecurity layer dataset
    file_ipc_food_insecurity = "data/PAK_misc/AcuteFoodInsecurity_ipc_pak_area_long_latest.csv"
    ipc_df = pd.read_csv(file_ipc_food_insecurity)
    # Filter for current projection and get all phases/levels (1-5)
    ipc_df = ipc_df.loc[(ipc_df['Validity period'] == 'first projection') & (ipc_df['Phase'] == 'all')]
    # Keep only relevant columns
    ipc_df = ipc_df[['Date of analysis', 'Area', 'Level 1', 'Number', 'Percentage']]

    # Read ipc geojson
    ipc_pak_geojson = "data/PAK_misc/ipc_pak.geojson"
    ipc_gdf = gpd.read_file(ipc_pak_geojson)
    # Keep only relevant columns
    ipc_gdf = ipc_gdf[['title', 'geometry', 'confidence_level', 'overall_phase', 'color', 'estimated_population']]

    # Merge ipc_gdf with ipc_df to get phase information
    ipc_pak_gdf = ipc_gdf.merge(ipc_df, left_on='title', right_on='Area', how='inner')

    # Function to convert GeometryCollection to MultiPolygon
    def convert_geomcollection_to_multipolygon(geom):
        if isinstance(geom, GeometryCollection):
            # Extract polygons from GeometryCollection parts
            polygons = [part for part in geom.geoms if isinstance(part, Polygon)]
            # Return MultiPolygon constructed from polygons
            return MultiPolygon(polygons)
        else:
            return geom

    # Apply the conversion function to the geometry column
    ipc_pak_gdf['geometry'] = ipc_pak_gdf['geometry'].apply(convert_geomcollection_to_multipolygon)
    # Clean up
    del ipc_gdf, ipc_df
    
    # Create different types of maps
    output_path = f"{Path(path_dir).parent}/{file_out}"
    create_folium_map(ipc_pak_gdf, f"{output_path}.html")
    # create_png_map(ipc_pak_gdf, f"{output_path}.png")
    
    logger.info(f"Map created – open '{file_out}' to view.")


if __name__ == "__main__":
    out_filename = 'AcuteFoodInsecurity_pakistan'
    generate_polygon_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)