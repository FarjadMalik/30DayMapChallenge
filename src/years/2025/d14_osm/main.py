import geopandas as gpd

from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def generate_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    admin_gdf = admin_gdf.loc[admin_gdf['NAME_1'] == 'Karachi',
                              ['NAME_1', 'geometry']]
    # Ensure the CRS is WGS84 (EPSG:4326)
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Load Osm data
    # poi_gdf = gpd.read_file("data/hotosm/hotosm_pak_points_of_interest_points_shp.shp")
    # amenity_list = ['college', 'university', 'prep_school', 'research_institute', 'school', 'kindergarten']
    # aoi_df = poi_gdf.loc[poi_gdf['amenity'].isin(amenity_list), []]

    # if aoi_df.crs != admin_gdf.crs:
    #     aoi_df.to_crs(admin_gdf.crs.to_string() , inplace=True)
    
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")


if __name__ == "__main__":
    # Get osm for pakistan and display important areas of centers
    # Karachi, fast food vs other needed amneties, health vs education vs recreation vs basic needs
    out_filename = 'osm_map'
    generate_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)
