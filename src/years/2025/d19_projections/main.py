import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def map_projection(ax, projection, title, extent=None):
    """
    Helper to draw a map on a given axis with standard features.
    """
    ax.set_title(title, fontsize=12, pad=10)
    # Set map extent
    if extent is not None:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    else:
        ax.set_global()
    # Add features
    ax.coastlines(resolution='110m', linewidth=0.8)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    # Gridlines
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.5, color='gray', alpha=0.7)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}
    # Plot some sample points
    lons = np.random.uniform(-180, 180, 100)
    lats = np.random.uniform(-80, 80, 100)
    ax.scatter(lons, lats, transform=ccrs.PlateCarree(), color='red', s=8, alpha=0.7)
    
def create_projection_png(projections, output_path):
    # Create figure
    fig = plt.figure(figsize=(20, 8))
    # Create subplots in 2 rows × 4 columns
    axes = []
    for i, (proj, title) in enumerate(projections):
        ax = fig.add_subplot(2, 4, i + 1, projection=proj)
        # For polar projections, set a limited extent
        if isinstance(proj, (ccrs.NorthPolarStereo, ccrs.SouthPolarStereo)):
            # For north, show from 30°N to pole; for south, similarly
            lat_lim = (30, 90) if isinstance(proj, ccrs.NorthPolarStereo) else (-90, -30)
            ax.set_extent([-180, 180, lat_lim[0], lat_lim[1]], crs=ccrs.PlateCarree())
        map_projection(ax, proj, title)
        axes.append(ax)

    # Add a super-title
    fig.suptitle(f"Comparison of {len(projections)} Cartopy Map Projections", fontsize=16)

    # Adjust spacing so things are not overlapping
    # Use tight_layout with padding, plus adjust top for suptitle
    plt.tight_layout(pad=3.0, w_pad=2.0, h_pad=2.0)  # pad, width-pad, height-pad :contentReference[oaicite:0]{index=0}
    fig.subplots_adjust(top=0.88)  # leave room for suptitle :contentReference[oaicite:1]{index=1}
       
    plt.savefig(f"{output_path}_{len(projections)}", dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
    """   
    """
    logger.info(f"Generating {path_dir}")
        
    # Define different projections to be visualized
    projections = [
        (ccrs.PlateCarree(), "Plate Carrée"),
        (ccrs.Mollweide(), "Mollweide"),
        (ccrs.Robinson(), "Robinson"),
        (ccrs.LambertConformal(central_longitude=-100, central_latitude=45), "Lambert Conformal"),
        (ccrs.Mercator(), "Mercator"),
        (ccrs.LambertAzimuthalEqualArea(central_longitude=0, central_latitude=0), "Lambert Azimuthal EQ"),
        (ccrs.NorthPolarStereo(), "North Polar Stereo"),
        (ccrs.SouthPolarStereo(), "South Polar Stereo"),
    ]

    # Generate and save figure
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_projection_png(projections, output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # (GIS Day) Focus entirely on map projections. See xkcd.com/977)
    filename = 'world_projections'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
