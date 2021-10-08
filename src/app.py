import json
import html
import re
from color_splash_rgb_table_helper import ColorSplashRGBTableHelper
from color_splash_image_ids_table_helper import ColorSplashImageIdsTableHelper
import ast
import numpy as np
from scipy.spatial import cKDTree
import json


def lambda_handler(event, context):
    try:
        hexCode = verifyInput(event)
    except KeyError as e:
        print(e)
        hexCode = 'xxxxxx'
    except RuntimeError as e:
        print(e)
        hexCode = 'xxxxxx'


    distance = 100
    matching_color = hex_to_rgb(hexCode)

    ddb_rgb = ColorSplashRGBTableHelper("ColorSplashRGB")
    ddb_imageIds = ColorSplashImageIdsTableHelper("ColorSplashImageIds")
    
    rgb_strings = ddb_rgb.scan_rgbs()
    rgb_coordinates = rgb_string_to_list(rgb_strings)
    T = cKDTree(rgb_coordinates)
    
    
    rgbs = T.data[T.query_ball_point(matching_color, r=distance)]
    
    closest_image_ids = get_closest_image_ids(rgb_list_to_string(rgbs), ddb_rgb)
    
    image_urls = []
    for image_id in closest_image_ids:
        image_urls.append(ddb_imageIds.get_key(image_id)["FullURL"])

    return {
        "statusCode": 200,
        "body": json.dumps(
            image_urls
        ),
        "headers": {
            "Access-Control-Allow-Origin" : "*", 
            "Access-Control-Allow-Credentials" : True,
            "Access-Control-Allow-Methods": "GET"            
        }
    }


def verifyInput(event):
    queryParameters = event['queryStringParameters']
    if queryParameters is None:
        raise KeyError("No 'queryStringParameters' key in event body")

    if len(queryParameters.keys()) > 1:
        raise RuntimeError("Too many keys in 'queryStringParameters'. Something fishy is going on.")

    hexCode = queryParameters['hex']

    if hexCode is None:
        raise KeyError("No 'hex' key in 'queryStringParameters'")

    hexCode = html.escape(hexCode)
    r = re.compile(r'[0-9A-Fa-f]{6}')
    if not r.match(hexCode):
        raise RuntimeError("Not a valid input")


    return hexCode.upper()

def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return list(int(hex[i:i+hlen//3], 16) for i in range(0, hlen, hlen//3))

def rgb_string_to_list(rgb_strings):
    rgbs_lists = []
    for key in rgb_strings:
        rgb = [float(x) for x in  ast.literal_eval(key)]
        rgbs_lists.append(rgb)
    return np.array(rgbs_lists)

def rgb_list_to_string(rgb_lists):
    rgb_strings = []
    for rgb_list in rgb_lists:
        if len(rgb_list) != 3:
            raise ValueError("List must contain 3 elements")
        
        rgb_string = '[' + str(float(rgb_list[0])) + ', ' + str(float(rgb_list[1])) + ', ' + str(float(rgb_list[2])) + ']'
        rgb_strings.append(rgb_string)

    return rgb_strings


def get_closest_image_ids(rgb_keys, table_helper):
    if len(rgb_keys) == 0:
        return []

    image_ids = []
    iter = 0
    while len(image_ids) < 18:
        if iter == len(rgb_keys) - 1:
            break

        rgb_key = rgb_keys[iter]
        image_ids.extend(list(table_helper.get_key(rgb_key)))
        iter += 1

    return image_ids



