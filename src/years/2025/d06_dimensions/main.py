import numpy as np
import rasterio
import geopandas as gpd
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from pathlib import Path
from rasterio.mask import mask
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_dimensions_map(path_dir: str, file_html: str):
    """
    Creates dimnesions map
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Filter for Islamabad Capital Territory to focus the map and plot population density over time    
    isb_gdf = admin_gdf[admin_gdf['NAME_3'] == 'Shikarpur']

    # Load population density raster data for Islamabad# 2. Load population density raster for year 2015 and 2020
    r2015 = rasterio.open("data/PAK_misc/pak_pop_2015_CN_100m_R2025A_v1.tif")
    r2020 = rasterio.open("data/PAK_misc/pak_pop_2020_CN_100m_R2025A_v1.tif")
    r2025 = rasterio.open("data/PAK_misc/pak_pop_2025_CN_100m_R2025A_v1.tif")
    r2030 = rasterio.open("data/PAK_misc/pak_pop_2030_CN_100m_R2025A_v1.tif")

    # 3. Clip raster to Isb boundary
    out_image2015, out_transform2015 = mask(r2015, isb_gdf.geometry, crop=True)
    out_image2020, out_transform2020 = mask(r2020, isb_gdf.geometry, crop=True)
    out_image2025, out_transform2025 = mask(r2025, isb_gdf.geometry, crop=True)
    out_image2030, out_transform2030 = mask(r2030, isb_gdf.geometry, crop=True)
    # 4. Prepare data for 3D surface
    # Use downsample to make manageable size
    data2015 = out_image2015[0]
    data2020 = out_image2020[0]
    data2025 = out_image2025[0]
    data2030 = out_image2030[0]
    # Mask no-data
    data2015 = np.where(data2015 < 0, np.nan, data2015)
    data2020 = np.where(data2020 < 0, np.nan, data2020)
    data2025 = np.where(data2025 < 0, np.nan, data2025)
    data2030 = np.where(data2030 < 0, np.nan, data2030)

    # Downsample for speed
    step = 10
    sub2015 = data2015[::step, ::step]
    sub2020 = data2020[::step, ::step]
    sub2025 = data2025[::step, ::step]
    sub2030 = data2030[::step, ::step]
    # Create X, Y grid
    nrows, ncols = sub2015.shape
    x = np.arange(ncols)
    y = np.arange(nrows)
    X, Y = np.meshgrid(x, y)

    # 5. Create plotly figure for year 2020
    # fig = go.Figure(data=[ go.Surface(
    #     z=sub2020,
    #     x=X,
    #     y=Y,
    #     colorscale='Viridis',
    #     colorbar=dict(title='pop dens / cell')
    # )])
    # fig.update_layout(
    #     title='Pakistan Population Density 2020 (3D)',
    #     scene=dict(
    #         xaxis_title='grid X',
    #         yaxis_title='grid Y',
    #         zaxis_title='Density'
    #     )
    # )
    # fig.show()

    # 6. Create animation frames for all years
    fig = go.Figure()
    for year, sub in zip([2015, 2020, 2025, 2030], [sub2015, sub2020, sub2025, sub2030]):
        fig.add_trace(go.Surface(
            z=sub,
            x=X,
            y=Y,
            colorscale='Viridis',
            visible=(year==2015)
        ))
    # create frames
    frames = []
    for i, (year, sub) in enumerate(zip([2015, 2020, 2025, 2030], [sub2015, sub2020, sub2025, sub2030])):
        frames.append(go.Frame(data=[go.Surface(z=sub, x=X, y=Y, colorscale='Viridis')], name=str(year)))
    fig.frames = frames

    # slider
    steps = []
    for i, year in enumerate([2015, 2020, 2025, 2030]):
        steps.append(dict(method='animate',
                    label=str(year),
                    args=[[str(year)],
                            dict(mode='immediate', frame=dict(duration=1000, redraw=True),
                                transition=dict(duration=500))]))
    fig.update_layout(
        updatemenus=[dict(type='buttons',
                        showactive=False,
                        buttons=[dict(label='Play',
                                        method='animate',
                                        args=[None, dict(frame=dict(duration=1000, redraw=True), 
                                                        transition=dict(duration=500),
                                                        fromcurrent=True,
                                                        mode='immediate')])])],
        sliders=[dict(active=1, pad={"t": 50}, steps=steps)]
    )

    fig.update_layout(
        title='Pakistan Population Density: 2015 → 2030 (3D)',
        scene=dict(zaxis_title='Density per grid cell')
    )
    fig.show()
    # Save locally as HTML
    fig.write_html(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'pop_density_isb'
    create_dimensions_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)