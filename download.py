from datetime import datetime, timedelta
import requests
import concurrent.futures


def select_gfs_cycle():
    """Attemps to figure out the most recent GFS
    cycle available on NOMADS for current time"""
    utc_hour = datetime.utcnow().hour
    if utc_hour >= 5 and utc_hour < 11:
        return "00"
    if utc_hour >= 11 and utc_hour < 17:
        return "06"
    if utc_hour >= 17 and utc_hour < 21:
        return "12"
    if utc_hour >= 21 or utc_hour < 5:
        return "18"


def is_last_cycle_yesterday():
    utc_hour = datetime.utcnow().hour
    if utc_hour < 5:
        return True
    else:
        return False


def latest_day_and_cycle():
    cycle = select_gfs_cycle()
    if is_last_cycle_yesterday():
        date = datetime.utcnow() - timedelta(days=1)
    else:
        date = datetime.utcnow()

    return date.strftime("%Y%m%d"), cycle


def grib_filename(cycle, fhour, model="gfs"):
    fhour = str(fhour).zfill(2)
    return f"{model}.t{cycle}z.f{fhour}.grib2"


def download_filtered_grib(day_of_year, cycle, fhour):
    """Downloads gribs filtered to selected area
    day_of_year = 'yyyymmdd'"""

    grib_dir = "data/grib"
    fname = grib_filename(cycle, fhour, "gfs")

    fhour = str(fhour).zfill(3)
    cycle = str(cycle).zfill(2)

    leflon = -125
    rightlon = -87
    toplat = 52
    bottomlat = 25

    params = {
        "file": f"gfs.t{cycle}z.pgrb2.0p25.f{fhour}",
        "subregion": "",
        "leftlon": leflon,
        "rightlon": rightlon,
        "toplat": toplat,
        "bottomlat": bottomlat,
        "dir": f"/gfs.{day_of_year}/{cycle}/atmos",
    }

    url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"

    print("Downloading", fname)
    r = requests.get(url, params=params)
    with open(f"{grib_dir}/{fname}", "wb") as f:
        f.write(r.content)

    return r.status_code


def download_gribs(date, cycle, flength):
    cycle = str(cycle).zfill(2)

    fhours = [i for i in range(flength + 1)]
    dates = [date for i in fhours]
    cycles = [cycle for i in fhours]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        responses = executor.map(download_filtered_grib, dates, cycles, fhours)

    return responses


def download_latest_grib():
    date, cycle = latest_day_and_cycle()
    download_gribs(date, cycle, 12)
    return date, cycle
