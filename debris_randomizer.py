from copy import deepcopy
import json

import pandas as pd
import numpy as np

from shapely.geometry import Point
import geopandas as gpd
from arcgis.gis import GIS
from arcgis import features
from arcgis import geometry


# Random point in a polygon function

def random_point_in_bbox(polygon_gdf):
    minx, miny, maxx, maxy = list(polygon_gdf.unary_union.bounds)
    x = (maxx - minx) * np.random.random() + minx
    y = (maxy - miny) * np.random.random() + miny
    point = Point(x, y)
    if point.within(polygon_gdf.unary_union):
        return point
    else:
        return random_point_in_bbox(polygon_gdf)


def main():        
    # Connect to GIS
    with open('config.json') as config_file:
        config = json.load(config_file)
    gis = GIS('https://ral.maps.arcgis.com', config['username'], config['password'])

    # Load, filter, and get the bounding box for Raleigh ETJ
    jurisdictions_gdf = gpd.read_file('wake_jurisdictions.geojson')
    ral_etj_gdf = jurisdictions_gdf.loc[jurisdictions_gdf['JURISDICTION'] == 'RALEIGH']

    # Get a feature from the debris layer to use as a template for the new feature
    debris_item_id = 'a36722a609ee418cacba53240e26db57'
    debris_item = gis.content.get(debris_item_id)
    debris_flayer = debris_item.layers[0]
    debris_fset = debris_flayer.query()
    template_feature = deepcopy(debris_fset.features[0])

    # Create random feature
    new_feature_list = []
    new_feature = deepcopy(template_feature)
    random_point = random_point_in_bbox(ral_etj_gdf)
    input_geometry = {'y': random_point.y,
                    'x': random_point.x}
    output_geometry = geometry.project(geometries = [input_geometry],
                                    in_sr = 4326,
                                    out_sr = debris_fset.spatial_reference['latestWkid'],
                                    gis = gis)

    new_feature.geometry = output_geometry[0]
    new_feature.attributes['DETAILS'] = None
    new_feature.attributes['STATUS'] = 'Submitted'

    new_feature_list.append(new_feature)
    
    # Add new feature
    debris_flayer.edit_features(adds = new_feature_list)

if __name__ == "__main__":
    main()