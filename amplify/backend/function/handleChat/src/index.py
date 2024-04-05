from fastapi import FastAPI, Query
from openai import AsyncOpenAI
from mangum import Mangum
from PyPDF2 import PdfReader
import json
import os
import asyncio

app = FastAPI()


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file located at a specific path."""
    with open(pdf_path, "rb") as pdf_file:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


async def ask_question_openai(question, document_text):
    """Ask a question using OpenAI based on the extracted text from a PDF."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a knowledgeable assistant trained on a specific document. Please base your responses on the document content provided and do not answering questions not related to the document.",
            },
            {
                "role": "user",
                "content": f"Document: {document_text}\n\nQuestion: {question}",
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
    # return response['choices'][0]['message']['content'].strip()


@app.get("/chat")
async def read_root(question: str = Query(...)):
    pdf_path = "data/resume.pdf"
    personal_json_path = "data/personal.json"
    linkedin_recommendations_path = "data/linkedinRecommendations.json"

    document_text_pdf = await asyncio.get_event_loop().run_in_executor(
        None, extract_text_from_pdf, pdf_path
    )

    with open(personal_json_path, "r") as json_file:
        document_text_json = json.dumps(json.load(json_file))
    with open(linkedin_recommendations_path, "r") as json_file:
        recommendations = json.load(json_file)

    document_text = (
        document_text_pdf + "\n" + document_text_json + "\n" + recommendations
    )

    if (
        "employee" in question.lower()
        or "coworker" in question.lower()
        or "people think" in question.lower()
    ):
        if recommendations:
            import random

            selected_recommendation = random.choice(recommendations)
            answer = f"Here's a recommendation from {selected_recommendation['recommender_name']} ({selected_recommendation['recommender_title']}): {selected_recommendation['recommendation_text']}"
        else:
            answer = "I don't have any LinkedIn recommendations stored yet."
    else:
        answer = await ask_question_openai(question, document_text)

    return {"question": question, "answer": answer}


handler = Mangum(app)
