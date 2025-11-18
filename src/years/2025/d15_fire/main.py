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

def create_animation(admin, dataset, column_to_use, output_path):
    """
    """
    # Plot basics, initialize a cartopy projection and set neutral background
    # proj = ccrs.Gnomonic()
    proj = ccrs.EckertI()
    # proj = ccrs.InterruptedGoodeHomolosine()
    background_color = "#fffdf3"
    
    # set correct projection for the dataset, to be used with ccrs
    admin = admin.to_crs(proj.proj4_init)
    dataset = dataset.to_crs(proj.proj4_init)
    
    # get range of years in the dataset
    min_value = dataset[column_to_use].min()
    max_value = dataset[column_to_use].max()
    
    # For each year map the wild fires
    frames = []
    for v in range(min_value, max_value+1):
        # filter out the desired data
        subset = dataset.loc[dataset[column_to_use]==v]
        
        # plot for the given series
        fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={"projection": proj})
        fig.set_facecolor(background_color)
        # add admin as in (in our case EU) and our fire shapefile for that particular subset (year)
        admin.plot(ax=ax, color="lightgrey", edgecolor="black", lw=0.2)
        subset.plot(ax=ax, color="red", edgecolor="red", lw=0.4)
        # grid lines and title
        ax.gridlines(draw_labels=True, color="grey", linestyle="--", lw=0.5)
        ax.set_title(f"WILDFIRES EU - {v}", fontsize=14)
        
        # Save figure in list
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=500)
        plt.close(fig)
        buf.seek(0)
        frames.append(imageio.v2.imread(buf))
        buf.close()

        # Store images locally if wanted
        # plt.savefig(f"{out_dir}/{file_out}_{y}.png", dpi=500, bbox_inches="tight")

    # Create an animation with the images from each year
    imageio.mimsave(f"{output_path}.gif", frames, duration=2.0)
    
def generate_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Read wildfires dataset
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

    # Read world boundaries
    world = gpd.read_file("data/countries.geojson")
    # only keep eu countries, countries with fires
    world = world.loc[world["name"].isin(effis_gdf["Name"].unique())]
    
    # Create and save animation   
    output_path = os.path.join(f"{Path(path_dir).parent}", f"{filename}")
    create_animation(admin=world, dataset=effis_gdf, column_to_use='YEAR', output_path=output_path)

    logger.info(f"Map created – open '{output_path}' to view.")


if __name__ == "__main__":
    # forest fires over several years in europe
    filename = 'Wildfires_EU_timeseries'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
