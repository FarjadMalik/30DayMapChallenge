import folium
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch
from branca.element import Template, MacroElement

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_html(admin, dataset, output_path):
   """
   """
   # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
   if admin is not None and admin.crs.to_string() != "EPSG:4326":
         admin = admin.to_crs(epsg=4326)
   if admin.crs != dataset.crs:
      dataset = dataset.to_crs(admin.crs)
      
   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   # Create and Center a base map
   basemap = folium.Map(location=[center_lat, center_lon], zoom_start=7, 
                        tiles='OpenStreetMap')

   # Add the administrative boundaries layer
   folium.GeoJson(
         admin,
         name='Administrative Boundaries',
         style_function=lambda feature: {
            'fillColor': None,
            'color': 'black',
            'weight': 1,
            'opacity': 0.5
         },
         tooltip=folium.GeoJsonTooltip(
            fields=['NAME_1'], 
            aliases=['Province:']
         )
   ).add_to(basemap)

   # Add dataset
   folium.GeoJson(
       dataset,
       name='',
       style_function=lambda feature: {
           'fillColor': feature['properties']['color'],
           'color': feature['properties']['color'],
           'weight': 1,
           'fillOpacity': 0.5
       },
       tooltip=folium.GeoJsonTooltip(
           fields=[''],
           aliases=[''],
           localize=True
       )
   ).add_to(basemap)

   # items = "".join([
   #      f'<i style="background:{name};width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
   #      f'{name}<br>'
   #      for name in dataset.amenity.unique()
   #  ])

   # legend_html = """{% macro html(this, kwargs) %}
   # <div style="position: fixed; 
   #             top: 10px; left: 50px; width: 320px; z-index:9999; 
   #             background-color: white; border:2px solid grey; border-radius:5px; 
   #             padding: 10px; font-size:14px;">
   #    <h4 style="margin-bottom:10px;"><b>Educational Institutes Per Province</b></h4>
      
   #    <b>Items:</b><br>
   #    """ + items + """
   # </div>
   # {% endmacro %}
   # """
   # legend = MacroElement()
   # legend._template = Template(legend_html)
   # basemap.get_root().add_child(legend)
   
   # # Add title
   # title_html = '''
   # <h3 align="center" style="font-size:20px; font-weight:bold; margin-top:10px">
   #    TITLE
   # </h3>
   # '''
   # basemap.get_root().html.add_child(folium.Element(title_html))

   # Allows toggling between layers interactively 
   folium.LayerControl().add_to(basemap)
   # Save and exit
   basemap.save(f"{output_path}.html")
   
def create_png(admin, dataset, output_path):
   """
   """
   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   # create fig and axis
   _, ax = plt.subplots(figsize=(12, 10))

   # plot admin boundaries
   admin.plot(
      ax=ax,
      color='white',
      edgecolor='black',
      linewidth=1
   )
   
   # plot polygons with colors
   dataset.plot(
      ax=ax,
      facecolor=dataset['color'], # fill
      edgecolor=dataset['color'], # outline
      # color='', # both fill and outline
      linewidth=1,
      alpha=0.7
   )
   # Set limits and range from the center coordinates
   ax.set_xlim(center_lon - 9, center_lon + 9)
   ax.set_ylim(center_lat - 9, center_lat + 9)

   # Add title & legend
   ax.set_title(
      "TITLE",
      fontsize=18,
      fontweight="bold",
      pad=20
   )

   # Define your color mapping for phases (for legend use, takes care of missing phases in the dataset)
   phase_color_dict = {
      1: '#fae61e', # Level 1
   }
   legend_elements = []
   for phase, color in phase_color_dict.items():
      legend_elements.append(Patch(facecolor=color, edgecolor=color,
                                    label=f"Level {phase}"))
   
   # Beautify, add legend and save
   ax.legend(
      handles=legend_elements,
      title="Legend Title",
      loc="upper left", # legend location
      frameon=True
   )
   ax.set_axis_off()
   # plt.tight_layout()
   plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for boundaries or admin units
   shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
   admin_gdf = gpd.read_file(shapefile_path)
   admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

   # Load desired 
   dataset = None

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)
   create_png(admin=admin_gdf, dataset=dataset, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # Classical Elements 4/4: Focus on the fluid. 
   # Map hydrology, oceans, currents, water accessibility, sea level rise, precipitation, or anything aquatic.
   # PCP can be one. WAPOR tifs, water species, or evaporation index                        
   filename = 'water'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)

"""
Great — very thoughtful direction. Here are several **map / visualization ideas** (with some background and rationale), focused on water in the Global South — especially for **Pakistan** and **Sudan**. Then, I'll sketch how to implement (or prototype) a couple of them using Python (Cartopy / geopandas / raster, etc.).

---

## Map / Visualization Ideas: Water‑focused for Pakistan, Sudan, and Global South

Here are some thematic map ideas, with their motivations and possible data sources:

1. **Water Stress Map**

   * **What:** Map per-capita water availability vs. demand (or “water stress”) for Pakistan, Sudan, and other Global South countries.
   * **Why:** Pakistan is facing acute water stress; per-capita availability is declining sharply. ([Dawn][1])
   * **Data Sources:** SDG 6 Data portal (for water stress / water availability). ([SDG 6 Data][2])
   * **Visualization Ideas:** Choropleth (country-level), or even basin-level if you can get finer-scale data.

2. **Hydrology & River Basin Map**

   * **What:** Map major river basins (e.g., Indus Basin in Pakistan) and overlay hydrological features (glacier melt, runoff, precipitation).
   * **Why:** The Indus is hugely important to Pakistan’s freshwater. ([PIDE][3])
   * **Data Sources:** Hydrological models (e.g., WaterGAP) ([Wikipedia][4]); regional precipitation / runoff from climate data.
   * **Visualization:** Use basin polygons, show runoff, precipitation, or projected changes under climate scenarios.

3. **Precipitation Change / Climate Projection Map**

   * **What:** Map historical and projected precipitation (or P-E, precipitation minus evaporation) change in Pakistan (or Sudan) under different climate scenarios (e.g., CMIP6).
   * **Why:** Climate change is affecting water availability; understanding where precipitation is increasing or decreasing is crucial. ([arXiv][5])
   * **Data Sources:** CMIP6 climate model outputs (bias-corrected data for South Asia) ([arXiv][5])
   * **Visualization:** Raster maps, difference maps, or time-lapse / animated maps.

4. **Groundwater / Aquifer Map**

   * **What:** Map aquifer systems (e.g., the **Nubian Sandstone Aquifer System**) in/around Sudan, showing groundwater storage.
   * **Why:** Aquifers are critical water resources in arid / semi-arid regions. ([Wikipedia][6])
   * **Data Sources:** Geological / hydrogeological datasets, IAEA aquifer data, or published maps.
   * **Visualization:** Subsurface cross-sections, contour maps, or spatial polygons of aquifer extent.

5. **Flood Risk / Historical Flood Map**

   * **What:** Map major flood events (e.g., the 2020 Sudan floods) or flood-prone zones, perhaps with flood frequency. ([Wikipedia][7])
   * **Why:** Flooding is a big water risk; visualizing flood history / risk can guide adaptation.
   * **Data Sources:** Remote-sensing data (e.g., satellite flood maps), historical records, national data.
   * **Visualization:** Raster flood extents, flood frequency (heatmap), or risk classification.

6. **Rainwater Harvesting Potential Map**

   * **What:** Map potential sites for rainwater harvesting / water storage (especially in arid parts of Pakistan).
   * **Why:** In water-scarce regions, rainwater harvesting can significantly improve resilience. There's already research on this in the Indus basin. ([PMC][8])
   * **Data Sources:** Digital elevation models (to find catchment / topography), rainfall data, land use.
   * **Visualization:** Suitability map (e.g., potential storage sites, catchment suitability).

7. **Water Risk / Vulnerability Index Map**

   * **What:** Create a composite “water risk / vulnerability” index for countries (or sub-national) in the Global South, combining factors like water stress, flood risk, drought risk, access to safe water.
   * **Why:** A single index helps in policy and decision-making — showing where water risk is most acute.
   * **Data Sources:** SDG 6 data, climate projections, hydrological models, local surveys.
   * **Visualization:** Choropleth of index, or ranking map; maybe also radar charts for each country.

8. **Sea Level Rise & Coastal Flood Risk Map**

   * **What:** For countries with coastlines (or deltas), map projected sea-level rise and coastal inundation risk.
   * **Why:** Many Global South countries have vulnerable coastal zones; saltwater intrusion and flooding threaten water resources and livelihoods.
   * **Data Sources:** Global sea-level rise projections, DEMs (digital elevation models), tidal data.
   * **Visualization:** Inundation maps under different SLR scenarios, risk zones, adaptation areas.

---

## Recommended Map Ideas for **Pakistan** and **Sudan**

Focusing specifically on **Pakistan** and **Sudan**, here are some especially relevant ones:

* **Pakistan**

  1. Water stress per capita map (current + projected) — to highlight scarcity.
  2. Indus Basin hydrology: precipitation, glacier melt, runoff, downstream vs upstream water availability. (Upstream water consumption is already increasing. ([hess.copernicus.org][9]))
  3. Rainwater‑harvesting potential / water storage suitability in arid / semi-arid regions of Pakistan.
  4. Drought vulnerability / water insecurity index (combining water availability, usage, climate risk, etc.).

* **Sudan**

  1. Map of the **Nubian Sandstone Aquifer System** coverage in Sudan (and neighboring countries). ([Wikipedia][6])
  2. Flood risk / historical floods (e.g., mapping the 2020 floods) to understand flood-prone zones. ([Wikipedia][7])
  3. Water stress / renewable water resources per capita (especially as population is growing, and water resources are under pressure).
  4. Combined water risk / vulnerability index across Sudan’s states: surface water, groundwater, flood risk, drought.

---

## Implementation Sketch (Python + Cartopy / GIS)

Here is a rough outline / pseudocode of how you could implement, say, **two** of the above maps in Python:

### Example 1: Water Stress Map (Pakistan + Global South)
"""
# ```python
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import rasterio  # if you have raster data
import xarray as xr

# 1. Load country shapefile (or GeoJSON) for Global South
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
# Define a list of Global South countries (or filter by some criteria)
global_south = world[world['continent'].isin(['Africa', 'Asia', 'South America'])]

# 2. Load water stress data
# Suppose you have a raster / gridded dataset for water stress, or a per-country table
# For simplicity, assume a CSV: country, water_stress_value
import pandas as pd
ws = pd.read_csv("water_stress_by_country.csv")  # you need to prepare this

# 3. Merge with GeoDataFrame
global_south = global_south.merge(ws, left_on="name", right_on="country")

# 4. Plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

global_south.plot(column='water_stress_value', ax=ax, legend=True,
                   cmap='Reds', edgecolor='black')

ax.coastlines()
ax.set_title("Water Stress (Per‑Country) — Global South")

plt.show()

### Example 2: Hydrology / Indus Basin Map (Pakistan)

#```python
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# 1. Load Indus Basin polygon (you might get this from a shapefile / basin dataset)
indus_basin = gpd.read_file("indus_basin_shapefile.shp")

# 2. Load climate / hydrology raster (e.g., precipitation)
# Suppose you have a NetCDF file with precipitation from CMIP6 or observational data
ds = xr.open_dataset("precipitation_indus.nc")
precip = ds['precipitation']  # dimension: lat, lon (and maybe time)

# For simplicity, take the long-term average
precip_mean = precip.mean(dim='time')

# 3. Plot
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(1,1,1, projection=ccrs.PlateCarree())

# Plot the basin outline
indus_basin.to_crs(epsg=4326).plot(ax=ax, facecolor='none', edgecolor='blue', linewidth=1)

# Plot precipitation raster
precip_mean.plot.pcolormesh(ax=ax, transform=ccrs.PlateCarree(), cmap='Blues', alpha=0.6)

# Add features
ax.coastlines()
ax.set_title("Mean Precipitation over the Indus Basin")

plt.show()
"""

---

## Why These Are Valuable

* These maps not only **illustrate** current water challenges (scarcity, stress) but also highlight **future risks** (climate change, floods).
* They can inform **policy / planning**: e.g., where to invest in water infrastructure, rainwater harvesting, flood defenses.
* By focusing on **vulnerable countries** like Pakistan and Sudan (which have distinct hydrological risks), the maps become tools for advocacy, resilience planning, and public awareness.

---

If you like, I can **design 3-4 polished map prototypes** (with realistic data sources + sample Python notebooks) for Pakistan and Sudan **right now** — do you want me to do that?

[1]: https://www.dawn.com/news/1913435/water-scarcity-in-pakistan-a-geopolitical-ticking-time-bomb?utm_source=chatgpt.com "Water scarcity in Pakistan — a geopolitical ticking time bomb - Pakistan - DAWN.COM"
[2]: https://www.sdg6data.org/en/maps?utm_source=chatgpt.com "Maps | SDG 6 Data"
[3]: https://pide.org.pk/research/impact-of-climate-change-on-water-in-pakistan/?utm_source=chatgpt.com "Impact of Climate Change on Water in Pakistan"
[4]: https://en.wikipedia.org/wiki/WaterGAP?utm_source=chatgpt.com "WaterGAP"
[5]: https://arxiv.org/abs/2006.12976?utm_source=chatgpt.com "Bias-corrected climate projections from Coupled Model Intercomparison Project-6 (CMIP6) for South Asia"
[6]: https://en.wikipedia.org/wiki/Nubian_Sandstone_Aquifer_System?utm_source=chatgpt.com "Nubian Sandstone Aquifer System"
[7]: https://en.wikipedia.org/wiki/2020_Sudan_floods?utm_source=chatgpt.com "2020 Sudan floods"
[8]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12546836/?utm_source=chatgpt.com "Mapping of potential storages and rainwater harvesting sites in arid region of Indus basin using analytical hierarchy technique - PMC"
[9]: https://hess.copernicus.org/articles/26/861/2022/hess-26-861-2022.html?utm_source=chatgpt.com "HESS - Future upstream water consumption and its impact on downstream water availability in the transboundary Indus Basin"
"""
"""
Great — mapping the **Nubian Sandstone Aquifer System (NSAS)** in/around Sudan is a powerful and insightful project. Below — I’ll walk you through (1) **how to prepare / gather the input data**, and (2) **how to map it in Python (Cartopy / GeoPandas)** with a concrete example.

---

## 1. Preparing Input Data for the Nubian Sandstone Aquifer Map

Mapping an aquifer system requires a few components of data, and for the NSAS, given its transboundary nature, you'll likely combine several sources.

### A. Identify Data Sources / Acquire Data

1. **Hydrogeological / Aquifer Maps**

   * According to BGS (British Geological Survey) “Hydrogeology of Sudan”, there is a downloadable shapefile for Sudan’s hydrogeology, including major aquifers. ([earthwise.bgs.ac.uk][1])
   * The INWEB (International Groundwater Resources Assessment Centre) database has an entry for the Nubian Sandstone Aquifer System (NSAS) with some boundary data / metadata. ([inweb.gr][2])
   * The IAEA’s *Regional Strategic Action Programme for the Nubian Aquifer* provides maps and descriptions of areal extent. ([IAEA][3])
   * Research / journal articles (e.g., the MDPI Sustainability paper) include digitized basin geometries (sub‑basins like Kufra, Dakhla, North Sudan Platform) and may provide figures/maps to trace in GIS. ([MDPI][4])
   * A continental‑scale aquifer‑productivity / storage map was developed in *“Developing quantitative aquifer maps for Africa”* (MacDonald et al.) using a geological base map from USGS / Persits et al. ([NERC Open Research Archive][5])
   * Also related: the **WHYMAP** “Groundwater Resources of Africa” project provides mapped groundwater provinces. ([whymap.org][6])

2. **Attribute Data (Hydrogeological Parameters)**
   Beyond geometry, you may want to map variables like **thickness**, **storage**, **transmissivity**, or **piezometric head**. These come from:

   * Hydrogeology reports (e.g., “Hydrogeology of Sudan” gives aquifer thickness, specific yield, productivity). ([earthwise.bgs.ac.uk][1])
   * Scientific publications: for instance, *The Groundwater Flow Behavior and the Recharge in the NSAS* (Sustainability) gives sub-basin definitions, thickness, flow direction, etc. ([MDPI][4])
   * Transmissivity studies, such as for the Kharga Oasis, provide values that you might interpolate or classify. ([MDPI][7])
   * Recharge / storage change estimates (e.g., from GRACE / geophysical / modeling data) — e.g., *Sedimentary cover & structural trends study* reports recharge / depletion. ([Frontiers][8])

3. **Base Maps / Baseline Geography**

   * Political boundaries (countries: Sudan, Egypt, Libya, Chad) — via Natural Earth or similar.
   * Topography / elevation (if you want to show structural features, basement uplifts) — e.g., SRTM DEM.

---

### B. Preparing the Data

Once you have raw data sources, here’s how to prepare:

1. **Obtain Shapefiles / Vector Data**

   * Download the Sudan hydrogeology shapefile from BGS / Earthwise. ([earthwise.bgs.ac.uk][1])
   * Check INWEB’s website / their map database for NSAS boundary polygon. ([inweb.gr][2])
   * If only maps are available in papers (PDFs or images), you might digitize the aquifer boundary:

     * Use GIS software (QGIS) to georeference the image.
     * Trace the aquifer outline into a polygon shapefile.
     * Save it as a GeoJSON / Shapefile for use in Python.

2. **Attribute Table / Hydrogeology Attributes**

   * Create or enrich the shapefile’s attribute table with columns like `thickness_m`, `storage_m3`, `transmissivity`, `subbasin_name` etc.
   * Use data from reports / papers: e.g., if a paper says the thickness of NSAS in “North Sudan Platform” is ~500 m (just example), put that into the attribute table for that sub-basin polygon.

3. **Coordinate Reference System (CRS)**

   * Choose a suitable CRS. For visualization, **EPSG:4326** (WGS84) is easy. If you're doing modeling, a projected CRS (e.g., UTM or a regional projection) may be better.
   * Make sure all your layers (aquifer polygons, country boundaries, base map) align / reproject to the same CRS.

4. **Optional Raster / Gridded Data**

   * If you have gridded data (e.g., recharge, storage change from GRACE), you can load NetCDF / GeoTIFF.
   * Align / reproject that raster to match your vector geometry (aquifer polygon) so you can mask / clip, and visualize the aquifer’s parameter distribution.

---

## 2. Mapping the Aquifer System in Python

Here’s a **Python (GeoPandas + Matplotlib / Cartopy)** example to map the NSAS over Sudan (and neighboring states) and visualize some attribute (e.g., thickness or storage).
"""
#```python
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import rasterio
import rasterio.mask
import numpy as np

def plot_nsas_aquifer(aquifer_gdf, country_gdf, attr=None, raster_path=None):
    """
    Plots the Nubian Sandstone Aquifer System (NSAS) polygon(s) and optionally overlays
    a raster (e.g., storage or recharge) clipped to the aquifer.
    
    Parameters:
    - aquifer_gdf: GeoDataFrame containing the NSAS polygon(s)
    - country_gdf: GeoDataFrame of country boundaries (Sudan, etc.)
    - attr: (optional) name of attribute in aquifer_gdf to color by (e.g. thickness)
    - raster_path: (optional) path to a raster file that can be masked to aquifer extent
    """
    # Set up figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # Plot country boundaries
    country_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.8)
    
    # Plot the aquifer polygon
    if attr and attr in aquifer_gdf.columns:
        aquifer_gdf.plot(
            ax=ax,
            column=attr,
            cmap='Blues',
            legend=True,
            edgecolor='darkblue',
            linewidth=1,
            alpha=0.6
        )
    else:
        aquifer_gdf.plot(
            ax=ax,
            facecolor='lightblue',
            edgecolor='darkblue',
            alpha=0.5,
            linewidth=1
        )
    
    # If raster is given, mask and plot raster
    if raster_path:
        with rasterio.open(raster_path) as src:
            # mask raster to aquifer extent
            shapes = [feature["geometry"] for feature in aquifer_gdf.__geo_interface__['features']]
            out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
            out_meta = src.meta.copy()
            
            # plot raster - assuming single band
            data = out_image[0]
            # mask no data
            data = np.where(data == src.nodata, np.nan, data)
            
            # plot
            ax.imshow(
                data,
                origin='upper',
                transform=ccrs.PlateCarree()._as_mpl_transform(ax),
                extent=(
                    out_transform[2],
                    out_transform[2] + out_transform[0] * data.shape[1],
                    out_transform[5] + out_transform[4] * data.shape[0],
                    out_transform[5]
                ),
                cmap='viridis',
                alpha=0.7
            )
            plt.colorbar(ax.images[-1], ax=ax, label="Raster Value")
    
    ax.set_title("Nubian Sandstone Aquifer System (NSAS)", fontsize=14)
    ax.coastlines(resolution='110m')
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    
    plt.show()


def main():
    # Load data
    # 1. Aquifer polygon – your prepared shapefile / GeoJSON
    aquifer_gdf = gpd.read_file("nsas_aquifer.shp")  # you need to prepare this
    
    # 2. Country boundaries (Sudan, Egypt, Libya, Chad, etc.)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    countries = world[world['name'].isin(['Sudan', 'Egypt', 'Libya', 'Chad'])]
    
    # Optional: reproject
    aquifer_gdf = aquifer_gdf.to_crs(epsg=4326)
    countries = countries.to_crs(epsg=4326)
    
    # Optionally, plot with attribute
    plot_nsas_aquifer(aquifer_gdf, countries, attr="thickness_m", raster_path="nsas_storage.tif")


if __name__ == "__main__":
    main()
"""

---

## 3. Interpretation & Considerations

* **Interpretation**:

  * If you plot `thickness_m`, you’ll visually show where the aquifer is thickest (suggesting more stored sediment volume).
  * If you overlay a **storage-change raster** (e.g., from GRACE / modeling), you can highlight zones of depletion or recharge within the aquifer footprint.

* **Uncertainty**:

  * Aquifer geometry (especially depth, thickness) often comes with large uncertainties. Many published maps / models are based on limited well / geophysical data.
  * Storage estimates (volume) are often “order-of-magnitude” or model-based; treat them carefully.

* **Management Implications**:

  * Visualizing aquifer extent + storage can inform policymakers where pumping might be unsustainable.
  * It can also highlight transboundary management needs — the NSAS spans Sudan, Libya, Egypt, and Chad. ([Wikipedia][9])
  * Overlaying data like transmissivity or recharge gives insight into where sustainable use could be possible, or risk of over-extraction.

---

If you like, I can **find publicly available, high-quality GIS shapefiles** (or vector data) specifically for the NSAS (or other aquifers in Sudan) so you don’t have to digitize manually — do you want me to do that?

[1]: https://earthwise.bgs.ac.uk/index.php/Hydrogeology_of_Sudan?utm_source=chatgpt.com "Hydrogeology of Sudan - MediaWiki - BGS Earthwise"
[2]: https://www.inweb.gr/index.php?Itemid=202&option=com_inwebmedamapsdatabase&utm_source=chatgpt.com "Aquifers Database - INWEB"
[3]: https://www.iaea.org/sites/default/files/sap180913.pdf?utm_source=chatgpt.com "Ragional Strategic Action Programme for Nubian Aquifer ..."
[4]: https://www.mdpi.com/2071-1050/14/11/6823?utm_source=chatgpt.com "The Groundwater Flow Behavior and the Recharge in ..."
[5]: https://nora.nerc.ac.uk/id/eprint/501779/1/IR-10-103_map_finalSG.pdf?utm_source=chatgpt.com "Developing quantitative aquifer maps for Africa"
[6]: https://www.whymap.org/whymap/EN/Maps_Data/Gwrafrica/gwrafrica_node_en.html?utm_source=chatgpt.com "Groundwater Resources of Africa"
[7]: https://www.mdpi.com/2073-4441/12/2/604?utm_source=chatgpt.com "Estimation and Mapping of the Transmissivity of the Nubian Sandstone Aquifer in the Kharga Oasis, Egypt"
[8]: https://www.frontiersin.org/articles/10.3389/feart.2023.1173569/full?utm_source=chatgpt.com "Frontiers | Sedimentary cover and structural trends affecting the groundwater flow in the Nubian Sandstone Aquifer System: Inferences from geophysical, field and geochemical data"
[9]: https://en.wikipedia.org/wiki/Nubian_Sandstone_Aquifer_System?utm_source=chatgpt.com "Nubian Sandstone Aquifer System"
"""