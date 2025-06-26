import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import json
import random
import datetime
import requests
from PIL import Image, ImageTk
from io import BytesIO
import threading
import os
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Load environment variables
load_dotenv()

# Sports knowledge database - expanded with more sports and details
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

# Sample user profiles and progress data
USER_PROFILES = {}
try:
    with open('user_profiles.json', 'r') as f:
        USER_PROFILES = json.load(f)
except:
    USER_PROFILES = {
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

# Initialize NLP components
class SportsNLP:
    def __init__(self):
        # Using a more modern small model
        self.tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")
        self.nlp = pipeline("text2text-generation", model=self.model, tokenizer=self.tokenizer)
    
    def generate_response(self, user_input, context=None):
        if context:
            input_text = f"Context: {context}\nUser: {user_input}"
        else:
            input_text = user_input
            
        response = self.nlp(input_text, max_length=200)[0]['generated_text']
        return response

# Sports news API integration
class SportsNews:
    @staticmethod
    def get_latest_news(sport="sports", count=5):
        try:
            # Get API key from environment variables
            api_key = os.getenv('NEWS_API_KEY')
            if not api_key:
                raise ValueError("No API key found")
                
            url = f"https://newsapi.org/v2/everything?q={sport}&language=en&sortBy=publishedAt&apiKey={api_key}"
            response = requests.get(url)
            articles = response.json().get('articles', [])[:count]
            
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'title': article['title'],
                    'description': article['description'],
                    'url': article['url'],
                    'image_url': article['urlToImage'],
                    'published_at': article['publishedAt']
                })
            return formatted_articles
        except Exception as e:
            print(f"Error fetching news: {e}")
            # Fallback if API fails
            return [
                {
                    'title': "SportsPal Daily Update",
                    'description': "Stay tuned for the latest sports news. Our news service is currently unavailable.",
                    'url': "",
                    'image_url': "",
                    'published_at': datetime.datetime.now().isoformat()
                }
            ]

# Workout and progress tracking
class WorkoutTracker:
    def __init__(self):
        self.load_user_data()
    
    def load_user_data(self):
        try:
            with open('user_workouts.json', 'r') as f:
                self.workouts = json.load(f)
        except:
            self.workouts = {}
    
    def save_user_data(self):
        with open('user_workouts.json', 'w') as f:
            json.dump(self.workouts, f)
    
    def log_workout(self, user, sport, workout_type, duration, intensity, notes=""):
        if user not in self.workouts:
            self.workouts[user] = []
        
        workout = {
            "date": datetime.datetime.now().isoformat(),
            "sport": sport,
            "type": workout_type,
            "duration": duration,
            "intensity": intensity,
            "notes": notes
        }
        
        self.workouts[user].append(workout)
        self.save_user_data()
        return workout
    
    def get_workout_history(self, user, limit=5):
        return self.workouts.get(user, [])[-limit:]
    
    def get_progress_stats(self, user):
        stats = {
            "total_workouts": 0,
            "workouts_by_sport": {},
            "weekly_avg": 0,
            "total_duration": 0
        }
        
        if user not in self.workouts:
            return stats
        
        workouts = self.workouts[user]
        stats["total_workouts"] = len(workouts)
        
        # Calculate by sport
        for workout in workouts:
            sport = workout["sport"]
            if sport not in stats["workouts_by_sport"]:
                stats["workouts_by_sport"][sport] = 0
            stats["workouts_by_sport"][sport] += 1
            
            try:
                stats["total_duration"] += int(workout["duration"])
            except:
                pass
        
        # Calculate weekly average
        if workouts:
            first_date = datetime.datetime.fromisoformat(workouts[0]["date"])
            weeks = (datetime.datetime.now() - first_date).days / 7
            stats["weekly_avg"] = len(workouts) / max(1, weeks)
        
        return stats

# GUI Application
class SportsPalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SPORTSPAL - Your Intelligent Sports Assistant")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set window icon
        try:
            logo_path = "C:/Users/Ankur Mukhopadhyay/OneDrive/Desktop/project/logo.jpg"
            img = Image.open(logo_path)
            photo = ImageTk.PhotoImage(img)
            self.root.iconphoto(False, photo)
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Initialize components
        self.nlp_engine = SportsNLP()
        self.news_fetcher = SportsNews()
        self.workout_tracker = WorkoutTracker()
        
        # User management
        self.current_user = "default"
        self.current_sport = None
        self.context = None
        
        # Create GUI
        self.create_widgets()
        
        # Load initial data
        self.load_news()
        self.update_progress_display()
        self.display_message("SportsPal", "Welcome to SPORTSPAL! Your ultimate sports assistant for knowledge, workout plans, diet advice, and progress tracking.")
    
    def create_widgets(self):
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        primary_color = "#2E86AB"
        secondary_color = "#F18F01"
        accent_color = "#C73E1D"
        background_color = "#F5F5F5"
        text_color = "#333333"
        
        style.configure('TFrame', background=background_color)
        style.configure('TLabel', background=background_color, font=('Arial', 10), foreground=text_color)
        style.configure('TButton', font=('Arial', 10), padding=5, background=primary_color, foreground='white')
        style.configure('TCombobox', fieldbackground='white')
        style.configure('TEntry', fieldbackground='white')
        style.configure('Header.TLabel', font=('Arial', 16, 'bold'), foreground=primary_color)
        style.configure('Bold.TLabel', font=('Arial', 10, 'bold'), foreground=primary_color)
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('TNotebook', background=background_color)
        style.configure('TNotebook.Tab', background=background_color, padding=[10, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', primary_color)], foreground=[('selected', 'white')])
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header frame with logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        try:
            logo_img = Image.open("C:/Users/Ankur Mukhopadhyay/OneDrive/Desktop/project/logo.jpg")
            logo_img = logo_img.resize((50, 50), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(header_frame, image=self.logo_photo)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            print(f"Could not load logo: {e}")
            logo_label = ttk.Label(header_frame, text="⚽", font=('Arial', 24))
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(header_frame, text="SPORTSPAL", style='Header.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Left panel - Chat and user management
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # User management frame
        user_frame = ttk.LabelFrame(left_frame, text="User Profile", padding=10)
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(user_frame, text="Current User:").grid(row=0, column=0, sticky=tk.W)
        self.user_var = tk.StringVar(value=self.current_user)
        user_entry = ttk.Entry(user_frame, textvariable=self.user_var)
        user_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        switch_btn = ttk.Button(user_frame, text="Switch User", command=self.switch_user, style='TButton')
        switch_btn.grid(row=0, column=2, padx=5)
        
        ttk.Label(user_frame, text="Main Sport:").grid(row=1, column=0, sticky=tk.W)
        self.sport_var = tk.StringVar()
        sport_combo = ttk.Combobox(user_frame, textvariable=self.sport_var, 
                                  values=["Football", "Basketball", "Tennis", "General"])
        sport_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        sport_combo.bind('<<ComboboxSelected>>', lambda e: self.update_user_sport())
        
        ttk.Label(user_frame, text="Skill Level:").grid(row=2, column=0, sticky=tk.W)
        self.level_var = tk.StringVar()
        level_combo = ttk.Combobox(user_frame, textvariable=self.level_var, 
                                  values=["Beginner", "Intermediate", "Advanced"])
        level_combo.grid(row=2, column=1, sticky=tk.EW, padx=5)
        level_combo.bind('<<ComboboxSelected>>', lambda e: self.update_user_level())
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            left_frame, wrap=tk.WORD, width=50, height=15,
            font=('Arial', 11), bg='white', bd=2, relief=tk.GROOVE
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # User input
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.user_input = ttk.Entry(input_frame, font=('Arial', 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message, style='TButton')
        send_button.pack(side=tk.RIGHT)
        
        # Right panel - Sports info, news, and progress
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # Notebook for multiple tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # News tab
        news_tab = ttk.Frame(self.notebook)
        self.notebook.add(news_tab, text="Sports News")
        
        self.news_list = tk.Listbox(
            news_tab, height=10, font=('Arial', 10),
            selectbackground=primary_color, selectforeground='white',
            bg='white', bd=2, relief=tk.GROOVE
        )
        self.news_list.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.news_list.bind('<<ListboxSelect>>', self.show_news_detail)
        
        self.news_detail = scrolledtext.ScrolledText(
            news_tab, wrap=tk.WORD, height=8,
            font=('Arial', 10), bg='white', bd=2, relief=tk.GROOVE
        )
        self.news_detail.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.news_image_label = ttk.Label(news_tab)
        self.news_image_label.pack(fill=tk.X)
        
        # Progress tab
        progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(progress_tab, text="Your Progress")
        
        self.progress_stats_frame = ttk.Frame(progress_tab)
        self.progress_stats_frame.pack(fill=tk.X, pady=5)
        
        self.progress_canvas_frame = ttk.Frame(progress_tab)
        self.progress_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Workout logging tab
        workout_tab = ttk.Frame(self.notebook)
        self.notebook.add(workout_tab, text="Log Workout")
        
        ttk.Label(workout_tab, text="Sport:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.workout_sport_var = tk.StringVar()
        sport_combo = ttk.Combobox(workout_tab, textvariable=self.workout_sport_var, 
                    values=["Football", "Basketball", "Tennis", "Running", "Cycling", "Other"])
        sport_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(workout_tab, text="Workout Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.workout_type_var = tk.StringVar()
        type_combo = ttk.Combobox(workout_tab, textvariable=self.workout_type_var, 
                     values=["Cardio", "Strength", "Flexibility", "Skills", "Game", "Other"])
        type_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(workout_tab, text="Duration (mins):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.workout_duration_var = tk.StringVar()
        ttk.Entry(workout_tab, textvariable=self.workout_duration_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(workout_tab, text="Intensity:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.workout_intensity_var = tk.StringVar()
        intensity_combo = ttk.Combobox(workout_tab, textvariable=self.workout_intensity_var, 
                     values=["Low", "Medium", "High"])
        intensity_combo.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(workout_tab, text="Notes:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.workout_notes_var = tk.StringVar()
        ttk.Entry(workout_tab, textvariable=self.workout_notes_var).grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)
        
        log_btn = ttk.Button(workout_tab, text="Log Workout", command=self.log_workout, style='TButton')
        log_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.workout_status_label = ttk.Label(workout_tab, text="", style='Success.TLabel')
        self.workout_status_label.grid(row=6, column=0, columnspan=2)
        
        # Diet tab
        diet_tab = ttk.Frame(self.notebook)
        self.notebook.add(diet_tab, text="Diet Plans")
        
        ttk.Label(diet_tab, text="Select Goal:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.diet_goal_var = tk.StringVar()
        goal_combo = ttk.Combobox(diet_tab, textvariable=self.diet_goal_var, 
                     values=["Weight Loss", "Muscle Gain", "Endurance"])
        goal_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        diet_btn = ttk.Button(diet_tab, text="Get Diet Plan", command=self.show_diet_plan, style='TButton')
        diet_btn.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.diet_display = scrolledtext.ScrolledText(
            diet_tab, wrap=tk.WORD, height=15,
            font=('Arial', 11), bg='white', bd=2, relief=tk.GROOVE
        )
        self.diet_display.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        # Configure grid weights
        workout_tab.grid_columnconfigure(1, weight=1)
        diet_tab.grid_columnconfigure(1, weight=1)
        diet_tab.grid_rowconfigure(2, weight=1)
    
    def switch_user(self):
        new_user = self.user_var.get().strip()
        if not new_user:
            messagebox.showerror("Error", "Please enter a username")
            return
        
        self.current_user = new_user
        if new_user not in USER_PROFILES:
            USER_PROFILES[new_user] = {
                "sport": "general",
                "level": "beginner",
                "goals": ["Get fit"],
                "progress": {
                    "workouts_completed": 0,
                    "weight": None,
                    "measurements": {}
                }
            }
            with open('user_profiles.json', 'w') as f:
                json.dump(USER_PROFILES, f)
        
        self.sport_var.set(USER_PROFILES[new_user]["sport"].capitalize())
        self.level_var.set(USER_PROFILES[new_user]["level"].capitalize())
        
        self.display_message("SportsPal", f"Switched to user: {new_user}")
        self.update_progress_display()
    
    def update_user_sport(self):
        sport = self.sport_var.get().lower()
        USER_PROFILES[self.current_user]["sport"] = sport
        with open('user_profiles.json', 'w') as f:
            json.dump(USER_PROFILES, f)
        
        self.current_sport = sport
        self.load_news()
        self.display_message("SportsPal", f"Your main sport has been set to {sport}")
    
    def update_user_level(self):
        level = self.level_var.get().lower()
        USER_PROFILES[self.current_user]["level"] = level
        with open('user_profiles.json', 'w') as f:
            json.dump(USER_PROFILES, f)
        
        self.display_message("SportsPal", f"Your skill level has been set to {level}")
    
    def send_message(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        
        self.display_message("You", user_text)
        self.user_input.delete(0, tk.END)
        
        # Process in a separate thread to keep UI responsive
        threading.Thread(target=self.process_message, args=(user_text,), daemon=True).start()
    
    def process_message(self, user_text):
        # Get response
        response = self.nlp_engine.generate_response(user_text, self.context)
        
        # Update context
        self.context = user_text
        
        # Display response
        self.root.after(0, self.display_message, "SportsPal", response)
    
    def display_message(self, sender, message):
        self.chat_display.config(state='normal')
        if sender == "SportsPal":
            self.chat_display.tag_config('assistant', foreground='blue')
            self.chat_display.insert(tk.END, f"{sender}: ", 'assistant')
        else:
            self.chat_display.insert(tk.END, f"{sender}: ")
            
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def load_news(self):
        def fetch_news():
            sport = self.current_sport or "sports"
            news = self.news_fetcher.get_latest_news(sport)
            self.root.after(0, self.update_news_display, news)
        
        threading.Thread(target=fetch_news, daemon=True).start()
    
    def update_news_display(self, news):
        self.news_list.delete(0, tk.END)
        self.news_articles = news
        
        for article in news:
            title = article['title'][:50] + "..." if len(article['title']) > 50 else article['title']
            self.news_list.insert(tk.END, title)
    
    def show_news_detail(self, event):
        if not self.news_articles:
            return
        
        selection = self.news_list.curselection()
        if not selection:
            return
        
        article = self.news_articles[selection[0]]
        
        # Update detail text
        self.news_detail.config(state='normal')
        self.news_detail.delete(1.0, tk.END)
        self.news_detail.insert(tk.END, f"{article['title']}\n\n", 'bold')
        self.news_detail.insert(tk.END, f"Published: {datetime.datetime.fromisoformat(article['published_at']).strftime('%Y-%m-%d %H:%M')}\n\n")
        self.news_detail.insert(tk.END, article['description'])
        self.news_detail.config(state='disabled')
        
        # Load image if available
        if article['image_url']:
            try:
                response = requests.get(article['image_url'])
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img.thumbnail((400, 300))
                photo = ImageTk.PhotoImage(img)
                
                self.news_image_label.config(image=photo)
                self.news_image_label.image = photo
            except:
                self.news_image_label.config(image='')
                self.news_image_label.image = None
        else:
            self.news_image_label.config(image='')
            self.news_image_label.image = None
    
    def log_workout(self):
        sport = self.workout_sport_var.get()
        workout_type = self.workout_type_var.get()
        duration = self.workout_duration_var.get()
        intensity = self.workout_intensity_var.get()
        notes = self.workout_notes_var.get()
        
        if not all([sport, workout_type, duration, intensity]):
            self.workout_status_label.config(text="Please fill all required fields", style='Error.TLabel')
            return
        
        try:
            duration = int(duration)
        except:
            self.workout_status_label.config(text="Duration must be a number", style='Error.TLabel')
            return
        
        workout = self.workout_tracker.log_workout(
            self.current_user,
            sport,
            workout_type,
            duration,
            intensity,
            notes
        )
        
        self.workout_status_label.config(text=f"Workout logged: {workout_type} for {duration} mins", style='Success.TLabel')
        self.update_progress_display()
        
        # Clear form
        self.workout_notes_var.set("")
    
    def update_progress_display(self):
        # Clear previous widgets
        for widget in self.progress_stats_frame.winfo_children():
            widget.destroy()
        
        for widget in self.progress_canvas_frame.winfo_children():
            widget.destroy()
        
        # Get stats
        stats = self.workout_tracker.get_progress_stats(self.current_user)
        
        # Display basic stats
        ttk.Label(self.progress_stats_frame, text="Total Workouts:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.progress_stats_frame, text=str(stats["total_workouts"])).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(self.progress_stats_frame, text="Weekly Average:", style='Bold.TLabel').grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self.progress_stats_frame, text=f"{stats['weekly_avg']:.1f} workouts/week").grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(self.progress_stats_frame, text="Total Duration:", style='Bold.TLabel').grid(row=2, column=0, sticky=tk.W)
        ttk.Label(self.progress_stats_frame, text=f"{stats['total_duration']} minutes").grid(row=2, column=1, sticky=tk.W)
        
        # Create chart
        if stats["workouts_by_sport"]:
            fig, ax = plt.subplots(figsize=(5, 3))
            sports = list(stats["workouts_by_sport"].keys())
            counts = list(stats["workouts_by_sport"].values())
            
            ax.bar(sports, counts, color='#2E86AB')
            ax.set_title("Workouts by Sport", fontsize=10)
            ax.set_ylabel("Number of Workouts", fontsize=8)
            plt.xticks(rotation=45, ha='right', fontsize=8)
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=self.progress_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_diet_plan(self):
        goal = self.diet_goal_var.get().lower().replace(" ", "_")
        
        if goal not in SPORTS_KNOWLEDGE['general']['diet']:
            self.diet_display.config(state='normal')
            self.diet_display.delete(1.0, tk.END)
            self.diet_display.insert(tk.END, "Please select a valid goal")
            self.diet_display.config(state='disabled')
            return
        
        diet_info = SPORTS_KNOWLEDGE['general']['diet'][goal]
        
        # Get sport-specific diet if available
        sport = USER_PROFILES[self.current_user]["sport"]
        if sport in SPORTS_KNOWLEDGE and 'diet' in SPORTS_KNOWLEDGE[sport]:
            sport_diet = SPORTS_KNOWLEDGE[sport]['diet']
            diet_info += f"\n\nFor {sport} specifically:\n"
            diet_info += f"Pre-activity: {sport_diet.get('pre_game', sport_diet.get('pre_match', 'N/A'))}\n"
            diet_info += f"Post-activity: {sport_diet.get('post_game', sport_diet.get('post_match', 'N/A'))}\n"
            diet_info += f"General: {sport_diet.get('general', 'N/A')}"
        
        self.diet_display.config(state='normal')
        self.diet_display.delete(1.0, tk.END)
        self.diet_display.insert(tk.END, diet_info)
        self.diet_display.config(state='disabled')

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SportsPalApp(root)
    root.mainloop()