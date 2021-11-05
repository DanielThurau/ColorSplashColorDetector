import ast
import html
import json
import logging
import os
import re

import numpy as np
from colorsplash_common.image_ids import ImageIdsTableHelper
from colorsplash_common.rgb import RGBTableHelper
from context import Context
from dotenv import load_dotenv
from exceptions.exceptions import InputError, ColorSplashException
from scipy.spatial import KDTree


def lambda_handler(event, lambdaContext):
    context = Context()
    context.env_vars = get_env_vars()
    logger = logging.getLogger()
    logger.setLevel(context.env_vars["LOGGING_LEVEL"])

    status_code = 200
    image_urls = []

    try:
        image_urls = handle(event, context)
    except Exception as e:
        logging.error("Error when detecting colors", exc_info=True)
        status_code = 500

    logging.info(
        "Request completed. The request's return status code is %d and returned %s results",
        status_code,
        len(image_urls),
    )
    return {
        "statusCode": status_code,
        "body": json.dumps(image_urls),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Methods": "GET",
        },
    }


def handle(event, context):
    context.hex = get_hex_from_event(event)
    context.distance = get_distance(context)
    context.rgb = hex_to_rgb(context.hex)
    logging.info("Request's context object: %s", context)

    rgb_table_helper = RGBTableHelper()
    image_ids_table_helper = ImageIdsTableHelper()

    try:
        rgb_strings = rgb_table_helper.scan_rgbs()
    except Exception as e:
        raise ColorSplashException from e

    if len(rgb_strings) == 0:
        raise ColorSplashException("Scanning The RGB Table returned 0 keys.")

    rgb_coordinates = rgb_string_to_list(rgb_strings)
    kdTree = KDTree(rgb_coordinates)

    valid_rgb_coordinates = kdTree.data[
        kdTree.query_ball_point(context.rgb, r=context.distance)
    ]
    if len(valid_rgb_coordinates) == 0:
        # While not currently and error, its possible with the dataset size there truly are no
        # RGB coordinates within the provided distance. However, as the dataset grows, this shouldn't
        # be a problem. This is why there is just a warning now to call attention, in the future just
        # interupting execution and returning an empty list & 200 may not be the best behavior.
        logging.WARNING(
            "The KDTree found 0 close RGB colors for Hex:#%s Distance:%s.",
            context.hex,
            context.distance,
        )
        return []

    valid_rgb_coordinates = rgb_list_to_string(valid_rgb_coordinates)
    closest_image_ids = get_closest_image_ids(
        valid_rgb_coordinates, rgb_table_helper, context
    )
    image_urls = get_urls_from_image_ids(closest_image_ids, image_ids_table_helper)

    return image_urls


def get_env_vars():
    env_vars = {}
    load_dotenv(".env")

    env_vars["LOGGING_LEVEL"] = os.environ.get("LOGGING_LEVEL", "INFO")
    env_vars["DISTANCE"] = os.environ.get("DISTANCE", 100)
    env_vars["MAX_CONTENT_LENGTH"] = os.environ.get("MAX_CONTENT_LENGTH", 18)

    return env_vars


def sanitize_input(input, pattern):
    html.escape(input)
    r = re.compile(pattern)
    if not r.match(input):
        raise InputError("Not a valid input")

    return input


def get_hex_from_event(event):
    queryParameters = event["queryStringParameters"]
    if queryParameters is None:
        raise InputError("No 'queryStringParameters' key in event body")

    if len(queryParameters.keys()) > 1:
        raise InputError("Too many keys in 'queryStringParameters'")

    hexCode = queryParameters["hex"]

    if hexCode is None:
        raise InputError("No 'hex' key in 'queryStringParameters'")

    hexCode = sanitize_input(hexCode, r"[0-9A-Fa-f]{6}")
    return hexCode.upper()


def get_distance(context):
    return context.env_vars["DISTANCE"]


def get_max_content_length(context):
    return context.env_vars["MAX_CONTENT_LENGTH"]


def hex_to_rgb(hex):
    hex = hex.lstrip("#")
    hlen = len(hex)
    return list(int(hex[i : i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))


def rgb_string_to_list(rgb_strings):
    rgbs_lists = []
    for key in rgb_strings:
        rgb = [float(x) for x in ast.literal_eval(key)]
        rgbs_lists.append(rgb)
    return np.array(rgbs_lists)


def rgb_list_to_string(rgb_lists):
    """
    Example Input: [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], ...]
    """
    rgb_strings = []
    for rgb_list in rgb_lists:
        if len(rgb_list) != 3:
            raise ColorSplashException(
                "Valid RGB Coordinate must contain 3 elements. Invalid Coordinate: {}".format(
                    " ".join(rgb_list)
                )
            )

        rgb_string = (
            "["
            + str(float(rgb_list[0]))
            + ", "
            + str(float(rgb_list[1]))
            + ", "
            + str(float(rgb_list[2]))
            + "]"
        )
        rgb_strings.append(rgb_string)

    return rgb_strings


def get_closest_image_ids(rgb_keys, rgb_table_helper, context):
    image_ids = []
    max_content_len = get_max_content_length(context)

    fixed_image_id_length = min(len(rgb_keys), max_content_len)
    for iter in range(0, fixed_image_id_length):
        rgb_key = rgb_keys[iter]
        try:
            logging.debug("Querying key: %s", rgb_key)
            image_ids_list = list(rgb_table_helper.get_key(rgb_key))
            logging.info(
                "Queried key {} and result was {}".format(
                    rgb_key, " ".join(image_ids_list)
                )
            )
        except Exception as e:
            raise ColorSplashException from e
        else:
            # Flattening multiple sets into a single list
            image_ids.extend(image_ids_list)
        iter += 1

    return image_ids


def get_urls_from_image_ids(image_ids, image_ids_table_helper):
    image_urls = []
    for image_id in image_ids:
        try:
            logging.debug("Querying key: %s", image_id)
            urls = image_ids_table_helper.get_key(image_id)
            logging.info(
                "Queried key {} and result was {}".format(image_id, " ".join(urls))
            )
        except Exception as e:
            raise ColorSplashException from e
        else:
            image_urls.append(urls["FullURL"])

    return image_urls
