from fastapi import FastAPI
from mangum import Mangum
import json

app = FastAPI()


@app.get("/recommendations")
async def get_recommendations():
    linkedin_recommendations_path = "data/linkedinRecommendations.json"

    with open(linkedin_recommendations_path, "r") as json_file:
        recommendations = json.load(json_file)

    return recommendations


handler = Mangum(app)
