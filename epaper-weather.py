#!/usr/bin/python
# -*- coding:utf-8 -*-
import epd2in13_V2
import requests, json
import time
from PIL import Image,ImageDraw,ImageFont
from datetime import datetime
import traceback
import threading

REFRESH_INTERVAL = 1 # in minutes

#Prepare display
epd = epd2in13_V2.EPD()
print("Init and clear")
epd.init(epd.FULL_UPDATE)
epd.Clear(0xff)

font12 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
font16 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)

def draw_weather(locale, temp, next_rain):
    HBlackimage = Image.new('1', (epd.height, epd.width), 255)  # 298*126
    #HRYimage = Image.new('1', (epd.height, epd.width), 255)  # 298*126  ryimage: red or yellow image
    drawblack = ImageDraw.Draw(HBlackimage)
    #drawry = ImageDraw.Draw(HRYimage)

    margin_left = 4
    margin_top = 20
    datetime_str = time.strftime("%H:%M on %m/%d", time.localtime())

    drawblack.text((margin_left, margin_top + 0), f"Weather for {locale} @ {datetime_str}", font = font12, fill = 0)
    drawblack.text((margin_left, margin_top + 16), f"Temp: {temp}", font = font16, fill = 0)
    if next_rain:
        drawblack.text((margin_left, margin_top + 36), f"Rain @ {next_rain.hour}:00 on {next_rain.month}/{next_rain.day}", font = font16, fill = 0)
    else:
        drawblack.text((4, margin_top + 36), f"No rain predicted for 48 hrs", font = font16, fill = 0)

    print("Updating display")
    epd.display(epd.getbuffer(HBlackimage))#, epd.getbuffer(HRYimage))

def fetch_weather(lat="47.6608",lon="-122.319"):

    pointsUrl = "https://api.weather.gov/points/%s,%s" % (lat, lon)
    points = requests.get(pointsUrl).json()

    forecastUrl = "https://api.weather.gov/gridpoints/%s/%s,%s/forecast" % (points["properties"]["gridId"], points["properties"]["gridX"], points["properties"]["gridY"])
    forecast = requests.get(forecastUrl).json()
    temperature = forecast["properties"]["periods"][0]["temperature"]

    print("Weather: %s, %sF" % (points["properties"]["gridId"], temperature))

    ##threading.Timer(60.0 * REFRESH_INTERVAL, fetch_weather).start()
    #base_url = "http://api.openweathermap.org/data/2.5/onecall"
    #req_url = f"{base_url}?appid={api_key}&exclude=minutely&lat=40.746&lon=-73.978&units=imperial"
    #response = requests.get(req_url) 
    #raw_data = response.json()
    #temp_F = raw_data["current"]["temp"]
    #rounded_temp = round(temp_F, 0)
    #hourly_data = raw_data["hourly"]
    #hourly_will_rain = [x["dt"] for x in hourly_data if "rain" in x["weather"][0]["main"].lower()]
    #next_rain = datetime.fromtimestamp(min(hourly_will_rain)) if len(hourly_will_rain) > 0 else None
    draw_weather(points["properties"]["gridId"], temperature, None)

fetch_weather()
epd.Clear(0xff)
epd2in13_V2.epdconfig.module_exit()
exit()