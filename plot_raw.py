"""Creates plts using the raw output from MPAS and not using the convert_mpas
   utility"""

import xarray as xr
import cartopy.crs as crs
from cartopy.feature import NaturalEarthFeature
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import matplotlib.colors as mcolors
import numpy as np
from scipy.interpolate import griddata
from metpy.plots import USCOUNTIES

RADIAN_TO_DEGREE = 180 / np.pi
M_PER_S_TO_KT = 1.94384

VORT_CMAP = (
    np.array(
        [
            (255, 255, 255),
            (190, 190, 190),
            (151, 151, 151),
            (131, 131, 131),
            (100, 100, 100),
            (0, 255, 255),
            (0, 231, 205),
            (0, 203, 126),
            (0, 179, 0),
            (126, 205, 0),
            (205, 231, 0),
            (255, 255, 0),
            (255, 205, 0),
            (255, 153, 0),
            (255, 102, 0),
            (255, 0, 0),
            (205, 0, 0),
            (161, 0, 0),
            (141, 0, 0),
            (121, 0, 0),
            (124, 0, 102),
            (145, 0, 155),
            (163, 0, 189),
            (255, 0, 231),
            (255, 201, 241),
        ]
    )
    / 255.0
)

VORT_LEVELS = [
    0.5,
    1,
    1.5,
    2,
    3,
    4,
    5,
    6,
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    25,
    30,
    35,
    40,
    45,
    50,
    55,
    60,
    85,
]


def longtitude_360_to_180(lon):
    "Converts 0:360 longitude to -180:180"
    return ((lon + 360) % 180) - 180


def grid_data(x, y, z):
    """Interpolates 3 1D arrays of xcoords, ycoords, values
    into a grid.
    Useful for plotting windbarbs"""

    x_side = np.sort(np.unique(x))
    y_side = np.sort(np.unique(y))

    # If necessary reduce grid dims to save compute time
    max_side_length = 500
    if len(x) > max_side_length:
        interval = int(len(x_side) / max_side_length)
        x_side = x_side[::interval]
        y_side = y_side[::interval]

    grid_x, grid_y = np.meshgrid(x_side, y_side)

    grid_z = griddata((x, y), z, (grid_x, grid_y))
    return grid_x, grid_y, grid_z


def basemap():
    projection = crs.PlateCarree()
    fig = plt.figure(figsize=(18, 10))
    ax = plt.axes(projection=projection)

    border_scale = "50m"
    county_scale = "20m"
    states = NaturalEarthFeature(
        category="cultural",
        scale=border_scale,
        facecolor="none",
        edgecolor="black",
        name="admin_1_states_provinces",
    )
    lakes = NaturalEarthFeature(
        "physical", "lakes", border_scale, edgecolor="blue", facecolor="none"
    )
    ax.add_feature(lakes, facecolor="none", edgecolor="blue", linewidth=0.5)
    ax.add_feature(states, facecolor="none", edgecolor="black")
    ax.coastlines(border_scale, linewidth=0.8)

    states = NaturalEarthFeature(
        category="cultural",
        scale=border_scale,
        facecolor="none",
        edgecolor="black",
        name="admin_1_states_provinces",
    )
    ax.add_feature(states, facecolor="none", edgecolor="black")
    ax.add_feature(USCOUNTIES.with_scale(county_scale), edgecolor="gray")

    return fig, ax


def add_500hPa_hgt(fig, ax, lons, lats, hgt_500):

    hgt_levels = np.arange(492, 594, 3)

    hgt_500_dm = hgt_500 / 10
    contours = ax.tricontour(
        lons,
        lats,
        hgt_500_dm,
        levels=hgt_levels,
        colors="black",
        transform=crs.PlateCarree(),
    )
    plt.clabel(contours, inline=1, fontsize=10, fmt="%i")

    return fig, ax


def add_rel_vorticity(fig, ax, lons, lats, rel_vort):
    cmap = mcolors.ListedColormap(VORT_CMAP)
    norm = mcolors.BoundaryNorm(VORT_LEVELS, cmap.N)

    vort_contours = ax.tricontourf(
        lons,
        lats,
        rel_vort,
        VORT_LEVELS,
        levels=VORT_LEVELS,
        norm=norm,
        cmap=cmap,
        transform=crs.PlateCarree(),
    )
    plt.colorbar(vort_contours, ax=ax, orientation="vertical", pad=0.05)

    return fig, ax


def add_wind_barbs(
    fig, ax, grid_lon, grid_lat, grid_u, grid_v, barb_length=5.5, barb_interval=0
):
    step = barb_interval
    ax.barbs(
        grid_lon[::step, ::step],
        grid_lat[::step, ::step],
        grid_u[::step, ::step],
        grid_v[::step, ::step],
        transform=crs.PlateCarree(),
        length=barb_length,
    )
    return fig, ax


def plot_500_vorticity(outfile_path, mesh_path):
    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """
    ds = xr.open_dataset("diag.2022-10-13_22.00.00.nc")
    ds_cells = xr.open_dataset("colorado.grid.nc")

    lats_cell = ds_cells["latCell"] * RADIAN_TO_DEGREE
    lons_cell = ds_cells["lonCell"] * RADIAN_TO_DEGREE
    lons_cell = longtitude_360_to_180(lons_cell)

    lats_vert = ds_cells["latVertex"] * RADIAN_TO_DEGREE
    lons_vert = ds_cells["lonVertex"] * RADIAN_TO_DEGREE
    lons_vert = longtitude_360_to_180(lons_vert)

    hgt_500_cell = ds["height_500hPa"][0]
    u_500_cell = ds["uzonal_500hPa"][0] * M_PER_S_TO_KT
    v_500_cell = ds["umeridional_500hPa"][0] * M_PER_S_TO_KT
    vort_500_vert = ds["vorticity_500hPa"][0]
    vort_500_vert_scaled = vort_500_vert * 10**5

    grid_500_x, grid_500_y, grid_500_u = grid_data(lons_cell, lats_cell, u_500_cell)
    _, _, grid_500_v = grid_data(lons_cell, lats_cell, v_500_cell)

    fig, ax = basemap()
    fig, ax = add_500hPa_hgt(fig, ax, lons_cell, lats_cell, hgt_500_cell)
    fig, ax = add_rel_vorticity(fig, ax, lons_vert, lats_vert, vort_500_vert_scaled)
    fig, ax = add_wind_barbs(
        fig,
        ax,
        grid_500_x,
        grid_500_y,
        grid_500_u,
        grid_500_v,
    )

    ax.set_xlim((np.min(lons_vert), np.max(lons_vert)))
    ax.set_ylim((np.min(lats_vert), np.max(lats_vert)))
    fig.show()
