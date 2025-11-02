import folium
import geopandas as gpd
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_poi_map():
    logger.info("Hello from d01_points!")

    # 1. Load the shapefile (replace the path with your actual .shp file)
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # 2. Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # 3. Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # 4. Create the Folium map, centered on Pakistan (admin boundaries center)
    pk_basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # 5. Add the administrative boundaries layer
    folium.GeoJson(
        admin_gdf,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 1,
            'dashArray': '5, 5'
        }
    ).add_to(pk_basemap)

    # # Load GeoJSON data for drinking water plants
    # with open('data/PAK_misc/drinkingwater_overpass_pak.geojson', 'r', encoding="utf-8") as f:
    #     poi_data = json.load(f)

    # Load GeoJSON data for points of interest
    # with open('data/hotosm/hotosm_pak_points_of_interest_points_shp.shp', 'r', encoding="utf-8") as f:
    poi_shapefile_path = 'data/hotosm/hotosm_pak_points_of_interest_points_shp.shp'    
    poi_data = gpd.read_file(poi_shapefile_path)

    # logger.info(f"POI Data Loaded – \n{poi_data.head()}")
    # logger.info(f"POI Data Columns – \n{poi_data.columns}")
    logger.info(f"POI Data Length – \n{len(poi_data)}")
    # logger.info(f"POI Data Coverage – \n{poi_data['amenity'].unique()}")

    # hospitals = poi_data[poi_data['amenity'] == 'clinic;hospital']
    # hospitals = poi_data.query("amenity == 'clinic;hospital' or amenity == 'hospital' or amenity == 'clinic'")
    amenity_list = ['clinic;hospital', 'hospital', 'clinic', 'pharmacy', 'doctors', 'food', 'waste_basket']
    aoi_df = poi_data.loc[poi_data['amenity'].isin(amenity_list)]
    logger.info(f"Amnesties of interest Data Length – \n{len(aoi_df)}")

    # Option 1: Add points of interest to the map, using geojson code directly for shapefile
    # folium.GeoJson(
    #     poi_data,
    #     name='Points of Interest',
    #     # style for non‑point geometries (if any)
    #     style_function = lambda feature: {
    #         'color': 'red',
    #         'weight': 1
    #     },
    #     # marker parameter for point geometries
    #     marker = folium.CircleMarker(
    #         radius = 6,
    #         color = 'red',
    #         fill = True,
    #         fill_color = 'red',
    #         fill_opacity = 0.7
    #     )
    #     ).add_to(pk_basemap)

    # Option 2: Add points of interest to the map, iterating through GeoDataFrame
    # Define a function to pick circle color based on amenity
    def amenity_color(value: str | None) -> str:
        if value == "food":
            return "blue"
        elif value == "waste_basket":
            return "green"
        elif value == "doctors" or value == "pharmacy":
            return "purple"
        else:
            return "red"
    
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
            f"{row.get('name_en', '')} <br>"
            f"Amenity: {row.get('amenity', '')} <br>"
            f"Address: {row.get('addr_full', '')} <br>"
            f"Address: {row.get('addr_full', '')} <br>"
            f"Address: {row.get('addr_full', '')} <br>"
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
        ).add_to(pk_basemap)

    # Save the map to an HTML file
    pk_basemap.save("src/years/2025/d01_points/pk_poi_map.html")
    logger.info("Map created – open 'admin_boundaries_map.html' to view.")


if __name__ == "__main__":
    create_poi_map()