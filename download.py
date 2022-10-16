from datetime import datetime, timedelta
import requests
import concurrent.futures
import f90nml
import os


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

    leflon = -125
    rightlon = -87
    toplat = 52
    bottomlat = 25

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
    namelist_date_format = "%Y-%m-%d_%H:%M:%S"
    start_str = init_date.strftime(namelist_date_format)
    end_date = init_date + timedelta(hours=flength)
    end_str = end_date.strftime(namelist_date_format)
    fpath = f"{os.environ['PROGRAM_DIR']}/WPS-4.4/namelist.wps"
    wps_nml = f90nml.read(fpath)

    wps_nml["share"]["start_date"] = start_str
    wps_nml["share"]["end_date"] = end_str
    wps_nml["share"]["interval_seconds"] = 3600
    with open(fpath, "w") as f:
        wps_nml.write(f)

    return wps_nml


if __name__ == "__main__":
    flength = 84 
    init_date = download_latest_grib(flength)
    update_wps_namelist(init_date, flength)
