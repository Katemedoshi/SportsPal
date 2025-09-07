import streamlit as st
import json
import datetime
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
from io import BytesIO
import base64

# Set page config
st.set_page_config(
    page_title="SportsPal - Your Intelligent Sports Assistant",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E86AB 0%, #A23B72 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
        margin-bottom: 1rem;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .chat-message {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

# Sports knowledge database
SPORTS_KNOWLEDGE = {
    "football": {
        "rules": "Football is played with 11 players on each team. The objective is to score by getting the ball into the opponent's goal.",
        "popular_leagues": ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"],
        "equipment": ["Football", "Cleats", "Shin guards", "Jersey", "Shorts"],
        "workouts": {
            "beginner": ["Jogging 30 mins", "Squats 3x10", "Lunges 3x10", "Push-ups 3x10"],
            "intermediate": ["Sprints 10x100m", "Box jumps 3x10", "Burpees 3x15", "Plank 3x1min"],
            "advanced": ["Interval training", "Plyometrics", "Hill runs", "Circuit training"]
        },
        "diet": {
            "pre_game": "High-carb meal 3-4 hours before (pasta, rice, potatoes)",
            "post_game": "Protein-rich recovery meal (chicken, fish, tofu) with carbs",
            "general": "Balanced diet with 55-65% carbs, 15-20% protein, 20-25% fat"
        }
    },
    "basketball": {
        "rules": "Basketball is played with 5 players on each team. Points are scored by shooting the ball through the opponent's hoop.",
        "popular_leagues": ["NBA", "EuroLeague", "CBA"],
        "equipment": ["Basketball", "Basketball shoes", "Jersey", "Shorts"],
        "workouts": {
            "beginner": ["Dribbling drills", "Jump shots 50/day", "Layups 30/day", "Defensive slides"],
            "intermediate": ["Three-point shooting", "Suicide runs", "Agility ladder", "Medicine ball throws"],
            "advanced": ["Plyometric jumps", "Full-court presses", "Game-situation drills", "Vertical jump training"]
        },
        "diet": {
            "pre_game": "Moderate carbs with protein (chicken sandwich, banana)",
            "post_game": "Protein shake + complex carbs (sweet potato, brown rice)",
            "general": "High protein (1.4-1.7g/kg body weight), moderate carbs, healthy fats"
        }
    },
    "tennis": {
        "rules": "Tennis is played between two players (singles) or two teams of two players (doubles). Players use rackets to hit a ball over a net.",
        "popular_leagues": ["ATP Tour", "WTA Tour", "Grand Slam tournaments"],
        "equipment": ["Tennis racket", "Tennis balls", "Appropriate shoes", "Comfortable clothing"],
        "workouts": {
            "beginner": ["Forehand/backhand drills", "Footwork patterns", "Serve practice", "Wall rallies"],
            "intermediate": ["Match simulations", "Interval sprints", "Core strengthening", "Multi-ball drills"],
            "advanced": ["High-intensity interval training", "Plyometric exercises", "Advanced stroke techniques", "Mental toughness training"]
        },
        "diet": {
            "pre_match": "Light meal with carbs and protein (fish with rice, energy bar)",
            "post_match": "Electrolyte replacement + protein (salmon with quinoa, nuts)",
            "general": "Balanced diet with emphasis on hydration and quick energy sources"
        }
    },
    "general": {
        "benefits": "Sports improve physical health, mental well-being, teamwork skills, and discipline.",
        "getting_started": "Choose a sport you enjoy, get basic equipment, find a local club or coach, and start with beginner exercises.",
        "workouts": {
            "cardio": ["Running", "Cycling", "Swimming", "Jump rope"],
            "strength": ["Bodyweight exercises", "Weight training", "Resistance bands", "Calisthenics"],
            "flexibility": ["Yoga", "Dynamic stretching", "Pilates", "Mobility drills"]
        },
        "diet": {
            "weight_loss": "Calorie deficit with high protein, moderate fat, low carbs",
            "muscle_gain": "Calorie surplus with high protein, moderate carbs, healthy fats",
            "endurance": "High carb intake (6-10g/kg), moderate protein, adequate hydration"
        }
    }
}

# Initialize session state
def init_session_state():
    if 'user_profiles' not in st.session_state:
        st.session_state.user_profiles = {
            "default": {
                "sport": "general",
                "level": "beginner",
                "goals": ["Get fit", "Learn basics"],
                "progress": {
                    "workouts_completed": 0,
                    "weight": None,
                    "measurements": {}
                }
            }
        }
    
    if 'workouts' not in st.session_state:
        st.session_state.workouts = {}
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "default"
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'news_data' not in st.session_state:
        st.session_state.news_data = []

# Sports News API integration
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_latest_news(sport="sports", count=5):
    try:
        # Try to get from environment or use placeholder
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            # Return sample news if no API key
            return [
                {
                    'title': f"Latest {sport.title()} News",
                    'description': f"Stay updated with the latest {sport} news and updates. Our news service will provide real-time updates when API key is configured.",
                    'url': "#",
                    'image_url': "",
                    'published_at': datetime.datetime.now().isoformat()
                }
            ]
            
        url = f"https://newsapi.org/v2/everything?q={sport}&language=en&sortBy=publishedAt&apiKey={api_key}"
        response = requests.get(url, timeout=10)
        articles = response.json().get('articles', [])[:count]
        
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('description', 'No description'),
                'url': article.get('url', '#'),
                'image_url': article.get('urlToImage', ''),
                'published_at': article.get('publishedAt', datetime.datetime.now().isoformat())
            })
        return formatted_articles
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# Workout tracking functions
def log_workout(user, sport, workout_type, duration, intensity, notes=""):
    if user not in st.session_state.workouts:
        st.session_state.workouts[user] = []
    
    workout = {
        "date": datetime.datetime.now().isoformat(),
        "sport": sport,
        "type": workout_type,
        "duration": duration,
        "intensity": intensity,
        "notes": notes
    }
    
    st.session_state.workouts[user].append(workout)
    return workout

def get_workout_history(user, limit=5):
    return st.session_state.workouts.get(user, [])[-limit:]

def get_progress_stats(user):
    stats = {
        "total_workouts": 0,
        "workouts_by_sport": {},
        "weekly_avg": 0,
        "total_duration": 0
    }
    
    if user not in st.session_state.workouts:
        return stats
    
    workouts = st.session_state.workouts[user]
    stats["total_workouts"] = len(workouts)
    
    for workout in workouts:
        sport = workout["sport"]
        if sport not in stats["workouts_by_sport"]:
            stats["workouts_by_sport"][sport] = 0
        stats["workouts_by_sport"][sport] += 1
        
        try:
            stats["total_duration"] += int(workout["duration"])
        except:
            pass
    
    if workouts:
        first_date = datetime.datetime.fromisoformat(workouts[0]["date"])
        weeks = max(1, (datetime.datetime.now() - first_date).days / 7)
        stats["weekly_avg"] = len(workouts) / weeks
    
    return stats

# Simple chatbot response
def get_sports_response(user_input, user_profile):
    user_input_lower = user_input.lower()
    sport = user_profile["sport"]
    level = user_profile["level"]
    
    # Simple keyword-based responses
    if any(word in user_input_lower for word in ["workout", "exercise", "training"]):
        if sport in SPORTS_KNOWLEDGE and level in SPORTS_KNOWLEDGE[sport]["workouts"]:
            workouts = SPORTS_KNOWLEDGE[sport]["workouts"][level]
            return f"Here are some {level} {sport} workouts for you:\n" + "\n".join([f"• {w}" for w in workouts])
        else:
            return "I'd recommend starting with basic cardio like jogging, and some strength exercises like push-ups and squats."
    
    elif any(word in user_input_lower for word in ["diet", "nutrition", "food", "eat"]):
        if sport in SPORTS_KNOWLEDGE and "diet" in SPORTS_KNOWLEDGE[sport]:
            diet_info = SPORTS_KNOWLEDGE[sport]["diet"]
            return f"For {sport}, here's what I recommend:\n• Pre-game: {diet_info.get('pre_game', diet_info.get('pre_match', 'Light meal with carbs'))}\n• Post-game: {diet_info.get('post_game', diet_info.get('post_match', 'Protein-rich recovery meal'))}\n• General: {diet_info.get('general', 'Balanced nutrition')}"
        else:
            return "A balanced diet with adequate protein, complex carbs, and healthy fats is key for any sport."
    
    elif any(word in user_input_lower for word in ["rule", "how to play", "basics"]):
        if sport in SPORTS_KNOWLEDGE:
            return SPORTS_KNOWLEDGE[sport]["rules"]
        else:
            return "Every sport has its own rules. What specific sport would you like to learn about?"
    
    elif any(word in user_input_lower for word in ["equipment", "gear", "what do i need"]):
        if sport in SPORTS_KNOWLEDGE and "equipment" in SPORTS_KNOWLEDGE[sport]:
            equipment = SPORTS_KNOWLEDGE[sport]["equipment"]
            return f"For {sport}, you'll need:\n" + "\n".join([f"• {item}" for item in equipment])
        else:
            return "Basic athletic clothing and appropriate footwear are essential for most sports."
    
    else:
        return f"As your sports assistant, I can help you with workouts, diet advice, rules, and equipment recommendations for {sport}. What would you like to know more about?"

# Main app
def main():
    init_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚽ SPORTSPAL</h1>
        <p>Your Intelligent Sports Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - User Management
    with st.sidebar:
        st.header("👤 User Profile")
        
        # User selection
        current_user = st.text_input("Username", value=st.session_state.current_user)
        if current_user != st.session_state.current_user:
            st.session_state.current_user = current_user
            if current_user not in st.session_state.user_profiles:
                st.session_state.user_profiles[current_user] = {
                    "sport": "general",
                    "level": "beginner",
                    "goals": ["Get fit"],
                    "progress": {"workouts_completed": 0, "weight": None, "measurements": {}}
                }
            st.rerun()
        
        user_profile = st.session_state.user_profiles[current_user]
        
        # Sport and level selection
        sport = st.selectbox(
            "Main Sport", 
            ["General", "Football", "Basketball", "Tennis"],
            index=["general", "football", "basketball", "tennis"].index(user_profile["sport"])
        ).lower()
        
        level = st.selectbox(
            "Skill Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=["beginner", "intermediate", "advanced"].index(user_profile["level"])
        ).lower()
        
        # Update profile if changed
        if sport != user_profile["sport"] or level != user_profile["level"]:
            st.session_state.user_profiles[current_user]["sport"] = sport
            st.session_state.user_profiles[current_user]["level"] = level
        
        st.divider()
        
        # Quick stats
        stats = get_progress_stats(current_user)
        st.metric("Total Workouts", stats["total_workouts"])
        st.metric("Total Duration", f"{stats['total_duration']} mins")
        st.metric("Weekly Average", f"{stats['weekly_avg']:.1f}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📰 Sports News", "📊 Progress", "🏋️ Log Workout", "🥗 Diet Plans"])
    
    # Chat Tab
    with tab1:
        st.header("Chat with SportsPal")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["sender"] == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message"><strong>SportsPal:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_input("Ask me anything about sports, workouts, or nutrition:", key="chat_input")
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("Send", type="primary"):
                if user_input:
                    # Add user message
                    st.session_state.chat_history.append({"sender": "user", "content": user_input})
                    
                    # Get response
                    response = get_sports_response(user_input, user_profile)
                    st.session_state.chat_history.append({"sender": "assistant", "content": response})
                    
                    st.rerun()
        
        with col2:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    # News Tab
    with tab2:
        st.header("📰 Latest Sports News")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Refresh News"):
                st.session_state.news_data = get_latest_news(sport)
                st.rerun()
        
        if not st.session_state.news_data:
            st.session_state.news_data = get_latest_news(sport)
        
        for article in st.session_state.news_data:
            with st.expander(article['title']):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(article['description'])
                    if article['url'] != "#":
                        st.link_button("Read Full Article", article['url'])
                    st.caption(f"Published: {datetime.datetime.fromisoformat(article['published_at']).strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    if article['image_url']:
                        try:
                            st.image(article['image_url'], width=200)
                        except:
                            st.write("Image unavailable")
    
    # Progress Tab
    with tab3:
        st.header("📊 Your Progress")
        
        stats = get_progress_stats(current_user)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Workouts", stats["total_workouts"])
        with col2:
            st.metric("Total Duration", f"{stats['total_duration']} mins")
        with col3:
            st.metric("Weekly Average", f"{stats['weekly_avg']:.1f}")
        with col4:
            avg_duration = stats['total_duration'] / max(1, stats['total_workouts'])
            st.metric("Avg Duration", f"{avg_duration:.1f} mins")
        
        # Charts
        if stats["workouts_by_sport"]:
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart of workouts by sport
                fig_pie = px.pie(
                    values=list(stats["workouts_by_sport"].values()),
                    names=list(stats["workouts_by_sport"].keys()),
                    title="Workouts by Sport"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = px.bar(
                    x=list(stats["workouts_by_sport"].keys()),
                    y=list(stats["workouts_by_sport"].values()),
                    title="Workout Count by Sport",
                    labels={'x': 'Sport', 'y': 'Count'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Recent workouts
        st.subheader("Recent Workouts")
        recent_workouts = get_workout_history(current_user, 10)
        
        if recent_workouts:
            df = pd.DataFrame(recent_workouts)
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No workouts logged yet. Use the 'Log Workout' tab to get started!")
    
    # Workout Logging Tab
    with tab4:
        st.header("🏋️ Log Your Workout")
        
        with st.form("workout_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                workout_sport = st.selectbox("Sport", ["Football", "Basketball", "Tennis", "Running", "Cycling", "Swimming", "Other"])
                workout_type = st.selectbox("Workout Type", ["Cardio", "Strength", "Flexibility", "Skills", "Game", "Other"])
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=300, value=30)
            
            with col2:
                intensity = st.select_slider("Intensity", ["Low", "Medium", "High"], value="Medium")
                notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Log Workout", type="primary")
            
            if submitted:
                workout = log_workout(current_user, workout_sport, workout_type, duration, intensity, notes)
                st.success(f"✅ Logged {workout_type} workout for {duration} minutes!")
                st.balloons()
    
    # Diet Plans Tab
    with tab5:
        st.header("🥗 Personalized Diet Plans")
        
        goal = st.selectbox("Select Your Goal", ["Weight Loss", "Muscle Gain", "Endurance", "General Health"])
        
        if st.button("Get Diet Plan", type="primary"):
            goal_key = goal.lower().replace(" ", "_")
            
            # General diet advice
            if goal_key in SPORTS_KNOWLEDGE['general']['diet']:
                st.subheader("General Diet Guidelines")
                st.info(SPORTS_KNOWLEDGE['general']['diet'][goal_key])
            
            # Sport-specific advice
            if sport in SPORTS_KNOWLEDGE and 'diet' in SPORTS_KNOWLEDGE[sport]:
                st.subheader(f"For {sport.title()} Players")
                sport_diet = SPORTS_KNOWLEDGE[sport]['diet']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Pre-Activity**")
                    st.write(sport_diet.get('pre_game', sport_diet.get('pre_match', 'Light meal with carbs')))
                
                with col2:
                    st.markdown("**Post-Activity**")
                    st.write(sport_diet.get('post_game', sport_diet.get('post_match', 'Protein-rich recovery meal')))
                
                with col3:
                    st.markdown("**General Guidelines**")
                    st.write(sport_diet.get('general', 'Balanced nutrition'))
            
            # Sample meal plan
            st.subheader("Sample Daily Meal Plan")
            meal_plan = {
                "Breakfast": "Oatmeal with berries and nuts, Greek yogurt",
                "Mid-Morning": "Banana with almond butter",
                "Lunch": "Grilled chicken salad with quinoa",
                "Afternoon": "Protein smoothie with spinach",
                "Dinner": "Salmon with sweet potato and vegetables",
                "Evening": "Casein protein or cottage cheese"
            }
            
            for meal, food in meal_plan.items():
                st.write(f"**{meal}:** {food}")

if __name__ == "__main__":
    main()
