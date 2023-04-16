"""Creates plots using the raw output from MPAS and not using the convert_mpas
   utility"""

import os
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
import multiprocessing as mp
import argparse

from geojson import GeometryCollection, LineString, Feature, FeatureCollection
import json
import time

import matplotlib.style as mplstyle

mplstyle.use("fast")


RADIAN_TO_DEGREE = 180 / np.pi
M_PER_S_TO_KT = 1.94384
MM_TO_IN = 0.03937008

NA_EXTENT = [-150, -60, 18, 80]
CONUS_EXTENT = [-126, -66, 15, 61]


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

PRECIP_CLEVS = [
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0,
    2.5,
    3,
    3.5,
    4,
    5,
    6,
    7,
    8,
    9,
]

PRECIP_CMAP_DATA = (
    np.array(
        [
            (190, 190, 190),
            (170, 165, 165),
            (130, 130, 130),
            (110, 110, 110),
            (180, 250, 170),
            (150, 245, 140),
            (120, 245, 115),
            (80, 240, 80),
            (30, 180, 30),
            (15, 160, 15),
            (20, 100, 210),
            (40, 130, 240),
            (80, 165, 245),
            (150, 210, 230),
            (180, 240, 250),
            (255, 250, 170),
            (255, 232, 120),
            (255, 192, 60),
            (253, 159, 0),
            (255, 96, 0),
            (253, 49, 0),
            (225, 20, 20),
            (191, 0, 0),
            (165, 0, 0),
            (135, 0, 0),
            (99, 59, 59),
            (139, 99, 89),
            (179, 139, 129),
            (199, 159, 149),
            (240, 240, 210),
        ]
    )
    / 255.0
)


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.5f} seconds to run.")
        return result

    return wrapper


def longtitude_360_to_180(lons):
    "Converts 0:360 longitude to -180:180"
    # return lons[lons > 180] -= 360
    None

    # return ((lon + 360) % 180) - 180



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


def basemap(projection=crs.PlateCarree()):
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
    ax.add_feature(states, facecolor="none", edgecolor="black")
    # ax.add_feature(USCOUNTIES.with_scale(county_scale), edgecolor="gray")

    return fig, ax


def add_geopotential_hgt(fig, ax, lons, lats, hgt, levels):

    contours = ax.tricontour(
        lons,
        lats,
        hgt,
        levels=levels,
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


def add_rel_vorticity_grid(fig, ax, lons, lats, rel_vort):
    cmap = mcolors.ListedColormap(VORT_CMAP)
    norm = mcolors.BoundaryNorm(VORT_LEVELS, cmap.N)

    vort_contours = ax.contourf(
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


def add_relative_humidity(fig, ax, lons, lats, rh):

    rh_levels = [
        0,
        1,
        2,
        3,
        5,
        10,
        15,
        20,
        25,
        30,
        40,
        50,
        60,
        65,
        70,
        75,
        80,
        85,
        90,
        95,
        99,
        100,
    ]

    cmap = get_cmap("BrBG")
    norm = mcolors.BoundaryNorm(rh_levels, cmap.N)

    rh_contours = ax.tricontourf(
        lons,
        lats,
        rh,
        # rh_levels,
        levels=rh_levels,
        cmap=cmap,
        norm=norm,
        transform=crs.PlateCarree(),
        extend="max",
    )

    fig.colorbar(rh_contours, ax=ax, orientation="vertical", pad=0.05)
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


def accumulated_precip_plot(diag_ds, mesh_ds, domain_name="colorado12km"):

    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """

    init_dt, valid_dt, fhour = ds_times(diag_ds)
    cycle = str(init_dt.hour).zfill(2)
    fhour_str = "f" + str(fhour).zfill(2)

    lats_cell = mesh_ds["latCell"] * RADIAN_TO_DEGREE
    lons_cell = mesh_ds["lonCell"] * RADIAN_TO_DEGREE
    lons_cell[lons_cell > 180] -= 360
    # lons_cell = longtitude_360_to_180(lons_cell)

    rain_in = diag_ds["rainnc"][0] * MM_TO_IN

    fig, ax = basemap()

    cmap = mcolors.ListedColormap(PRECIP_CMAP_DATA)
    norm = mcolors.BoundaryNorm(PRECIP_CLEVS, cmap.N)

    rain_contours = ax.tricontourf(
        lons_cell,
        lats_cell,
        rain_in,
        PRECIP_CLEVS,
        levels=PRECIP_CLEVS,
        cmap=cmap,
        norm=norm,
        # tranform=crs.PlateCarree(),
    )
    fig.colorbar(rain_contours, ax=ax, orientation="vertical", pad=0.05)
    title = plot_title(init_dt, valid_dt, fhour, "Accum Precip", "Dan MPAS", "in")
    ax.set_title(title)
    ax.set_extent(CONUS_EXTENT, crs=crs.PlateCarree())

    print("saving", f"products/images/{domain_name}-{cycle}z-precip-{fhour_str}.png")
    fig.savefig(
        f"products/images/{domain_name}-{cycle}z-precip-{fhour_str}.png",
        bbox_inches="tight",
    )
    plt.close(fig)

    # fig.show()


def accumulated_swe_plot(diag_ds, mesh_ds, domain_name="colorado12km"):

    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """

    init_dt, valid_dt, fhour = ds_times(diag_ds)
    cycle = str(init_dt.hour).zfill(2)
    fhour_str = "f" + str(fhour).zfill(2)

    lats_cell = mesh_ds["latCell"] * RADIAN_TO_DEGREE
    lons_cell = mesh_ds["lonCell"] * RADIAN_TO_DEGREE
    lons_cell[lons_cell > 180] -= 360
    # lons_cell = longtitude_360_to_180(lons_cell)

    rain_in = diag_ds["snownc"][0] * MM_TO_IN

    fig, ax = basemap()

    cmap = mcolors.ListedColormap(PRECIP_CMAP_DATA)
    norm = mcolors.BoundaryNorm(PRECIP_CLEVS, cmap.N)

    rain_contours = ax.tricontourf(
        lons_cell,
        lats_cell,
        rain_in,
        PRECIP_CLEVS,
        levels=PRECIP_CLEVS,
        cmap=cmap,
        norm=norm,
        tranform=crs.PlateCarree(),
    )
    fig.colorbar(rain_contours, ax=ax, orientation="vertical", pad=0.05)
    title = plot_title(init_dt, valid_dt, fhour, "Accum Swe", "Dan MPAS", "in")
    ax.set_title(title)
    ax.set_extent(CONUS_EXTENT, crs=crs.PlateCarree())

    print("saving", f"products/images/{domain_name}-{cycle}z-swe-{fhour_str}.png")
    fig.savefig(
        f"products/images/{domain_name}-{cycle}z-swe-{fhour_str}.png",
        bbox_inches="tight",
    )
    plt.close(fig)

    # fig.show()


@time_it
def plot_500_vorticity(diag_ds, mesh_ds, domain_name="colorado12km"):
    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """

    init_dt, valid_dt, fhour = ds_times(diag_ds)
    cycle = str(init_dt.hour).zfill(2)
    fhour_str = "f" + str(fhour).zfill(2)

    lats_cell = mesh_ds["latCell"] * RADIAN_TO_DEGREE
    lons_cell = mesh_ds["lonCell"] * RADIAN_TO_DEGREE
    lons_cell[lons_cell > 180] -= 360
    # lons_cell = longtitude_360_to_180(lons_cell)

    lats_vert = mesh_ds["latVertex"] * RADIAN_TO_DEGREE
    lons_vert = mesh_ds["lonVertex"] * RADIAN_TO_DEGREE
    lons_vert[lons_vert > 180] -= 360
    # lons_vert = longtitude_360_to_180(lons_vert)

    hgt_500_cell = diag_ds["height_500hPa"][0]
    hgt_500_cell_dm = hgt_500_cell / 10
    hgt_levels = np.arange(492, 594, 3)
    u_500_cell = diag_ds["uzonal_500hPa"][0] * M_PER_S_TO_KT
    v_500_cell = diag_ds["umeridional_500hPa"][0] * M_PER_S_TO_KT
    vort_500_vert = diag_ds["vorticity_500hPa"][0]
    vort_500_vert_scaled = vort_500_vert * 10**5

    grid_500_x, grid_500_y, grid_500_u = grid_data(lons_cell, lats_cell, u_500_cell)
    # grid_500_xvort, grid_500_yvort, grid_500_vert_scaled = grid_data(lons_vert, lats_vert, vort_500_vert_scaled)
    _, _, grid_500_v = grid_data(lons_cell, lats_cell, v_500_cell)

    fig, ax = basemap(crs.LambertConformal(central_longitude=-100))

    fig, ax = add_geopotential_hgt(
        fig, ax, lons_cell, lats_cell, hgt_500_cell_dm, hgt_levels
    )
    fig, ax = add_rel_vorticity(fig, ax, lons_vert, lats_vert, vort_500_vert_scaled)
    # fig, ax = add_rel_vorticity_grid(fig, ax, grid_500_xvort, grid_500_yvort, grid_500_vert_scaled)
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
    ax.set_extent(NA_EXTENT, crs=crs.PlateCarree())

    fig.savefig(
        f"products/images/{domain_name}-{cycle}z-vort500-{fhour_str}.png",
        bbox_inches="tight",
    )

    plt.close(fig)

    # fig.show()


@time_it
def plot_700_rh(diag_ds, mesh_ds, domain_name="colorado12km"):
    """outfile_path: Path of MPAS output file (history*, diagnostics*)
       mesh_path: Path of static/init mesh to provide cell lat/lons.

    Note: Some fields are on cell coordinates and some are on vertex coordinates
           hence the _cell and _vert suffix
    """

    init_dt, valid_dt, fhour = ds_times(diag_ds)
    cycle = str(init_dt.hour).zfill(2)
    fhour_str = "f" + str(fhour).zfill(2)

    lats_cell = mesh_ds["latCell"] * RADIAN_TO_DEGREE
    lons_cell = mesh_ds["lonCell"] * RADIAN_TO_DEGREE
    lons_cell[lons_cell > 180] -= 360
    # lons_cell = longtitude_360_to_180(lons_cell)

    rh_700 = diag_ds["relhum_700hPa"][0]
    hgt_700_cell = diag_ds["height_700hPa"][0]
    hgt_700_cell_dm = hgt_700_cell / 10
    hgt_700_levels = np.arange(180, 420, 3)

    u_700_cell = diag_ds["uzonal_700hPa"][0] * M_PER_S_TO_KT
    v_700_cell = diag_ds["umeridional_700hPa"][0] * M_PER_S_TO_KT

    grid_700_x, grid_700_y, grid_700_u = grid_data(lons_cell, lats_cell, u_700_cell)
    _, _, grid_700_v = grid_data(lons_cell, lats_cell, v_700_cell)

    fig, ax = basemap(crs.LambertConformal(central_longitude=-100))
    ax.set_extent(NA_EXTENT, crs=crs.PlateCarree())

    # Remove points where terrain is above the lowest contour level
    # to not have messed up contour lines in these areas
    unmasked = mesh_ds.ter < (10 * 180)
    lons_cell_unmasked = lons_cell[unmasked]
    lats_cell_unmasked = lats_cell[unmasked]
    hgt_700_cell_dm_unmasked = hgt_700_cell_dm[unmasked]
    fig, ax = add_geopotential_hgt(
        fig,
        ax,
        lons_cell_unmasked,
        lats_cell_unmasked,
        hgt_700_cell_dm_unmasked,
        hgt_700_levels,
    )

    fig, ax = add_relative_humidity(fig, ax, lons_cell, lats_cell, rh_700)

    fig, ax = add_wind_barbs(
        fig,
        ax,
        grid_700_x,
        grid_700_y,
        grid_700_u,
        grid_700_v,
    )

    title = plot_title(init_dt, valid_dt, fhour, "700mb RH", "Dan MPAS", "%")
    ax.set_title(title)
    ax.set_extent(NA_EXTENT, crs=crs.PlateCarree())

    print("saving", f"products/images/{domain_name}-{cycle}z-rh700-{fhour_str}.png")
    fig.savefig(
        f"products/images/{domain_name}-{cycle}z-rh700-{fhour_str}.png",
        bbox_inches="tight",
    )
    plt.close(fig)


def interp_terrain(mesh_ds):
    "Plots terrain using two methods"
    lats_cell = mesh_ds["latCell"] * RADIAN_TO_DEGREE
    lons_cell = mesh_ds["lonCell"] * RADIAN_TO_DEGREE
    lons_cell[lons_cell > 180] -= 360
    # lons_cell = longtitude_360_to_180(lons_cell)
    ter = mesh_ds["ter"]
    ter_ft = ter * 3.281

    fig1, ax1 = basemap()
    fig2, ax2 = basemap()

    grid_x, grid_y, grid_h = grid_data(
        lons_cell,
        lats_cell,
        ter_ft,
    )
    tricolor = ax2.tripcolor(lons_cell, lats_cell, ter_ft, transform=crs.PlateCarree())
    contourf = ax1.contourf(
        grid_x, grid_y, grid_h, levels=500, transform=crs.PlateCarree()
    )
    plt.colorbar(tricolor)
    plt.colorbar(contourf)
    plt.show()


def make_mesh(mesh_ds):
    """Creates kml linestrings from mesh.
    Caution: Will take a long time to make.
             Will take long time to draw on map
             Only use on regional meshes"""
    verts_on_edge = mesh_ds["verticesOnEdge"]
    lats_vert = mesh_ds["latVertex"] * RADIAN_TO_DEGREE
    lons_vert = mesh_ds["lonVertex"] * RADIAN_TO_DEGREE
    lons_vert[lons_vert > 180] -= 360
    # lons_vert = longtitude_360_to_180(lons_vert)

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


def make_cell_geojson(mesh_ds):
    "Creates lines of all cell edges"

    verts_on_edge = mesh_ds["verticesOnEdge"]
    lats_vert = mesh_ds["latVertex"] * RADIAN_TO_DEGREE
    lons_vert = mesh_ds["lonVertex"] * RADIAN_TO_DEGREE
    lons_vert[lons_vert > 180] -= 360

    # preallocate list of len(verts_on_edge)

    lines = np.empty(len(verts_on_edge), dtype=object)

    num_verts = len(verts_on_edge)

    for i, vert_idx in enumerate(verts_on_edge):
        if i % 1000 == 0:
            print(i, i / num_verts)

        vert0 = vert_idx[0]
        vert1 = vert_idx[1]

        x1 = float(lons_vert[vert0 - 1])
        x2 = float(lons_vert[vert1 - 1])

        y1 = float(lats_vert[vert0 - 1])
        y2 = float(lats_vert[vert1 - 1])

        # hack for lines that cross the 0/180 meridians that mess up displaying
        if (x1 > 0 and x2 < 0) or (x1 < 0 and x2 > 0):
            x1 = 0
            x2 = 0
            y1 = 0
            y2 = 0

        lines[i] = Feature(geometry=LineString([(x1, y1), (x2, y2)]))

    collection = FeatureCollection(lines.tolist())

    with open("global25km.geojson", "w") as f:
        json.dump(collection, f)


def error_callback(e):
    print(e)


def vort_500_plots(diag_files, mesh_file, domain_name):
    mesh_ds = xr.open_dataset(mesh_file)
    for diag_file in diag_files:
        try:
            diag_ds = xr.open_dataset(diag_file)
            plot_500_vorticity(diag_ds, mesh_ds, domain_name)
        except Exception as e:
            print("vort 500 plot exception: ", str(e))


def rh_700_plots(diag_files, mesh_file, domain_name):
    mesh_ds = xr.open_dataset(mesh_file)
    for diag_file in diag_files:
        try:
            diag_ds = xr.open_dataset(diag_file)
            plot_700_rh(diag_ds, mesh_ds, domain_name)
        except Exception as e:
            print("rh 700 plot exception: ", str(e))


def swe_plots(diag_files, mesh_file, domain_name):
    mesh_ds = xr.open_dataset(mesh_file)
    for diag_file in diag_files:
        try:
            diag_ds = xr.open_dataset(diag_file)
            accumulated_swe_plot(diag_ds, mesh_ds, domain_name)
        except Exception as e:
            print("swe plot exception: ", str(e))


def precip_plots(diag_files, mesh_file, domain_name):
    mesh_ds = xr.open_dataset(mesh_file)
    for diag_file in diag_files:
        try:
            diag_ds = xr.open_dataset(diag_file)
            accumulated_precip_plot(diag_ds, mesh_ds, domain_name)
        except Exception as e:
            print("precip plot exception: ", str(e))


def main(domain_name="colorado12km"):
    # domain_name = "colorado12km"
    file_dir = "products/mpas"
    files = sorted([f"{file_dir}/{f}" for f in os.listdir(file_dir) if ".nc" in f])

    # mesh_ds = xr.open_dataset(f"MPAS-Model/{domain_name}.static.nc")
    mesh_file = f"MPAS-Model/{domain_name}.static.nc"

    with mp.Pool() as pool:

        """
        vort_500_plots(files[0:1], mesh_file)
        rh_700_plots(files, mesh_file)
        precip_plots(files, mesh_file)
        swe_plots(files, mesh_file)
        """

        pool.apply_async(
            vort_500_plots,
            (files, mesh_file, domain_name),
            error_callback=error_callback,
        )

        pool.apply_async(
            rh_700_plots, (files, mesh_file, domain_name), error_callback=error_callback
        )

        pool.apply_async(
            precip_plots, (files, mesh_file, domain_name), error_callback=error_callback
        )

        # pool.apply_async(swe_plots, (files, mesh_file), error_callback=error_callback)

        pool.close()
        pool.join()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--domain",
        type=str,
        default="colorado12km",
        help="Domain name",
    )
    args = parser.parse_args()

    print("Domain", args.domain)
    main(domain_name=args.domain)
