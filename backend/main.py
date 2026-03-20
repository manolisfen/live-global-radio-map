from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import requests
import redis
import json
import asyncio

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

async def warm_cache():
    countries = ["Greece", "Italy", "Spain", "Germany", "France"]
    for country in countries:
        if not r.get(country):
            url = f"https://de2.api.radio-browser.info/json/stations/bycountry/{country}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    all_stations = response.json()
                    valid_stations = [
                        s for s in all_stations 
                        if s.get("geo_lat") is not None and s.get("geo_long") is not None
                    ]
                    r.setex(country, 3600, json.dumps(valid_stations[:50]))
            except requests.exceptions.RequestException:
                pass
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(warm_cache())

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