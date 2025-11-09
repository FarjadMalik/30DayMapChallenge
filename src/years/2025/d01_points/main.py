import folium
import geopandas as gpd
import pandas as pd

from pathlib import Path
from branca.element import Template, MacroElement

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path

logger = get_logger(__name__)


def create_poi_map(path_dir: str, file_html: str):
    """
    Creates points of interest map, for educational institutes.
    
    """
    logger.info(f"Hello from {path_dir}!")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]
    # logger.debug(f"admin_gdf LEVEL 1 – {admin_gdf['NAME_1'].unique()}")

    
    # Load GeoJSON data for points of interest
    poi_shapefile_path = 'data/hotosm/hotosm_pak_points_of_interest_points_shp.shp'    
    poi_gdf = gpd.read_file(poi_shapefile_path)

    # Keep only amenities of interest in our case educational institutes
    # logger.debug(f"POI Data Coverage – \n{poi_data['amenity'].unique()}")
    amenity_list = ['college', 'university', 'prep_school', 'research_institute', 'school', 'kindergarten']
    aoi_df = poi_gdf.loc[poi_gdf['amenity'].isin(amenity_list)]
    # logger.debug(f"Amnesties of interest Data Length – {len(aoi_df)}")

    if aoi_df.crs != admin_gdf.crs:
        aoi_df.to_crs(admin_gdf.crs.to_string() , inplace=True)

    # Get counts of amnesties (educational institutes) per province (admmin unit)
    aoi_df = gpd.sjoin(aoi_df, admin_gdf, how="left", predicate="within")
    provincial_counts = aoi_df.groupby('NAME_1').size().reset_index(name='count_institutes')
    admin_gdf = admin_gdf.merge(provincial_counts, on='NAME_1', how='left')
    admin_gdf['count_institutes'] = admin_gdf['count_institutes'].fillna(0).astype(int)

    # clean up
    del poi_gdf, provincial_counts

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles='OpenStreetMap')
    colors = {
        'Punjab': 'red',
        'Sindh': 'blue',
        'Balochistan': 'yellow',
        'Khyber-Pakhtunkhwa': 'brown',
        'Azad Kashmir': 'green',
        'Federally Administered Tribal Ar': 'brown',
        'Gilgit-Baltistan': 'orange',
        'Islamabad': 'green'
    }
    # Add the administrative boundaries layer
    folium.GeoJson(
        admin_gdf,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': colors.get(feature['properties']['NAME_1'], 'gray'),
            'color': colors.get(feature['properties']['NAME_1'], 'gray'),
            'weight': 1,
            'opacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME_1', 'count_institutes'], 
            aliases=['Province:', 'Educational Institues:']
        )
    ).add_to(basemap)

    # Define a function to pick circle color based on amenity
    def amenity_color(value: str | None) -> str:
        if value == "university": # graduate level
            return "red"
        elif value == "school" or value == "college": # secondary and higher secondary
            return "green"
        elif value == "prep_school" or value == "kindergarten": # primary level
            return "blue"
        else:    # other
            return "purple"
    
    # Define a function to compute radius based on attributes
    def compute_radius(row, min_radius=4, max_radius=20, scale_factor=1.0):
        """Compute radius in pixels (for CircleMarker) or meters (for Circle)."""
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

    # Iterate and add each point to the map
    for _, row in aoi_df.iterrows():
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
        f'<i style="background:{colors.get(row["NAME_1"], "gray")};'
        f'width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
        f'{row["NAME_1"]}: {int(row["count_institutes"])} POIs<br>'
        for _, row in admin_gdf.iterrows()
    ])

    poi_items = "".join([
        f'<i style="background:{amenity_color(name)};width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
        f'{name}<br>'
        for name in aoi_df.amenity.unique()
    ])

    # Now insert them safely into a triple-quoted string (no f-string)
    legend_html = """
    {% macro html(this, kwargs) %}

    <div style="position: fixed; 
                top: 10px; left: 50px; width: 320px; z-index:9999; 
                background-color: white; border:2px solid grey; border-radius:5px; 
                padding: 10px; font-size:14px;">
        <h4 style="margin-bottom:10px;">Educational Institutes Per Province</h4>
        
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
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'educational_institutes_pakistan'
    create_poi_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)