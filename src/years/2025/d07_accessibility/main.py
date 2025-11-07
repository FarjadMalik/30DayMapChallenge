import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from pathlib import Path
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge, unary_union
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def get_start_end_points(route_gdf):
    """
    Determine the start and end points of the route.
    Works whether the geometry is a LineString or MultiLineString.
    Returns tuple (start_point, end_point) as shapely Points.
    """
    # Combine all geometries
    unioned = unary_union(route_gdf.geometry)
    # Try to merge into contiguous segments
    merged = linemerge(unioned)
    # If still MultiLineString, optionally pick the longest segment
    if isinstance(merged, MultiLineString):
        # determine the longest linestring component
        merged = max(merged.geoms, key=lambda ls: ls.length)
        # return longest  # return a single LineString
    
    if not isinstance(merged, LineString):
        raise ValueError("Expected a LineString geometry, got %s" % type(line_geom))
    coords = list(merged.coords)
    start_pt = Point(coords[0])
    end_pt   = Point(coords[-1])
    return start_pt, end_pt

    # merged = route_gdf.geometry.unary_union
    # # If it’s a MultiLineString, merge into one LineString if possible
    # if isinstance(merged, MultiLineString):
    #     merged = linemerge(merged)
    # logger.info(f"Merged geometry type: {type(merged)}")
    # # After merging we expect a LineString
    # if isinstance(merged, LineString):
    #     coords = list(merged.coords)
    # else:
    #     # fallback: if still multi or something else, take first part
    #     try:
    #         coords = list(merged.geoms)[0].coords
    #     except Exception:
    #         raise ValueError("Cannot determine start/end of geometry type: %s" % type(merged))
    # start_pt = Point(coords[0])
    # end_pt   = Point(coords[-1])
    # return start_pt, end_pt

def add_route_to_map(route_gdf, fmap, popup_field="etapa"):
    """Add the route geometry to Folium map with popups on each segment."""
    for _, row in route_gdf.iterrows():
        geom = row.geometry
        label = f"{popup_field}: {row.get(popup_field, 'N/A')}"
        folium.GeoJson(
            geom,
            tooltip=label,
            style_function=lambda x: {"color": "#FF6600", "weight": 3, "opacity": 0.8}
        ).add_to(fmap)

def add_point_marker(point, fmap, label, color="blue"):
    """Add a point marker to Folium map."""
    folium.CircleMarker(
        location=(point.y, point.x),
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=label
    ).add_to(fmap)

def compute_total_length(route_gdf):
    """
    Approximate total length of the route in km.
    Uses geodetic length calculation by re-projecting to an appropriate CRS.
    """
    # project to a metric CRS (here UTM zone 30N for Spain approx)
    metric = route_gdf.to_crs(epsg=25830)
    length_m = metric.geometry.length.sum()
    return length_m / 1000.0  # km

def plot_route_map(route_gdf, output_png):
    """Create the figure and save to PNG."""
    fig, ax = plt.subplots(figsize=(12, 8))
    route_gdf.plot(ax=ax, linewidth=2.5, color="#FF4500", label="Camino Francés")
    start_pt, end_pt = get_start_end_points(route_gdf)
    # Plot points
    ax.scatter(start_pt.x, start_pt.y, color="green", s=100, label="Start")
    ax.scatter(end_pt.x, end_pt.y, color="red", s=100, label="End")

    # Compute length and annotate
    total_km = compute_total_length(route_gdf)
    ax.text(0.02, 0.95, f"Total length ≈ {total_km:.1f} km", transform=ax.transAxes,
            fontsize=14, color="#333", verticalalignment='top')

    # Add legend
    start_patch = mpatches.Patch(color='green', label='Start Point')
    end_patch = mpatches.Patch(color='red', label='End Point')
    route_patch = mpatches.Patch(color='#FF4500', label='Route Path')
    ax.legend(handles=[route_patch, start_patch, end_patch], loc="lower left")

    ax.set_title("Camino Francés – Pilgrim Route Accessibility Map", fontsize=16)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved static map PNG to {output_png}")
    
def create_accessibility_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/Camino/CaminoDeSantiago_CSFFR.shp"
    camino_fr_gdf = gpd.read_file(shapefile_path)

    # # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if camino_fr_gdf is not None and camino_fr_gdf.crs.to_string() != "EPSG:4326":
        camino_fr_gdf = camino_fr_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = camino_fr_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    # Extract the route as a GeoDataFrame
    route = camino_fr_gdf.sort_values(by='etapa').reset_index(drop=True)
    start_pt, end_pt = get_start_end_points(route)
    total_km = compute_total_length(route)

    # add route
    add_route_to_map(route, basemap, popup_field="etapa")

    # add start/end markers
    add_point_marker(start_pt, basemap, f"START → Id {route.iloc[0]['id_camino']} – {route.iloc[0]['camino']}", color="green")
    add_point_marker(end_pt, basemap, f"END → {route.iloc[-1]['camino']}", color="red")

    # Add a popup or marker for total length
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.DivIcon(html=f"""<div style="font-size:14pt; color:#333;">Total length ≈ {total_km:.1f} km</div>""")
    ).add_to(basemap)


    # # Add the polygon layer to the map
    # folium.GeoJson(
    #     camino_fr_gdf,
    #     name='Camino de Santiago',
    #     style_function=lambda feature: {
    #         'fillColor': 'blue',
    #         'color': 'blue',
    #         'weight': 2,
    #         'fillOpacity': 0.5,
    #     }
    # ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")

    # Also create a static PNG map
    output_png = f"{Path(path_dir).parent}/{file_html}.png"
    plot_route_map(route, output_png)


if __name__ == "__main__":
    out_filename = 'camino_de_santiago'
    create_accessibility_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)