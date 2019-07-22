# terrain-profile
Retrieves the elevation profile between two points on earth via the open-elevation API. It contains a class used to construct a terrain profile.

__It uses the open elevation API - https://open-elevation.com/ . Consider donating.__

PS: the elevation API could be slow, and sometimes fail. A binary exponential backoff retry mechanism is in use, and in case of HTTP POST error a PostException (included in the py file) is thrown. If you are behind a proxy consider modifying the method `get_altitude` from the `TerrainProfile` class, e.g. as https://2.python-requests.org/en/master/user/advanced/#proxies .

## Example of usage

```python
    from geopy import Point
    from terrain_profile import TerrainProfile
    
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

![simple elevation](/examples/pinzolo_andalo.png)

In case one wants to plot the earth curvature between the two points, one can set the `plot_curvature` flag to `True`:
```python
    from geopy import Point
    from terrain_profile import TerrainProfile
    
    # Plots the terrain profile between Civitavecchia (Italy) and San benedetto del Tronto (Italy), including the earth
    # curvature
    p_civitavecchia = Point(latitude=42.087076, longitude=11.796718)
    p_sbt = Point(latitude=42.947266, longitude=13.888322)
    n_points = 100

    T = TerrainProfile()
    ret = T.plot_profile(p_civitavecchia, p_sbt, n_points, plot_curvature=True)
```
The resulting elevation profile is shown below.

![curvature elevation](/examples/civita_sbt.png)
