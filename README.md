# terrain-profile
Retrieves the elevation profile between two points on earth via the open-elevation API. It contains a lass used to construct a terrain profile. It uses the open elevation API - https://open-elevation.com/ . Consider donating.

#example of usage

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
