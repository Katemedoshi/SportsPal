# SportsPal

# Overview
SportsPal is a comprehensive desktop application designed to be your ultimate sports companion. It combines sports knowledge, workout tracking, diet planning, and progress visualization into a single, user-friendly interface. Whether you're a beginner looking to get started or an experienced athlete aiming to optimize your performance, SportsPal provides personalized guidance and tools to help you achieve your fitness goals.

# Key Features
🗣️ Intelligent Chat Assistant
Natural language processing for sports-related questions

Context-aware responses about rules, techniques, and training

Personalized recommendations based on your profile

📰 Sports News Integration
Latest sports news from around the world

Sport-specific news filtering

Article summaries with images

💪 Workout Tracking
Log workouts with details (sport, type, duration, intensity)

Track progress over time

Visualize workout statistics with charts

🥗 Diet Planning
Personalized diet plans based on goals (weight loss, muscle gain, endurance)

Sport-specific nutrition advice

Pre- and post-workout meal recommendations

📊 Progress Monitoring
Workout history tracking

Performance statistics and trends

Visual progress charts

# Installation
Prerequisites
Python 3.8 or higher

pip package manager

# Steps
Clone the repository:

bash
git clone https://github.com/yourusername/SportsPal.git
cd SportsPal
Install required packages:

bash
pip install -r requirements.txt
Create a .env file in the project root with your NewsAPI key:

text
NEWS_API_KEY=your_api_key_here
Run the application:

bash
python sportsPal.py

# Usage
Set up your profile:

Enter your username

Select your main sport and skill level

Ask questions:

Type sports-related questions in the chat interface

Get instant answers about rules, techniques, and training

Track workouts:

Log your training sessions in the "Log Workout" tab

View your progress in the "Your Progress" tab

Get diet plans:

Select your fitness goal

Receive personalized nutrition advice

Stay updated:

Check the latest sports news in the "Sports News" tab

# Technical Details
Built With
Python 3

Tkinter (GUI)

Transformers (NLP)

Matplotlib (Data Visualization)

NewsAPI (News Integration)

PIL/Pillow (Image Processing)

File Structure
sportsPal.py: Main application file

user_profiles.json: Stores user profile data

user_workouts.json: Stores workout history

.env: Configuration file for API keys
