import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

from pathlib import Path
from rasterstats import zonal_stats

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Generating {path_dir}")

    # Raster file with the population density data from WorldPop
    pop2025_tif_file = "data/PAK_misc/pak_pop_2025_CN_100m_R2025A_v1.tif"
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    # Keep only necessary columns
    admin_gdf = admin_gdf.loc[:,['COUNTRY', 'NAME_1', 'NAME_2', 'NAME_3', 'geometry']]
    logger.info(f"Number of admin units: {len(admin_gdf)}")

    # Calculate bounds and a center, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")
    
    # Read raster and create statistics per district
    with rasterio.open(pop2025_tif_file) as src:
        raster_crs = src.crs
        # img = src.read(1)
        # img_bounds = src.bounds
        # meta = src.meta.copy()
        # nodata = meta.get("nodata", None)

        if admin_gdf.crs != raster_crs:
            logger.debug(f"Raster CRS - {raster_crs}")
            logger.debug(f"Admin CRS - {admin_gdf.crs}")
            admin_gdf = admin_gdf.to_crs(raster_crs)
        
        stats = zonal_stats(
            vectors=admin_gdf['geometry'],
            raster=pop2025_tif_file,
            stats=["count", "sum", "mean"], # which zonal statistics to compute
            all_touched=True,              # If True, counts any raster cell touched by polygon.
            prefix='pop2025_',
            geojson_out=False,              # we will merge later manually
            nodata=src.nodata,
        )
    
    # stats is a list of dict, one per polygon (admin unit)
    logger.debug(f"Zonal stats computed for {len(stats)} features")

    # Merge stats with our admin units
    pop_stats_gdf = gpd.GeoDataFrame(admin_gdf.copy())
    for s_type in (["count", "sum", "mean"]):
        pop_stats_gdf[f"pop_{s_type}"] = [s.get(f"pop2025_{s_type}") for s in stats]
    
    # Compute derived metrics, e.g., population density, first check if crs is okay
    if not admin_gdf.crs.is_projected:
        logger.warning("Vector CRS is not projected; area computation may not be accurate.")
    
    # Calculate area in sq km, EPSG:32643 UTM CRS for Pakistan
    pop_stats_gdf["area_km"] = pop_stats_gdf.geometry.to_crs(epsg=32643).area / 1e6
    # Density = pop_sum / area
    pop_stats_gdf["pop_density"] = pop_stats_gdf["pop_sum"]/pop_stats_gdf["area_km"]
    
    # Save output
    pop_stats_gdf.to_file(f"data/PAK_misc/pak_population_2025_stats.geojson", driver="GeoJSON")

    # Plotting
    _, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    pop_stats_gdf.plot(
        ax=ax,
        column="pop_density",
        cmap="OrRd",
        linewidth=0.8,
        edgecolor="black",
        legend=True,
        missing_kwds={"color": "lightgrey", "label": "No data"},
        scheme="quantiles", 
        k=5,
    )
    # Beautification
    ax.set_title("2025 - Population Density by Districts")
    ax.axis("off")
    plt.tight_layout()

    # Save as image
    output_path = Path(path_dir).parent / f"{file_out}.png"
    plt.savefig(output_path, dpi=500, bbox_inches="tight")
    logger.info(f"Map created – open '{file_out}.png' to view.")


if __name__ == "__main__":
    # Plot population density over Pakistan as cells
    out_filename = 'populationdensity_cells'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)