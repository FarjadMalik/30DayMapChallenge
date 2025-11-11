import rasterio
import folium
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from rasterio import features

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def generate_map(path_dir: str, file_html: str):
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
    
    # Create and Center a base map
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')

    # Add desired data

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")

def load_dem(path):
    with rasterio.open(path) as src:
        dem = src.read(1)
        meta = src.meta.copy()
    return dem, meta

def compute_inundation_mask(dem, sea_rise, nodata=None):
    mask = dem <= sea_rise
    if nodata is not None:
        mask = np.where(dem == nodata, False, mask)
    return mask

def mask_to_vector(mask, meta, transform, min_area=1000):
    # convert mask to polygons (optionally filter small areas)
    shapes = features.shapes(mask.astype(np.uint8), transform=transform)
    geoms = []
    vals = []
    for geom, val in shapes:
        if val == 1:
            geoms.append(geom)
            vals.append(val)
    gdf = gpd.GeoDataFrame({"value": vals}, geometry=geoms, crs=meta["crs"])
    # filter by area if needed
    if min_area:
        gdf["area"] = gdf.geometry.area
        gdf = gdf[gdf["area"] >= min_area]
    return gdf

def main(dem_path, sea_rise_list):
    dem, meta = load_dem(dem_path)
    nodata = meta.get("nodata", None)
    for sr in sea_rise_list:
        print(f"Simulating sea level rise = {sr} m")
        mask = compute_inundation_mask(dem, sr, nodata=nodata)
        frac = np.count_nonzero(mask) / mask.size
        print(f" -> Fraction inundated: {frac:.2%}")
        # save raster
        out_meta = meta.copy()
        out_meta.update({"dtype": "uint8", "count": 1})
        out_path = f"inundation_{sr:.1f}m.tif"
        with rasterio.open(out_path, "w", **out_meta) as dst:
            dst.write(mask.astype(np.uint8), 1)
        # optionally vectorise
        # gdf = mask_to_vector(mask, meta, transform=meta["transform"])
        # gdf.to_file(f"inundation_{sr:.1f}m.geojson", driver="GeoJSON")
        # plot
        plt.figure(figsize=(8,6))
        plt.imshow(mask, cmap="Blues")
        plt.title(f"Inundation map at {sr:.1f} m rise")
        plt.colorbar(label="Inundated (1=yes)")
        plt.show()


if __name__ == "__main__":
    # remove water and national borders, show map with small communities, maybe a projection?
    out_filename = '2125_map'
    generate_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)    
    dem_path = "your_dem_srilanka.tif"
    # choose scenarios
    sea_rise_scenarios = [0.5, 1.0, 2.0]
    main(dem_path, sea_rise_scenarios)
