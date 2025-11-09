import os
import folium
import imageio
import numpy as np
import contextily as ctx
import matplotlib.pyplot as plt

from PIL import Image
from folium import raster_layers
from rasterio.plot import reshape_as_image
from branca.element import Template, MacroElement

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path

logger = get_logger(__name__)


def overlay_image_matplotlib(image_path, bounds, zoom=6, figsize=(10, 10)):
    """
    Overlay a static image (analog map) over a basemap using matplotlib and contextily.

    Parameters
    ----------
    image_path : str
        Path to the static PNG/JPG map.
    bounds : list
        Bounding box [min_lon, min_lat, max_lon, max_lat] of the image in WGS84.
    zoom : int
        Zoom level for contextily basemap.
    figsize : tuple
        Size of the matplotlib figure.
    """
    min_lon, min_lat, max_lon, max_lat = bounds

    # Load image
    img = Image.open(image_path)
    img_arr = np.array(img)

    # Convert to Web Mercator for contextily
    import pyproj
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x_min, y_min = transformer.transform(min_lon, min_lat)
    x_max, y_max = transformer.transform(max_lon, max_lat)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=zoom)

    # Overlay image
    ax.imshow(img_arr, extent=[x_min, x_max, y_min, y_max], origin='upper', alpha=0.6)
    ax.set_axis_off()
    plt.show()

def overlay_image_folium(image_path, bounds, file_html, 
                         map_center=None, zoom_start=5, map_tiles='OpenStreetMap', opacity=0.6):
    """
    Overlay a static image (analog map) over a Folium map.

    Parameters
    ----------
    image_path : str
        Path to the static PNG/JPG map.
    bounds : list
        Bounding box [min_lon, min_lat, max_lon, max_lat] of the image in WGS84.
    file_html: str
        Name of the html file to store the resultant map.
    map_center : list
        [lat, lon] for initial map center. If None, center of bounds is used.
    zoom_start : int
        Initial zoom level.
    map_tiles: str
        Basemap tiles to be used for display.
    opacity : float
        Transparency of overlay.
    """
    if map_center is None:
        min_lon, min_lat, max_lon, max_lat = bounds
        map_center = [(min_lat + max_lat)/2, (min_lon + max_lon)/2]

    basemap = folium.Map(location=map_center, zoom_start=zoom_start, tiles=map_tiles)
    
    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, )
    folium.raster_layers.ImageOverlay(
        name="Analog Map",
        image=image_path,
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],  # [[lat_min, lon_min], [lat_max, lon_max]]
        opacity=opacity,
        interactive=True,
        cross_origin=False,
        zindex=1
    ).add_to(basemap)

    folium.LayerControl().add_to(basemap)
    
    # Save the map to an HTML file
    basemap.save(file_html)
    logger.info(f"Map created – open '{file_html}.html' to view.")

def create_time_slider_map(maps_info, file_html, map_center=None, zoom_start=5, map_tiles='OpenStreetMap', opacity=0.6):
    """
    Create a Folium map overlaying multiple analog maps with a time slider.

    Parameters
    ----------
    maps_info : list of dicts
        Each dict should contain: path, bounds [min_lon, min_lat, max_lon, max_lat], year.        
    file_html: str
        Name of the html file to store the resultant map.
    map_center : list
        [lat, lon] for initial map center. If None, center of bounds is used.
    zoom_start : int
        Initial zoom level.
    map_tiles: str
        Basemap tiles to be used for display.
    opacity : float
        Transparency of the overlays.
    """
    if map_center is None:
        min_lon, min_lat, max_lon, max_lat = maps_info[0]["bounds"]
        map_center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]

    basemap = folium.Map(location=map_center, zoom_start=zoom_start, tiles=map_tiles, control_scale=True)

    # Create FeatureGroups for each map
    fg_dict = {}
    for info in maps_info:
        fg = folium.FeatureGroup(name=str(info["year"]), show=(info["year"] == maps_info[0]["year"]))
        raster_layers.ImageOverlay(
            image=info["path"],
            bounds=[[info["bounds"][1], info["bounds"][0]], [info["bounds"][3], info["bounds"][2]]],
            opacity=opacity,
            interactive=True,
            cross_origin=False,
            zindex=1
        ).add_to(fg)
        fg.add_to(basemap)
        fg_dict[info["year"]] = fg

    # Add LayerControl (optional)
    folium.LayerControl().add_to(basemap)

    # Add custom slider
    years = [str(info["year"]) for info in maps_info]
    slider_template = """
    {% macro html(this, kwargs) %}
    <div id="slider-container" style="position: fixed; bottom: 50px; left: 50px; width: 300px; z-index:9999; background-color:white; padding:10px; border-radius:5px;">
        <label for="yearSlider">Year: <span id="yearLabel">{{years[0]}}</span></label>
        <input type="range" min="0" max="{{max_idx}}" value="0" step="1" id="yearSlider" style="width:100%;">
    </div>
    <script>
        var years = {{years}};
        var layers = {};
        {% for y in years %}
            layers["{{y}}"] = {{this.get_name()}}.layerManager.getLayer('{{y}}');
        {% endfor %}

        var slider = document.getElementById('yearSlider');
        var label = document.getElementById('yearLabel');

        slider.oninput = function() {
            var year = years[this.value];
            label.innerHTML = year;

            for (var i=0; i<years.length; i++){
                var y = years[i];
                if(y === year){
                    layers[y].addTo({{this._parent.get_name()}});
                } else {
                    {{this._parent.get_name()}}.removeLayer(layers[y]);
                }
            }
        };
    </script>
    {% endmacro %}
    """
    macro = MacroElement()
    macro._template = Template(slider_template).render(years=years, max_idx=len(years)-1)
    basemap.get_root().add_child(macro)
    
    # Save the map to an HTML file
    basemap.save(file_html)
    logger.info(f"Map created – open '{file_html}.html' to view.")
    
def create_static_map_animation(maps_info, out_path="india_animation.gif", figsize=(10, 10), zoom=6, alpha=0.6):
    """
    Create a GIF animation from multiple analog maps overlayed on basemap.

    Parameters
    ----------
    maps_info : list of dicts
        Each dict should contain: path, bounds [min_lon, min_lat, max_lon, max_lat], year.
    out_path : str
        Path to save GIF.
    figsize : tuple
        Figure size.
    zoom : int
        Basemap zoom.
    alpha : float
        Overlay transparency.
    """
    frames = []

    for info in maps_info:
        fig, ax = plt.subplots(figsize=figsize)
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=zoom)

        # Convert bounds to Web Mercator
        import pyproj
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x_min, y_min = transformer.transform(info["bounds"][0], info["bounds"][1])
        x_max, y_max = transformer.transform(info["bounds"][2], info["bounds"][3])

        # Load image
        img = Image.open(info["path"])
        img_arr = np.array(img)

        ax.imshow(img_arr, extent=[x_min, x_max, y_min, y_max], origin='upper', alpha=alpha)
        ax.set_axis_off()
        ax.set_title(f"Year: {info['year']}", fontsize=14)

        # Save to buffer
        buf_path = f"temp_{info['year']}.png"
        plt.savefig(buf_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        frames.append(imageio.v2.imread(buf_path))
        os.remove(buf_path)

    imageio.mimsave(out_path, frames, duration=1.0)
    logger.info(f"Animation saved at {out_path}")


# overlay_image_matplotlib(
#     "british_india_map.png",
#     bounds=[68, 6, 97, 36],  # Approx India bounding box
#     zoom=6
# )

# overlay_image_folium(
#     "british_india_map.png",
#     file_html=f"{Path(path_dir).parent}/{file_html}.html",
#     bounds=[68, 6, 97, 36],
#     zoom_start=5,
#     map_tiles='OpenStreetMap',
#     opacity=0.7
# )

# create_time_slider_map(
#     maps_info, 
#     file_html=f"{Path(path_dir).parent}/{file_html}.html", 
#     opacity=0.7
# )

# create_static_map_animation(maps_info, out_path="india_animation.gif", alpha=0.6)