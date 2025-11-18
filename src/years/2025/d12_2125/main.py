import rasterio
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_raster_png(admin, raster, raster_bounds, title, output_path, text=None):
    """
    """
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin is not None and admin.crs.to_string() != "EPSG:4326":
        admin = admin.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin.total_bounds  # [minx, miny, maxx, maxy] 
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    fig, ax = plt.subplots(figsize=(8,6))
    
    # Plot the polygon layer first, boundary only if needed
    # world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.0)

    # Plot the mask raster on top  
    # We need to consider the spatial extent if this is georeferenced.
    # If mask is aligned in pixel coordinates only, you may not specify extent.
    im = ax.imshow(raster,
                cmap="Blues",
                alpha=0.7,
                extent=(raster_bounds[0], raster_bounds[2], raster_bounds[1], raster_bounds[3]), 
                # [left, right, bottom, top],
                origin='upper')   # adjust origin if needed

    # Title & colorbar
    ax.set_title(f"")
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', label="Inundated (1=yes)")

    # Axis labels, aspect
    ax.set_xlabel("Longitude / Easting")
    ax.set_ylabel("Latitude / Northing")
    ax.set_aspect('equal')  # so map scales properly for geographic display 
    # ax.set_axis_off()   
    if text is not None:
        # Add text at bottom‑left
        ax.text(
            -0.6,            # x‑coordinate in axes fraction (just inside left)
            0.9,            # y‑coordinate in axes fraction (just inside bottom)
            f"{text}", 
            transform=ax.transAxes,         # use axes coordinate system (0,0 = bottom left, 1,1 = top right)
            ha='left',                      # horizontal alignment of text box (“left” means text start at x position)
            va='bottom',                    # vertical alignment (“bottom” means the bottom of text is at y position)
            fontsize=10,
            color='black',                  # or whatever colour suits
            bbox=dict(facecolor='red', alpha=0.5)  # background box to make it stand out
        )
    # plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    

def generate_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")
    
    # Read our world data and filter on the country of interest
    world = gpd.read_file("data/countries.geojson")
    # world = world.to_crs(proj.proj4_init)
    world = world[world["name"].isin(["Sri Lanka"])]
    
    # Load and read raster 
    dem_path = "data/output_hh.tif"
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        meta = src.meta.copy()
        img_bounds = src.bounds
    nodata = meta.get("nodata", None)
    
    # Sea Level Rise scenarios in meters
    # sea_rise_scenarios = [0.5, 1.0, 2.0] 
    sr = 2.0 # which is the average model speculation
    logger.debug(f"Simulating sea level rise = {sr} m")
    
    # Mask dem values below our sea level speculation
    # DEM values are already in meters
    mask = (dem > 0.0) & (dem <= sr)
    if nodata is not None:
        mask = np.where(dem == nodata, False, mask)
        
    # Calculate how much of the island will be under water
    frac = np.count_nonzero(mask) / np.count_nonzero(dem)
    logger.debug(f"Fraction inundated  ->  {frac:.2%}")
    
    # save raster
    out_meta = meta.copy()
    out_meta.update({"dtype": "uint8", "count": 1})
    out_path = Path(path_dir).parent / f"srilanka_inundation_{sr:.1f}m.tif"
    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(mask.astype(np.uint8), 1)
    
    # Save as image
    output_path = Path(path_dir).parent / f"{filename}"
    title = f"Sea Level Inundation at {sr:.1f} m rise Sri Lanka"
    complimentary_text = f"{frac:.2%} of Sri Lanka \nwill be under water\nby 2125"
    create_raster_png(world, mask, img_bounds, title, output_path, complimentary_text)

    logger.info(f"Map created – open '{filename}' to view.")

if __name__ == "__main__":
    # remove water and national borders, show map with small communities, maybe a projection?
    filename = 'SeaLevelRise_2125'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
