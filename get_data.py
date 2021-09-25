import requests
from selenium import webdriver
import re
import pandas as pd
import json


def get_postcode(postcode):
    """Generate the location identifier from postcode

    Args:
        postcode (str): The postcode in the form KT2+6LS

    Returns:
        str: The location identifier
    """
    driver = webdriver.Chrome("./webdriver/chromedriver")
    url = f"https://www.rightmove.co.uk/property-for-sale/search.html?searchLocation={postcode}"
    driver.get(url)
    driver.find_element_by_class_name("button").click()
    location_id = re.search("%.*?&", driver.current_url).group(0)[1:-1]
    driver.close()
    return location_id


def get_response(location_identifier, number_of_properties, radius):
    base_url = "https://www.rightmove.co.uk/api/_search?"
    location = "locationIdentifier=POSTCODE%"
    location_identifier = location_identifier
    number_properties_str = "&numberOfPropertiesPerPage="
    radius_str = "&radius="
    the_rest = "&sortType=2&index=0&includeSSTC=true&viewType=LIST&channel=BUY&areaSizeUnit=sqft&currencyCode=GBP&isFetching=true&viewport="

    house_request = f"{base_url}{location}{location_identifier}{number_properties_str}{number_of_properties}{radius_str}{radius}{the_rest}"
    
    response = requests.get(house_request)

    return response


def find_yield(summary):
    search = re.search("\d\.\d\%", summary)
    if search is not None:
        search = search.group(0)
    return search


def data_to_pandas(postcode, number_of_properties):
    location_id = get_postcode(postcode)
    appended_data = []

    response = get_response(location_id, number_of_properties, 1)
    property_list = json.loads(response.text)["properties"]

    if len(property_list) > number_of_properties:
        property_list = property_list[:number_of_properties]

    for property in property_list:
        data = {
            "json": property,
            "id": property["id"],
            "bedrooms": property["bedrooms"],
            "bathrooms": property["bathrooms"],
            "price": property["price"]["amount"],
            "size": property["displaySize"],
            "description": property["propertyTypeFullDescription"],
            "lat": property["location"]["latitude"],
            "long": property["location"]["longitude"],
            "summary": property["summary"],
            "property_type": property["propertySubType"],
            "yield": find_yield(property['summary']),
        }
        appended_data.append(data)
    return pd.DataFrame(appended_data)
