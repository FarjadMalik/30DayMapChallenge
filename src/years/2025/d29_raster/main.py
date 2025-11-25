import rasterio
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch
from pypalettes import load_cmap
from pyfonts import load_font
from rasterio.plot import show

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_raster_png(raster_path, output_path):
   """
   """
   # Load raster data
   with rasterio.open(raster_path) as src:
    raster_data = src.read(1)
   
   text_color = "#000000"
   cmap1 = load_cmap("bee_eater", cmap_type="continuous")
   cmap1 = load_cmap("Beach", cmap_type="continuous")
   cmap2 = load_cmap("blaziken", cmap_type="continuous", reverse=True)
   cmap3 = load_cmap("bobcats", cmap_type="continuous", reverse=True)
   cmap4 = load_cmap("bryce", cmap_type="continuous", reverse=True)
   font = load_font(
      "https://raw.githubusercontent.com/BornaIz/markazitext/master/fonts/ttf/MarkaziText-Regular.ttf"
   )

   fig, mainax = plt.subplots(figsize=(9.7, 5))
   mainax.axis("off")

   ax1 = mainax.inset_axes([0, 0, 0.5, 0.5])
   ax2 = mainax.inset_axes([0.5, 0.5, 0.5, 0.5])
   ax3 = mainax.inset_axes([0.5, 0, 0.5, 0.5])
   ax4 = mainax.inset_axes([0, 0.5, 0.5, 0.5])

   ax1.set_xlim(-180, 0)
   ax1.set_ylim(-90, 0)

   ax2.set_xlim(0, 180)
   ax2.set_ylim(0, 90)

   ax3.set_xlim(0, 180)
   ax3.set_ylim(-90, 0)

   ax4.set_xlim(-180, 0)
   ax4.set_ylim(0, 90)

   show(raster_data, transform=src.transform, cmap=cmap1, ax=ax1)
   show(raster_data, transform=src.transform, cmap=cmap2, ax=ax2)
   show(raster_data, transform=src.transform, cmap=cmap3, ax=ax3)
   show(raster_data, transform=src.transform, cmap=cmap4, ax=ax4)

   for ax in [ax1, ax2, ax3, ax4]:
      ax.axis("off")

   text_prop = dict(size=11, color=text_color, ha="left", font=font)
   fig.text(x=0.05, y=0.18, s="#30daymapchallenge 2025", **text_prop)
   # fig.text(x=0.05, y=0.13, s="Raster Data", weight="bold", size=16, **text_prop)
   
   plt.tight_layout()
   plt.savefig(output_path, dpi=800, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for boundaries or admin units
   gr_50_fpath = "data/GRAY_50M_SR_OB/GRAY_50M_SR_OB.tif"

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_raster_png(raster_path=gr_50_fpath, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Map using raster data. Focus on satellite imagery, elevation models (DEMs), land cover, or pixel-based art.
    filename = 'raster'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
