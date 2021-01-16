This is another variation on scripts I did before. This script fetches weather information, then sets the color on a given bulb according to an easily modifiable color mapping. 

## Installation
First, edit the settings.yaml.example file and add your HUE IP and the Openweathermap API key. See the settings file for more info.   
```bash
pip install -r requirements.txt
mv settings.yaml.example settings.yaml
python3 weatherhue.py
```
