#/usr/bin/python3
import logging
import os
import sched
import sys
import time
import urllib.request
import json

# Class that downloads the weather for a city ID and generates a score based on a small scoring table
import yaml
from rgbxy import Converter, GamutA, GamutC, GamutB

try:
    from phue import Bridge
except ImportError:
    pass


class WeatherColor:
    # I don't understand these XY colors very well. It seems whatever I feed in the way of RGB colors is only
    # used to calculate a ratio between the colors and ignores the actual value

    def __init__(self, city_id, apikey, weather_table):
        self.city_id = city_id
        self.apikey = apikey
        self.bad_score = 0
        self.score = 0
        self.main, self.desc = False, False
        self.weather_table = weather_table

    def get_forecast(self):
        url = f"https://api.openweathermap.org/data/2.5/forecast?id={self.city_id}&appid={self.apikey}&mode=json"
        with urllib.request.urlopen(url) as open_url:
            data = json.loads(open_url.read().decode())
            logging.debug(f"Got forecast results:\n{data}")
        return data

    def get_weather_for_main_desc(self, main, desc):
        if not main or main not in self.weather_table:
            raise ValueError(f"Could not find a matching weather set for main {main}")

        mainset = self.weather_table[main]
        color, brightness = mainset.get(desc) if mainset.get(desc) else mainset.get("default")
        logging.debug(f"Will be setting to {color} and brightness {brightness}")
        return color, brightness

    def get_weather_color(self):
        weather = self.get_forecast()
        next_weather = weather["list"][0]["weather"][0]
        self.main = next_weather["main"]
        self.desc = next_weather["description"]
        logging.info(f"Got next weather information - it will be {self.main} with {self.desc}")
        return self.get_weather_for_main_desc(self.main, self.desc)

    def get_last_weather_description(self):
        if not self.main:
            self.get_weather_color()
        return f"In the last forecast weather for your location ({self.city_id}) was thought to be {self.main} - {self.desc}"


class HueColor:
    gamuts = {
        "gamutA": GamutA,
        "gamutB": GamutB,
        "gamutC": GamutC,
    }

    def __init__(self, ip, bulbnames):
        self.ip = ip
        self.huebridge = False
        self.bulbs = list(bulbnames)

    def _connect(self):
        if not self.huebridge:
            self.huebridge = Bridge(self.ip)
        logging.debug(f"Attempting to connect to bridge {self.ip} - if this fails, try pushing the button first")
        self.huebridge.connect()

    def set_bulbs_to_color(self, colortuple, bri, transition_time=100, gamut="gamutB"):
        converter = Converter(HueColor.gamuts[gamut])
        self._connect()
        lights = self.huebridge.get_light_objects('name')
        for bulb in self.bulbs:
            logging.debug(f"Now setting {bulb} to {colortuple}")
            target = lights[bulb]
            color = converter.rgb_to_xy(*colortuple)
            target.transitiontime = transition_time
            target.xy = color
            target.brightness = bri
            # Sleep a little bit to prevent flooding the bridge
            time.sleep(0.3)
        logging.info("Done setting colors")


class WeatherHueScheduler:
    refresh_time = 900

    def __init__(self, weather_color: WeatherColor, hue_color: HueColor):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.weather_color = weather_color
        self.hue_color = hue_color

    def start(self):
        weather_color, weather_brightness = wc.get_weather_color()
        hc.set_bulbs_to_color(weather_color, weather_brightness)
        self.scheduler.enter(WeatherHueScheduler.refresh_time, 1, WeatherHueScheduler.set_next,
                             (self.hue_color, self.weather_color, self.scheduler))
        self.scheduler.run()

    @staticmethod
    def set_next(hue_color: HueColor, weather_score: WeatherColor, scheduler_instance):
        print("Running!)")
        weather_color, weather_brightness = wc.get_weather_color()
        hc.set_bulbs_to_color(weather_color, weather_brightness)
        scheduler_instance.enter(WeatherHueScheduler.refresh_time, 1, WeatherHueScheduler.set_next,
                                 (hue_color, weather_score, scheduler_instance))


if __name__ == "__main__":
    config_file = "settings.yaml"
    config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
    if not os.path.exists(config_file_path):
        if os.path.exists(config_file_path + ".example"):
            print(
                f"Could not find a {config_file} configuration file, but there was a {config_file}.example - please "
                f"update this file with your settings and rename it to {config_file}")
            sys.exit(1)

    with open(config_file_path) as file:
        settings = yaml.load(file, Loader=yaml.FullLoader)
        print(f"Succesfully read settings file.")
        print(f"City ID: https://openweathermap.org/city/{settings['city_id']}")
        print(f"HUE ip: https://{settings['hue_ip']}")
        print(f"Bulbs to change: {', '.join(settings['bulbs'])}")
        print(f"..checking the weather every {settings['refreshtime'] // 60} minutes, CTRL-C to stop")

    if settings["verbosity"] > 0:
        level = logging.INFO if settings["verbosity"] == 1 else logging.DEBUG
        logging.getLogger().setLevel(level)

    logging.debug(f"Got settings: {settings}")

    wc = WeatherColor(settings["city_id"], settings["api_key"], settings["weathercolormap"])
    hc = HueColor(settings["hue_ip"], settings["bulbs"])
    WeatherHueScheduler.refresh_time = settings['refreshtime']
    whs = WeatherHueScheduler(wc, hc)
    whs.start()
