from langchain.tools import tool
import json

# Mock data - realistic enough for the demo
MOCK_HOTELS = {
    "default": [
        {"name": "The Grand Plaza", "price_per_night": 120, "rating": 4.5, "amenities": ["WiFi", "Pool", "Breakfast"], "type": "luxury"},
        {"name": "City Budget Inn", "price_per_night": 45, "rating": 3.8, "amenities": ["WiFi", "AC"], "type": "budget"},
        {"name": "Boutique Stay", "price_per_night": 80, "rating": 4.2, "amenities": ["WiFi", "Gym", "Bar"], "type": "mid-range"},
        {"name": "Backpacker Hostel", "price_per_night": 20, "rating": 3.5, "amenities": ["WiFi", "Shared Kitchen"], "type": "hostel"},
    ]
}

MOCK_FLIGHTS = {
    "default": [
        {"airline": "Singapore Airlines", "price": 450, "duration": "8h 30m", "class": "Economy"},
        {"airline": "Cathay Pacific", "price": 380, "duration": "9h 10m", "class": "Economy"},
        {"airline": "Emirates", "price": 520, "duration": "11h 00m", "class": "Economy"},
        {"airline": "AirAsia", "price": 210, "duration": "10h 45m", "class": "Economy"},
    ]
}


@tool
def search_hotels(city: str, budget_per_night: str = "any", trip_type: str = "any") -> str:
    """
    Search for available hotels in a city. 
    budget_per_night: can be 'budget' (under $50), 'mid-range' ($50-$100), 'luxury' (over $100), or 'any'.
    trip_type: type of trip e.g. 'family', 'solo', 'couple', 'business'.
    """
    hotels = MOCK_HOTELS.get(city.lower(), MOCK_HOTELS["default"])

    # Filter by budget
    if budget_per_night == "budget":
        hotels = [h for h in hotels if h["price_per_night"] < 50]
    elif budget_per_night == "mid-range":
        hotels = [h for h in hotels if 50 <= h["price_per_night"] <= 100]
    elif budget_per_night == "luxury":
        hotels = [h for h in hotels if h["price_per_night"] > 100]

    if not hotels:
        hotels = MOCK_HOTELS["default"]

    result = f"Available hotels in {city}:\n"
    for h in hotels[:3]:
        result += (
            f"\n🏨 {h['name']}\n"
            f"   Price: ${h['price_per_night']}/night | Rating: {h['rating']}⭐\n"
            f"   Amenities: {', '.join(h['amenities'])}\n"
        )
    result += f"\n💡 Tip: Book early for better rates in {city}!"
    return result


@tool
def search_flights(destination: str, budget: str = "any") -> str:
    """
    Search for available flights to a destination city.
    budget: 'cheap' (under $300), 'moderate' ($300-$500), 'flexible' (any price).
    """
    flights = MOCK_FLIGHTS.get(destination.lower(), MOCK_FLIGHTS["default"])

    if budget == "cheap":
        flights = [f for f in flights if f["price"] < 300]
    elif budget == "moderate":
        flights = [f for f in flights if 300 <= f["price"] <= 500]

    if not flights:
        flights = MOCK_FLIGHTS["default"]

    result = f"Available flights to {destination}:\n"
    for f in flights[:3]:
        result += (
            f"\n✈️ {f['airline']}\n"
            f"   Price: ${f['price']} | Duration: {f['duration']} | Class: {f['class']}\n"
        )
    result += f"\n💡 Prices are round-trip estimates. Book in advance to save more!"
    return result
