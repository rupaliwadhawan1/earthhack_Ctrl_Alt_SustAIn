from flask import Flask, render_template, request, jsonify
import tensorflow as tf
from flask_cors import CORS
from tensorflow import keras
from transformers import pipeline
import pandas as pd
from textblob import TextBlob
from joblib import load
import pandas as pd
import string
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textblob import TextBlob

df=pd.read_csv('/Users/rupaliwadhawan/Downloads/new_df.csv')
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


# Load the vectorizer and model during app initialization
vectorizer = load('/Users/rupaliwadhawan/schulich_data_science/Hackathon/vectorizer.pkl')
model = load('/Users/rupaliwadhawan/schulich_data_science/Hackathon/model.pkl')

stop_words = set(stopwords.words('english'))
nltk.download('stopwords')
nltk.download('punkt')

# Define preprocessing function
def preprocess_text(text):
    # Function to remove punctuation
    def remove_punctuation(text):
        return text.translate(str.maketrans('', '', string.punctuation))

    # Function to remove URLs
    def remove_url(text):
        return re.sub(r'https?://\S+|www\.\S+', '', text)

    # Function to remove HTML tags
    def remove_html_tags(text):
        return re.sub(r'<[^>]+>', '', text)

    # Function to clean text (convert to lowercase, remove punctuation, URLs, HTML tags)
    def clean_text(text):
        text = text.lower()  # Convert to lowercase
        text = remove_punctuation(text)  # Remove punctuation
        text = remove_url(text)  # Remove URLs
        text = remove_html_tags(text)  # Remove HTML tags
        return text

    # Preprocess the text
    processed_text = clean_text(text)

    # Tokenize and remove stopwords
    words = word_tokenize(processed_text)
    tokens = [w for w in words if w not in stop_words]

    # Join the tokens into a space-separated string
    cleaned_text = ' '.join(tokens)

    # Use the TF-IDF vectorizer to convert text to numeric features
    tfidf_features = vectorizer.transform([cleaned_text]).toarray()

    return tfidf_features  # Return TF-IDF vectorized features as a numeric array

@app.route('/evaluate', methods=['POST'])
def evaluate():
    # Get idea text from the request
    data = request.get_json()
    idea_text = data['idea_text']

    # Preprocess the idea text for model prediction
    preprocessed_text = preprocess_text(idea_text)
    
    # Predict KPI scores using the model
    predicted_scores = model.predict(preprocessed_text)

    # Convert the predicted scores into a dictionary
    kpi_categories = ["Innovation and Feasibility", "Resource Efficiency", "Environmental Impact", "Scalability and Adaptability"]
    kpi_scores = dict(zip(kpi_categories, predicted_scores[0]))

    # Generate expert advice based on the KPI scores and idea text
    expert_advice = get_expert_advice(kpi_scores, idea_text)

    # Return the evaluation results and expert advice as JSON
    return jsonify({"kpis": kpi_scores, "advice": expert_advice})

@app.route('/update_kpis', methods=['POST'])
def update_kpis():
    kpi_data = request.get_json()
    updated_kpis = calculate_kpis(kpi_data)
    return jsonify(updated_kpis)


@app.route('/calculate-kpis', methods=['POST'])
def calculate_kpis():
    data = request.json
    print("Received KPI data:", data)  # Debug print

    updated_kpis = {
        "Innovation and Feasibility": calculate_innovation_and_feasibility(data),
        "Resource Efficiency": calculate_resource_efficiency(data),
        "Environmental Impact": calculate_environmental_impact(data),
        "Scalability and Adaptability": calculate_scalability_and_adaptability(data)
    }

    print("Updated KPIs:", updated_kpis)  # Debug print
    return jsonify(updated_kpis)


def get_expert_advice(kpi_scores, idea_text):
    advice = ""
    gpt_feedback = get_gpt_feedback(idea_text)
    advice += f"\nGuidance From SustAIn: {gpt_feedback}"

    return advice

from openai import OpenAI
import os

client = OpenAI()


def get_gpt_feedback(idea_text):
    client.api_key = os.getenv('OPENAI_API_KEY_1','hidden-api-key')

    try:
        response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Imagine a highly advanced version of GPT-4, specifically trained to be an expert in the field of circular economy. This AI system is the core of a sophisticated web application designed to assess user-submitted ideas focused on sustainable business practices. Users enter their business concepts, which could range from product designs, service models, waste management strategies, to resource efficiency improvements. The AI's task is to meticulously analyze each idea based on key circular economy principles like resource efficiency, waste reduction, lifecycle analysis, and sustainability. It evaluates the feasibility, scalability, environmental impact, and innovation level of the ideas. Moreover, it considers market trends, regulatory compliance, and potential economic benefits. After the analysis, the AI provides detailed feedback. This feedback includes strengths and weaknesses of the idea, areas for improvement, potential challenges, and suggestions for aligning the concept more closely with circular economy principles. The AI also offers resources for further learning and examples of best practices in the field. The training for this AI involves extensive data on circular economy case studies, current environmental regulations, market analysis reports, and user interaction scenarios to simulate realistic idea evaluation. The goal is to create an AI assistant that not only assesses ideas but also educates and inspires users towards sustainable innovation."},
            {"role": "user", "content": f"Please provide brief logical feedback on the following business idea focusing on environmental impact:{idea_text}"}
        ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Feedback currently unavailable."

def adjust_kpi(value, impact, increase=True):
    """Adjust the KPI value based on impact. Ensure it remains within 1 to 5."""
    if increase:
        return max(min(value + impact, 5), 1)
    else:
        return max(min(value - impact, 5), 1)

def calculate_innovation_and_feasibility(data):
    # Innovation and Feasibility is influenced by Resource Efficiency and Scalability
    resource_efficiency = float(data['Resource Efficiency'])
    scalability_adaptability = float(data['Scalability and Adaptability'])

    innovation_feasibility = adjust_kpi(resource_efficiency, 1, increase=False)
    innovation_feasibility = adjust_kpi(scalability_adaptability, 1, increase=True)
    return innovation_feasibility

def calculate_resource_efficiency(data):
    # Resource Efficiency is influenced by Innovation and Feasibility
    innovation_feasibility = float(data['Innovation and Feasibility'])

    resource_efficiency = adjust_kpi(innovation_feasibility, 1, increase=False)
    return resource_efficiency

def calculate_environmental_impact(data):
    # Environmental Impact is influenced by Scalability and Adaptability
    scalability_adaptability = float(data['Scalability and Adaptability'])

    environmental_impact = adjust_kpi(scalability_adaptability, 1, increase=False)
    return environmental_impact

def calculate_scalability_and_adaptability(data):
    # Scalability and Adaptability is influenced by Innovation and Feasibility
    innovation_feasibility = float(data['Innovation and Feasibility'])

    scalability_adaptability = adjust_kpi(innovation_feasibility, 1, increase=True)
    return scalability_adaptability

@app.route('/simulate', methods=['POST'])
def simulate():
    # Extract parameters from request
    data = request.json
    initial_investment = data.get('initial_investment', 0)
    resource_type = data.get('resource_type')  # Assuming it's a single value
    years = data.get('years', 0)

    # Check if resource_type is provided
    if not resource_type:
        return jsonify({"error": "Resource type not provided"}), 400

    # Perform calculations or model predictions
    results = perform_simulation(initial_investment, resource_type, years)
    print(results)
    # Return the results as JSON
    return jsonify(results)



def perform_simulation(initial_investment, resource_type, years):
    
    try:
        # Convert initial_investment to a float
        initial_investment = float(initial_investment)
    except ValueError:
        # Handle the case where the conversion fails
        return {"error": "Invalid initial investment value"}

    # Constants for calculation
    resource_efficiency_factor = {'type1': 1.2, 'type2': 0.8}
    environmental_impact_factor = {'type1': 0.5, 'type2': 1.5}
    
    # Ensure years is an integer
    try:
        years = int(years)
    except ValueError:
        # Handle invalid year values
        return {"error": "Invalid years value"}
    
    investment_impact = initial_investment * 0.0001  # Simplified impact factor
    
    # Calculate resource efficiency and environmental impact
    resource_efficiency = 100 * resource_efficiency_factor[resource_type] * investment_impact
    environmental_impact = 100 / (environmental_impact_factor[resource_type] * investment_impact)

    # Adjust for time
    resource_efficiency *= (1 + 0.05 * years)  # 5% improvement per year
    environmental_impact /= (1 + 0.03 * years)  # 3% reduction per year

    # Ensure values are within a logical range
    resource_efficiency = min(max(resource_efficiency, 0), 100)
    environmental_impact = min(max(environmental_impact, 0), 100)

    return {
        'resource_efficiency': resource_efficiency,
        'environmental_impact': environmental_impact
    }


if __name__ == '__main__':
    app.run(debug=True)
