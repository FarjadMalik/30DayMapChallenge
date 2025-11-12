import folium
import geopandas as gpd
import contextily as ctx
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

def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_2.shp"
    admin_gdf = gpd.read_file(shapefile_path)
    admin_gdf = admin_gdf.loc[admin_gdf['NAME_2'] == 'Karachi',
                              ['NAME_2', 'geometry']]
    # Ensure the CRS is WGS84 (EPSG:4326)
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)
    
    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")

    # Load Osm data
    poi_gdf = gpd.read_file("data/hotosm/hotosm_pak_points_of_interest_points_shp.shp", 
                            bbox=(bounds[0], bounds[1], bounds[2], bounds[3]))
    logger.debug(f"poi_gdf len - {len(poi_gdf)}")
    amenity_list = ['clinic;hospital', 'hookah_lounge', 'gambling', 'bank;restaurant', 'shop', 'Food_Court_-_Forum_Mall',
                    'pub', 'bbq', 'bar', 'cinema', 'food', 'ice_cream',
                    'theatre', 'kindergarten', 'music_school', 'library', 'food_court', 'dentist',
                    'childcare', 'doctors', 'research_institute', 'prep_school', 'taxi', 'townhall',
                    'university', 'public_bookcase', 'clinic', 'fast_food', 'school', 'hospital',
                    'restaurant', 'college', 'driving_school', 'dancing_school', 'trade_school', ]
    poi_gdf = poi_gdf.loc[((poi_gdf['amenity'].isin(amenity_list)) | (poi_gdf['shop'].notna())),
                          ['name', 'amenity', 'shop', 'geometry']]
    if poi_gdf.crs != admin_gdf.crs:
        poi_gdf.to_crs(admin_gdf.crs.to_string() , inplace=True)
    logger.debug(f"poi_gdf len - {len(poi_gdf)}")
    # logger.debug(f"poi_gdf amenities - {poi_gdf.amenity.unique()}")
    # logger.debug(f"poi_gdf shops - {poi_gdf.shop.unique()}")

    def classify_usage(row):
        amenity = (row.get('amenity') or '').lower()
        shop = (row.get('shop') or '').lower()

        for usage, keywords in usage_map.items():
            if any((k and k.lower() in amenity) or (k and k.lower() in shop) for k in keywords):
                return usage
        return 'other'

    poi_gdf['usage'] = poi_gdf.apply(classify_usage, axis=1)
    logger.debug(f"POI usage counts - {poi_gdf['usage'].value_counts()}")

    # Get unique usage categories
    usage_categories = poi_gdf['usage'].unique()

    # # Pick a color map with enough distinct colors
    # cmap = plt.get_cmap('Accent', len(usage_categories))  # 'tab20', 'Set3', 'Accent' are good for categories

    # # Create a mapping from usage category to color
    # colors = {cat: cmap(i) for i, cat in enumerate(usage_categories)}

    # # Plot setup
    # # Make sure your GeoDataFrame is projected to Web Mercator
    # # (required for contextily basemaps)
    # poi_gdf = poi_gdf.to_crs(epsg=3857)
    # fig, ax = plt.subplots(figsize=(10, 10))
    # poi_gdf.plot(
    #     ax=ax,
    #     color=poi_gdf['usage'].map(colors),
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
    # plt.show()
    # import leafmap.foliumap as leafmap

    # m = leafmap.Map(center=(center_lat, center_lon), zoom=6)
    # m.add_gdf(poi_gdf, layer_name="POIs", color_column="usage", cmap="Accent")
    # m.add_basemap("CartoDB.Positron")
    # # Allows toggling between layers interactively
    # # m.LayerControl().add_to(basemap)
    # # Save the map to an HTML file
    # m.save(f"{Path(path_dir).parent}/{file_out}.html")
    # logger.info(f"Map created – open '{file_out}.html' to view.")

    # Define color map by usage
    usage_categories = poi_gdf['usage'].unique()
    # Choose a qualitative colormap
    cmap = plt.get_cmap('tab20', len(usage_categories))
    # Map each category to a hex color
    colors = {cat: mcolors.to_hex(cmap(i)) for i, cat in enumerate(usage_categories)}
    # Create base map centered on mean coordinates
    center = [poi_gdf.geometry.y.mean(), poi_gdf.geometry.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

    # Add points with color by usage
    for idx, row in poi_gdf.iterrows():
        usage = row['usage']
        color = colors.get(usage, "gray")
        tooltip = f"<b>Usage:</b> {usage}<br><b>Amenity:</b> {row.get('amenity')}<br><b>Shop:</b> {row.get('shop')}"
        
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.8,
            tooltip=tooltip
        ).add_to(m)

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

    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)
    # Save the map to an HTML file
    m.save(f"{Path(path_dir).parent}/{file_out}.html")
    logger.info(f"Map created – open '{file_out}.html' to view.")


if __name__ == "__main__":
    # Get osm for pakistan and display important areas of centers
    # Karachi, fast food vs other needed amneties, health vs education vs recreation vs basic needs
    out_filename = 'karachi_osm_amenities'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)
