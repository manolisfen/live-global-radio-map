from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import requests
import redis
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host='redis', port=6379, decode_responses=True)

Instrumentator().instrument(app).expose(app)

@app.get("/stations/{country}")
def get_stations(country: str):
    try:
        cached_data = r.get(country)
        if cached_data:
            return json.loads(cached_data)
    except redis.exceptions.ConnectionError:
        pass
    
    url = f"https://de2.api.radio-browser.info/json/stations/bycountry/{country}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        all_stations = response.json()
        valid_stations = [
            station for station in all_stations 
            if station.get("geo_lat") is not None and station.get("geo_long") is not None
        ]
        data = valid_stations[:50]
        
    except requests.exceptions.RequestException:
        return {"error": "API is unreachable or DNS failed"}
    
    try:
        r.setex(country, 3600, json.dumps(data))
    except redis.exceptions.ConnectionError:
        pass
        
    return data