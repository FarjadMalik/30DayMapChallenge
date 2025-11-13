import pandas as pd
import geopandas as gpd
from shapely import make_valid

from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def explore_and_repivot_dataset(out_shp: str):
    """
    Convert individual fire events into a dissolved fire map over years and per country
    """
    effis_gdf = gpd.read_file("data/effis_layer/modis.ba.poly.shp")
    # Filter out relevant data
    effis_gdf = effis_gdf.loc[effis_gdf['CLASS'] == 'FireSeason', 
                              ['id', 'FIREDATE', 'COUNTRY', 'AREA_HA', 'geometry']]
    effis_gdf['FIREDATE'] = pd.to_datetime(effis_gdf['FIREDATE'], format='mixed')
    # Make year column to base our analysis on
    effis_gdf['YEAR'] = effis_gdf['FIREDATE'].dt.year
    effis_gdf.drop(columns='FIREDATE', inplace=True)
    # Fix/Remove invalid geometries
    invalid = effis_gdf[~effis_gdf.is_valid]
    logger.debug(f"{len(invalid)} invalid geometries found")
    effis_gdf["geometry"] = effis_gdf["geometry"].apply(make_valid)
    effis_gdf = effis_gdf[effis_gdf.is_valid & ~effis_gdf.is_empty]
    # group by year and country
    effis_gdf = effis_gdf.dissolve(by=["YEAR", "COUNTRY"],
                                   aggfunc={
                                       "AREA_HA": "sum",
                                    #    "FIREDATE": "first"       # keep first date (or "min" if you want earliest)
                                       }
                                       ).reset_index()
    effis_gdf.to_file(out_shp)

def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Generating {path_dir}")
    shp_file = Path("data/effis_layer/effis_pc_by_year.shp")
    if not shp_file.exists():
        explore_and_repivot_dataset(str(shp_file))
    
    effis_gdf = gpd.read_file(shp_file)
    # logger.debug(f"effis gdf head - {effis_gdf.head()}")
    # logger.debug(f"effis gdf len - {len(effis_gdf)}")
    # logger.debug(f"effis gdf columns - {effis_gdf.columns}")

    countrycodes = pd.read_csv("data/country-codes-list.csv")
    # logger.debug(f"countrycodes head - {countrycodes.head()}")
    # logger.debug(f"countrycodes len - {len(countrycodes)}")
    # logger.debug(f"countrycodes columns - {countrycodes.columns}")

    effis_gdf = effis_gdf.merge(countrycodes, how="left", left_on="COUNTRY", right_on="Code")
    effis_gdf.drop(columns=['COUNTRY'], inplace=True)
    # logger.debug(f"effis gdf head - {effis_gdf.head()}")
    # logger.debug(f"effis gdf len - {len(effis_gdf)}")
    # logger.debug(f"effis gdf columns - {effis_gdf.columns}")
    # logger.debug(f"effis gdf Name count - {effis_gdf[['YEAR', 'Name']].groupby('Name').count()}")
    min_year = effis_gdf["YEAR"].min()
    max_year = effis_gdf["YEAR"].max()
    logger.debug(f"effis gdf min max - {min_year, max_year}")
    for y in range(min_year, max_year+1):
        logger.debug(y)
        effis_y_gdf = effis_gdf.loc[effis_gdf['YEAR']==y]
        logger.debug(f"effis gdf len - {len(effis_y_gdf)}")
        logger.debug(f"effis country count - {effis_y_gdf.groupby('Name').count()}")


    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = effis_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")
    
    # # Create and Center a base map
    # basemap = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')

    # # Add desired data

    # # Allows toggling between layers interactively 
    # folium.LayerControl().add_to(basemap)
    # # Save the map to an HTML file
    # basemap.save(f"{Path(path_dir).parent}/{file_out}.html")
    # logger.info(f"Map created – open '{file_out}.html' to view.")


if __name__ == "__main__":
    # forest fires over several years in europe
    out_filename = 'wildfires_eu'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)