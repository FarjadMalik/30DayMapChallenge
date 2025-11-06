import folium
import json
import geopandas as gpd

from pathlib import Path
from shapely.geometry import box
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)

def load_routes(routes_json: dict) -> list[dict]:
    """
    Load commute routes from Google Takeout data.
    """
    routes = routes_json.get("trips", [])
    trips = []
    for r in routes:
        visit = r.get("place_visits", [])
        # Expect exactly two place visits (source and destination)
        if len(visit) < 2:
            continue
        src = visit[0]["place"]["lat_lng"]
        dst = visit[1]["place"]["lat_lng"]
        
        trip = {
            "id": r.get("id"),
            "source": (src["latitude"], src["longitude"]),
            "destination": (dst["latitude"], dst["longitude"]),
            "transportation_mode": r.get("transition", "unknown")
        }
        trips.append(trip)

    return trips

def create_routes_map(path_dir: str, file_html: str):
    """
    Creates routes map from Google Takeout data and saves it as an HTML file.
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Read the commute routes json file
    routes_path = "data/Takeout/Maps/Commute routes/Commute routes.json"
    routes_json = json.load(open(routes_path))
    logger.info(f"Routes type: {type(routes_json)}")
    trips = load_routes(routes_json)
    logger.info(f"Trips: {trips}")


    # # Create the Folium map, centered on Pakistan (admin boundaries center)
    # basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')


    # # Allows toggling between layers interactively 
    # folium.LayerControl().add_to(basemap)
    # # Save the map to an HTML file
    # basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    # logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'Leuven_walking_path'
    create_routes_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)