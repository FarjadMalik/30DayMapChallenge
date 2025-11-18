import pandas as pd
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


# Define color scheme
def plant_color(value: str | None) -> str:
    """
    """
    if value == "Nuclear":
        return "red"
    elif value in ("Oil", "Gas", "Coal"):
        return "black"
    elif value in ("Solar", "Hydro", "Wind"):
        return "green"
    else:
        return "blue"

# Compute marker size
def compute_radius(row, min_radius=4, max_radius=25, scale_factor=0.1):
    """
    """
    val = row.get('capacity_mw', None)
    if pd.isna(val):
        return min_radius
    radius = min_radius + (val * scale_factor)
    return min(radius, max_radius)
    
def create_png(admin, dataset, output_path):
    """
    """
    # Reproject to Web Mercator for contextily
    dataset = dataset.to_crs(epsg=3857)

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(10, 10))
    # Plot boundary
    admin.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1)
    # Plot powerplants
    dataset.plot(
        ax=ax,
        color=dataset["color"],
        markersize=dataset["radius"] * 10,  # scale up for visibility
        alpha=0.7,
        edgecolor="white",
        linewidth=0.3
    )

    # Add basemap from contextily
    ctx.add_basemap(ax, crs=admin.crs.to_string(), source=ctx.providers.CartoDB.VoyagerNoLabels)

    # Beautify
    ax.set_title("Power Plants in Pakistan (WRI)", fontsize=14, fontweight="bold")
    ax.set_axis_off()

    # # Remove extra white padding
    # plt.tight_layout(pad=0)
    # # Set transparent background (if needed)
    # fig.patch.set_alpha(0)
    # # Slightly larger figure for better resolution
    # fig.set_size_inches(8, 8)


    # Add custom legend, can be dynamically created using dataset
    legend_entries = {
        "Nuclear": "red",
        "Fossil Fuels (Oil/Gas/Coal)": "black",
        "Renewables (Solar/Hydro/Wind)": "green",
        "Other/Unknown": "blue"
    }
    for _, (label, color) in enumerate(legend_entries.items()):
        ax.scatter([], [], color=color, label=label, s=60)
    ax.legend(frameon=True, loc='lower left')

    # Save as image and exit
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")
    plt.close(fig)
    
def generate_minimal_map(path_dir: str, filename: str):
    """
    Creates a static PNG map using matplotlib + contextily
    """
    logger.info(f"Generating {path_dir}")

    # Load admin boundaries
    admin_gdf = gpd.read_file("data/pakistan_admin/gadm41_PAK_0.shp")
    admin_gdf = admin_gdf.to_crs(epsg=3857)

    # Load powerplant dataset
    gpkg_path = "data/PAK_misc/wri_powerplants/wri-powerplants__PAK.gpkg"
    powerplants_gdf = gpd.read_file(gpkg_path, layer='wri-powerplants')

    # Filter for Pakistan and keep minimal columns
    powerplants_gdf = powerplants_gdf.loc[
        powerplants_gdf['country'] == 'PAK',
        ['country', 'name', 'capacity_mw', 'latitude', 'longitude',
         'primary_fuel', 'owner', 'source', 'geometry']
    ]

    # Compute style attributes
    powerplants_gdf["color"] = powerplants_gdf["primary_fuel"].apply(plant_color)
    powerplants_gdf["radius"] = powerplants_gdf.apply(compute_radius, axis=1)

    # Generate and save map
    output_path = Path(path_dir).parent / f"{filename}"
    create_png(admin_gdf, powerplants_gdf, output_path)

    logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    filename = 'pak_powerplants'
    generate_minimal_map(path_dir=str(get_relative_path(__file__)), filename=filename)
