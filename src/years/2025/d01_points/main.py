import folium
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch
from branca.element import Template, MacroElement

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path
from src.utils.map_helpers import provincial_colors

logger = get_logger(__name__)


# Define a function to compute radius based on attributes
def compute_radius(row, min_radius=4, max_radius=20, scale_factor=1.0):
    """
    Compute radius in pixels (for CircleMarker) or meters (for Circle).
    """
    # Choose attribute
    val = None
    if pd.notna(row.get('beds')):
        val = row['beds']
    elif pd.notna(row.get('rooms')):
        val = row['rooms']
    # Default if neither
    if val is None:
        return min_radius
    # Scale val to reasonable radius
    # Simple linear scaling: e.g., radius = min_radius + (val * scale_factor)
    radius = min_radius + (val * scale_factor)
    # Cap it at max_radius
    return min(radius, max_radius)

# Define a function to pick circle color based on amenity
def amenity_color(value: str | None) -> str:
    """
    """
    if value == "university": # graduate level
        return "red"
    elif value == "school" or value == "college": # secondary and higher secondary
        return "green"
    elif value == "prep_school" or value == "kindergarten": # primary level
        return "blue"
    else:    # other
        return "purple"
    
def create_html(admin, dataset, output_path):
    """
    """
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles='OpenStreetMap')

    # Add the administrative boundaries layer
    folium.GeoJson(
        admin,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': provincial_colors.get(feature['properties']['NAME_1'], 'gray'),
            'color': provincial_colors.get(feature['properties']['NAME_1'], 'gray'),
            'weight': 1,
            'opacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME_1', 'count_institutes'], 
            aliases=['Province:', 'Educational Institues:']
        )
    ).add_to(basemap)

    # Iterate and add each point to the map
    for _, row in dataset.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x
        pop_text = (
            f"{row.get('name_en', 'Unknown')} <br>"
            f"Type: {row.get('amenity', '')} <br>"
            f"Name Ur: {row.get('name_ur', 'Unknown')} <br>"
            f"OSM Type: {row.get('osm_type', 'Unknown')} <br>"
            f"Hours: {row.get('opening_ho', '12:00')} <br>"
            f"Address: {row.get('addr_full', row.get('NAME_1', 'Unknown'))} <br>"
        )
        radius = compute_radius(row, min_radius=4, max_radius=25, scale_factor=0.5)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=amenity_color(row.get('amenity')),
            fill=True,
            fill_color=amenity_color(row.get('amenity')),
            fill_opacity=0.6,
            popup=folium.Popup(pop_text, max_width=300)
        ).add_to(basemap)
    
    # Add title and legends
    # Build the dynamic HTML fragments separately
    province_items = "".join([
        f'<i style="background:{provincial_colors.get(row["NAME_1"], "gray")};'
        f'width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
        f'{row["NAME_1"]}: {int(row["count_institutes"])} POIs<br>'
        for _, row in admin.iterrows()
    ])

    poi_items = "".join([
        f'<i style="background:{amenity_color(name)};width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
        f'{name}<br>'
        for name in dataset.amenity.unique()
    ])

    # Now insert them safely into a triple-quoted string (no f-string)
    legend_html = """
    {% macro html(this, kwargs) %}

    <div style="position: fixed; 
                top: 10px; left: 50px; width: 320px; z-index:9999; 
                background-color: white; border:2px solid grey; border-radius:5px; 
                padding: 10px; font-size:14px;">
        <h4 style="margin-bottom:10px;"><b>Educational Institutes Per Province</b></h4>
        
        <b>Provinces:</b><br>
        """ + province_items + """<br>
        <b>Education Type:</b><br>
        """ + poi_items + """
    </div>

    {% endmacro %}
    """
    legend = MacroElement()
    legend._template = Template(legend_html)
    basemap.get_root().add_child(legend)

    # Allows toggling between layers interactively
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{output_path}.html")
    

def create_png(admin, dataset, output_path):
    """
    """
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # create fig and axis
    fig, ax = plt.subplots(figsize=(12, 10))

    # plot admin boundaries
    admin.plot(
        ax=ax,
        color=[provincial_colors.get(x) for x in admin['NAME_1']],
        alpha=0.5,
        linewidth=1
    )
    # Set map focus and limits
    ax.set_xlim(center_lon - 9, center_lon + 9)
    ax.set_ylim(center_lat - 9, center_lat + 9)

    # plot dataset
    dataset.plot(
        ax=ax,
        color=[amenity_color(x) for x in dataset['amenity']]
    )
    
    # Add title & legend
    ax.set_title(
        "Educational Institutes Per Province - Pakistan",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    legend_elements = []
    for name in dataset.amenity.unique():
        legend_elements.append(Patch(facecolor=amenity_color(name), edgecolor=amenity_color(name),
                                     label=f"{name}"))

    # Beautify, add legend and save
    ax.legend(
        handles=legend_elements,
        title="Type of Educational Institute",
        loc="upper left",
        frameon=True
    )
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_poi_map(path_dir: str, filename: str):
    """
    Creates points of interest map, for educational institutes.    
    """
    logger.info(f"Generating {path_dir}!")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]
    
    # Load GeoJSON data for points of interest
    poi_shapefile_path = 'data/hotosm/hotosm_pak_points_of_interest_points_shp.shp'    
    poi_gdf = gpd.read_file(poi_shapefile_path)

    # Keep only amenities of interest in our case educational institutes
    # logger.debug(f"POI Data Coverage – \n{poi_data['amenity'].unique()}")
    amenity_list = ['college', 'university', 'prep_school', 'research_institute', 'school', 'kindergarten']
    aoi_gdf = poi_gdf.loc[poi_gdf['amenity'].isin(amenity_list)]
    # logger.debug(f"Amnesties of interest Data Length – {len(aoi_df)}")

    if aoi_gdf.crs != admin_gdf.crs:
        aoi_gdf.to_crs(admin_gdf.crs.to_string() , inplace=True)

    # Get counts of amnesties (educational institutes) per province (admmin unit)
    aoi_gdf = gpd.sjoin(aoi_gdf, admin_gdf, how="left", predicate="within")
    provincial_counts = aoi_gdf.groupby('NAME_1').size().reset_index(name='count_institutes')
    admin_gdf = admin_gdf.merge(provincial_counts, on='NAME_1', how='left')
    admin_gdf['count_institutes'] = admin_gdf['count_institutes'].fillna(0).astype(int)

    # clean up
    del poi_gdf, provincial_counts
    
    # create and save maps
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(admin=admin_gdf, dataset=aoi_gdf, output_path=output_path)
    create_png(admin=admin_gdf, dataset=aoi_gdf, output_path=output_path)

    logger.info(f"Map created – open '{filename}.html' to view.")


if __name__ == "__main__":
    filename = 'educational_institutes_pakistan'
    generate_poi_map(path_dir=str(get_relative_path(__file__)), filename=filename)
