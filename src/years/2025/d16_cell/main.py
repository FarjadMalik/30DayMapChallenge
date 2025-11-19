import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

from pathlib import Path
from rasterstats import zonal_stats

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_png(dataset, column_to_use, output_path):
    """
    """
    # Plotting
    _, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    dataset.plot(
        ax=ax,
        column=column_to_use,
        cmap="OrRd",
        linewidth=0.8,
        edgecolor="black",
        legend=True,
        missing_kwds={"color": "lightgrey", "label": "No data"},
        scheme="quantiles", 
        k=5,
    )
    # Beautification
    ax.set_title("2025 - Population Density (Per Km) by Districts")
    ax.axis("off")
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_zonal_stats(admin, raster_path, output_path=None):
    """
    """
    # Read raster and create statistics per district
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        # img = src.read(1)
        # img_bounds = src.bounds
        # meta = src.meta.copy()
        # nodata = meta.get("nodata", None)

        if admin.crs != raster_crs:
            logger.debug(f"Raster CRS - {raster_crs}")
            logger.debug(f"Admin CRS - {admin.crs}")
            admin = admin.to_crs(raster_crs)
        
        stats = zonal_stats(
            vectors=admin['geometry'],
            raster=raster_path,
            stats=["count", "sum", "mean"], # which zonal statistics to compute
            all_touched=True,              # If True, counts any raster cell touched by polygon.
            prefix='stat_',
            geojson_out=False,              # we will merge later manually
            nodata=src.nodata,
        )
    
    # Merge stats with our admin units
    stats_gdf = gpd.GeoDataFrame(admin.copy())
    for s_type in (["count", "sum", "mean"]):
        stats_gdf[f"stat_{s_type}"] = [s.get(f"stat_{s_type}") for s in stats]
    
    # Compute derived metrics, e.g., population density, first check if crs is okay
    if not admin.crs.is_projected:
        logger.warning("Vector CRS is not projected; area computation may not be accurate.")
    
    # Calculate area in sq km, EPSG:32643 UTM CRS for Pakistan
    stats_gdf["area_km"] = stats_gdf.geometry.to_crs(epsg=32643).area / 1e6
    # Density = pop_sum / area
    stats_gdf["stat_density"] = stats_gdf["stat_sum"]/stats_gdf["area_km"]
    
    # Save output
    if output_path:
        stats_gdf.to_file(f"{output_path}.geojson", driver="GeoJSON")

    return stats_gdf

def generate_cellular_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Raster file with the population density data from WorldPop
    pop2025_tif_file = "data/PAK_misc/pak_pop_2025_CN_100m_R2025A_v1.tif"
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    # Keep only necessary columns
    admin_gdf = admin_gdf.loc[:,['COUNTRY', 'NAME_1', 'NAME_2', 'NAME_3', 'geometry']]

    pop_stats_gdf = generate_zonal_stats(admin=admin_gdf, raster_path=pop2025_tif_file, 
                                         output_path='data/PAK_misc/pak_population_2025_stats')    

    # Save as image
    output_path = Path(path_dir).parent / f"{filename}"
    create_png(pop_stats_gdf, "stat_density", output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Plot population density over Pakistan as cells
    filename = 'populationdensity_cells'
    generate_cellular_map(path_dir=str(get_relative_path(__file__)), filename=filename)
