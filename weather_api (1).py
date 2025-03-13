from flask import Flask, request, jsonify
import requests
import time
from urllib.parse import quote

app = Flask(__name__)

API_KEY = ""
API_TOKEN = ""

@app.route('/weather', methods=['POST'])
def get_weather():
    data = request.get_json()


    requested_by = data.get('requested_by', 'Anonymous')
    private_key = data.get('private_key', '')
    

    if not requested_by or not private_key:
        return jsonify({'error': 'User identification required'}), 401
    

    if private_key != API_TOKEN:
        return jsonify({'error': 'Invalid private key'}), 401
    

    city = data.get('city', '')
    if not city:
        return jsonify({'error': 'City name is required'}), 400
    

    preset = data.get('preset', 'base').lower()

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    # Getting city coordinates
    geo_url = f'http://api.openweathermap.org/geo/1.0/direct?q={quote(city)}&limit=1&appid={API_KEY}'
    try:
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()

        geo_data = geo_response.json()
        if not geo_data:
            return jsonify({'error': 'City not found'}), 404

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

        # get weather 
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}'
        air_quality_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}'  # Для рівня пилу та радіації
        weather_response = requests.get(weather_url)
        air_quality_response = requests.get(air_quality_url)

        weather_response.raise_for_status()
        air_quality_response.raise_for_status()

        weather_data = weather_response.json()
        air_quality_data = air_quality_response.json()

        # main response
        response = {
            "requested_by": requested_by,
            "city": city,
            "timestamp": timestamp,
            "weather": {
                "temperature": weather_data['main']['temp'],
                "description": weather_data['weather'][0]['description'],
                "humidity": weather_data['main']['humidity'],
                "wind_speed": weather_data['wind']['speed']
            }
        }

        # preset = "drone"
        if preset == 'drone':
            response["weather"].update({
                "wind_direction": weather_data['wind']['deg'],  # Напрямок вітру в градусах
                "gust_speed": weather_data['wind'].get('gust', 'N/A')  # Сила пориву вітру
            })
        if preset == 'full_info':
    # Погода
            weather_details = weather_data.get('main', {})
            wind_details = weather_data.get('wind', {})
            cloud_details = weather_data.get('clouds', {})
            rain_details = weather_data.get('rain', {})
    
            response["weather"].update({
                "temperature": weather_details.get('temp', 'N/A'),
                "feels_like": weather_details.get('feels_like', 'N/A'),
                "temp_min": weather_details.get('temp_min', 'N/A'),
                "temp_max": weather_details.get('temp_max', 'N/A'),
                "pressure": weather_details.get('pressure', 'N/A'),
                "humidity": weather_details.get('humidity', 'N/A'),
                "weather_description": weather_data['weather'][0].get('description', 'N/A'),
                "wind_speed": wind_details.get('speed', 'N/A'),
                "wind_direction": wind_details.get('deg', 'N/A'),
                "wind_gust": wind_details.get('gust', 'N/A'),
                "cloud_coverage": cloud_details.get('all', 'N/A'),
                "rain_last_3h": rain_details.get('3h', 'N/A'),
                "visibility": weather_data.get('visibility', 'N/A'),
                "pop": weather_data.get('pop', 'N/A')
            })


        return jsonify(response)

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
