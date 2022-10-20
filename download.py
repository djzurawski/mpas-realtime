from datetime import datetime, timedelta
import requests
import concurrent.futures
import f90nml
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

NAMELIST_DATE_FORMAT = "%Y-%m-%d_%H:%M:%S"
RUN_DURATION_FORMAT = "%-d_%H:%M:%S"


PREPROC_STAGES = {
    "config_static_interp": False,
    "config_native_gwd_static": False,
    "config_vertical_grid": True,
    "config_met_interp": True,
    "config_input_sst": False,
    "config_frac_seaice": True,
}


def run_duration_format(td):
    "Could not find a way to 'strftime' timedelta objects"
    seconds_elapsed = td.total_seconds()

    days = int(seconds_elapsed // (24 * 3600))
    seconds_elapsed -= days * 24 * 3600

    hours = int(seconds_elapsed // 3600)
    seconds_elapsed -= hours * 3600

    minutes = int(seconds_elapsed // 60)
    seconds_elapsed -= minutes * 60

    seconds = int(seconds_elapsed)

    hours_str = str(hours).zfill(2)
    minutes = str(minutes).zfill(2)
    seconds_str = str(seconds).zfill(2)

    duration_str = f"{days}_{hours_str}:{minutes}:{seconds_str}"

    return duration_str


def select_gfs_cycle():
    """Attemps to figure out the most recent GFS
    cycle available on NOMADS for current time"""
    utc_hour = datetime.utcnow().hour
    if utc_hour >= 5 and utc_hour < 11:
        return 0
    if utc_hour >= 11 and utc_hour < 17:
        return 6
    if utc_hour >= 17 and utc_hour < 21:
        return 12
    if utc_hour >= 21 or utc_hour < 5:
        return 18


def is_last_cycle_yesterday():
    utc_hour = datetime.utcnow().hour
    if utc_hour < 5:
        return True
    else:
        return False


def latest_gfs_init_date():
    now = datetime.utcnow()
    cycle = select_gfs_cycle()
    if is_last_cycle_yesterday():
        date = now - timedelta(days=1)
    else:
        date = now

    date = date.replace(hour=cycle, minute=0, second=0, microsecond=0)

    return date


def grib_filename(valid_dt, cycle, fhour, model="gfs"):
    fhour = str(fhour).zfill(2)
    date = valid_dt.replace(second=0, microsecond=0)
    date_str = date.isoformat()
    fname = f"{model}.t{cycle}.f{fhour}.{date_str}.grib2"
    return fname


def download_filtered_grib(init_date, cycle, fhour):
    """Downloads gribs filtered to selected area"""

    valid_date = init_date + timedelta(hours=fhour)

    grib_dir = "data/grib"
    fname = grib_filename(valid_date, cycle, fhour, "gfs")

    fhour = str(fhour).zfill(3)
    cycle = str(cycle).zfill(2)

    leflon = -135
    rightlon = -80
    toplat = 60
    bottomlat = 20

    init_day_of_year = init_date.strftime("%Y%m%d")

    params = {
        "file": f"gfs.t{cycle}z.pgrb2.0p25.f{fhour}",
        "all_lev": "on",
        "all_var": "on",
        "subregion": "",
        "leftlon": leflon,
        "rightlon": rightlon,
        "toplat": toplat,
        "bottomlat": bottomlat,
        "dir": f"/gfs.{init_day_of_year}/{cycle}/atmos",
    }

    url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?"

    print("Downloading", fname)
    r = requests.get(url, params=params)
    with open(f"{grib_dir}/{fname}", "wb") as f:
        f.write(r.content)

    return r.status_code


def download_gribs(init_date, flength):
    cycle = str(init_date.hour).zfill(2)

    fhours = [i for i in range(flength + 1)]
    init_dates = [init_date for i in fhours]
    cycles = [cycle for i in fhours]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        responses = executor.map(download_filtered_grib, init_dates, cycles, fhours)

    return responses


def download_latest_grib(flength=12):
    init_date = latest_gfs_init_date()
    download_gribs(init_date, flength)
    return init_date


def update_wps_namelist(init_date, flength):

    start_str = init_date.strftime(NAMELIST_DATE_FORMAT)
    end_date = init_date + timedelta(hours=flength)
    end_str = end_date.strftime(NAMELIST_DATE_FORMAT)
    fpath = f"{os.environ['PROGRAM_DIR']}/WPS-4.4/namelist.wps"
    wps_nml = f90nml.read(fpath)

    wps_nml["share"]["start_date"] = start_str
    wps_nml["share"]["end_date"] = end_str
    wps_nml["share"]["interval_seconds"] = 3600
    with open(fpath, "w") as f:
        wps_nml.write(f)

    return wps_nml


def prep_initial_streams(domain_name):
    tree = ET.parse("MPAS-Model/streams.init_atmosphere")
    root = tree.getroot()

    for node in root:
        if node.attrib["name"] == "input":
            node.attrib["filename_template"] = f"{domain_name}.static.nc"
        if node.attrib["name"] == "output":
            node.attrib["filename_template"] = f"{domain_name}.init.nc"

    new_xml = ET.tostring(root)
    pretty_xml = minidom.parseString(new_xml).toprettyxml(indent="    ")
    pretty_xml_lines = pretty_xml.splitlines()
    pretty_xml_no_version = pretty_xml_lines[1:]
    # remove excessive blank lines
    pretty_xml = os.linesep.join([s for s in pretty_xml_no_version if s.strip()])

    with open("MPAS-Model/streams.init_atmosphere", "w") as f:
        f.write(pretty_xml)


def prep_lbc_streams(domain_name):
    tree = ET.parse("MPAS-Model/streams.init_atmosphere")
    root = tree.getroot()

    for node in root:
        if node.attrib["name"] == "input":
            node.attrib["filename_template"] = f"{domain_name}.init.nc"
        if node.attrib["name"] == "output":
            node.attrib["filename_template"] = f"{domain_name}.foo.nc"

    new_xml = ET.tostring(root)
    pretty_xml = minidom.parseString(new_xml).toprettyxml(indent="    ")
    pretty_xml_lines = pretty_xml.splitlines()
    pretty_xml_no_version = pretty_xml_lines[1:]
    # remove excessive blank lines
    pretty_xml = os.linesep.join([s for s in pretty_xml_no_version if s.strip()])

    with open("MPAS-Model/streams.init_atmosphere", "w") as f:
        f.write(pretty_xml)


def prep_run_streams(domain_name):
    tree = ET.parse("MPAS-Model/streams.atmosphere")
    root = tree.getroot()

    for node in root:
        if node.attrib["name"] == "input":
            node.attrib["filename_template"] = f"{domain_name}.init.nc"

        if node.attrib["name"] == "lbc_in":
            node.attrib["input_interval"] = "1:00:00"

    new_xml = ET.tostring(root)
    pretty_xml = minidom.parseString(new_xml).toprettyxml(indent="    ")
    pretty_xml_lines = pretty_xml.splitlines()
    pretty_xml_no_version = pretty_xml_lines[1:]
    # remove excessive blank lines
    pretty_xml = os.linesep.join([s for s in pretty_xml_no_version if s.strip()])

    with open("MPAS-Model/streams.atmosphere", "w") as f:
        f.write(pretty_xml)


def prep_initial_namelist(domain_name, init_date, flength):
    nml = f90nml.read("MPAS-Model/namelist.init_atmosphere")

    start_str = init_date.strftime(NAMELIST_DATE_FORMAT)
    end_date = init_date + timedelta(hours=flength)
    end_str = end_date.strftime(NAMELIST_DATE_FORMAT)
    case = 7

    nml["nhyd_model"]["config_init_case"] = case
    nml["nhyd_model"]["config_start_time"] = start_str
    nml["nhyd_model"]["config_stop_time"] = end_str

    nml["preproc_stages"] = PREPROC_STAGES
    nml["decomposition"][
        "config_block_decomp_file_prefix"
    ] = f"{domain_name}.graph.info.part."

    with open("MPAS-Model/namelist.init_atmosphere", "w") as f:
        nml.write(f)


def prep_lbc_namelist(domain_name, init_date, flength):
    nml = f90nml.read("MPAS-Model/namelist.init_atmosphere")

    start_str = init_date.strftime(NAMELIST_DATE_FORMAT)
    end_date = init_date + timedelta(hours=flength)
    end_str = end_date.strftime(NAMELIST_DATE_FORMAT)
    case = 9

    nml["nhyd_model"]["config_init_case"] = case
    nml["nhyd_model"]["config_start_time"] = start_str
    nml["nhyd_model"]["config_stop_time"] = end_str

    nml["preproc_stages"] = PREPROC_STAGES
    nml["data_sources"]["config_fg_interval"] = 3600
    nml["data_sources"]["config_met_prefix"] = "FILE"
    nml["decomposition"][
        "config_block_decomp_file_prefix"
    ] = f"{domain_name}.graph.info.part."

    with open("MPAS-Model/namelist.init_atmosphere", "w") as f:
        nml.write(f)


def prep_run_namelist(domain_name, init_date, flength):
    nml = f90nml.read("MPAS-Model/namelist.atmosphere")

    td = timedelta(hours=flength)
    run_duration_str = run_duration_format(td)
    start_str = init_date.strftime(NAMELIST_DATE_FORMAT)

    nml["nhyd_model"]["config_start_time"] = start_str
    nml["nhyd_model"]["config_run_duration"] = run_duration_str
    nml["limited_area"]["config_apply_lbcs"] = True
    nml["decomposition"][
        "config_block_decomp_file_prefix"
    ] = f"{domain_name}.graph.info.part."

    with open("MPAS-Model/namelist.atmosphere", "w") as f:
        nml.write(f)


def prep_initial_conditions(domain_name, init_date, flength):
    prep_initial_streams(domain_name)
    prep_initial_namelist(domain_name, init_date, flength)


def prep_lbc(domain_name, init_date, flength):
    prep_lbc_streams(domain_name)
    prep_lbc_namelist(domain_name, init_date, flength)


def prep_run(domain_name, init_date, flength):
    prep_run_streams(domain_name)
    prep_run_namelist(domain_name, init_date, flength)


if __name__ == "__main__":
    flength = 84 
    init_date = download_latest_grib(flength)
    update_wps_namelist(init_date, flength)
