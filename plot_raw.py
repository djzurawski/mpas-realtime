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
import simplekml
from dateutil.parser import isoparse
from datetime import timezone

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


def grid_data(x, y, z, side_len=None):
    """Interpolates 3 1D arrays of xcoords, ycoords, values
    into a grid.
    Useful for plotting windbarbs"""

    if not side_len:
        side_len = int(np.sqrt(len(x)))

    x_pts = np.linspace(np.min(x), np.max(x), side_len)
    y_pts = np.linspace(np.min(y), np.max(y), side_len)

    grid_x, grid_y = np.meshgrid(x_pts, y_pts)
    grid_z = griddata((x, y), z, (grid_x, grid_y), method="cubic")
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
    fig, ax, grid_lon, grid_lat, grid_u, grid_v, barb_length=5.5, barb_interval=10
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


def ds_times(ds):
    valid_date_str = ds.xtime.values[0].strip()
    valid_dt = isoparse(valid_date_str).replace(tzinfo=timezone.utc)

    initial_date_str = ds.initial_time.item().decode().strip()
    initial_dt = isoparse(initial_date_str).replace(tzinfo=timezone.utc)

    elapsed_secs = (valid_dt - initial_dt).total_seconds()
    secs_per_hour = 3600
    elapsed_hours = int(elapsed_secs // secs_per_hour)

    return initial_dt, valid_dt, elapsed_hours


def plot_title(init_dt, valid_dt, fhour, field_name, model_name="", field_units=""):

    date_format = "%Y-%m-%dT%HZ"
    init_str = init_dt.strftime(date_format)
    valid_str = valid_dt.strftime(date_format)
    fhour = str(fhour).zfill(2)

    return f"{model_name}   Init: {init_str}    Valid: {valid_str}    {field_name} ({field_units})   Hour: {fhour}"


def plot_500_vorticity(outfile_path, mesh_path):
    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """
    ds = xr.open_dataset("diag-small.nc")
    ds_cells = xr.open_dataset("colorado-small.static.nc")

    init_dt, valid_dt, fhour = ds_times(ds)

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

    title = plot_title(init_dt, valid_dt, fhour, "Rel Vort", "Dan MPAS", "10^5 s^-1")
    ax.set_title(title)
    fig.show()


def interp_terrain(grid_path):
    "Plots terrain using two methods"
    ds_cells = xr.open_dataset(grid_path)
    lats_cell = ds_cells["latCell"] * RADIAN_TO_DEGREE
    lons_cell = ds_cells["lonCell"] * RADIAN_TO_DEGREE
    lons_cell = longtitude_360_to_180(lons_cell)
    ter = ds_cells["ter"]
    ter_ft = ter * 3.281

    fig1, ax1 = basemap()
    fig2, ax2 = basemap()

    grid_x, grid_y, grid_h = grid_data(
        lons_cell,
        lats_cell,
        ter_ft,
    )
    ax2.tripcolor(lons_cell, lats_cell, ter_ft, transform=crs.PlateCarree())
    ax1.contourf(grid_x, grid_y, grid_h, levels=500, transform=crs.PlateCarree())
    plt.show()


def make_mesh(grid_path):
    """Creates kml linestrings from mesh.
    Caution: Will take a long time to make.
             Will take long time to draw on map
             Only use on regional meshes"""
    ds_cells = xr.open_dataset(grid_path)
    verts_on_edge = ds_cells["verticesOnEdge"]
    lats_vert = ds_cells["latVertex"] * RADIAN_TO_DEGREE
    lons_vert = ds_cells["lonVertex"] * RADIAN_TO_DEGREE
    lons_vert = longtitude_360_to_180(lons_vert)

    kml = simplekml.Kml()
    for i, vert_idx in enumerate(verts_on_edge):
        if i % 1000 == 0:
            print(i, i / len(verts_on_edge))

        x1 = float(lons_vert[vert_idx[0] - 1])
        x2 = float(lons_vert[vert_idx[1] - 1])

        y1 = float(lats_vert[vert_idx[0] - 1])
        y2 = float(lats_vert[vert_idx[1] - 1])

        ls = kml.newlinestring()
        ls.coords = [(x1, y1), (x2, y2)]
        ls.style.linestyle.width = 1
        ls.style.linestyle.color = simplekml.Color.blue
    kml.save("mpas_mesh.kml")
