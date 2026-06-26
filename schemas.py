from fastapi import FastAPI
from pydantic import BaseModel, Field


class City(BaseModel):
    title: str = Field(min_length=2, max_length=20)


class WeatherResponse(BaseModel):
    temperature: str
    condition: str
