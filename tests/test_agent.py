"""Unit tests for the agent's tools."""
import pytest
from my_agent.agent import get_weather, get_current_time


class TestGetWeather:
    """Test the get_weather function."""
    
    def test_get_weather_new_york(self):
        """Test weather for New York."""
        result = get_weather("New York")
        assert result["status"] == "success"
        assert "New York" in result["report"]
        assert "sunny" in result["report"]
        assert "25 degrees" in result["report"]
    
    def test_get_weather_london(self):
        """Test weather for London."""
        result = get_weather("London")
        assert result["status"] == "success"
        assert "London" in result["report"]
        assert "rainy" in result["report"]
        assert "15 degrees" in result["report"]
    
    def test_get_weather_unknown_city(self):
        """Test weather for an unknown city."""
        result = get_weather("Paris")
        assert result["status"] == "success"
        assert "Paris" in result["report"]
        assert "partly cloudy" in result["report"]
        assert "20 degrees" in result["report"]
    
    def test_get_weather_case_insensitive(self):
        """Test that city name is case-insensitive."""
        result1 = get_weather("new york")
        result2 = get_weather("NEW YORK")
        result3 = get_weather("New York")
        
        assert result1["report"] == result2["report"] == result3["report"]


class TestGetCurrentTime:
    """Test the get_current_time function."""
    
    def test_get_time_new_york(self):
        """Test time for New York."""
        result = get_current_time("New York")
        assert result["status"] == "success"
        assert "New York" in result["report"]
        assert "current time" in result["report"]
    
    def test_get_time_london(self):
        """Test time for London."""
        result = get_current_time("London")
        assert result["status"] == "success"
        assert "London" in result["report"]
        assert "current time" in result["report"]
    
    def test_get_time_tokyo(self):
        """Test time for Tokyo."""
        result = get_current_time("Tokyo")
        assert result["status"] == "success"
        assert "Tokyo" in result["report"]
    
    def test_get_time_unknown_city_uses_utc(self):
        """Test that unknown cities default to UTC."""
        result = get_current_time("Unknown City")
        assert result["status"] == "success"
        assert "Unknown City" in result["report"]
    
    def test_get_time_case_insensitive(self):
        """Test that city name is case-insensitive."""
        result1 = get_current_time("tokyo")
        result2 = get_current_time("TOKYO")
        result3 = get_current_time("Tokyo")
        
        # All should succeed
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result3["status"] == "success"
