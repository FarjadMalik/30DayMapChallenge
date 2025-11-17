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
    
def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")
    
    # Define different projections
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
    fig.suptitle("Comparison of 8 Cartopy Map Projections", fontsize=16)

    # Adjust spacing so things are not overlapping
    # Use tight_layout with padding, plus adjust top for suptitle
    plt.tight_layout(pad=3.0, w_pad=2.0, h_pad=2.0)  # pad, width-pad, height-pad :contentReference[oaicite:0]{index=0}
    fig.subplots_adjust(top=0.88)  # leave room for suptitle :contentReference[oaicite:1]{index=1}
    # plt.show()

    # # Define the projections for each of the 4 axes
    # projections = [
    #     ccrs.PlateCarree(),                 # simple geographic (equirectangular)
    #     ccrs.Mollweide(),                    # Mollweide (equal-area)
    #     ccrs.LambertConformal(central_longitude=-100, central_latitude=35),  # Lambert Conformal
    #     ccrs.NorthPolarStereo()              # North Polar Stereographic
    # ]

    # # Create figure + subplots
    # fig = plt.figure(figsize=(12, 8))

    # axes = []  # store axes references
    # for i, proj in enumerate(projections):
    #     ax = fig.add_subplot(2, 2, i + 1, projection=proj)
    #     axes.append(ax)

    # # For demonstration: set extent, add features, plot something simple
    # for ax, proj in zip(axes, projections):
    #     # Set a global or regional extent depending on projection
    #     if isinstance(proj, ccrs.NorthPolarStereo):
    #         # limit to Northern Hemisphere
    #         ax.set_extent([-180, 180, 45, 90], crs=ccrs.PlateCarree())
    #     else:
    #         ax.set_global()

    #     # Add coastlines and land
    #     ax.coastlines(linewidth=1)
    #     ax.add_feature(cfeature.LAND, facecolor='lightgray')
    #     ax.add_feature(cfeature.BORDERS, linestyle=':')

    #     # Add some gridlines
    #     gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
    #     # Draw gridline labels only where it makes sense
    #     gl.top_labels = False
    #     gl.right_labels = False

    #     # As a toy example, plot some random points: longitudes and latitudes
    #     lons = np.random.uniform(-180, 180, size=50)
    #     lats = np.random.uniform(-80, 80, size=50)
    #     ax.scatter(lons, lats, transform=ccrs.PlateCarree(), color='red', s=10)

    #     # Give each subplot a title
    #     ax.set_title(type(proj).__name__)

    # # --- 4. Adjust layout and show ---
    # plt.tight_layout()
    # plt.suptitle("Comparison of Different Cartopy Projections", fontsize=16, y=1.02)
    # plt.show()

    # Save figure
    output_path = f"{Path(path_dir).parent}/{file_out}_8.png"
    plt.savefig(output_path, dpi=500, bbox_inches="tight")
    logger.info(f"Map created – open '{output_path}' to view.")


if __name__ == "__main__":
    # (GIS Day) Focus entirely on map projections. 
    # Choose an unusual or misunderstood projection to highlight a theme, or visualize distortion. (See xkcd.com/977)
    # ccrss projections, plot something from sudan data 
    out_filename = 'world_projections'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)