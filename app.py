from datetime import datetime
import math

from flask import Flask, render_template, request

import requests

API_KEY = 'DEMO_KEY'
# You can apply for an API key here:
# https://api.nasa.gov/
# This will give you up to 1,000 requests per hour.

# Alternatively, you can use:
# 'DEMO_KEY'
# for 30 requests per hour and 50 requests per day per API.


app = Flask(__name__)
apod_url = f'https://api.nasa.gov/planetary/apod?api_key={API_KEY}'
insight_url = f'https://api.nasa.gov/insight_weather/?api_key={API_KEY}&feedtype=json&ver=1.0'


def create_sol_dict(sol_json):
    """Return dict with the necessary sol information"""
    sol_dict = {}
    sol_dict['high'] = math.ceil(sol_json['AT']['mx'])
    sol_dict['low'] = math.ceil(sol_json['AT']['mn'])
    sol_datetime = datetime.strptime(
        sol_json['First_UTC'].split('T')[0], '%Y-%m-%d')
    month = sol_datetime.strftime('%b')
    day, suffix = day_and_suffix(sol_datetime.day)
    sol_dict['date'] = f'{month} {day}'
    sol_dict['suffix'] = suffix
    return sol_dict


def day_and_suffix(day):
    """Return [day, suffix] list from day"""
    suffix = ""
    if (3 < day < 21) or (23 < day < 31):
        suffix = 'th'
    else:
        if day % 10 == 1:
            suffix = 'st'
        elif day % 10 == 2:
            suffix = 'nd'
        else:
            suffix = 'rd'
    return [str(day), suffix]


def get_top_images(results_json, n):
    """Get n image objects from the json file"""
    items = results_json['collection']['items']
    top_items = []
    i = 0
    while len(top_items) < n:
        item = items[i]
        item_dict = {}
        if is_valid_image(item):
            item_dict['img_url'] = item['links'][0]['href']
            item_dict['title'] = item['data'][0]['title']
            item_dict['desc'] = item['data'][0]['description']
            top_items.append(item_dict)
        i += 1
    return top_items


def is_valid_image(item):
    if 'links' in item and 'data' in item:
        if 'href' not in item['links'][0]:
            return False
        if 'title' not in item['data'][0]:
            return False
        if 'description' not in item['data'][0]:
            return False
        return True
    return False


@app.route('/', methods=['GET'])
def render_page():
    """Render the page"""
    #  IMAGE SEARCH  #
    top_images = []
    max_images = 21
    query = request.args.get('query')
    if query:
        image_search_url = f'https://images-api.nasa.gov/search?q={query}&media_type=image'
        results_json = requests.get(image_search_url).json()
        top_images = get_top_images(results_json, max_images)

    #  APOD  #
    apod_json = requests.get(apod_url).json()
    apod_data = {}
    if 'copyright' in apod_json:
        apod_data['apod_copyright'] = apod_json['copyright']
    else:
        apod_data['copyright'] = ""
    apod_data['title'] = apod_json['title']
    apod_data['desc'] = apod_json['explanation']
    apod_data['type'] = apod_json['media_type']
    apod_data['url'] = apod_json['url']

    #  MARS WEATHER  #
    insight_json = requests.get(insight_url).json()
    sol_data = []
    for sol_num in insight_json['sol_keys'][:2:-1]:  # Iterates last 4 days
        sol_dict = create_sol_dict(insight_json[sol_num])
        sol_dict['sol'] = sol_num
        sol_data.append(sol_dict)

    return render_template(
        'index.j2',
        apod_data=apod_data,
        sol_data=sol_data,
        search_results_list=top_images
    )


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
