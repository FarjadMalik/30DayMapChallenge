import fiona
import folium
import geopandas as gpd

from pathlib import Path
from shapely.geometry import box
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_polygon_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    # if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
    #     admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Add the administrative boundaries layer
    folium.GeoJson(
        admin_gdf,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 1,
            'dashArray': '5, 5'
        }
    ).add_to(basemap)

    # Load hydro/rivers layer from geopackage
    gdb_path = "data/HydroRIVERS_v10_as.gdb"
    logger.info(f"HydroRIVERS_v10 gdb layers: {fiona.listlayers(gdb_path)}")
    # hydro_gdf = gpd.read_file(gdb_path, layer='HydroRIVERS_v10_as')    
    # hydro_gdf= gpd.clip(hydro_gdf, admin_gdf)    

    # Open the GDB layer with Fiona
    # Use Fiona's bbox filter to read only features within bounds
    with fiona.open(gdb_path, layer='HydroRIVERS_v10_as', bbox=(bounds[0], bounds[1], bounds[2], bounds[3])) as src:
        hydro_gdf = gpd.GeoDataFrame.from_features(src, crs=src.crs)
        
    
    logger.info(f"Hydro gdf len: {len(hydro_gdf)}")
    logger.info(f"Hydro gdf crs: {hydro_gdf.crs}")
    logger.info(f"Hydro gdf head: {hydro_gdf.head()}")
    
    with fiona.open(gdb_path, layer='HydroRIVERS_v10_as') as src:
        # Create a generator for features that intersect the bbox
        filtered_features = (
            feat for feat in src 
            if box(*src.bounds).intersects(box(bounds[0], bounds[1], bounds[2], bounds[3]))
        )
        
        # Convert filtered features to a GeoDataFrame
        hydro_gdf = gpd.GeoDataFrame.from_features(filtered_features, crs=src.crs)

    logger.info(f"Hydro gdf len: {len(hydro_gdf)}")
    logger.info(f"Hydro gdf crs: {hydro_gdf.crs}")
    logger.info(f"Hydro gdf head: {hydro_gdf.head()}")

    # Add hydro/rivers layer to map
    folium.GeoJson(
        hydro_gdf,
        name='Hydro Rivers',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 1,
        },
        # highlight_function=lambda feature: {
        #     "weight": 3,
        #     "color": "red"
        # }
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'AcuteFoodInsecurity_pakistan'
    create_polygon_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)