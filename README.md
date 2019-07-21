# terrain-profile
Retrieves the elevation profile between two points on earth via the open-elevation API. It contains a lass used to construct a terrain profile. It uses the open elevation API - https://open-elevation.com/ . Consider donating.

PS: the elevation API could be slow, and sometimes fail. A binary exponential backoff retry mechanism is in use, and in case of HTTP POST error a PostException (included in the py file) is thrown. If you are behind a proxy consider modifying the method `get_altitude` from the `TerrainProfile` class, e.g. as https://2.python-requests.org/en/master/user/advanced/#proxies .

## example of usage

```python
    # Plots and prints ot the terrain profile between Pinzolo (Italy) and Andalo (Italy). Coordinates are in
    # WGS 84 Web Mercator, the same used by Google Maps.
    p_pinzolo = Point(latitude=46.1617322, longitude=10.7650043)
    p_andalo = Point(latitude=46.1661363, longitude=11.003402)
    n_points = 20

    T = TerrainProfile()
    ret = T.plot_profile(p_pinzolo, p_andalo, n_points)
    print(ret)
```
The resulting elevation profile is shown below.

![GitHub Logo](/examples/pinzolo_andalo.png)

## TODOs
- Add the earth curvature
