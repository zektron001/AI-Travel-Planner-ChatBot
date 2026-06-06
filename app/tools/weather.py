import requests
import os
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get current weather and forecast for a city. Use this when the user asks about weather at their destination."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather API key not configured."

    try:
        # Current weather
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"Could not fetch weather for {city}. Please check the city name."

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]

        return (
            f"Weather in {city}: {weather_desc.capitalize()}, "
            f"Temperature: {temp}°C (feels like {feels_like}°C), "
            f"Humidity: {humidity}%. "
            f"Pack accordingly for your trip!"
        )
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
