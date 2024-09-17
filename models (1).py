from django.db import models

class WeatherData(models.Model):
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timezone = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return f"{self.city} - {self.description}"


class DailyWeather(models.Model):
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE)
    date = models.DateField()
    temperature = models.FloatField()
    feelslike = models.FloatField()
    cloudcover = models.FloatField(null=True, blank=True)
    dew = models.FloatField(null=True, blank=True)
    sunrise = models.TimeField(null=True, blank=True)
    sunset = models.TimeField(null=True, blank=True)
    uvindex = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.date} - {self.temperature}°C"
