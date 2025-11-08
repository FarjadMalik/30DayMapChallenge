import fiona
import folium
import geopandas as gpd

from pathlib import Path
from shapely.geometry import box
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_urban_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    admin_shp_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(admin_shp_path)
    # Filter for urban areas of interest: Islamabad, Lahore, Karachi
    admin_of_interest = ['Islamabad', 'Lahore', 'Karachi']
    admin_gdf = admin_gdf[admin_gdf['NAME_2'].isin(admin_of_interest)]
    admin_gdf = admin_gdf.reset_index(drop=True)
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'NAME_2', 'NAME_3', 'TYPE_3', 'geometry']]

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='OpenStreetMap')

    # Load the natural spaces shapefile
    natural_shp_path = "data/PAK_misc/natural.shp"
    natural_gdf = gpd.read_file(natural_shp_path)
    # Filter for natural green spaces (e.g., parks, forests)
    green_gdf = natural_gdf[natural_gdf['type'].isin(['forest', 'park'])]

    # Calculate urban green percentage for each admin unit
    # -------------------------------------------------------    
    # Reproject both to a metric CRS (UTM zone 43N for Pakistan)
    gdf_admin = admin_gdf.to_crs(epsg=32643)
    gdf_green = green_gdf.to_crs(epsg=32643)

    # Compute intersection between admin units and green areas
    gdf_intersection = gpd.overlay(gdf_admin, gdf_green, how="intersection")

    # Compute area (in square meters)
    gdf_admin["admin_area_m2"] = gdf_admin.geometry.area
    gdf_intersection["green_area_m2"] = gdf_intersection.geometry.area

    # Sum up green area by each admin unit
    # Replace "admin_id" below with your column identifying each admin unit
    id_col = "NAME_3"

    green_by_admin = (
        gdf_intersection.groupby(id_col)["green_area_m2"]
        .sum()
        .reset_index()
    )
    # Merge back with the admin GeoDataFrame
    gdf_admin = gdf_admin.merge(green_by_admin, on=id_col, how="left")
    # Fill NaN (for admins without green areas)
    gdf_admin["green_area_m2"] = gdf_admin["green_area_m2"].fillna(0)
    # Calculate percentage of green area
    gdf_admin["green_pct"] = (
        gdf_admin["green_area_m2"] / gdf_admin["admin_area_m2"] * 100
    )
    # Merge percentage back to original admin_gdf (in WGS84)
    admin_gdf['green_pct'] = gdf_admin.set_index(id_col).loc[
        admin_gdf[id_col], "green_pct"
    ].values
    # -------------------------------------------------------

    # Clip natural green spaces to urban areas
    green_urban_gdf = gpd.overlay(green_gdf, admin_gdf, how='intersection')
    green_urban_gdf = green_urban_gdf.reset_index(drop=True)

    # Add admin boundaries to the map
     # Add urban area polygons to the map
    folium.GeoJson(
        admin_gdf,
        name="Urban Areas",
        style_function=lambda feature: {
            'fillColor': 'black',
            'color': 'black',
            'weight': 4
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME_3', 'green_pct'],
            aliases=['Urban Area:', 'Green Area Percentage:'],
            localize=True
        )
    ).add_to(basemap)
    
    # Add natural green spaces to the map
    folium.GeoJson(
        green_urban_gdf,
        name="Natural Green Spaces",
        style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'green',
            'weight': 2,
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'type', 'NAME_3'],
            aliases=['Name:', 'Type:', 'District:'],
            localize=True
        )
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    # TODO: Plot natural green spaces in urban areas of pakistan isb, khi, lhr
    # Use natural shape file from OSM and filter by urban areas
    out_filename = 'pk_urban_green_mapping'
    create_urban_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)