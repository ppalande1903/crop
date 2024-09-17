import requests
from django.shortcuts import render
from .models import WeatherData, DailyWeather
from django.conf import settings
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import google.generativeai as genai

def get_weather(request):
    city = request.GET.get('city', None) or request.session.get('city', None)
    
    if not city:
        return render(request, 'index.html', {'weather_data': None, 'chart_html': None})
    
    request.session['city'] = city

    api_key = settings.VISUALCROSS_API_KEY
    url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?key={api_key}&unitGroup=metric'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return render(request, 'index.html', {'weather_data': None, 'chart_html': None})

    weather_data = WeatherData(
        city=data.get('resolvedAddress', 'Unknown'),
        latitude=data.get('latitude', 0),
        longitude=data.get('longitude', 0),
        timezone=data.get('timezone', 'Unknown'),
        description=data.get('description', 'No description'),
    )
    weather_data.save()

    for day in data.get('days', []):
        daily_weather = DailyWeather(
            weather_data=weather_data,
            date=day.get('datetime', 'Unknown'),
            temperature=day.get('temp', 0),
            feelslike=day.get('feelslike', 0),
            cloudcover=day.get('cloudcover', 0),
            dew=day.get('dew', 0),
            sunrise=day.get('sunrise', None),
            sunset=day.get('sunset', None),
            uvindex=day.get('uvindex', 0),
        )
        daily_weather.save()
    
    daily_weather = DailyWeather.objects.filter(weather_data=weather_data)
    df = pd.DataFrame(list(daily_weather.values()))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['temperature'], mode='lines', name='Temperature'))
    fig.update_layout(title="Weather Trends Over Time", xaxis_title="Date", yaxis_title="Temperature")
    chart_html = pio.to_html(fig, full_html=False)
    
    context = {
        'weather_data': weather_data,
        'chart_html': chart_html
    }
    
    return render(request, 'index.html', context)

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '')

        # Get city from session or query parameters
        city = request.GET.get('city', None) or request.session.get('city', None)
        
        if not city:
            return JsonResponse({'response': "Please provide a city in your message for weather analysis."})

        # Fetch weather data directly from the API
        api_key = settings.VISUALCROSS_API_KEY
        url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?key={api_key}&unitGroup=metric'
        response = requests.get(url)
        data = response.json()

        if 'days' not in data:
            return JsonResponse({'response': f"No weather data available for {city}. Please try again."})

        # Extract data for chatbot analysis
        df = extract_weather_info_to_df(data)

        detailed_insight = request.session.get('detailed_insight', 'No plant disease insights available.')
        print(detailed_insight)
        # Generate AI-based response using LangChain or Google API
        model = genai.GenerativeModel("gemini-1.5-flash")
        default_prompt = f'''                    The user is in {city}. 
                Based on the CNN model's prediction from the Plant Village dataset, here is the output:
                {detailed_insight}
                The model will also be getting a CSV file containing columns of dates, temperature, soil temperature, and other weather parameters.
                You have to answer queries related to weather details for specific days, such as temperature or soil conditions.
                You should provide recommendations on environmentally suitable crops that can be grown in the area based on the weather data and the CNN prediction.
                The recommendations should be solely based on provided weather data, the location, and the CNN model's output.
                Do not return code as answer.

        '''
        combined_prompt = f"{default_prompt}\nUser: {message}\nInsight: {detailed_insight}"
        data_text = df.to_string()

        response = model.generate_content(
            [combined_prompt, data_text],
            generation_config=genai.types.GenerationConfig(temperature=0.2),
            stream=True
        )
        response.resolve()
        response_text = response.text

        return JsonResponse({'response': response_text})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def extract_weather_info_to_df(response):
    daily_data = []
    for day in response['days']:
        weather_data = {
            'date': day['datetime'],
            'average_temp': day['temp'],
            'feels_like_avg': day['feelslike'],
            'dew_point': day['dew'],
            'humidity': day['humidity'],
            'precipitation': day['precip'],
            'wind_speed': day['windspeed'],
            'uv_index': day['uvindex'],
            'sunrise': day['sunrise'],
            'sunset': day['sunset'],
            'description': day['description']
        }
        daily_data.append(weather_data)
    df = pd.DataFrame(daily_data)
    return df