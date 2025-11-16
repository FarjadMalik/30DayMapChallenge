import pyvista as pv

from pathlib import Path
from pyvista import examples
from pypalettes import load_cmap

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def generate_map(path_dir: str, file_out: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Generating {path_dir}")

    # Load and prepare the Earth topography data
    land = examples.download_topo_land().triangulate().decimate(0.98)
    land.point_data["Elevation"] = land.points[:, 2]
    
    # Initialize the plotter with transparent background
    p = pv.Plotter()
    cmap = load_cmap("Coconut", cmap_type="continuous")
    p.add_mesh(land, cmap=cmap, show_scalar_bar=False)  # Disable scalar bar

    # Set the background to be fully transparent
    # p.background_color = (245, 40, 145, 0)
    p.set_background(color="#080c14")

    # Save as image
    output_path = Path(path_dir).parent / f"{file_out}"
    # Export the plot to an HTML file with transparency
    p.save_graphic(f"{output_path}.svg")
    p.export_html(f"{output_path}.html")
    
    logger.info(f"Map created – open '{file_out}.png' to view.")


if __name__ == "__main__":
    # use pretty maps or a new tool pyvista, TODO: see and load other example data for this
    out_filename = 'newtool'
    generate_map(path_dir=str(get_relative_path(__file__)), file_out=out_filename)
