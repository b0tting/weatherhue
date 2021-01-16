This is another variation on earlier scripts. This version fetches weather information, then sets the color on a given bulb according to an easily modifiable color mapping.

## WeatherHue
This is a python 3 based script which runs in the background and, given a city, retrieves weather information for the next few hours. Depending on the type of weather expected it will color a Philips HUE bulb accordingly. 

Note that if the bulb is off this won't explicitely turn it on. This script can be combined just fine with any on/off scheduling you have. 


## Installation
First, edit the settings.yaml.example file and add your HUE IP and the Openweathermap API key. See the settings file for more info.   
```bash
pip3 install -r requirements.txt -U
mv settings.yaml.example settings.yaml
python3 weatherhue.py
```
For the initial start, press the button on your hue bridge to allow the phue library to create an access key. 

You could also add a simple systemd service unit script for later starts:
```
[Unit]
Description=WeatherHue python app

[Service]
PIDFile=/var/run/weatherhue.pid
WorkingDirectory=/usr/local/weatherhue
ExecStart=/usr/bin/python3 weatherhue.py
StandardOutput=file:/var/log/weatherhue.log
StandardError=file:/var/log/weatherhue.log

[Install]
WantedBy=multi-user.target
```

..this would allow you to register and stop/start the weatherhue app easily:
```
systemctl enable weatherhue
systemctl start weatherhue
```