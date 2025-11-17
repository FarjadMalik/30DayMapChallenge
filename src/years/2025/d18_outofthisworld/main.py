import folium
import numpy as np 
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from shapely import Point
from folium.plugins import MarkerCluster, HeatMap

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def eda_and_clean_dataset(ds : pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Remove any extra columns or rows with missing values.
    """
    # Assign correct datatypes and remove extra fields
    ds["lat"] = ds["reclat"].astype(float)
    ds["long"] = ds["reclong"].astype(float)
    ds.drop(columns=['reclat', 'reclong', 'GeoLocation', ], inplace=True)
        
    # # Check Missing Values
    # missing_counts = ds.isnull().sum()
    # missing_percent = ds.isnull().mean() * 100
    # logger.debug(f"Missing values per column:\n{missing_counts}")
    # logger.debug(f"Missing % per column:\n{missing_percent}")
    # # Number of rows with any null
    # n_any_null = ds.isna().any(axis=1).sum()
    # pct_any_null = n_any_null / ds.shape[0] * 100
    # logger.debug(f"Rows with any null: {n_any_null} ({pct_any_null:.2f}%)")
    # # Unique / Duplicates
    # logger.debug(f"Unique values per column:\n{ds.nunique()}")
    # logger.debug(f"Number of duplicated rows:{ds.duplicated().sum()}")
    # # Descriptive Stats
    # logger.debug("Descriptive statistics (numeric):")
    # logger.debug(ds.describe().T)
    # # For categorical (if any)
    # cat_cols = ds.select_dtypes(include=['object', 'category']).columns
    # if len(cat_cols) > 0:
    #     logger.debug("Descriptive for categorical columns:")
    #     logger.debug(ds[cat_cols].describe())
    #     for col in cat_cols:
    #         logger.debug(f"Unique Meteorites col - {col} = {ds[col].unique()}")
    # # Univariate Plots
    # numeric_cols = meteorite_landings.select_dtypes(include=[np.number]).columns.tolist()
    # # Histograms
    # meteorite_landings[numeric_cols].hist(bins=30, figsize=(12, 8))
    # plt.suptitle("Histograms of numeric columns")
    # plt.show()
    # # KDE plots (density)
    # for col in numeric_cols:
    #     plt.figure(figsize=(6, 4))
    #     sns.kdeplot(data=df, x=col, shade=True)
    #     plt.title(f"Density plot: {col}\nSkew: {df[col].skew():.2f}")
    #     plt.show()
    # # Box plots for outliers
    # plt.figure(figsize=(12, 6))
    # sns.boxplot(data=df[numeric_cols], orient='h')
    # plt.title("Box plots for numeric variables")
    # plt.show()
    # # Bivariate / Multivariate
    # # Correlation matrix
    # corr = ds[numeric_cols].corr()
    # logger.debug(f"Correlation matrix:\n{}", corr)
    # plt.figure(figsize=(8, 6))
    # sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm')
    # plt.title("Correlation heatmap")
    # plt.show()
    # # Pairplot (if not too many numeric columns)
    # sns.pairplot(ds[numeric_cols].dropna())  # dropna just for plotting ease
    # plt.suptitle("Pairplot of numeric variables", y=1.02)
    # plt.show()
    # # Scatter plot example: year vs latitude (or any other pair)
    # if 'year' in ds.columns and 'latitude' in ds.columns:
    #     plt.figure(figsize=(6, 4))
    #     sns.scatterplot(data=ds, x='year', y='latitude')
    #     plt.title("Scatter: Year vs Latitude")
    #     plt.show()
    # # Time series / Trend (landings per year)
    # if 'year' in ds.columns:
    #     landings_by_year = ds.groupby('year').size()
    #     plt.figure(figsize=(10, 5))
    #     landings_by_year.plot(kind='line', marker='o')
    #     plt.title("Meteor landings per year")
    #     plt.xlabel("Year")
    #     plt.ylabel("Number of landings")
    #     plt.grid(True)
    #     plt.show()
    # # Geospatial summary basic
    # if 'latitude' in ds.columns and 'longitude' in ds.columns:
    #     logger.debug(f"Latitude range:{ds['latitude'].min()}-{ds['latitude'].max()}")
    #     logger.debug(f"Longitude range:{ds['longitude'].min()}-{ds['longitude'].max()}")
    # # Outlier detection (simple IQR method for each numeric)
    # outliers = {}
    # for col in numeric_cols:
    #     q1 = ds[col].quantile(0.25)
    #     q3 = ds[col].quantile(0.75)
    #     iqr = q3 - q1
    #     lower = q1 - 1.5 * iqr
    #     upper = q3 + 1.5 * iqr
    #     mask = (ds[col] < lower) | (ds[col] > upper)
    #     outliers[col] = mask.sum()
    # logger.debug(f"Outliers (IQR method) per numeric column: {outliers}")
    # # Handling Missing Values – example strategies
    # # Option A: Drop rows with too many nulls
    # ds_clean = ds.dropna(thresh=int(0.7 * ds.shape[1]))  # keep rows with at least 70% non-null
    # # Option B: Impute (example)
    # ds_imputed = ds.copy()
    # for col in numeric_cols:
    #     if ds_imputed[col].isnull().any():
    #         median = ds_imputed[col].median()
    #         ds_imputed[col].fillna(median, inplace=True)
    # # Feature Engineering
    # # Example: decade from year
    # if 'year' in ds.columns:
    #     ds['decade'] = (ds['year'] // 10) * 10
    # logger.debug(f"{ds['decade'].value_counts() =}")
    # Summarize Key Findings (you should write down your observations)
    
    # ------------------------------------------------------------------------------------------- #
    # Create GeoDataFrame
    # Create geometry series: Points(long, lat)
    geometry = [Point(xy) for xy in zip(ds['long'], ds['lat'])]
    meteorite_landings = gpd.GeoDataFrame(ds, geometry=geometry, crs="EPSG:4326")

    # # Check Missing Values in Geodataframe
    # missing_counts = meteorite_landings.isnull().sum()
    # missing_percent = meteorite_landings.isnull().mean() * 100
    # logger.debug(f"Missing values per column:\n{missing_counts}")
    # logger.debug(f"Missing % per column:\n{missing_percent}")
    # # Check for missing (null) geometries
    # missing_geom = meteorite_landings[meteorite_landings.geometry.isna()]
    # logger.debug(f"Rows with missing geometry (None):\n{len(missing_geom)}")
    # # Check for empty geometries
    # empty_geom = meteorite_landings[meteorite_landings.geometry.is_empty]
    # logger.debug(f"Rows with empty geometry objects:\n{len(empty_geom)}")

    # Combine both: either missing or empty
    meteorite_landings = meteorite_landings[
        ~(meteorite_landings.geometry.isna() | meteorite_landings.geometry.is_empty)].copy()
    # # Count how many remaining meteorites
    # logger.debug(f"Count missing or empty: {meteorite_landings.shape}")

    return meteorite_landings
    
def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Read Meteorite Landing dataset
    file_meteorite_landing = "data/Meteorite_Landings_NASA.csv"
    meteorite_df = pd.read_csv(file_meteorite_landing)
    meteorite_landings = eda_and_clean_dataset(meteorite_df)
    
    # Clean up and see if our dataset has valid rows
    del meteorite_df    
    if meteorite_landings is None or len(meteorite_landings) < 1:
        return None
    
    logger.debug(f"Meteorite Landings len: {len(meteorite_landings)}")
    logger.debug(f"Meteorite Landings columns: {meteorite_landings.columns}")

    # Compute center of the map = mean of lat/lon
    center_lat = meteorite_landings.geometry.y.mean()
    center_lon = meteorite_landings.geometry.x.mean()

    # Create and Center a base map
    basemap = folium.Map([center_lat, center_lon], zoom_start=3, tiles='CartoDB Positron')

    # Add desired data to the basemap
    # Initialize a marker cluster layer
    marker_cluster = MarkerCluster(name="Meteor Clusters").add_to(basemap)
    for _, row in meteorite_landings.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x

        # Build popup HTML
        popup_html = f"""
        <b>Name:</b> {row.get('name', 'Unknown')}<br>
        <b>Year:</b> {row.get('year', 'N/A')}<br>
        <b>Mass:</b> {row.get('mass', 'N/A')} grams<br>
        <b>Type:</b> {row.get('recclass', 'N/A')}<br>
        <b>Found/Fell:</b> {row.get('fall', 'N/A')}
        """
        # Build tooltip - simpler and shorter
        tooltip_f = folium.Tooltip(
            f"{row.get('meteor_name', 'meteor')} ({row.get('year')})",
            sticky=True,  # tooltip follows the mouse
            style="font-size: 12px; color: black;"
        )
        # try:
        #     icon_color = class_color[row['recclass']]
        # except:
        #     #Catch nans
        #     icon_color = 'black'
        icon_f = folium.Icon(color="black",icon='meteor',prefix='fa')

        folium.Marker(
            location=[lat, lon],
            icon=icon_f,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_f
        ).add_to(marker_cluster)
    
    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_out}.html")
    logger.info(f"Map created – open '{file_out}.html' to view.")


if __name__ == "__main__":
    # meteor showers over earth
    out_filename = 'outofthisworld'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)