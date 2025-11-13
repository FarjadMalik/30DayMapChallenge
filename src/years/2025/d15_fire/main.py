import os
import imageio
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from pathlib import Path
from io import BytesIO
from shapely import make_valid

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
    
    # Read wildfires dataset (per year for countries)
    effis_gdf = gpd.read_file(shp_file)
    # Merge with country codes to get actual country name
    countrycodes = pd.read_csv("data/country-codes-list.csv")
    effis_gdf = effis_gdf.merge(countrycodes, how="left", left_on="COUNTRY", right_on="Code")
    # Remove extra column
    effis_gdf.drop(columns=['COUNTRY'], inplace=True)
    
    # Plot basics
    # proj = ccrs.Gnomonic()
    proj = ccrs.EckertI()
    # proj = ccrs.InterruptedGoodeHomolosine()
    background_color = "#fffdf3"
    
    # set correct projection for the dataset, to be used with ccrs
    effis_gdf = effis_gdf.to_crs(proj.proj4_init)
    # Read world boundaries
    world = gpd.read_file("data/countries.geojson")
    world = world.to_crs(proj.proj4_init)
    # only keep eu countries, countries with fires
    world = world.loc[world["name"].isin(effis_gdf["Name"].unique())]

    # if needed to store each image locally in a cache dir
    # out_dir = f"{Path(path_dir).parent}/.cache"
    # os.makedirs(out_dir, exist_ok=True)

    # get range of years in the dataset
    min_year = effis_gdf["YEAR"].min()
    max_year = effis_gdf["YEAR"].max()
    logger.debug(f"effis gdf min max - {min_year, max_year}")
    
    # For each year map the wild fires
    frames = []
    for y in range(min_year, max_year+1):
        logger.debug(y)
        # filter out the desired year
        effis_y_gdf = effis_gdf.loc[effis_gdf['YEAR']==y]
        
        # plot
        fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={"projection": proj})
        fig.set_facecolor(background_color)
        # add world (EU) and our fire shapefile for that year
        world.plot(ax=ax, color="lightgrey", edgecolor="black", lw=0.2)
        effis_y_gdf.plot(ax=ax, color="red", edgecolor="red", lw=0.4)
        # grid lines and title
        ax.gridlines(draw_labels=True, color="grey", linestyle="--", lw=0.5)
        ax.set_title(f"WILDFIRES EU - {y}", fontsize=14)
        
        # Save figure in list
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=500)
        plt.close(fig)
        buf.seek(0)
        frames.append(imageio.v2.imread(buf))
        buf.close()

        # Store images locally if wanted
        # plt.tight_layout()
        # plt.savefig(f"{out_dir}/{file_out}_{y}.png", dpi=500, bbox_inches="tight")

    # Create an animation with the images from each year
    gif_name = os.path.join(f"{Path(path_dir).parent}", f"Yearly_wildfires_EU_timeseries.gif")
    imageio.mimsave(gif_name, frames, duration=2.0)
    logger.info(f"Map created – open '{gif_name}' to view.")


if __name__ == "__main__":
    # forest fires over several years in europe
    out_filename = 'wildfires_eu'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)
