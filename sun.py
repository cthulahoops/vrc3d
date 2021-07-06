import datetime
from math import asin, acos, sin, cos, pi, radians, degrees
from collections import namedtuple

from vector import Vector
from skyfield import api

AngularPosition = namedtuple("AngularPosition", ("azimuth", "elevation"))

LONGITUDE = radians(-73.985)
LATITUDE = radians(40.6913)

TS = api.load.timescale()
PLANETS = api.load("de421.bsp")
SUN, EARTH, MOON = PLANETS['sun'], PLANETS['earth'], PLANETS['moon']
BROOKLYN = EARTH + api.wgs84.latlon(40.6913, -73.985)

def time_of_day(dt):
    return (dt - dt.replace(hour=0, minute=0, second=0)).seconds


def day_of_year(dt):
    return (dt - dt.replace(month=1, day=1)).days + 1


def year_angle(days):
    return (days - 81) * 2 * pi / 365


def equation_of_time(days):
    b = year_angle(day_of_year(days))
    return 9.87 * sin(2 * b) - 7.53 * cos(b) - 1.5 * sin(b)


def tc(longitude, utctime):
    return 4 * degrees(longitude) + equation_of_time(utctime)


def lst(longitude, utctime):
    return utctime + datetime.timedelta(minutes=tc(longitude, utctime))


def declination(dt):
    b = year_angle(day_of_year(dt))
    return radians(23.45 * sin(b))


def hour_angle(longitude, dt):
    solar_time = lst(longitude, dt)
    hours = time_of_day(solar_time) / 3600
    return radians(15) * (hours - 12)


def angular_position(longitude, latitude, dt):
    hra = hour_angle(longitude, dt)
    decl = declination(dt)
    elevation = asin(sin(decl) * sin(latitude) + cos(decl) * cos(latitude) * cos(hra))
    azimuth = acos((sin(decl) * cos(latitude) - cos(decl) * sin(latitude) * cos(hra)) / cos(elevation))
    if hra > 0:
        azimuth = 2 * pi - azimuth

    return AngularPosition(azimuth, elevation)


def to_cartesian(polar):
    x = sin(polar.azimuth) * cos(polar.elevation)
    z = -cos(polar.azimuth) * cos(polar.elevation)
    y = sin(polar.elevation)

    return Vector(x, y, z)


def position(longitude, latitude, dt):
    dt = dt.replace(tzinfo=api.utc)
    t = TS.from_datetime(dt)
    (alt, az, _dis) = BROOKLYN.at(t).observe(SUN).apparent().altaz()
    return to_cartesian(AngularPosition(az.radians, alt.radians))

def moon_position(longitude, latitude, dt):
    dt = dt.replace(tzinfo=api.utc)
    t = TS.from_datetime(dt)
    (alt, az, _dis) = BROOKLYN.at(t).observe(MOON).apparent().altaz()
    return to_cartesian(AngularPosition(az.radians, alt.radians))

# return to_cartesian(angular_position(longitude, latitude, dt))


def run_example():
    import time
    latitude = radians(40.7)
    longitude = radians(-74.006)
    dt = datetime.datetime.utcnow()
    print(dt)
    print(f"SUMMARY FOR {degrees(longitude)}, {degrees(latitude)}")
    print(f"Equation of time: {equation_of_time(dt)}")
    print(f"Declination: {degrees(declination(dt))}")
    print(f"Hour angle: {degrees(hour_angle(longitude, dt))}")
    print(f"Local solar time: {lst(longitude, dt)}")
    ap = angular_position(longitude, latitude, dt)
    print(f"Azimuth: {degrees(ap.azimuth)}")
    print(f"Elevation: {degrees(ap.elevation)}")
    t0 = time.time()
    print(position(longitude, latitude, dt))
    print("Time: ", time.time() - t0)

#     from astropy.coordinates import SkyCoord, AltAz, EarthLocation
#     import astropy.time
#     import astropy.coordinates
#     import time

#     t0 = time.time()

# #    print(time.time())
#     obs_time = astropy.time.Time(dt)
#     location = EarthLocation(lon=-73.985, lat=40.6913)
#     sun = astropy.coordinates.get_body('sun', obs_time, location)
#     print(sun)
#     print(time.time() - t0)
#     t0 = time.time()
#     altaz = sun.transform_to(AltAz(location=location))
#     print(altaz)
#     print(time.time() - t0)


    # import time
    # print("# SKYFIELD")
    # from skyfield import api

    # t0 = time.time()

    # print("Time = ", t)

    # brooklyn = earth + api.wgs84.latlon(40.6913, -73.985)
    # print("Brooklyn: ", brooklyn)
    # (alt, az, _dis) = brooklyn.at(t).observe(sun).apparent().altaz()
    # print(to_cartesian(AngularPosition(az.radians, alt.radians)))

    # print("Moon: ", brooklyn.at(t).observe(moon).apparent().altaz())

    # print(time.time() - t0)


if __name__ == "__main__":
    run_example()
