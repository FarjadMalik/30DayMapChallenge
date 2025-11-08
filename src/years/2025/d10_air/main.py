import os 
import imageio
import folium
import geopandas as gpd
import pandas as pd
import contextily as ctx
import matplotlib.pyplot as plt
import branca.colormap as cm
import matplotlib.colors as mcolors

from io import BytesIO
from datetime import datetime
from folium import plugins
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_animation(dataset, column, out_path, freq='Q', use_cache=False):
    """
    Creates a GIF animation of a GeoDataFrame column over time with optional aggregation and caching.

    Parameters:
        dataset: GeoDataFrame with 'Date' column and geometry.
        column: Column to visualize (e.g., 'AQI_avg').
        out_path: Path to save the GIF.
        freq: Frequency of aggregation: 'D' = daily, 'M' = monthly, 'Q' = seasonal.
        use_cache: If True, temporary frames are stored in ./cache_frames folder.
    """

    # Ensure datetime
    dataset['Date'] = pd.to_datetime(dataset['Date'])
    # Aggregate if needed
    if freq != 'D':
        dataset_agg = dataset.copy()
        dataset_agg['Period'] = dataset_agg['Date'].dt.to_period(freq)
        numeric_cols = dataset_agg.select_dtypes(include='number').columns
        dataset_agg = dataset_agg.groupby('Period')[list(numeric_cols)].mean().reset_index()
        dataset_agg['geometry'] = dataset.geometry.iloc[0]
        dataset_agg['Date'] = dataset_agg['Period'].dt.to_timestamp()
        dataset = gpd.GeoDataFrame(dataset_agg, geometry='geometry')
        if dataset.crs is None:
            dataset = dataset.set_crs("EPSG:4326", inplace=False)  
    else:
        dataset = dataset.sort_values('Date')
    
    # Ensure Web Mercator CRS for contextily
    dataset = dataset.to_crs(epsg=3857)
    # Assign a source map provider
    # logger.info(f"CTX Providers: {ctx.providers.keys()}")
    # logger.info(f"CTX Providers: {ctx.providers.OpenStreetMap.keys()}")
    map_provider = ctx.providers.OpenStreetMap.Mapnik

    # Normalize for colormap
    vmin = dataset[column].min()
    vmax = dataset[column].max()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.cm.Reds

    # Base geometry
    base_geom = dataset.geometry.iloc[0]

    # Optional cache folder
    if use_cache:
        cache_dir = os.path.join(out_path, '.cache')
        os.makedirs(cache_dir, exist_ok=True)
        temp_files = []

    frames = []

    for i, row in dataset.iterrows():
        fig, ax = plt.subplots(figsize=(8,6))

        # Set axis limits to your geometry bounds
        # minx, miny, maxx, maxy = base_geom.bounds
        # ax.set_xlim(minx-1000, maxx+1000)  # small buffer
        # ax.set_ylim(miny-1000, maxy+1000)

        # Plot base polygon
        gpd.GeoSeries(base_geom).plot(ax=ax, color='lightgrey', edgecolor='black', zorder=2)
        # Plot AQI polygon
        gpd.GeoSeries(row.geometry).plot(ax=ax, color=cmap(norm(row[column])), zorder=3)

        # Now add basemap (will respect current axis extent)
        ctx.add_basemap(ax, source=map_provider, zoom=11)

        ax.set_title(f"{column} on {row['Date'].strftime('%Y-%m-%d')}", fontsize=14)
        ax.axis('off')

        if use_cache:
            filename = os.path.join(cache_dir, f"frame_{i}.png")
            plt.savefig(filename, bbox_inches='tight', dpi=150)
            temp_files.append(filename)
            plt.close()
        else:
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buf.seek(0)
            frames.append(imageio.v2.imread(buf))
            buf.close()

    # Save GIF
    gif_name = os.path.join(out_path, f"Average_{column}_timeseries_{freq}.gif")
    if use_cache:
        with imageio.get_writer(gif_name, mode='I', duration=0.5) as writer:
            for file in temp_files:
                img = imageio.v2.imread(file)
                writer.append_data(img)
        # Clean up cache
        for file in temp_files:
            os.remove(file)
    else:
        imageio.mimsave(gif_name, frames, duration=0.5)
        # os.remove(frames)

    logger.info(f"Average {column} time series heatmap saved as {gif_name}")

def create_heatmap_folium(dataset, index_column, path_dir, file_html, center_lat=None, center_lon=None):
    """

    """
    # Ensure your dataset has datetime
    dataset['Date'] = pd.to_datetime(dataset['Date'])

    # Create a color map for AQI
    vmin = dataset[index_column].min()
    vmax = dataset[index_column].max()
    colormap = cm.linear.Reds_09.scale(vmin, vmax)  # Reds gradient

    if (center_lat is None) or (center_lon is None):
        # Get the city centroid to plot the AQI as a point
        center_lat = dataset.geometry.centroid.y
        center_lon = dataset.geometry.centroid.x

    # Create a GeoJSON FeatureCollection for TimestampedGeoJson
    # Create features for TimestampedGeoJson
    features = []
    for _, row in dataset.iterrows():
        # Convert polygon to GeoJSON-like mapping
        geom = row['geometry'].__geo_interface__

        feature = {
            'type': 'Feature',
            'geometry': geom,
            'properties': {
                'time': row['Date'].strftime('%Y-%m-%d'),
                'style': {
                    'fillColor': colormap(row[index_column]),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                'popup': f"{index_column}I: {row[index_column]:.1f}"
            }
        }
        features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    # Center the map on the city
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')

    # Add TimestampedGeoJson
    plugins.TimestampedGeoJson(
        geojson,
        period='P1D',       # each step = 1 day
        add_last_point=True,
        auto_play=True,
        loop=False,
        max_speed=1,
        loop_button=True,
        date_options='YYYY-MM-DD',
        time_slider_drag_update=True
    ).add_to(basemap)

    # Add color legend
    colormap.caption = f"Daily {index_column} over {dataset.iloc[0]['NAME_3']}"
    colormap.add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}_{index_column}.html")
    logger.info(f"Map created – open '{file_html}_{index_column}.html' to view.")

def create_air_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    # Filter for urban areas of interest: Lahore, maybe Multan
    admin_of_interest = ['Lahore']
    admin_gdf = admin_gdf[admin_gdf['NAME_3'].isin(admin_of_interest)]
    admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'NAME_2', 'NAME_3', 'TYPE_3', 'geometry']]
    admin_gdf = admin_gdf.reset_index(drop=True)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    logger.info(f"Center Lat Lon: {center_lat, center_lon}")

    # Read historical air pollution dataset for lahore
    lhr_ap_df = pd.read_csv("data/PAK_misc/historical_air_pollution_all_lahore.csv")
    # Convert Timestamp to datetime
    lhr_ap_df['Timestamp'] = pd.to_datetime(lhr_ap_df['Timestamp'])
    # Aggregate AQI per day
    lhr_ap_df['Date'] = lhr_ap_df['Timestamp'].dt.date
    daily_ap_lhr_df = lhr_ap_df.groupby('Date').mean().reset_index()
    # Rename and delete extra  columns
    daily_ap_lhr_df.rename(columns={'AQI': 'AQI_scale_US'}, inplace=True)
    daily_ap_lhr_df.drop(columns=['Timestamp'], inplace=True)

    # Load AQI dataset
    daily_aqi_lhr_df = pd.read_csv("data/PAK_misc/lahore_air_quality_index/lahore_aqi_2019_to_2023.csv")
    # Convert date
    daily_aqi_lhr_df['Date'] = pd.to_datetime(daily_aqi_lhr_df['date'], format='%d-%m-%y').dt.date
    # Rename AQI column to distinguish
    daily_aqi_lhr_df.rename(columns={'aqi_pm2.5': 'AQI_score'}, inplace=True)
    daily_aqi_lhr_df.drop(columns=['date'], inplace=True)

    # Merge on Date
    aqi_lhr_df = pd.merge(daily_ap_lhr_df, daily_aqi_lhr_df, on='Date', how='outer')
    aqi_lhr_df = aqi_lhr_df.fillna(0)

    # Clean up 
    del daily_ap_lhr_df, daily_aqi_lhr_df, lhr_ap_df

    # Add geometry to our historical AQI data

    # Broadcast city geometry over the dataframe
    # aqi_lhr_gdf = gpd.GeoDataFrame(aqi_lhr_df.copy(), geometry=[admin_gdf.geometry.iloc[0]]*len(aqi_lhr_df))
    # aqi_lhr_gdf.set_crs(admin_gdf.crs, inplace=True)

    # Merge the datasets
    # Add a dummy key to enable merge
    admin_gdf['key'] = 1
    aqi_lhr_df['key'] = 1
    aqi_lhr_gdf = pd.merge(aqi_lhr_df, admin_gdf, on='key', how='left')
    # Convert to GeoDataFrame
    aqi_lhr_gdf = gpd.GeoDataFrame(aqi_lhr_gdf, geometry='geometry')
    # Drop the dummy key 
    aqi_lhr_gdf.drop(columns=['key'], inplace=True)

    # Create maps with the desired data and column
    create_animation(dataset=aqi_lhr_gdf, column='AQI_score', out_path=str(Path(path_dir).parent))
    create_heatmap_folium(aqi_lhr_gdf, 'AQI_score', path_dir, file_html, center_lat, center_lon)


if __name__ == "__main__":
    out_filename = 'air_quality_lahore'
    create_air_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)