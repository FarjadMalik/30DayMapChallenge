import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from pathlib import Path
from pypalettes import load_cmap
from pyfonts import load_font

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_png(dataset, column_to_use, output_path):
    """
    """
    # Create a Mercator project
    proj = ccrs.Mercator()
    dataset = dataset.to_crs(proj.proj4_init)
    
    # Load plot beautifications
    font = load_font(
        "https://github.com/BornaIz/markazitext/blob/master/fonts/ttf/MarkaziText-Regular.ttf?raw=true"
    )
    cmap = load_cmap("Acadia", keep=[False, False, True, False, True, True])
    background_color = "#fffdf3"

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={"projection": proj})
    fig.set_facecolor(background_color)
    ax.axis("off")

    # Plot world
    dataset.plot(ax=ax, column=column_to_use, edgecolor="black", lw=0.2, cmap=cmap)

    fig.text(
        x=0.5,
        y=1.05,
        s="An uncompleted list of",
        size=20,
        ha="center",
        va="top",
        font=font,
        color="#cfcdcd",
    )
    
    fig.text(
        x=0.5,
        y=1.01,
        s="Countries visited",
        size=30,
        ha="center",
        va="top",
        font=font,
    )

    fig.text(x=0.25, y=0.2, s="National\n\nVisited\n\nBucket List?", ha="left", font=font, size=12)

    ax.add_patch(
        plt.Rectangle(
            (0.11, 0.274),
            0.02,
            0.025,
            facecolor=cmap.colors[0],
            lw=0.5,
            edgecolor="black",
            transform=ax.transAxes,
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (0.11, 0.227),
            0.02,
            0.025,
            facecolor=cmap.colors[1],
            lw=0.5,
            edgecolor="black",
            transform=ax.transAxes,
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (0.11, 0.18),
            0.02,
            0.025,
            facecolor=cmap.colors[2],
            lw=0.5,
            edgecolor="black",
            transform=ax.transAxes,
        )
    )

    fig.text(
        x=0.75,
        y=0.1,
        s="#30DayMapChallenge",
        font=font,
        ha="right",
        size=8,
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
    """    
    """
    logger.info(f"Generating {path_dir}")

    # Load the shapefile for world admin boundaries
    world_gdf = gpd.read_file("data/countries.geojson")
    world_gdf = world_gdf[~world_gdf["name"].isin(["Antarctica"])]
    
    # Add countries i have been to
    world_gdf["visited"] = world_gdf["name"].apply(
        lambda x: (
            0 if x in ["Belgium", "Pakistan"]
            else 
                1 if x in ["Italy", "Spain", "Germany", "United Kingdom", 
                            "Netherlands", "Austria", "India", "France"] 
                else 2  
        )
    )

    # Generate and save map
    output_path = Path(path_dir).parent / f"{filename}"
    create_png(world_gdf, "visited", output_path)

    logger.info(f"Map created – open '{filename}' to view.")

if __name__ == "__main__":
    # --- Plot countries you have been (use fonts and custom legend)---
    filename = '10min_map'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
