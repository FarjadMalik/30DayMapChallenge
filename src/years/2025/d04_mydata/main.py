import folium
import json
import geopandas as gpd

from pathlib import Path
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
        visit = r.get("place_visit", [])
        # Expect exactly two place visits (source and destination) with lat/lng
        if len(visit) < 2:
            continue
        if "place" not in visit[0] or "place" not in visit[1]:
            continue
        src = visit[0]["place"]["lat_lng"]
        dst = visit[1]["place"]["lat_lng"]
        
        # transition can be walking, driving, etc.
        mode = "unknown"
        transition = r.get("transition", [])
        if transition and isinstance(transition, list):
            transition = transition[0]
            route = transition.get("route", {})
            if route:
                mode = route.get("travel_mode", "unknown")
    
        trip = {
            "id": r.get("id"),
            "src": (src["latitude"], src["longitude"]),
            "dst": (dst["latitude"], dst["longitude"]),
            "t_mode": mode
        }
        trips.append(trip)
    logger.info(f"Loaded {len(trips)} trips.")
    return trips

def create_routes_map(path_dir: str, file_html: str):
    """
    Creates routes map from Google Takeout data and saves it as an HTML file.
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Read the commute routes json file
    routes_path = "data/Takeout/Maps/Commute routes/Commute routes.json"
    routes_json = json.load(open(routes_path))
    trips = load_routes(routes_json)
    logger.info(f"Trips: {trips}")

    # Calculate center for the map
    all_lat = [lat for tr in trips for lat,_ in (tr["src"], tr["dst"])]
    all_lon = [lon for tr in trips for _,lon in (tr["src"], tr["dst"])]
    map_center = (sum(all_lat)/len(all_lat), sum(all_lon)/len(all_lon))
    
    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=map_center, zoom_start=10, tiles='OpenStreetMap')

    # Plot the routes on a map    
    for tr in trips:
        folium.PolyLine(
            locations=[ tr["src"], tr["dst"] ],
            color="blue",
            weight=5,
            opacity=0.8,
            popup=f'Trip Id: {tr["id"]}, Transportation Mode: {tr["t_mode"]}'
        ).add_to(basemap)
        # optionally: mark source & destination
        folium.Marker(tr["src"], tooltip="Start", icon=folium.Icon(color="green")).add_to(basemap)
        folium.Marker(tr["dst"], tooltip="End", icon=folium.Icon(color="red")).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'Google_routes_map'
    create_routes_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)