__author__ = 'antonio franco'

'''
Copyright (C) 2019  Antonio Franco (antonio_franco@live.it)
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import json
import requests
import backoff
from geopy import distance, Point
from math import radians, sin, cos, atan2, degrees, asin
import matplotlib.pyplot as plt


class PostException(Exception):
    def __init__(self, message: str, error_code: int) -> None:
        """
        Custom exception for POST requests
        :param message: standard message for Exception objects
        :param error_code: POST request error code
        """
        super().__init__(message)
        print("POST status code: " + str(error_code))
        self.error = error_code


def backoff_hdlr(details):
    print("Backing off {wait:0.1f} seconds after {tries} tries "
          "calling function {target} with args {args} and kwargs "
          "{kwargs}".format(**details))


class TerrainProfile(object):
    def __init__(self) -> None:
        """
        Class used to construct a terrain profile. It uses the open elevation API -
         https://github.com/Jorl17/open-elevation/blob/master/docs/api.md .
         Consider donating.
        """
        super().__init__()

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8,
                          jitter=None,
                          on_backoff=backoff_hdlr)
    def get_altitude(self, locations: list) -> list:
        """
        Returns the elevations above sea level in meters, given a list of tuple of geographic coordinates
        (in WGS 84 Web Mercator), e.g. locations = [(10,10),(20,20),(41.161758,-8.583933)] . It retries a maximum of 8
        times in case of timeout, with an exponential backoff. It raises an error if the returned POST status code is
        not 200.
        Note:
        In case of proxy the method must be modified ( https://2.python-requests.org/en/master/user/advanced/#proxies ).
        :param locations (list): list of tuple of geographic coordinates (in WGS 84 Web Mercator), e.g.
         locations = [(10,10),(20,20),(41.161758,-8.583933)]
        :return (list): list of dicts in the format {"latitude": float, "longitude": float, "elevation": float}
        """
        loc_vector = []
        for i in range(0, len(locations)):
            temp_dict = {"latitude": locations[i][0], "longitude": locations[i][1]}
            loc_vector.append(temp_dict)

        loc_dict = {"locations": loc_vector}

        loc_json = json.dumps(loc_dict)

        headers = {'content-type': 'application/json', "Accept": "application/json"}

        # In case of proxies modify here
        r = requests.post("https://api.open-elevation.com/api/v1/lookup",
                          data=loc_json, headers=headers)

        if r.status_code != 200:
            raise PostException("POST not successful with code: " + str(r.status_code), r.status_code)

        el_dict = json.loads(r.text)

        ret_vec = []
        for el in el_dict["results"]:
            temp_dict = {"latitude": float(el["latitude"]), "longitude": float(el["longitude"]),
                         "elevation": float(el["elevation"])}
            ret_vec.append(temp_dict)

        return ret_vec

    @staticmethod
    def get_distance(p1: Point, p2: Point) -> float:
        """
        Returns the distance, in meters, between two geopy.point
        :param p1: geopy.Point
        :param p2: geopy.Point
        :return (float): distance in meters
        """
        return distance.distance(p1, p2).m

    @staticmethod
    def get_bearing(p1: Point, p2: Point) -> float:
        """
       Calculation of direction between two geographical points in degrees.
       Thanks to: http://pastebin.com/JbhWKJ5m
        :param p1: geopy.Point
        :param p2: geopy.Point
        :return (float): bearing (angle) between the two points in degrees
       """
        latitude_1 = p1.latitude
        latitude_2 = p2.latitude

        longitude_1 = p1.longitude
        longitude_2 = p2.longitude

        rlat1 = radians(latitude_1)
        rlat2 = radians(latitude_2)
        rlon1 = radians(longitude_1)
        rlon2 = radians(longitude_2)
        drlon = rlon2 - rlon1

        b = atan2(sin(drlon) * cos(rlat2),
                  cos(rlat1) * sin(rlat2) - sin(rlat1) * cos(
                      rlat2) * cos(drlon))
        return (degrees(b) + 360) % 360

    @staticmethod
    def point_from_dist_and_angle(p: Point, bearin: float, dist: float) -> Point:
        """
        Given an origin point p, a bearing in degrees and a distance in meters, it calculates the point from p with
        angle bearin and distance dist from p .
        Thanks: https://stackoverflow.com/a/7835325
        :param p: origin point p
        :param brng: bearing in degrees
        :param dist: distance in meters from p
        :return: resulting point
        """
        brng = radians(bearin)
        d = 1e-3 * dist
        R = distance.EARTH_RADIUS

        lat1 = radians(p.latitude)  # Current lat point converted to radians
        lon1 = radians(p.longitude)  # Current long point converted to radians

        lat2 = asin(sin(lat1) * cos(d / R) +
                    cos(lat1) * sin(d / R) * cos(brng))

        lon2 = lon1 + atan2(sin(brng) * sin(d / R) * cos(lat1),
                            cos(d / R) - sin(lat1) * sin(lat2))

        lat2 = degrees(lat2)
        lon2 = degrees(lon2)

        return Point(latitude=lat2, longitude=lon2)

    @staticmethod
    def get_curvature_elevation(dist: float) -> float:
        """
        Given the distance between two points on a sphere, it returns the difference in elevation due to the earth
        curvature between the two points.
        :param dist: distance in meters
        """
        d = 1e-3 * dist
        R = distance.EARTH_RADIUS

        h = R * (1 - cos(d / R))

        return h * 1e3

    @staticmethod
    def get_curvature_profile(p1: Point, p2: Point, n_points: int) -> list:
        """
        returns the difference in elevation profile due to the earth curvature between the two points, sampled with
         n_points points
        :param p1: geopy.Point
        :param p2: geopy.Point
        :param n_points: number of samples
        :return: list of differences in elevation
        """
        tot_dist = TerrainProfile.get_distance(p1, p2)

        # maximum difference in altitude: middle point
        hmax = TerrainProfile.get_curvature_elevation(tot_dist/2.0)

        my_step = 1.0 * tot_dist / n_points

        h = []

        for i in range(1, n_points):
            if my_step * i < tot_dist/2.0:
                temp_dist = tot_dist/2.0 - my_step * i
            else:
                temp_dist = my_step * i - tot_dist/2.0

            h_diff = TerrainProfile.get_curvature_elevation(temp_dist)

            h.append(hmax - h_diff)

        return h

    def get_profile(self, p1: Point, p2: Point, n_points: int) -> dict:
        """
        Returns the profile between p1 and p2, sampled with n_points points
        :param p1: geopy.Point
        :param p2: geopy.Point
        :param n_points: number of samples
        :return: dict in the form: {"dist": (float) distance in m, "point": geopy.Point with altitude set,
        "curvature": difference in height due to the curvature of the earth in m}
        """
        dist = TerrainProfile.get_distance(p1, p2)
        bearin = TerrainProfile.get_bearing(p1, p2)

        my_step = 1.0 * dist / n_points

        pointz = [(p1.latitude, p1.longitude)]
        distz = [0]

        for i in range(1, n_points):
            distz.append(my_step * i)
            p_temp = TerrainProfile.point_from_dist_and_angle(p1, bearin, my_step * i)
            pointz.append((p_temp.latitude, p_temp.longitude))

        pointz.append((p2.latitude, p2.longitude))
        distz.append(dist)

        pointz_alt = self.get_altitude(pointz)

        h_c = TerrainProfile.get_curvature_profile(p1, p2, n_points)

        p_ret = []

        for el in pointz_alt:
            my_dict = {"dist": -1,
                       "point": Point(latitude=el["latitude"], longitude=el["longitude"], altitude=el["elevation"]),
                       "curvature": 0}
            p_ret.append(my_dict)

        for i in range(0, len(distz)):
            p_ret[i]["dist"] = distz[i]

        for i in range(0, len(h_c)):
            p_ret[i]["curvature"] = h_c[i]

        return p_ret

    def plot_profile(self, p1: Point, p2: Point, n_points: int, plot_curvature: bool = False) -> dict:
        """
        Plots and then returns the profile between p1 and p2, sampled with n_points points
        :param p1: geopy.Point
        :param p2: geopy.Point
        :param n_points: number of samples
        :param plot_curvature: if true plots the profile including the earth curvature
        :return: dict in the form: {"dist": (float) distance in m, "point": geopy.Point with altitude set,
        "curvature": difference in height due to the curvature of the earth in m}
        """
        p_ret = self.get_profile(p1, p2, n_points)

        alt_min = 1e10 #Used in case of curvature plotting

        x = []
        y = []
        y_c = []

        plt.figure()

        for p in p_ret:
            x.append(p["dist"])
            if plot_curvature:
                y_c.append(p["curvature"])
                y.append(p["point"].altitude + p["curvature"])
                alt_min = min([p["point"].altitude, alt_min])
            else:
                y.append(p["point"].altitude)

        if plot_curvature:
            for i in range(0, len(y_c)):
                y_c[i] = y_c[i] + alt_min
            plt.plot(x, y, 'b')
            plt.plot(x, y_c, 'r--')
        else:
            plt.plot(x, y)

        plt.xlabel("distance (m)")
        plt.ylabel("elevation (m)")

        plt.show()

        return p_ret


if __name__ == "__main__":
    # Plots and prints ot the terrain profile between Pinzolo (Italy) and Andalo (Italy). Coordinates are in
    # WGS 84 Web Mercator, the same used by Google Maps.
    p_pinzolo = Point(latitude=46.1617322, longitude=10.7650043)
    p_andalo = Point(latitude=46.1661363, longitude=11.003402)
    n_points = 20

    T = TerrainProfile()
    ret = T.plot_profile(p_pinzolo, p_andalo, n_points)
    print(ret)

    # Plots the terrain profile between Civitavecchia (Italy) and San benedetto del Tronto (Italy), including the earth
    # curvature
    p_civitavecchia = Point(latitude=42.087076, longitude=11.796718)
    p_sbt = Point(latitude=42.947266, longitude=13.888322)
    n_points = 100
    ret = T.plot_profile(p_civitavecchia, p_sbt, n_points, plot_curvature=True)
