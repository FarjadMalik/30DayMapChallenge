import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx

from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.ops import linemerge, unary_union
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def get_start_end_points(route_gdf):
    """
    Determine the start and end points of the route. Takes as input a route sorted by order,
    and then takes first and last segment. Works whether the geometry is a LineString or MultiLineString.

    Returns tuple (start_point, end_point) as shapely Points.
    """
    if route_gdf.empty:
        raise ValueError("func get_start_end_points received empty GeoDataFrame")

    first_segment = route_gdf.iloc[0].geometry
    # Second last because of id_etap 32a and 32b at the end and 32a ends at the correct end point
    last_segment = route_gdf.iloc[-2].geometry
    
    if not isinstance(first_segment, LineString) or not isinstance(last_segment, LineString):
        raise ValueError(f"func get_start_end_points expects LineString geometries segments, got {type(first_segment)} and {type(last_segment)}")

    # Extract coordinates
    first_segment_coords = list(first_segment.coords)
    start_pt = Point(first_segment_coords[0])    
    last_segment_coords = list(last_segment.coords)
    end_pt   = Point(last_segment_coords[-1])
    return start_pt, end_pt

def add_route_to_map(route_gdf, fmap):
    """
    Add the route geometry to Folium map with popups on each segment.
    """
    for _, row in route_gdf.iterrows():
        geom = row.geometry
        label = f"Segment: {row.get('etapa', 'Unknown')}\nDistance to next: {row.get('lon_etapa', '-')} km"
        folium.GeoJson(
            geom,
            tooltip=label,
            style_function=lambda x: {"color": "#FF6600", "weight": 5, "opacity": 0.7}
        ).add_to(fmap)
        last_point = None
        if isinstance(geom, LineString):
            last_point = Point(geom.coords[-1])
            stop = row.get('etapa', 'Unknown')
            folium.CircleMarker(
                location=(last_point.y, last_point.x),
                radius=6,               # size of the circle in pixels
                color="#FF4400",        # outline color
                fill=True,
                fill_color="#FF4400",   # fill color (same as outline if you want solid color)
                fill_opacity=0.7,       # transparency
                popup=stop
            ).add_to(fmap)


def add_point_marker(point, fmap, label, color="blue"):
    """
    Add a point marker to Folium map.
    """
    folium.Marker(
        location=(point.y, point.x),
        popup=label,
        icon=folium.Icon(color=color)
    ).add_to(fmap)

# def compute_total_length(route_gdf):
#     """
#     Approximate total length of the route in km.
#     Uses geodetic length calculation by re-projecting to an appropriate CRS.
#     """
#     # project to a metric CRS (here UTM zone 30N for Spain approx)
#     metric = route_gdf.to_crs(epsg=25830)
#     length_m = metric.geometry.length.sum()
#     return length_m / 1000.0  # km

def create_html(route, output_path):
    """
    """
    start_pt, end_pt = get_start_end_points(route)
    # total length is already given in the dataframe so just extract it
    total_km = float(route.loc[0, 'lon_camino'])
    
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = route.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    # add route
    add_route_to_map(route, basemap)
    # add start/end markers
    add_point_marker(start_pt, basemap, f"START: {route.iloc[0]['etapa']} – {route.iloc[0]['camino']}", color="green")
    add_point_marker(end_pt, basemap, f"END: {route.iloc[-2]['etapa']} – {route.iloc[-2]['camino']}", color="red")

    # Add a popup or marker for total length
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.DivIcon(html=f"""
                            <div style="font-size:14pt; color:#333;">
                                Camino Francés\nTotal length ≈ {total_km:.1f} km
                            </div>
                            """)
    ).add_to(basemap)

    basemap.save(f"{output_path}.html")

def create_png(route_gdf, output_path):
    """Create the figure and save to PNG."""

    fig, ax = plt.subplots(figsize=(12, 8))
    # TODO: Add contextily basemap
    # ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=20)
    route_gdf.plot(ax=ax, linewidth=2.5, color="#FF4500", label="Camino Francés")
    start_pt, end_pt = get_start_end_points(route_gdf)
    # Plot points
    ax.scatter(start_pt.x, start_pt.y, color="green", s=100, label="Start")
    ax.scatter(end_pt.x, end_pt.y, color="red", s=100, label="End")

    # Compute length and annotate
    total_km = float(route_gdf.loc[0, 'lon_camino'])
    ax.text(0.95, 0.95, f"Total length ≈ {total_km:.1f} km", transform=ax.transAxes,
            fontsize=14, color="#333", verticalalignment='top')

    # Add legend
    start_patch = mpatches.Patch(color='green', label='Start Point')
    end_patch = mpatches.Patch(color='red', label='End Point')
    # route_patch = mpatches.Patch(color='#FF4500', label='Route Path')
    ax.legend(handles=[start_patch, end_patch], loc="lower left")
    # ax.legend(handles=[route_patch, start_patch, end_patch], loc="lower left")

    ax.set_title("Camino Francés – Pilgrim Route Accessibility Map", fontsize=16)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
def generate_accessibility_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")
    
    # Load the shapefile for camino de santiago
    shapefile_path = "data/Camino/CaminoDeSantiago_CSFFR.shp"
    camino_fr_gdf = gpd.read_file(shapefile_path)

    #  Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if camino_fr_gdf is not None and camino_fr_gdf.crs.to_string() != "EPSG:4326":
        camino_fr_gdf = camino_fr_gdf.to_crs(epsg=4326)

    # Extract the route as a GeoDataFrame
    route = camino_fr_gdf.sort_values(by='id_etapa').reset_index(drop=True)

    # Generate and Save maps
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(route, output_path)
    create_png(route, output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # TODO: Fix and beautify this map
    filename = 'camino_de_santiago'
    generate_accessibility_map(path_dir=str(get_relative_path(__file__)), filename=filename)
