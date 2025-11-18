import folium
import geopandas as gpd
import contextily as ctx
import leafmap.foliumap as leafmap
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


usage_map = {
    'education': [
        'university', 'school', 'college', 'kindergarten',
        'prep_school', 'driving_school', 'music_school',
        'research_institute', 'library', 'public_bookcase'
    ],
    'health': [
        'clinic', 'hospital', 'doctors', 'dentist',
        'pharmacy', 'childcare', 'optician', 'medical_supply',
        'chemist', 'hearing_aids'
    ],
    'food&recreation': [
        'restaurant', 'fast_food', 'food_court', 'cafe', 'ice_cream',
        'bbq', 'bar', 'pub', 'bakery', 'supermarket', 'butcher',
        'confectionery', 'dairy', 'beverages', 'juice', 'tea',
        'coffee', 'sweets', 'organic_food_store', 'nimco', 'naan_house',
        'grocery', 'general_store', 'convenience', 'health_food',
        'theatre', 'cinema', 'hookah_lounge', 'gambling', 'martial_arts_club',
        'fitness_equipment_wholesaler', 'swimming_pool', 'video_games',
        'music', 'tattoo', 'mall', 'shop', 'hardware', 'furniture', 'clothes', 'tailor',
        'electronics', 'computer', 'mobile_phone', 'mobile_shop',
        'department_store', 'variety_store', 'art', 'fashion',
        'toys', 'gift', 'cosmetics', 'jewelry', 'optics', 'shoes',
        'stationery', 'bag', 'watch', 'perfume', 'pet', 'florist',
        'hairdresser', 'beauty', 'laundry', 'dry_cleaning',
        'photo', 'repair', 'printing', 'print_shop', 'travel_agency',
        'funeral_directors', 'massage', 'rental', 'cleaning',
        'welding', 'locksmith', 'pest_control_service', 'marketplace'
    ],
    'other': [
        'unknown', 'misc', 'place_of_worship', 'religion', 'townhall', None
    ]
}

def classify_usage(row):
    """
    """
    amenity = (row.get('amenity') or '').lower()
    shop = (row.get('shop') or '').lower()

    for usage, keywords in usage_map.items():
        if any((k and k.lower() in amenity) or (k and k.lower() in shop) for k in keywords):
            return usage
    return 'other'

# def create_leafmap(admin, dataset, output_path, layer_name, color, cmap = "Accent"):
#     """
#     """
    
#     # Calculate a center for the map, e.g., the mean of the bounds
#     bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
#     center_lat = (bounds[1] + bounds[3]) / 2
#     center_lon = (bounds[0] + bounds[2]) / 2

#     # Plot basemap and center accordingly
#     basemap = leafmap.Map(center=(center_lat, center_lon), zoom=6)
#     basemap.add_basemap("CartoDB.Positron")
#     # Add our dataset
#     basemap.add_gdf(dataset, layer_name=layer_name, color_column=color, cmap=cmap)
    
#     # Save the map to an HTML file
#     basemap.save(f"{output_path}.html")

def create_html(dataset, column_to_use, output_path):
    """
    """
    # Ensure the CRS is WGS84 (EPSG:4326)
    if dataset is not None and dataset.crs.to_string() != "EPSG:4326":
        dataset = dataset.to_crs(epsg=4326) 

    # Get unique usage categories for defining color map
    usage_categories = dataset[column_to_use].unique()
    # Choose a qualitative colormap
    cmap = plt.get_cmap('tab20', len(usage_categories))
    # Map each category to a hex color
    colors = {cat: mcolors.to_hex(cmap(i)) for i, cat in enumerate(usage_categories)}
    # Create base map centered on mean coordinates
    center = [dataset.geometry.y.mean(), dataset.geometry.x.mean()]
    basemap = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

    # Add points with color by usage
    for idx, row in dataset.iterrows():
        usage = row[column_to_use]
        color = colors.get(usage, "gray")
        tooltip = f"<b>Usage:</b> {usage}<br><b>Amenity:</b> {row.get('amenity')}<br><b>Shop:</b> {row.get('shop')}"
        
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.8,
            tooltip=tooltip
        ).add_to(basemap)

    # Add a legend
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 200px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:12px;
        ">
        <b>&nbsp;Usage Legend</b><br>
    """
    for cat, col in colors.items():
        legend_html += f'&nbsp;<i style="background:{col};width:10px;height:10px;float:left;margin-right:5px"></i>{cat}<br>'
    legend_html += "</div>"

    basemap.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{output_path}.html")

# def create_png(admin, dataset, output_path, cmap, colors):
    # """
    # """
    # usage_categories = 
    # # Pick a color map with enough distinct colors
    # cmap = plt.get_cmap('Accent', len(usage_categories))  # 'tab20', 'Set3', 'Accent' are good for categories

    # # Create a mapping from usage category to color
    # colors = {cat: cmap(i) for i, cat in enumerate(usage_categories)}

    # # Plot setup
    # # Make sure your GeoDataFrame is projected to Web Mercator
    # # (required for contextily basemaps)
    # dataset = dataset.to_crs(epsg=3857)
    # fig, ax = plt.subplots(figsize=(10, 10))
    # dataset.plot(
    #     ax=ax,
    #     color=dataset['usage'].map(colors),
    #     markersize=10,
    #     alpha=0.8
    # )
    # # Add a basemap (many options available)
    # ctx.add_basemap(
    #     ax,
    #     source=ctx.providers.OpenStreetMap.Mapnik,  # Try: CartoDB.Positron, OpenStreetMap.Mapnik, etc.
    #     attribution=False
    # )
    # # Legend setup
    # handles = [plt.Line2D([0], [0], marker='o', color='w', label=cat,
    #                     markerfacecolor=colors[cat], markersize=8)
    #         for cat in usage_categories]

    # ax.legend(handles=handles, title="OSM POI Usage Categories", loc='upper right', bbox_to_anchor=(1.3, 1))
    # ax.set_title("OSM Points of Interest by Usage", fontsize=14)
    # ax.set_axis_off()
    # plt.tight_layout()
    # plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
    """
    """
    logger.info(f"Generating {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_2.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    admin_gdf = admin_gdf.loc[admin_gdf['NAME_2'] == 'Karachi',
                              ['NAME_2', 'geometry']]
    
    
    # Calculate bounds to only read necessary osm data, file too big
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    # Load Osm data
    poi_gdf = gpd.read_file("data/hotosm/hotosm_pak_points_of_interest_points_shp.shp", 
                            bbox=(bounds[0], bounds[1], bounds[2], bounds[3]))
    
    # Filter only major amenities/POIs
    amenity_list = ['clinic;hospital', 'hookah_lounge', 'gambling', 'bank;restaurant', 'shop', 'Food_Court_-_Forum_Mall',
                    'pub', 'bbq', 'bar', 'cinema', 'food', 'ice_cream',
                    'theatre', 'kindergarten', 'music_school', 'library', 'food_court', 'dentist',
                    'childcare', 'doctors', 'research_institute', 'prep_school', 'taxi', 'townhall',
                    'university', 'public_bookcase', 'clinic', 'fast_food', 'school', 'hospital',
                    'restaurant', 'college', 'driving_school', 'dancing_school', 'trade_school', ]
    poi_gdf = poi_gdf.loc[((poi_gdf['amenity'].isin(amenity_list)) | (poi_gdf['shop'].notna())),
                          ['name', 'amenity', 'shop', 'geometry']]

    poi_gdf['usage'] = poi_gdf.apply(classify_usage, axis=1)

    # Generate and save map
    output_path = f"{Path(path_dir).parent}/{filename}"
    create_html(poi_gdf, 'usage', output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Get osm for pakistan and display important areas of centers
    # Karachi, fast food vs other needed amneties, health vs education vs recreation vs basic needs
    filename = 'karachi_osm_amenities'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
