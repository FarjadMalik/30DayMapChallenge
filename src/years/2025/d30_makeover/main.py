import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from pathlib import Path
from matplotlib.patches import Patch
from matplotlib.animation import FuncAnimation
from pypalettes import add_cmap
from pyfonts import load_font

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path

logger = get_logger(__name__)


def create_png(admin, dataset, indicator_code, output_path):
   """
   """
   # Get basic indicator subsets and info
   subset = dataset[(dataset["Indicator Code"] == indicator_code)]
   indicator_name = subset["Indicator Name"].unique()[0]
   # logger.debug(f"Subset Len - {len(subset)}")
   # logger.debug(f"indicator_name - {indicator_name}")
   
   # Get min and max values for indicator
   subset_min = subset["Value"].min()
   subset_max = subset["Value"].max()
   # Subset min is less than 0 than, for linegraph y axis 
   if subset_min < 0:
      y_axis_values = [1.05 * subset_min, 0, subset_max/2, subset_max * 1.05]
   else:
      y_axis_values = [0, subset_max/4, subset_max/2, subset_max * 1.05]
   
   logger.debug(f"y_axis_values - {y_axis_values}")

   # Get list of years for frames and also its min/max
   years = sorted(dataset["Year"].unique())
   min_year = years[0]
   max_year = years[-1]
   # logger.debug(f"Years to frame len - {len(years)} - {min_year=} - {max_year=}")

   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   font = load_font(
    "https://raw.githubusercontent.com/coreyhu/Urbanist/main/fonts/ttf/Urbanist-Medium.ttf"
   )
   boldfont = load_font(
      "https://raw.githubusercontent.com/coreyhu/Urbanist/main/fonts/ttf/Urbanist-ExtraBold.ttf"
   )

   green = "#115740"
   white = "#FFFFFF"
   red = "#FF0000"
   # if the minimum value of indicator is less than 0 than we show red first, otherwise the higher the worse
   if subset_min < 0:
      cmap = add_cmap(colors=[red, white, green], name="PakistanWithDanger", cmap_type="continuous")
   else:
      cmap = add_cmap(colors=[green, white, red], name="PakistanWithDanger", cmap_type="continuous")

   # create fig and axis
   # _, ax = plt.subplots(figsize=(12, 10))
   fig, ax = plt.subplots(dpi=500)
   fig.set_facecolor("#ffffff")

   text_args = dict(
      # va="top",
      # ha="left",
      transform=fig.transFigure,
   )
   
   def update(year):
      # Clear and set up axis
      ax.clear()
      ax.set_axis_off()
      # Set map focus and limits
      # ax.set_xlim(center_lon - 7, center_lon + 7)
      ax.set_ylim(center_lat - 9, center_lat + 9)

      subset_lty = subset.loc[subset["Year"] <= year]
      value = subset.loc[subset["Year"] == year, "Value"].values[0]
      # logger.debug(f"CPI: Year - {year}, Value - {value}")
      color = cmap((value - subset_min) / (subset_max - subset_min))

      # Plot Pakistan with colors 
      admin.plot(ax=ax, color=color, edgecolor="black", linewidth=0.2)
      lineax = ax.inset_axes(bounds=(-0.1, 0.62, 0.6, 0.22), transform=ax.transAxes)
      lineax.set_ylim(subset_min, subset_max * 1.1)
      lineax.axis("off")

      lineax.scatter(
         subset_lty["Year"],
         subset_lty["Value"],
         c=subset_lty["Value"],
         cmap=cmap,
         s=7,
         zorder=5,
      )

      lineax.hlines(
         y=y_axis_values,
         xmin=min_year,
         xmax=max_year,
         color="black",
         linewidth=0.3,
         zorder=1,
         alpha=0.4,
      )
      for y_value in y_axis_values:
         lineax.text(
            x=min_year,
            y=y_value,
            s=f"{y_value:.0f}%",
            font=font,
            size=5,
            va="center",
            ha="left",
         )

      ax.text(
         x=0.5,
         y=0.9,
         s=f"Pakistan {indicator_name} - {str(year)[:4]}",
         size=12,
         font=font,
         va="top",
         ha="center",
         **text_args
      )
      ax.text(
         x=0.69,
         y=0.40,
         s=f"{value:.1f}%",
         size=16,
         color=color,
         path_effects=[pe.Stroke(linewidth=1, foreground="black"), pe.Normal()],
         font=boldfont,
         va="top",
         ha="left",
         **text_args,
      )
      ax.text(
         x=0.6, y=0.3, s=f"#30DayMapChallenge - WDI Inflation Indicators", size=5, font=boldfont, **text_args
      )

   # Save and exit
   anim = FuncAnimation(fig, update, frames=years)
   anim.save(f"{output_path}.gif", fps=5)

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")

   # Load the shapefile for boundaries or admin units
   admin_gdf = gpd.read_file("data/pakistan_admin/gadm41_PAK_3.shp")
   admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'NAME_3', 'geometry']]
   
   # Read WDI File for Pakistan
   wdi_df = pd.read_csv("data/WDI_CSV_10_08/WDICSV.csv")
   wdi_df = wdi_df.loc[wdi_df['Country Name'] == "Pakistan"]
   # Only get a few indicators worth mentioning
   wdi_df = wdi_df.loc[wdi_df['Indicator Code'].isin([
                                 'NY.GDP.PCAP.KD.ZG',    # GDP per capita
                                 'FP.CPI.TOTL'           # Consumer Price index
                                 ]), :]
   # reshape (wide → long)
   wdi_df = pd.melt(
         wdi_df,
         id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],  # fixed columns
         var_name="Year",
         value_name="Value"
      )
   wdi_df["Year"] = wdi_df["Year"].astype(int)
   
   # Sort so that years are in order
   wdi_df = wdi_df.sort_values(
      by=["Country Name", "Indicator Code", "Year"]
   ).reset_index(drop=True)
   # Now do group-based fill: for each country & indicator, forward-fill and back-fill missing Values
   wdi_df["Value"] = (
      wdi_df
      .groupby(["Country Name", "Indicator Code"])["Value"]
      .ffill()
      .bfill()
   )

   logger.debug(f"World Development Indicators len  - {len(wdi_df)}")
   logger.debug(f"World Development Indicators columns  - {wdi_df.columns}")
   logger.debug(f"World Development Indicators GDP  - {wdi_df.loc[wdi_df['Indicator Code']=='NY.GDP.PCAP.KD.ZG'].head()}")
   logger.debug(f"World Development Indicators GDP  - {wdi_df.loc[wdi_df['Indicator Code']=='FP.CPI.TOTL'].head()}")

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(admin=admin_gdf, dataset=wdi_df, indicator_code='FP.CPI.TOTL', output_path=f"{output_path}_CPI")
   create_png(admin=admin_gdf, dataset=wdi_df, indicator_code='NY.GDP.PCAP.KD.ZG', output_path=f"{output_path}_GDP")

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # A line graph gif with map over time (inflation, food prices, etc)
    filename = 'WDI_makeover' # World Development Indicators
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
