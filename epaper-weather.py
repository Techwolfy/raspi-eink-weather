#!/usr/bin/python3
#Raspberry Pi Zero e-ink weather display using NOAA API
#Inspired by https://learn.adafruit.com/raspberry-pi-e-ink-weather-station-using-python

import atexit
import datetime
import json
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import epd2in13_V2


LOCATION_TEXT = "Seattle, WA"
LOCATION_LATLON = "47.6597,-122.3191"
LOCATION_URL = "https://api.weather.gov/points/%s" % LOCATION_LATLON
FORECAST_URL = "https://api.weather.gov/gridpoints/%s/%s,%s/forecast"

FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
FONT_ICON = ImageFont.truetype("./meteocons.ttf", 48)

ICON_MAP = {
    "skc": "BC",              #Fair/clear
    "few": "BC",              #A few clouds
    "sct": "HI",              #Partly cloudy
    "bkn": "NN",              #Mostly cloudy
    "ovc": "YY",              #Overcast
    "wind_skc": "FF",         #Fair/clear and windy
    "wind_few": "FF",         #A few clouds and windy
    "wind_sct": "SS",         #Partly cloudy and windy
    "wind_bkn": "SS",         #Mostly cloudy and windy
    "wind_ovc": "SS",         #Overcast and windy
    "snow": "VV",             #Snow
    "rain_snow": "XX",        #Rain/snow
    "rain_sleet": "XX",       #Rain/sleet
    "snow_sleet": "WW",       #Snow/sleet
    "fzra": "RR",             #Freezing rain
    "rain_fzra": "RR",        #Rain/freezing rain
    "snow_fzra": "WW",        #Freezing rain/snow
    "sleet": "XX",            #Sleet
    "rain": "RR",             #Rain
    "rain_showers": "QQ",     #Rain showers (high cloud cover)
    "rain_showers_hi": "QQ",  #Rain showers (low cloud cover)
    "tsra": "00",             #Thunderstorm (high cloud cover)
    "tsra_sct": "00",         #Thunderstorm (medium cloud cover)
    "tsra_hi": "00",          #Thunderstorm (low cloud cover)
    "tornado": "((",          #Tornado
    "hurricane": "((",        #Hurricane conditions
    "tropical_storm": "((",   #Tropical storm conditions
    "dust": "EE",             #Dust
    "smoke": "EE",            #Smoke
    "haze": "JK",             #Haze
    "hot": "''",              #Hot
    "cold": "GG",             #Cold
    "blizzard": "WW",         #Blizzard
    "fog": "JK",              #Fog/mist
}


class WeatherGraphics:
    def __init__(self, display, locationText):
        self._display = display
        self._image = None

        self._weatherIcon = None
        self._locationText = locationText
        self._mainText = None
        self._temperature = None
        self._description = None
        self._timeText = None

    def updateWeather(self, forecast):
        weather = forecast["properties"]["periods"][0]
        print(weather)

        iconId = weather["icon"].split('?', 1)[0].split(',', 1)[0].rsplit('/', 2)
        self._weatherIcon = ICON_MAP[iconId[2]][0 if iconId[1] == "day" else 1]

        main = weather["shortForecast"]
        self._mainText = main

        temperature = "%d °%s" % (weather["temperature"], weather["temperatureUnit"])
        self._temperature = temperature

        description = weather["detailedForecast"].split('.', 1)[0] + "."
        self._description = description

        self.updateTime()

    def updateTime(self):
        now = datetime.datetime.now()
        self._timeText = now.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")

    def updateImage(self):
        displayWidth = self._display.height
        displayHeight = self._display.width

        image = Image.new('1', (displayWidth, displayHeight), color=0xff)
        draw = ImageDraw.Draw(image)

        # Draw the icon
        (fontWidth, fontHeight) = FONT_ICON.getsize(self._weatherIcon)
        draw.text(
            (
                displayWidth // 2 - fontWidth // 2,
                displayHeight // 2 - fontHeight // 2 - 5
            ),
            self._weatherIcon,
            font=FONT_ICON,
            fill=0x00,
        )

        # Draw the location text
        draw.text(
            (5, 5),
            self._locationText,
            font=FONT_MEDIUM,
            fill=0x00,
        )

        # Draw the time
        (fontWidth, fontHeight) = FONT_MEDIUM.getsize(self._timeText)
        draw.text(
            (5, fontHeight * 2 - 5),
            self._timeText,
            font=FONT_MEDIUM,
            fill=0x00,
        )

        # Draw the main text
        (fontWidth, fontHeight) = FONT_LARGE.getsize(self._mainText)
        draw.text(
            (5, displayHeight - fontHeight - 5), #(5, displayHeight - fontHeight * 2),
            self._mainText,
            font=FONT_LARGE,
            fill=0x00,
        )

        # Draw the description text
        #(fontWidth, fontHeight) = FONT_SMALL.getsize(self._description)
        #draw.text(
        #    (5, displayHeight - fontHeight - 5),
        #    self._description,
        #    font=FONT_SMALL,
        #    fill=0x00,
        #)

        # Draw the temperature
        (fontWidth, fontHeight) = FONT_LARGE.getsize(self._temperature)
        draw.text(
            (
                displayWidth - fontWidth - 5,
                5 #displayHeight - fontHeight * 2
            ),
            self._temperature,
            font=FONT_LARGE,
            fill=0x00,
        )

        self._image = image

    def display(self):
        self.updateImage()

        self._display.init(display.FULL_UPDATE)
        self._display.display(self._display.getbuffer(self._image))
        self._display.sleep()


#Initialize display
display = epd2in13_V2.EPD()

def clearDisplay():
    display.init(display.FULL_UPDATE)
    display.Clear(0xff)
    display.sleep()

atexit.register(clearDisplay)


#Query gridpoint
gridpointData = requests.get(LOCATION_URL)
if gridpointData.status_code != 200:
    print("Gridpoint query failed: %d", gridpointData.status_code)
    exit(1)

gridpoint = gridpointData.json()


#Display weather
displayGFX = WeatherGraphics(display, LOCATION_TEXT)
displayRefresh = 0

while True:
    #Update once every 15 minutes (on the quarter hour)
    if time.monotonic() - displayRefresh < 60 or (datetime.datetime.now().minute % 15 != 0 and displayRefresh != 0):
        time.sleep(30)
        continue

    #Query weather and update display
    forecastUrl = FORECAST_URL % (gridpoint["properties"]["gridId"], gridpoint["properties"]["gridX"], gridpoint["properties"]["gridY"])
    forecast = requests.get(forecastUrl)
    if forecast.status_code == 200:
        displayGFX.updateWeather(forecast.json())
        displayGFX.display()
        displayRefresh = time.monotonic()
    else:
        print("Forecast query failed: %d" % forecast.status_code)

    time.sleep(30)
