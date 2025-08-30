# Author: Michael Kaminski at Multiaxis
# Description: Multiaxis Intelligence Quiz Generator


CURRENT_VERSION = "1.0.0.0"
BUILD_DATE = "August 29, 2025"
STATUS = "β Release"

"""
# --- Sample Quizzes ---
# --- Quiz Generator ---
# --- Quiz Generator App ---
# --- Main ---
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import logging
import traceback
from datetime import datetime
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import webbrowser
import os
import sys
import secrets
import hashlib
import base64
import html
import winreg
import ctypes
import ctypes.wintypes

# Windows Registry Path where values are stored
WINDOWS_REGISTRY_PATH = r"Software\Multiaxis LLC\Multiaxis Intelligence - Quiz Generator\Info"

# Application constants
APP_NAME = "Multiaxis Quiz Generator"
APP_COMPANY = "Multiaxis LLC"
APP_DATA_FOLDER = os.path.join(os.getenv('APPDATA'), APP_COMPANY, APP_NAME)

# Mutex for single instance
APP_MUTEX = None


def create_app_mutex():
    """Create a Windows mutex to ensure only one instance of the app runs."""
    global APP_MUTEX
    
    kernel32 = ctypes.windll.kernel32
    mutex_name = "Global\\MultiaxisQuizGenerator_Mutex_v1"
    
    # Try to create the mutex
    APP_MUTEX = kernel32.CreateMutexW(None, True, mutex_name)
    last_error = kernel32.GetLastError()
    
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        logging.warning("Another instance of Quiz Generator is already running")
        return False
    
    logging.info("Mutex created successfully - single instance ensured")
    return True


def setup_application_folders():
    """Create necessary application folders in AppData."""
    folders = [
        APP_DATA_FOLDER,
        os.path.join(APP_DATA_FOLDER, 'logs'),
        os.path.join(APP_DATA_FOLDER, 'settings'),
        os.path.join(APP_DATA_FOLDER, 'temp')
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    return True


def set_registry_value(name, value, registry_path=WINDOWS_REGISTRY_PATH):
    """Set a value in the registry."""
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value))
        logging.debug(f"Registry value set - {name}: {value}")
    except Exception as e:
        logging.error(f"Failed to set registry value {name}: {e}")
        print(f"Failed to set registry value {name}: {e}")


def get_registry_value(name, registry_path=WINDOWS_REGISTRY_PATH):
    """Get a value from the registry, or return None if not found."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            logging.debug(f"Retrieved registry value - {name}: {value}")
            return value
    except FileNotFoundError:
        logging.debug(f"Registry value not found: {name}")
        return None
    except Exception as e:
        logging.error(f"Failed to get registry value {name}: {e}")
        print(f"Failed to get registry value {name}: {e}")
        return None


def resource_path(relative_path):
    """Get absolute path to resource, works for both development and PyInstaller environments."""
    try:
        # PyInstaller creates a temporary folder and stores the path in sys._MEIPASS
        base_path = sys._MEIPASS
        logging.debug(f"PyInstaller temp folder path (sys._MEIPASS): {base_path}")
    except AttributeError:
        # If not running in a PyInstaller bundle, use the script's directory
        # Get the directory where this script is located
        base_path = os.path.dirname(os.path.abspath(__file__))
        # If we're in a src directory, go up one level to find assets
        if os.path.basename(base_path) == 'src':
            base_path = os.path.dirname(base_path)
        logging.debug(f"Development base path: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    logging.debug(f"Full resource path: {full_path}")
    return full_path


def setup_logging():
    """Initialize logging with proper AppData location."""
    try:
        # Ensure folders exist
        setup_application_folders()
        
        # Create logs directory
        logs_dir = os.path.join(APP_DATA_FOLDER, 'logs')
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"quiz_generator_{timestamp}.log"
        LOG_FILE = os.path.join(logs_dir, log_filename)
        
        # Also create a 'latest.log' that always points to the most recent session
        latest_log = os.path.join(logs_dir, 'latest.log')
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.FileHandler(latest_log, mode='w'),  # Overwrite latest.log
                logging.StreamHandler()  # Still log to console
            ]
        )
        
        logging.info("="*60)
        logging.info("Quiz Generator App Started")
        logging.info(f"Log file: {LOG_FILE}")
        logging.info(f"AppData folder: {APP_DATA_FOLDER}")
        logging.info("="*60)
        
        # Clean up old logs (keep only last 10)
        clean_old_logs(logs_dir)
        
        return LOG_FILE
        
    except Exception as e:
        # Fallback to local directory if AppData fails
        fallback_log = "MultiaxisQuizGenerator.log"
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
            filename=fallback_log
        )
        logging.error(f"Error setting up logging in AppData: {e}")
        logging.info(f"Using fallback log file: {fallback_log}")
        return fallback_log


def clean_old_logs(logs_dir, keep_count=10):
    """Clean up old log files, keeping only the most recent ones."""
    try:
        # Get all log files except 'latest.log'
        log_files = [f for f in os.listdir(logs_dir) 
                    if f.startswith('quiz_generator_') and f.endswith('.log')]
        
        # Sort by modification time
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)))
        
        # Remove oldest files if we have too many
        while len(log_files) > keep_count:
            old_file = log_files.pop(0)
            try:
                os.remove(os.path.join(logs_dir, old_file))
                logging.debug(f"Removed old log file: {old_file}")
            except:
                pass
                
    except Exception as e:
        logging.debug(f"Error cleaning old logs: {e}")


# Initialize logging before anything else
LOG_FILE = setup_logging()


# --- Sample Quizzes --


SAMPLE_QUIZZES = {
    "CNC Manufacturing Fundamentals": {
        "description": "Test your knowledge of CNC machining and manufacturing processes",
        "questions": [
            {
                "question": "What does CNC stand for?",
                "options": ["Computer Numerical Control", "Central Network Computer", "Computerized Navigation Center", "Control Number Code"],
                "correct": 0,
                "explanation": "CNC stands for Computer Numerical Control, which refers to the automated control of machining tools by means of a computer."
            },
            {
                "question": "Which G-code is typically used for rapid positioning?",
                "options": ["G00", "G01", "G02", "G03"],
                "correct": 0,
                "explanation": "G00 is the rapid positioning command that moves the tool at maximum speed to a specified position without cutting."
            },
            {
                "question": "What is the primary purpose of coolant in CNC machining?",
                "options": ["To make the machine run faster", "To reduce heat and remove chips", "To increase tool sharpness", "To reduce machine noise"],
                "correct": 1,
                "explanation": "Coolant serves to reduce heat generated during cutting and helps flush away chips from the cutting area."
            },
            {
                "question": "How many axes does a standard 5-axis CNC machine have?",
                "options": ["3 linear axes only", "2 linear and 3 rotary axes", "3 linear and 2 rotary axes", "5 linear axes"],
                "correct": 2,
                "explanation": "A 5-axis CNC machine has 3 linear axes (X, Y, Z) and 2 rotary axes (typically A and B or A and C)."
            },
            {
                "question": "What does CAM software stand for?",
                "options": ["Computer Aided Machining", "Central Axis Management", "Computer Aided Manufacturing", "Controlled Automation Module"],
                "correct": 2,
                "explanation": "CAM stands for Computer Aided Manufacturing, software used to generate toolpaths and G-code from CAD models."
            }
        ]
    },
    "Project Management Essentials": {
        "description": "Essential concepts for effective project management",
        "questions": [
            {
                "question": "What does SMART stand for in SMART goals?",
                "options": ["Strategic, Managed, Achievable, Realistic, Timed", "Specific, Measurable, Achievable, Relevant, Time-bound", "Simple, Meaningful, Actionable, Reasonable, Targeted", "Structured, Monitored, Attainable, Resourced, Tracked"],
                "correct": 1,
                "explanation": "SMART goals are Specific, Measurable, Achievable, Relevant, and Time-bound."
            },
            {
                "question": "What are the three constraints in the project management triangle?",
                "options": ["People, Process, Technology", "Plan, Execute, Monitor", "Scope, Time, Cost", "Quality, Risk, Resources"],
                "correct": 2,
                "explanation": "The classic project management triangle consists of Scope, Time, and Cost constraints."
            },
            {
                "question": "Which project management methodology uses sprints?",
                "options": ["Waterfall", "Agile/Scrum", "Six Sigma", "PRINCE2"],
                "correct": 1,
                "explanation": "Agile/Scrum methodology uses sprints, which are fixed-length iterations typically lasting 2-4 weeks."
            },
            {
                "question": "What is a Gantt chart primarily used for?",
                "options": ["Budget tracking", "Risk assessment", "Schedule visualization", "Quality control"],
                "correct": 2,
                "explanation": "A Gantt chart is primarily used for schedule visualization, showing project tasks over time."
            },
            {
                "question": "What does WBS stand for?",
                "options": ["Work Breakdown Structure", "Weekly Business Summary", "Workflow Balance System", "Working Budget Statement"],
                "correct": 0,
                "explanation": "WBS stands for Work Breakdown Structure, a hierarchical decomposition of project deliverables."
            }
        ]
    },
    "Safety Protocols Quiz": {
        "description": "Workplace safety and OSHA compliance basics",
        "questions": [
            {
                "question": "What does PPE stand for?",
                "options": ["Personal Protection Equipment", "Personal Protective Equipment", "Professional Protection Equipment", "Protective Personal Equipment"],
                "correct": 1,
                "explanation": "PPE stands for Personal Protective Equipment, which includes items worn to minimize exposure to hazards."
            },
            {
                "question": "What is the purpose of a lockout/tagout procedure?",
                "options": ["To secure the building", "To prevent unauthorized machine startup during maintenance", "To track tool inventory", "To schedule maintenance"],
                "correct": 1,
                "explanation": "Lockout/tagout procedures prevent unexpected machine startup or energy release during servicing and maintenance."
            },
            {
                "question": "What does SDS stand for in workplace safety?",
                "options": ["Safety Data Sheet", "Standard Documentation System", "Safety Department Standards", "Secure Data Storage"],
                "correct": 0,
                "explanation": "SDS stands for Safety Data Sheet, which provides information about chemical hazards and safe handling procedures."
            },
            {
                "question": "What is the recommended lifting technique to prevent back injury?",
                "options": ["Bend at the waist", "Lift with your legs, not your back", "Twist while lifting", "Hold breath while lifting"],
                "correct": 1,
                "explanation": "Proper lifting technique involves bending at the knees and lifting with leg muscles while keeping the back straight."
            },
            {
                "question": "How often should fire extinguishers be inspected?",
                "options": ["Annually", "Monthly", "Weekly", "Only after use"],
                "correct": 1,
                "explanation": "Fire extinguishers should be visually inspected monthly and receive professional maintenance annually."
            }
        ]
    },
    "Basic Python Programming": {
        "description": "Fundamental concepts in Python programming",
        "questions": [
            {
                "question": "Which of the following is used to define a function in Python?",
                "options": ["function", "def", "func", "define"],
                "correct": 1,
                "explanation": "The 'def' keyword is used to define a function in Python."
            },
            {
                "question": "What data type is [1, 2, 3] in Python?",
                "options": ["Tuple", "Set", "List", "Dictionary"],
                "correct": 2,
                "explanation": "Square brackets [] denote a list in Python, which is a mutable, ordered collection."
            },
            {
                "question": "Which operator is used for exponentiation in Python?",
                "options": ["^", "**", "^^", "exp()"],
                "correct": 1,
                "explanation": "The ** operator is used for exponentiation in Python (e.g., 2**3 equals 8)."
            },
            {
                "question": "What is the output of print(type(5))?",
                "options": ["&lt;class 'float'&gt;", "&lt;class 'int'&gt;", "&lt;class 'number'&gt;", "&lt;class 'digit'&gt;"],
                "correct": 1,
                "explanation": "The number 5 is an integer, so type(5) returns &lt;class 'int'&gt;."
            },
            {
                "question": "Which statement is used to handle exceptions in Python?",
                "options": ["try/except", "catch/throw", "error/handle", "test/fail"],
                "correct": 0,
                "explanation": "Python uses try/except blocks to handle exceptions and errors in code."
            }
        ]
    }
}


# --- Quiz Generator ---


class QuizGenerator:
    def __init__(self, quiz_title: str = "Interactive Knowledge Quiz", 
                 quiz_description: str = "Test your knowledge with this interactive quiz."):
        self.quiz_title = quiz_title
        self.quiz_description = quiz_description
        self.questions = []


    def add_question(self, question: str, options: List[str], correct_index: int, 
                     explanation: str = "", image_filename: str = ""):
        """Add a question to the quiz."""
        self.questions.append({
            "question": question,
            "options": options,
            "correct": correct_index,
            "explanation": explanation,
            "image": image_filename
        })


    def clear_questions(self):
        """Clear all questions."""
        self.questions = []


    def get_question_count(self):
        """Get number of questions."""
        return len(self.questions)


    def load_from_csv(self, csv_file: str):
        """Load questions from CSV file."""
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    question = row.get('question') or row.get('Question')
                    
                    options = []
                    if 'option_a' in row:
                        options = [row['option_a'], row['option_b'], row['option_c'], row['option_d']]
                    elif 'Option A' in row:
                        options = [row['Option A'], row['Option B'], row['Option C'], row['Option D']]
                    
                    options = [opt for opt in options if opt and opt.strip()]
                    
                    correct_answer = row.get('correct_answer') or row.get('correct') or row.get('answer')
                    correct_index = self._parse_correct_answer(correct_answer, options)
                    
                    explanation = row.get('explanation') or row.get('Explanation') or ""
                    
                    if question and options and correct_index is not None:
                        self.add_question(question, options, correct_index, explanation)
                        count += 1
                
                return True, f"Loaded {count} questions from CSV"
        except Exception as e:
            return False, f"Error loading CSV: {str(e)}"


    def load_from_json(self, json_file: str):
        """Load questions from JSON file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if 'title' in data:
                self.quiz_title = data['title']
            if 'description' in data:
                self.quiz_description = data['description']
            
            questions = data.get('questions', data if isinstance(data, list) else [])
            count = 0
            for q in questions:
                if all(key in q for key in ['question', 'options', 'correct']):
                    self.add_question(
                        question=q['question'],
                        options=q['options'],
                        correct_index=q['correct'],
                        explanation=q.get('explanation', '')
                    )
                    count += 1
            
            return True, f"Loaded {count} questions from JSON"
        except Exception as e:
            return False, f"Error loading JSON: {str(e)}"


    def load_from_text(self, text_content: str):
        """Load questions from formatted text."""
        try:
            questions_found = 0
            question_blocks = text_content.split('---')
            
            for block in question_blocks:
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                question = ""
                options = []
                correct_answer = ""
                explanation = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Q:'):
                        question = line[2:].strip()
                    elif re.match(r'^[A-D]:', line):
                        options.append(line[2:].strip())
                    elif line.startswith('Correct:'):
                        correct_answer = line[8:].strip()
                    elif line.startswith('Explanation:'):
                        explanation = line[12:].strip()
                
                if question and options:
                    correct_index = self._parse_correct_answer(correct_answer, options)
                    if correct_index is not None:
                        self.add_question(question, options, correct_index, explanation)
                        questions_found += 1
            
            return True, f"Loaded {questions_found} questions from text"
        except Exception as e:
            return False, f"Error parsing text: {str(e)}"


    def _parse_correct_answer(self, correct_answer: str, options: List[str]) -> Optional[int]:
        """Parse correct answer from various formats."""
        if not correct_answer:
            return None
        
        correct_answer = str(correct_answer).strip().upper()
        
        if correct_answer in ['A', 'B', 'C', 'D']:
            return ord(correct_answer) - ord('A')
        
        try:
            index = int(correct_answer) - 1
            if 0 <= index < len(options):
                return index
        except ValueError:
            pass
        
        return None


    def save_to_csv(self, output_file: str):
        """Save questions to CSV."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation'])
                
                for q in self.questions:
                    options = q['options'] + [''] * (4 - len(q['options']))
                    correct_letter = chr(65 + q['correct'])
                    writer.writerow([
                        q['question'],
                        options[0],
                        options[1],
                        options[2],
                        options[3],
                        correct_letter,
                        q['explanation']
                    ])
            
            return True, f"Saved {len(self.questions)} questions to CSV"
        except Exception as e:
            return False, f"Error saving CSV: {str(e)}"


    def save_to_json(self, output_file: str):
        """Save questions to JSON."""
        try:
            data = {
                "title": self.quiz_title,
                "description": self.quiz_description,
                "questions": self.questions
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True, f"Saved {len(self.questions)} questions to JSON"
        except Exception as e:
            return False, f"Error saving JSON: {str(e)}"


    def generate_html(self, output_file: str):
        """Generate clean HTML quiz file without image instructions."""
        logging.info(f"Starting HTML generation for: {output_file}")
        
        if not self.questions:
            logging.warning("No questions available for HTML generation")
            return False, "No questions to generate"
        
        try:
            # Log quiz details
            logging.info(f"Quiz title: {self.quiz_title}")
            logging.info(f"Number of questions: {len(self.questions)}")
            
            # Try to embed logo as base64 FIRST - before using it
            logo_base64 = ""
            logo_path = resource_path('assets/MultiaxisQuizGenerator_logo.png')
            try:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
                    logging.info("Logo successfully encoded as base64")
            except Exception as e:
                logging.warning(f"Could not load logo: {e}")
                # Fallback to SVG placeholder
                logo_base64 = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='80' viewBox='0 0 200 80'%3E%3Crect width='200' height='80' fill='%232C5282'/%3E%3Ctext x='100' y='40' font-family='Arial' font-size='16' fill='white' text-anchor='middle' dominant-baseline='middle'%3EMULTIAXIS%3C/text%3E%3C/svg%3E"

            # Check if any questions have images
            has_images = any(q.get('image', '') for q in self.questions)
            logging.info(f"Has images: {has_images}")
            
            # Get settings from parent app if available
            author = getattr(self, 'author', 'Arlo AI Assistant')
            company = getattr(self, 'company', 'Multiaxis Intelligence')
            show_results = getattr(self, 'show_results', True)
            show_explanations = getattr(self, 'show_explanations', True)
            allow_review = getattr(self, 'allow_review', True)
            randomize = getattr(self, 'randomize', False)
            timer_minutes = getattr(self, 'timer_minutes', 0)
            pass_threshold = getattr(self, 'pass_threshold', 70)
            enable_certificate = getattr(self, 'enable_certificate', False)
            
            logging.debug(f"Settings - Author: {author}, Company: {company}, Timer: {timer_minutes}")
            
            # Generate image constants section if needed (but cleaner)
            image_constants = ""
            if has_images:
                logging.info("Generating image constants section")
                image_constants = """
    <script>
        // Image configuration - see answer key for setup instructions
        const IMAGE_PATHS = {"""
                
                # Collect unique image filenames
                image_files = set()
                for i, q in enumerate(self.questions, 1):
                    if q.get('image'):
                        image_files.add(q['image'])
                        logging.debug(f"Question {i} has image: {q['image']}")
                
                # Add image path entries
                for img in sorted(image_files):
                    image_constants += f'\n            "{img}": "{img}",'
                
                image_constants = image_constants.rstrip(',')
                image_constants += """
        };
        
        // Placeholder image
        const PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'%3E%3Crect width='1024' height='1024' fill='%23f0f0f0'/%3E%3Ctext x='512' y='512' font-family='Arial' font-size='48' fill='%23999' text-anchor='middle' dominant-baseline='middle'%3EImage Loading...%3C/text%3E%3C/svg%3E";
        
        function getImagePath(filename) {
            return IMAGE_PATHS[filename] || PLACEHOLDER_IMAGE;
        }
    </script>
"""
            
            # Quiz configuration script
            quiz_config = f"""
    <script>
        // Quiz Configuration
        const QUIZ_CONFIG = {{
            showResults: {str(show_results).lower()},
            showExplanations: {str(show_explanations).lower()},
            allowReview: {str(allow_review).lower()},
            randomizeQuestions: {str(randomize).lower()},
            timerMinutes: {timer_minutes},
            passThreshold: {pass_threshold},
            enableCertificate: {str(enable_certificate).lower()},
            author: "{author}",
            company: "{company}",
            quizTitle: "{self.quiz_title}", 
            copyright: "©2025 {company}. All rights reserved"
        }};
        
        let timeRemaining = QUIZ_CONFIG.timerMinutes * 60; // Convert to seconds
        let timerInterval = null;
    </script>
"""
            
            logging.info("Building HTML template")
            
            html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="{author}">
    <meta name="company" content="{company}">
    <meta name="generator" content="Quiz Generator - Multiaxis Intelligence">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            min-height: 100vh;
        }}
        .quiz-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px auto;
            max-width: 900px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2C5282;
            text-align: center;
            margin-bottom: 10px;
        }}
        .quiz-description {{
            text-align: center;
            color: #666;
            margin-bottom: 10px;
        }}
        .quiz-meta {{
            text-align: center;
            color: #999;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .timer-display {{
            text-align: center;
            font-size: 24px;
            color: #2C5282;
            font-weight: bold;
            margin: 15px 0;
            padding: 10px;
            background: #f0f4ff;
            border-radius: 8px;
            display: none;
        }}
        .timer-display.warning {{
            color: #ffc107;
            background: #fff3cd;
        }}
        .timer-display.danger {{
            color: #dc3545;
            background: #f8d7da;
        }}
        .quiz-question {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #5B9BD5;
        }}
        .quiz-question h4 {{
            color: #2C5282;
            margin-bottom: 15px;
        }}
        .difficulty-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .difficulty-easy {{
            background: #d4edda;
            color: #155724;
        }}
        .difficulty-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        .difficulty-hard {{
            background: #f8d7da;
            color: #721c24;
        }}
        .question-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            margin: 20px auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .quiz-options {{
            margin: 15px 0;
        }}
        .quiz-option {{
            display: block;
            margin: 10px 0;
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .quiz-option:hover {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            transform: translateX(5px);
        }}
        .quiz-option.selected {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            font-weight: 600;
        }}
        .quiz-button {{
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            transition: transform 0.2s;
        }}
        .quiz-button:hover {{
            transform: scale(1.05);
        }}
        .quiz-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: scale(1);
        }}
        .quiz-results {{
            padding: 30px;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border-radius: 15px;
            margin: 20px 0;
            display: none;
        }}
        .quiz-score {{
            font-size: 28px;
            color: #2C5282;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .quiz-progress {{
            background: #e2e8f0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .quiz-progress-bar {{
            background: linear-gradient(90deg, #5B9BD5 0%, #2C5282 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .result-item {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
        }}
        .result-item.correct {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .result-item.incorrect {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .certificate-wrapper {{
            display: none;
            margin: 30px auto;
            text-align: center;
        }}
        .certificate-iframe {{
            width: 100%;
            height: 900px;
            border: none;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #666;
            font-size: 12px;
        }}
    </style>
    {quiz_config}
    {image_constants}
</head>
<body>
    <div class="quiz-container">
        <h1>{title}</h1>
        <p class="quiz-description">{description}</p>
        <div class="quiz-meta">
            {author_line}
            {company_line}
        </div>
        
        <div class="timer-display" id="timerDisplay">
            Time Remaining: <span id="timerValue">00:00</span>
        </div>
        
        <div class="quiz-progress">
            <div class="quiz-progress-bar" id="progressBar">0%</div>
        </div>

        <div id="quizContent"></div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="quiz-button" id="prevBtn" onclick="prevQuestion()" style="display:none;">← Previous</button>
            <button class="quiz-button" id="nextBtn" onclick="nextQuestion()" style="display:none;">Next →</button>
            <button class="quiz-button" id="startBtn" onclick="startQuiz()">Start Quiz</button>
            <button class="quiz-button" id="submitBtn" onclick="submitQuiz()" style="display:none;">Submit Quiz</button>
            <button class="quiz-button" id="restartBtn" onclick="restartQuiz()" style="display:none;">Restart Quiz</button>
        </div>

        <div class="quiz-results" id="quizResults">
            <h2 style="text-align: center; color: #2C5282;">Quiz Results</h2>
            <div class="quiz-score" id="quizScore"></div>
            <div id="resultDetails"></div>
        </div>
        
        <div class="certificate-wrapper" id="certificateWrapper">
            <h2 style="color: #2C5282; margin-bottom: 20px;">🏆 Your Certificate of Achievement 🏆</h2>
            <iframe id="certificateFrame" class="certificate-iframe"></iframe>
            <div style="margin-top: 20px;">
                <button class="quiz-button" onclick="downloadCertificate()">📥 Download Certificate</button>
                <button class="quiz-button" onclick="printCertificate()">🖨️ Print Certificate</button>
            </div>
        </div>
        
        <div class="footer">
            {footer_text}
        </div>
    </div>

    <script>
        let quizQuestions = {questions_json};
        let currentQuestion = 0;
        let userAnswers = [];
        let quizStarted = false;
        
        // Apply randomization if configured
        if (QUIZ_CONFIG.randomizeQuestions) {{
            quizQuestions = quizQuestions.sort(() => Math.random() - 0.5);
        }}
        
        function startTimer() {{
            if (QUIZ_CONFIG.timerMinutes > 0) {{
                document.getElementById('timerDisplay').style.display = 'block';
                updateTimerDisplay();
                
                timerInterval = setInterval(() => {{
                    timeRemaining--;
                    updateTimerDisplay();
                    
                    if (timeRemaining <= 0) {{
                        clearInterval(timerInterval);
                        alert('Time is up! Submitting quiz...');
                        submitQuiz();
                    }}
                }}, 1000);
            }}
        }}
        
        function updateTimerDisplay() {{
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            const display = `${{String(minutes).padStart(2, '0')}}:${{String(seconds).padStart(2, '0')}}`;
            document.getElementById('timerValue').textContent = display;
            
            const timerDiv = document.getElementById('timerDisplay');
            if (timeRemaining < 60) {{
                timerDiv.classList.add('danger');
            }} else if (timeRemaining < 300) {{
                timerDiv.classList.add('warning');
            }}
        }}

        function startQuiz() {{
            quizStarted = true;
            currentQuestion = 0;
            userAnswers = new Array(quizQuestions.length).fill(null);
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'inline-block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('certificateWrapper').style.display = 'none';
            startTimer();
            showQuestion();
        }}

        function showQuestion() {{
            const question = quizQuestions[currentQuestion];
            const quizContent = document.getElementById('quizContent');
            
            let difficultyBadge = '';
            if (question.difficulty) {{
                const diffClass = `difficulty-${{question.difficulty.toLowerCase()}}`;
                difficultyBadge = `<span class="difficulty-badge ${{diffClass}}">${{question.difficulty}}</span>`;
            }}
            
            let html = `
                <div class="quiz-question">
                    <h4>Question ${{currentQuestion + 1}} of ${{quizQuestions.length}} ${{difficultyBadge}}</h4>
                    <p style="font-size: 18px; margin: 20px 0;">${{question.question}}</p>
            `;
            
            // Add image if present
            if (question.image) {{
                const imagePath = typeof getImagePath === 'function' ? getImagePath(question.image) : question.image;
                html += `<img src="${{imagePath}}" alt="Question ${{currentQuestion + 1}} Image" class="question-image" onerror="this.src='${{typeof PLACEHOLDER_IMAGE !== 'undefined' ? PLACEHOLDER_IMAGE : ''}}'">`;
            }}
            
            html += '<div class="quiz-options">';
            
            question.options.forEach((option, index) => {{
                const isSelected = userAnswers[currentQuestion] === index;
                html += `
                    <label class="quiz-option ${{isSelected ? 'selected' : ''}}" onclick="selectAnswer(${{index}})">
                        <input type="radio" name="q${{currentQuestion}}" value="${{index}}" 
                            ${{isSelected ? 'checked' : ''}} style="margin-right: 10px;">
                        ${{String.fromCharCode(65 + index)}}) ${{option}}
                    </label>
                `;
            }});
            
            html += '</div></div>';
            quizContent.innerHTML = html;
            
            // Update navigation buttons
            if (QUIZ_CONFIG.allowReview) {{
                document.getElementById('prevBtn').style.display = currentQuestion > 0 ? 'inline-block' : 'none';
            }}
            document.getElementById('nextBtn').style.display = currentQuestion < quizQuestions.length - 1 ? 'inline-block' : 'none';
            document.getElementById('submitBtn').style.display = currentQuestion === quizQuestions.length - 1 ? 'inline-block' : 'none';
            
            updateProgress();
        }}

        function selectAnswer(index) {{
            userAnswers[currentQuestion] = index;
            const options = document.querySelectorAll('.quiz-option');
            options.forEach((option, i) => {{
                option.classList.toggle('selected', i === index);
            }});
        }}

        function nextQuestion() {{
            if (currentQuestion < quizQuestions.length - 1) {{
                currentQuestion++;
                showQuestion();
            }}
        }}

        function prevQuestion() {{
            if (currentQuestion > 0) {{
                currentQuestion--;
                showQuestion();
            }}
        }}

        function updateProgress() {{
            const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
        }}

        function submitQuiz() {{
            if (timerInterval) {{
                clearInterval(timerInterval);
            }}
            
            if (!QUIZ_CONFIG.showResults) {{
                alert('Quiz submitted successfully!');
                location.reload();
                return;
            }}
            
            let correct = 0;
            let resultHTML = '<div style="margin-top: 20px;">';
            
            quizQuestions.forEach((question, index) => {{
                const userAnswer = userAnswers[index];
                const isCorrect = userAnswer === question.correct;
                if (isCorrect) correct++;
                
                resultHTML += `
                    <div class="result-item ${{isCorrect ? 'correct' : 'incorrect'}}">
                        <strong>Q${{index + 1}}: ${{isCorrect ? '✓ Correct' : '✗ Incorrect'}}</strong><br>
                        <p style="margin: 10px 0;">${{question.question}}</p>
                        <p style="color: #666;">Your answer: ${{userAnswer !== null ? question.options[userAnswer] : 'Not answered'}}</p>
                        ${{!isCorrect ? `<p style="color: #155724;">Correct answer: ${{question.options[question.correct]}}</p>` : ''}}
                        ${{QUIZ_CONFIG.showExplanations && question.explanation ? `<p style="font-style: italic; margin-top: 10px;">${{question.explanation}}</p>` : ''}}
                    </div>
                `;
            }});
            
            resultHTML += '</div>';
            
            const percentage = Math.round((correct / quizQuestions.length) * 100);
            const passed = percentage >= QUIZ_CONFIG.passThreshold;
            
            let feedback = '';
            let color = '';
            
            if (percentage >= 90) {{
                feedback = '🎉 Outstanding!';
                color = '#28a745';
            }} else if (percentage >= 80) {{
                feedback = '🎉 Excellent work!';
                color = '#28a745';
            }} else if (percentage >= QUIZ_CONFIG.passThreshold) {{
                feedback = '👍 Good job! You passed!';
                color = '#ffc107';
            }} else {{
                feedback = '📚 Keep studying and try again!';
                color = '#dc3545';
            }}
            
            document.getElementById('quizScore').innerHTML = `
                <div style="font-size: 48px; margin: 20px 0;">${{percentage}}%</div>
                <div>You scored ${{correct}} out of ${{quizQuestions.length}}</div>
                <div style="font-size: 20px; color: ${{color}}; margin-top: 15px;">${{feedback}}</div>
                <div style="margin-top: 10px; font-size: 16px;">
                    Pass Threshold: ${{QUIZ_CONFIG.passThreshold}}% - 
                    <strong>${{passed ? 'PASSED ✓' : 'NOT PASSED ✗'}}</strong>
                </div>
            `;
            document.getElementById('resultDetails').innerHTML = resultHTML;

            // Show certificate if enabled and passed
            if (QUIZ_CONFIG.enableCertificate && passed) {{
                const userName = prompt('Congratulations! Enter your name for the certificate:') || 'Participant';
    
                // Generate certificate ID here
                const timestamp = Date.now().toString();
                const random = Math.random().toString(36).substr(2, 4).toUpperCase();
                const certData = userName + QUIZ_CONFIG.quizTitle + percentage + timestamp + random;
                const certId = btoa(certData).replace(/[^A-Z0-9]/gi, '').substr(0, 12).toUpperCase();
    
                // Pass certId to the function
                const certHTML = generateProfessionalCertificate(userName, percentage, certId);
    
                const iframe = document.getElementById('certificateFrame');
                iframe.srcdoc = certHTML;
                document.getElementById('certificateWrapper').style.display = 'block';
            }}
            
            document.getElementById('quizContent').style.display = 'none';
            document.getElementById('quizResults').style.display = 'block';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'none';
            document.getElementById('prevBtn').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'inline-block';
            document.getElementById('timerDisplay').style.display = 'none';
            
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').textContent = '100%';
        }} 

        function generateProfessionalCertificate(name, score, certId) {{
            const date = new Date().toLocaleDateString('en-US', {{ year: 'numeric', month: 'long', day: 'numeric' }});
 
            let performance = 'Successful Completion';
            let sealColor = '#5B9BD5';
   
            if (score >= 95) {{
                performance = 'Outstanding Achievement';
                sealColor = '#FFD700';
            }} else if (score >= 90) {{
                performance = 'Excellent Performance';
                sealColor = '#C0C0C0';
            }} else if (score >= 80) {{
                performance = 'Superior Performance';
                sealColor = '#CD7F32';
            }}
    
            // Try to use logo if available, otherwise use placeholder
            const logoData = "{logo_base64}";
    
            return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Certificate - ${{name}}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Open+Sans:wght@400;600&display=swap');
        
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
                body {{
                    font-family: 'Open Sans', sans-serif;
                    background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }}
        
                .certificate {{
                    max-width: 1100px;
                    width: 95%;
                    min-height: 800px;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 30px 60px rgba(0,0,0,0.3);
                    position: relative;
                    padding: 60px;
                    margin: 20px auto;
                    border: 3px solid ${{sealColor}};
                }}
        
                .header {{
                    background: linear-gradient(135deg, #2C5282 0%, #5B9BD5 100%);
                    margin: -60px -60px 40px;
                    padding: 40px;
                    text-align: center;
                    border-radius: 17px 17px 0 0;
                }}
        
                .logo {{
                    max-width: 200px;
                    height: auto;
                    margin-bottom: 20px;
                }}
        
                h1 {{
                    font-family: 'Playfair Display', serif;
                    font-size: 42px;
                    color: white;
                    text-align: center;
                    margin-bottom: 10px;
                }}
        
                .recipient {{
                    font-family: 'Playfair Display', serif;
                    font-size: 56px;
                    color: #2C5282;
                    text-align: center;
                    margin: 40px 0;
                    padding-bottom: 20px;
                    border-bottom: 3px solid ${{sealColor}};
                }}
        
                .details {{
                    text-align: center;
                    font-size: 20px;
                    line-height: 2;
                    color: #333;
                    margin: 40px 0;
                }}
        
                .performance {{
                    background: ${{sealColor}};
                    color: white;
                    padding: 15px 40px;
                    border-radius: 30px;
                    display: inline-block;
                    font-weight: bold;
                    font-size: 20px;
                    margin: 20px 0;
                }}
        
                .score {{
                    font-size: 60px;
                    color: ${{sealColor}};
                    font-weight: bold;
                    margin: 20px 0;
                }}
        
                .footer {{
                    display: flex;
                    justify-content: space-between;
                    margin-top: 60px;
                    padding-top: 40px;
                    border-top: 2px solid #ddd;
                }}
        
                .signature {{
                    text-align: center;
                    flex: 1;
                }}
        
                .signature-line {{
                    width: 200px;
                    border-bottom: 2px solid #333;
                    margin: 0 auto 10px;
                    height: 40px;
                }}
        
                .meta {{
                    background: #2C5282;
                    color: white;
                    padding: 20px;
                    margin: 60px -60px -60px;
                    border-radius: 0 0 17px 17px;
                    text-align: center;
                }}
        
                @media print {{
                    body {{
                        background: white;
                    }}
                    .certificate {{
                        box-shadow: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="certificate">
                <div class="header">
                    <img src="${{logoData}}" alt="Company Logo" class="logo">
                    <h1>Certificate of Achievement</h1>
                </div>
                <div class="details">This certifies that</div>
                <div class="recipient">${{name}}</div>
                <div class="details">
                    has successfully completed<br>
                    <strong>"${{QUIZ_CONFIG.quizTitle || 'Professional Assessment'}}"</strong><br>
                    <div class="performance">${{performance}}</div><br>
                    <div class="score">${{score}}%</div>
                </div>
                <div class="footer">
                    <div class="signature">
                        <div class="signature-line"></div>
                        <div>${{QUIZ_CONFIG.author || 'Instructor'}}</div>
                    </div>
                    <div class="signature">
                        <div class="signature-line"></div>
                        <div>${{date}}</div>
                    </div>
                    <div class="signature">
                        <div class="signature-line"></div>
                        <div>Michael Kaminski<br>CodeEO, Multiaxis LLC</div>
                    </div>
                </div>
                <div class="meta">
                    <div>©2025 ${{QUIZ_CONFIG.company}}. All rights reserved.</div>
                    <div>The Power of MULTIAXIS® with the Intelligence of ARLO™</div>
                    <div style="margin-top: 10px; font-size: 12px;">
                        Certificate ID: ${{certId}}<br>
                        To register this certificate for verification, email this ID along with your name to:<br>
                        <strong>support@multiaxis.llc</strong><br>
                        Once registered, verify at: www.multiaxis.ai/verify
                    </div>
                </div>
            </div>
        </body>
        </html>`;
        }}

        function downloadCertificate() {{
            const iframe = document.getElementById('certificateFrame');
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const certificateHTML = iframeDoc.documentElement.outerHTML;
    
            const blob = new Blob([certificateHTML], {{type: 'text/html;charset=utf-8'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `certificate_${{Date.now()}}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}

        function printCertificate() {{
            const iframe = document.getElementById('certificateFrame');
            iframe.contentWindow.print();
        }}
            
        function restartQuiz() {{
            currentQuestion = 0;
            userAnswers = [];
            timeRemaining = QUIZ_CONFIG.timerMinutes * 60;
            document.getElementById('quizContent').style.display = 'block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('certificateWrapper').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'none';
            startQuiz();
        }}
    </script>
</body>
</html>'''
            
            # Format author and company lines
            author_line = f"Created by: {author}" if author else ""
            company_line = f"Organization: {company}" if company else ""
            footer_text = f"©2025 {company}. All rights reserved | Generated with Quiz Generator - Multiaxis Intelligence"
            
            logging.info("Formatting HTML with template values")
            
            # Safely convert questions to JSON
            try:
                questions_json = json.dumps(self.questions)
                logging.debug(f"Questions JSON generated, length: {len(questions_json)}")
            except Exception as e:
                logging.error(f"Error converting questions to JSON: {e}")
                logging.error(f"Questions data: {self.questions}")
                raise
            
            formatted_html = html_template.format(
                title=self.quiz_title,
                logo_base64=logo_base64,
                description=self.quiz_description,
                author=author,
                company=company,
                author_line=author_line,
                company_line=company_line,
                footer_text=footer_text,
                questions_json=questions_json,
                quiz_config=quiz_config,
                image_constants=image_constants if has_images else ""
            )
            
            logging.info(f"Writing HTML to file: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_html)
            
            msg = f"Generated clean HTML quiz with {len(self.questions)} questions"
            if has_images:
                msg += "\n⚠️ See answer key file for image setup instructions"
            
            logging.info(f"HTML generation successful: {msg}")
            return True, msg
            
        except Exception as e:
            error_msg = f"Error generating HTML: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return False, error_msg
        """Generate clean HTML quiz file without image instructions."""
        if not self.questions:
            return False, "No questions to generate"
        
        try:
            # Check if any questions have images
            has_images = any(q.get('image', '') for q in self.questions)
            
            # Get settings from parent app if available
            author = getattr(self, 'author', '')
            company = getattr(self, 'company', 'Multiaxis Intelligence')
            show_results = getattr(self, 'show_results', True)
            show_explanations = getattr(self, 'show_explanations', True)
            allow_review = getattr(self, 'allow_review', True)
            randomize = getattr(self, 'randomize', False)
            timer_minutes = getattr(self, 'timer_minutes', 0)
            pass_threshold = getattr(self, 'pass_threshold', 70)
            enable_certificate = getattr(self, 'enable_certificate', False)
            
            # Generate image constants section if needed (but cleaner)
            image_constants = ""
            if has_images:
                image_constants = """
    <script>
        // Image configuration - see answer key for setup instructions
        const IMAGE_PATHS = {"""
                
                # Collect unique image filenames
                image_files = set()
                for i, q in enumerate(self.questions, 1):
                    if q.get('image'):
                        image_files.add(q['image'])
                
                # Add image path entries
                for img in sorted(image_files):
                    image_constants += f'\n            "{img}": "{img}",'
                
                image_constants = image_constants.rstrip(',')
                image_constants += """
        };
        
        // Placeholder image
        const PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'%3E%3Crect width='1024' height='1024' fill='%23f0f0f0'/%3E%3Ctext x='512' y='512' font-family='Arial' font-size='48' fill='%23999' text-anchor='middle' dominant-baseline='middle'%3EImage Loading...%3C/text%3E%3C/svg%3E";
        
        function getImagePath(filename) {
            return IMAGE_PATHS[filename] || PLACEHOLDER_IMAGE;
        }
    </script>
"""
            
            # Quiz configuration script
            quiz_config = f"""
    <script>
        // Quiz Configuration
        const QUIZ_CONFIG = {{
            showResults: {str(show_results).lower()},
            showExplanations: {str(show_explanations).lower()},
            allowReview: {str(allow_review).lower()},
            randomizeQuestions: {str(randomize).lower()},
            timerMinutes: {timer_minutes},
            passThreshold: {pass_threshold},
            enableCertificate: {str(enable_certificate).lower()},
            author: "{author}",
            company: "{company}",
            quizTitle: "{self.quiz_title}", 
            copyright: "©2025 {company}. All rights reserved"
        }};
        
        let timeRemaining = QUIZ_CONFIG.timerMinutes * 60; // Convert to seconds
        let timerInterval = null;
    </script>
"""
            
            html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="{author}">
    <meta name="company" content="{company}">
    <meta name="generator" content="Quiz Generator - Multiaxis Intelligence">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            min-height: 100vh;
        }}
        .quiz-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px auto;
            max-width: 900px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2C5282;
            text-align: center;
            margin-bottom: 10px;
        }}
        .quiz-description {{
            text-align: center;
            color: #666;
            margin-bottom: 10px;
        }}
        .quiz-meta {{
            text-align: center;
            color: #999;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .timer-display {{
            text-align: center;
            font-size: 24px;
            color: #2C5282;
            font-weight: bold;
            margin: 15px 0;
            padding: 10px;
            background: #f0f4ff;
            border-radius: 8px;
            display: none;
        }}
        .timer-display.warning {{
            color: #ffc107;
            background: #fff3cd;
        }}
        .timer-display.danger {{
            color: #dc3545;
            background: #f8d7da;
        }}
        .quiz-question {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #5B9BD5;
        }}
        .quiz-question h4 {{
            color: #2C5282;
            margin-bottom: 15px;
        }}
        .difficulty-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .difficulty-easy {{
            background: #d4edda;
            color: #155724;
        }}
        .difficulty-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        .difficulty-hard {{
            background: #f8d7da;
            color: #721c24;
        }}
        .question-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            margin: 20px auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .quiz-options {{
            margin: 15px 0;
        }}
        .quiz-option {{
            display: block;
            margin: 10px 0;
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .quiz-option:hover {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            transform: translateX(5px);
        }}
        .quiz-option.selected {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            font-weight: 600;
        }}
        .quiz-button {{
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            transition: transform 0.2s;
        }}
        .quiz-button:hover {{
            transform: scale(1.05);
        }}
        .quiz-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: scale(1);
        }}
        .quiz-results {{
            padding: 30px;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border-radius: 15px;
            margin: 20px 0;
            display: none;
        }}
        .quiz-score {{
            font-size: 28px;
            color: #2C5282;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .quiz-progress {{
            background: #e2e8f0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .quiz-progress-bar {{
            background: linear-gradient(90deg, #5B9BD5 0%, #2C5282 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .result-item {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
        }}
        .result-item.correct {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .result-item.incorrect {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .certificate {{
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            border: 3px solid #ffd700;
            border-radius: 15px;
            padding: 40px;
            margin: 30px auto;
            max-width: 600px;
            text-align: center;
            display: none;
        }}
        .certificate h2 {{
            color: #2C5282;
            margin-bottom: 20px;
        }}
        .certificate-name {{
            font-size: 28px;
            font-weight: bold;
            color: #2C5282;
            margin: 20px 0;
        }}
        .certificate-score {{
            font-size: 24px;
            color: #155724;
            margin: 15px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #666;
            font-size: 12px;
        }}
    </style>
    {quiz_config}
    {image_constants}
</head>
<body>
    <div class="quiz-container">
        <h1>{title}</h1>
        <p class="quiz-description">{description}</p>
        <div class="quiz-meta">
            {author_line}
            {company_line}
        </div>
        
        <div class="timer-display" id="timerDisplay">
            Time Remaining: <span id="timerValue">00:00</span>
        </div>
        
        <div class="quiz-progress">
            <div class="quiz-progress-bar" id="progressBar">0%</div>
        </div>

        <div id="quizContent"></div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="quiz-button" id="prevBtn" onclick="prevQuestion()" style="display:none;">← Previous</button>
            <button class="quiz-button" id="nextBtn" onclick="nextQuestion()" style="display:none;">Next →</button>
            <button class="quiz-button" id="startBtn" onclick="startQuiz()">Start Quiz</button>
            <button class="quiz-button" id="submitBtn" onclick="submitQuiz()" style="display:none;">Submit Quiz</button>
            <button class="quiz-button" id="restartBtn" onclick="restartQuiz()" style="display:none;">Restart Quiz</button>
        </div>

        <div class="quiz-results" id="quizResults">
            <h2 style="text-align: center; color: #2C5282;">Quiz Results</h2>
            <div class="quiz-score" id="quizScore"></div>
            <div id="resultDetails"></div>
        </div>
        
        <div class="certificate" id="certificate">
            <h2>🏆 Certificate of Completion 🏆</h2>
            <p>This certifies that</p>
            <div class="certificate-name" id="certificateName">[Name]</div>
            <p>has successfully completed</p>
            <div style="font-size: 20px; margin: 15px 0;"><strong>{title}</strong></div>
            <div class="certificate-score" id="certificateScore"></div>
            <div style="margin-top: 30px; color: #666;">
                <p>{company}</p>
                <p id="certificateDate"></p>
            </div>
        </div>
        
        <div class="footer">
            {footer_text}
        </div>
    </div>

    <script>
        let quizQuestions = {questions_json};
        let currentQuestion = 0;
        let userAnswers = [];
        let quizStarted = false;
        
        // Apply randomization if configured
        if (QUIZ_CONFIG.randomizeQuestions) {{
            quizQuestions = quizQuestions.sort(() => Math.random() - 0.5);
        }}
        
        function startTimer() {{
            if (QUIZ_CONFIG.timerMinutes > 0) {{
                document.getElementById('timerDisplay').style.display = 'block';
                updateTimerDisplay();
                
                timerInterval = setInterval(() => {{
                    timeRemaining--;
                    updateTimerDisplay();
                    
                    if (timeRemaining <= 0) {{
                        clearInterval(timerInterval);
                        alert('Time is up! Submitting quiz...');
                        submitQuiz();
                    }}
                }}, 1000);
            }}
        }}
        
        function updateTimerDisplay() {{
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            const display = `${{String(minutes).padStart(2, '0')}}:${{String(seconds).padStart(2, '0')}}`;
            document.getElementById('timerValue').textContent = display;
            
            const timerDiv = document.getElementById('timerDisplay');
            if (timeRemaining < 60) {{
                timerDiv.classList.add('danger');
            }} else if (timeRemaining < 300) {{
                timerDiv.classList.add('warning');
            }}
        }}

        function startQuiz() {{
            quizStarted = true;
            currentQuestion = 0;
            userAnswers = new Array(quizQuestions.length).fill(null);
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'inline-block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('certificateWrapper').style.display = 'none';
            startTimer();
            showQuestion();
        }}

        function showQuestion() {{
            const question = quizQuestions[currentQuestion];
            const quizContent = document.getElementById('quizContent');
            
            let difficultyBadge = '';
            if (question.difficulty) {{
                const diffClass = `difficulty-${{question.difficulty.toLowerCase()}}`;
                difficultyBadge = `<span class="difficulty-badge ${{diffClass}}">${{question.difficulty}}</span>`;
            }}
            
            let html = `
                <div class="quiz-question">
                    <h4>Question ${{currentQuestion + 1}} of ${{quizQuestions.length}} ${{difficultyBadge}}</h4>
                    <p style="font-size: 18px; margin: 20px 0;">${{question.question}}</p>
            `;
            
            // Add image if present
            if (question.image) {{
                const imagePath = typeof getImagePath === 'function' ? getImagePath(question.image) : question.image;
                html += `<img src="${{imagePath}}" alt="Question ${{currentQuestion + 1}} Image" class="question-image" onerror="this.src='${{typeof PLACEHOLDER_IMAGE !== 'undefined' ? PLACEHOLDER_IMAGE : ''}}'">`;
            }}
            
            html += '<div class="quiz-options">';
            
            question.options.forEach((option, index) => {{
                const isSelected = userAnswers[currentQuestion] === index;
                html += `
                    <label class="quiz-option ${{isSelected ? 'selected' : ''}}" onclick="selectAnswer(${{index}})">
                        <input type="radio" name="q${{currentQuestion}}" value="${{index}}" 
                            ${{isSelected ? 'checked' : ''}} style="margin-right: 10px;">
                        ${{String.fromCharCode(65 + index)}}) ${{option}}
                    </label>
                `;
            }});
            
            html += '</div></div>';
            quizContent.innerHTML = html;
            
            // Update navigation buttons
            if (QUIZ_CONFIG.allowReview) {{
                document.getElementById('prevBtn').style.display = currentQuestion > 0 ? 'inline-block' : 'none';
            }}
            document.getElementById('nextBtn').style.display = currentQuestion < quizQuestions.length - 1 ? 'inline-block' : 'none';
            document.getElementById('submitBtn').style.display = currentQuestion === quizQuestions.length - 1 ? 'inline-block' : 'none';
            
            updateProgress();
        }}

        function selectAnswer(index) {{
            userAnswers[currentQuestion] = index;
            const options = document.querySelectorAll('.quiz-option');
            options.forEach((option, i) => {{
                option.classList.toggle('selected', i === index);
            }});
        }}

        function nextQuestion() {{
            if (currentQuestion < quizQuestions.length - 1) {{
                currentQuestion++;
                showQuestion();
            }}
        }}

        function prevQuestion() {{
            if (currentQuestion > 0) {{
                currentQuestion--;
                showQuestion();
            }}
        }}

        function updateProgress() {{
            const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
        }}

        function submitQuiz() {{
            if (timerInterval) {{
                clearInterval(timerInterval);
            }}
            
            if (!QUIZ_CONFIG.showResults) {{
                alert('Quiz submitted successfully!');
                location.reload();
                return;
            }}
            
            let correct = 0;
            let resultHTML = '<div style="margin-top: 20px;">';
            
            quizQuestions.forEach((question, index) => {{
                const userAnswer = userAnswers[index];
                const isCorrect = userAnswer === question.correct;
                if (isCorrect) correct++;
                
                resultHTML += `
                    <div class="result-item ${{isCorrect ? 'correct' : 'incorrect'}}">
                        <strong>Q${{index + 1}}: ${{isCorrect ? '✓ Correct' : '✗ Incorrect'}}</strong><br>
                        <p style="margin: 10px 0;">${{question.question}}</p>
                        <p style="color: #666;">Your answer: ${{userAnswer !== null ? question.options[userAnswer] : 'Not answered'}}</p>
                        ${{!isCorrect ? `<p style="color: #155724;">Correct answer: ${{question.options[question.correct]}}</p>` : ''}}
                        ${{QUIZ_CONFIG.showExplanations && question.explanation ? `<p style="font-style: italic; margin-top: 10px;">${{question.explanation}}</p>` : ''}}
                    </div>
                `;
            }});
            
            resultHTML += '</div>';
            
            const percentage = Math.round((correct / quizQuestions.length) * 100);
            const passed = percentage >= QUIZ_CONFIG.passThreshold;
            
            let feedback = '';
            let color = '';
            
            if (percentage >= 90) {{
                feedback = '🎉 Outstanding!';
                color = '#28a745';
            }} else if (percentage >= 80) {{
                feedback = '🎉 Excellent work!';
                color = '#28a745';
            }} else if (percentage >= QUIZ_CONFIG.passThreshold) {{
                feedback = '👍 Good job! You passed!';
                color = '#ffc107';
            }} else {{
                feedback = '📚 Keep studying and try again!';
                color = '#dc3545';
            }}
            
            document.getElementById('quizScore').innerHTML = `
                <div style="font-size: 48px; margin: 20px 0;">${{percentage}}%</div>
                <div>You scored ${{correct}} out of ${{quizQuestions.length}}</div>
                <div style="font-size: 20px; color: ${{color}}; margin-top: 15px;">${{feedback}}</div>
                <div style="margin-top: 10px; font-size: 16px;">
                    Pass Threshold: ${{QUIZ_CONFIG.passThreshold}}% - 
                    <strong>${{passed ? 'PASSED ✓' : 'NOT PASSED ✗'}}</strong>
                </div>
            `;
            document.getElementById('resultDetails').innerHTML = resultHTML;
            
            // Show certificate if enabled and passed
            if (QUIZ_CONFIG.enableCertificate && passed) {{
                const userName = prompt('Congratulations! Enter your name for the certificate:') || 'Participant';
    
                // Generate certificate ID here
                const timestamp = Date.now().toString();
                const random = Math.random().toString(36).substr(2, 4).toUpperCase();
                const certData = userName + QUIZ_CONFIG.quizTitle + percentage + timestamp + random;
                const certId = btoa(certData).replace(/[^A-Z0-9]/gi, '').substr(0, 12).toUpperCase();
    
                // Pass certId to the function
                const certHTML = generateProfessionalCertificate(userName, percentage, certId);
    
                const iframe = document.getElementById('certificateFrame');
                iframe.srcdoc = certHTML;
                document.getElementById('certificateWrapper').style.display = 'block';
            }}
            
            document.getElementById('quizContent').style.display = 'none';
            document.getElementById('quizResults').style.display = 'block';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'none';
            document.getElementById('prevBtn').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'inline-block';
            document.getElementById('timerDisplay').style.display = 'none';
            
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').textContent = '100%';
        }} 

        function restartQuiz() {{
            currentQuestion = 0;
            userAnswers = [];
            timeRemaining = QUIZ_CONFIG.timerMinutes * 60;
            document.getElementById('quizContent').style.display = 'block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('certificateWrapper').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'none';
            startQuiz();
        }}
    </script>
</body>
</html>'''
            
            # Format author and company lines
            author_line = f"Created by: {author}" if author else ""
            company_line = f"Organization: {company}" if company else ""
            footer_text = f"©2025 {company}. All rights reserved | Generated with Quiz Generator - Multiaxis Intelligence"
            
            formatted_html = html_template.format(
                title=self.quiz_title,
                description=self.quiz_description,
                author=author,
                company=company,
                author_line=author_line,
                company_line=company_line,
                footer_text=footer_text,
                questions_json=json.dumps(self.questions),
                quiz_config=quiz_config,
                image_constants=image_constants if has_images else ""
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_html)
            
            msg = f"Generated clean HTML quiz with {len(self.questions)} questions"
            if has_images:
                msg += "\n⚠️ See answer key file for image setup instructions"
            
            return True, msg
        except Exception as e:
            return False, f"Error generating HTML: {str(e)}"
        """Generate HTML quiz file with image support and company branding."""
        if not self.questions:
            return False, "No questions to generate"
        
        try:
            # Check if any questions have images
            has_images = any(q.get('image', '') for q in self.questions)
            
            # Get settings from parent app if available
            author = getattr(self, 'author', '')
            company = getattr(self, 'company', 'Multiaxis Intelligence')
            show_results = getattr(self, 'show_results', True)
            show_explanations = getattr(self, 'show_explanations', True)
            allow_review = getattr(self, 'allow_review', True)
            randomize = getattr(self, 'randomize', False)
            
            # Generate image constants section if needed
            image_constants = ""
            if has_images:
                image_constants = """
    <!-- ============================================= -->
    <!-- IMAGE CONFIGURATION SECTION                   -->
    <!-- Edit these paths to match your image files    -->
    <!-- Images should be 1024x1024 for best display   -->
    <!-- Place images in same folder as HTML file      -->
    <!-- ============================================= -->
    <script>
        const IMAGE_PATHS = {
            // Default image paths - edit these to match your files
            // Format: "filename": "path/to/image.png"
            """
                
                # Collect unique image filenames
                image_files = set()
                for i, q in enumerate(self.questions, 1):
                    if q.get('image'):
                        image_files.add(q['image'])
                    elif q.get('image') == "auto":
                        image_files.add(f"q{i}.png")
                
                # Add image path entries
                for img in sorted(image_files):
                    image_constants += f'\n            "{img}": "{img}",  // Question image'
                
                image_constants = image_constants.rstrip(',')
                image_constants += """
            
            // Placeholder image (displays when image not found)
            "placeholder": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'%3E%3Crect width='1024' height='1024' fill='%23f0f0f0'/%3E%3Ctext x='512' y='512' font-family='Arial' font-size='48' fill='%23999' text-anchor='middle' dominant-baseline='middle'%3EImage Placeholder%3C/text%3E%3Ctext x='512' y='570' font-family='Arial' font-size='24' fill='%23999' text-anchor='middle'%3E1024 x 1024%3C/text%3E%3C/svg%3E"
        };
        
        // Function to get image path with fallback
        function getImagePath(filename) {
            return IMAGE_PATHS[filename] || IMAGE_PATHS["placeholder"];
        }
    </script>
"""
            
            # Quiz configuration script
            quiz_config = f"""
    <script>
        // Quiz Configuration
        const QUIZ_CONFIG = {{
            showResults: {str(show_results).lower()},
            showExplanations: {str(show_explanations).lower()},
            allowReview: {str(allow_review).lower()},
            randomizeQuestions: {str(randomize).lower()},
            author: "{author}",
            company: "{company}",
            quizTitle: "{self.quiz_title}", 
            copyright: "©2025 {company}. All rights reserved"
        }};
    </script>
"""
            
            html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="{author}">
    <meta name="company" content="{company}">
    <meta name="generator" content="Quiz Generator - Multiaxis Intelligence">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            min-height: 100vh;
        }}
        .quiz-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px auto;
            max-width: 900px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2C5282;
            text-align: center;
            margin-bottom: 10px;
        }}
        .quiz-description {{
            text-align: center;
            color: #666;
            margin-bottom: 10px;
        }}
        .quiz-meta {{
            text-align: center;
            color: #999;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .quiz-question {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #5B9BD5;
        }}
        .quiz-question h4 {{
            color: #2C5282;
            margin-bottom: 15px;
        }}
        .question-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            margin: 20px auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .quiz-options {{
            margin: 15px 0;
        }}
        .quiz-option {{
            display: block;
            margin: 10px 0;
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .quiz-option:hover {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            transform: translateX(5px);
        }}
        .quiz-option.selected {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            font-weight: 600;
        }}
        .quiz-button {{
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            transition: transform 0.2s;
        }}
        .quiz-button:hover {{
            transform: scale(1.05);
        }}
        .quiz-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: scale(1);
        }}
        .quiz-results {{
            padding: 30px;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border-radius: 15px;
            margin: 20px 0;
            display: none;
        }}
        .quiz-score {{
            font-size: 28px;
            color: #2C5282;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .quiz-progress {{
            background: #e2e8f0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .quiz-progress-bar {{
            background: linear-gradient(90deg, #5B9BD5 0%, #2C5282 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .result-item {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
        }}
        .result-item.correct {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .result-item.incorrect {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .image-note {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            margin: 20px 0;
            border-radius: 5px;
            font-size: 14px;
            color: #856404;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #666;
            font-size: 12px;
        }}
    </style>
    {quiz_config}
    {image_constants}
</head>
<body>
    <div class="quiz-container">
        <h1>{title}</h1>
        <p class="quiz-description">{description}</p>
        <div class="quiz-meta">
            {author_line}
            {company_line}
        </div>
        {image_section}
        
        <div class="quiz-progress">
            <div class="quiz-progress-bar" id="progressBar">0%</div>
        </div>

        <div id="quizContent"></div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="quiz-button" id="prevBtn" onclick="prevQuestion()" style="display:none;">← Previous</button>
            <button class="quiz-button" id="nextBtn" onclick="nextQuestion()" style="display:none;">Next →</button>
            <button class="quiz-button" id="startBtn" onclick="startQuiz()">Start Quiz</button>
            <button class="quiz-button" id="submitBtn" onclick="submitQuiz()" style="display:none;">Submit Quiz</button>
            <button class="quiz-button" id="restartBtn" onclick="restartQuiz()" style="display:none;">Restart Quiz</button>
        </div>

        <div class="quiz-results" id="quizResults">
            <h2 style="text-align: center; color: #2C5282;">Quiz Results</h2>
            <div class="quiz-score" id="quizScore"></div>
            <div id="resultDetails"></div>
        </div>
        
        <div class="footer">
            {footer_text}
        </div>
    </div>

    <script>
        let quizQuestions = {questions_json};
        let currentQuestion = 0;
        let userAnswers = [];
        let quizStarted = false;
        
        // Apply randomization if configured
        if (QUIZ_CONFIG.randomizeQuestions) {{
            quizQuestions = quizQuestions.sort(() => Math.random() - 0.5);
        }}

        function startQuiz() {{
            quizStarted = true;
            currentQuestion = 0;
            userAnswers = new Array(quizQuestions.length).fill(null);
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'inline-block';
            document.getElementById('quizResults').style.display = 'none';
            showQuestion();
        }}

        function showQuestion() {{
            const question = quizQuestions[currentQuestion];
            const quizContent = document.getElementById('quizContent');
            
            let html = `
                <div class="quiz-question">
                    <h4>Question ${{currentQuestion + 1}} of ${{quizQuestions.length}}</h4>
                    <p style="font-size: 18px; margin: 20px 0;">${{question.question}}</p>
            `;
            
            // Add image if present
            if (question.image) {{
                const imagePath = typeof getImagePath === 'function' ? getImagePath(question.image) : question.image;
                html += `<img src="${{imagePath}}" alt="Question ${{currentQuestion + 1}} Image" class="question-image" onerror="this.src='${{typeof getImagePath === 'function' ? getImagePath('placeholder') : ''}}'">`;
            }}
            
            html += '<div class="quiz-options">';
            
            question.options.forEach((option, index) => {{
                const isSelected = userAnswers[currentQuestion] === index;
                html += `
                    <label class="quiz-option ${{isSelected ? 'selected' : ''}}" onclick="selectAnswer(${{index}})">
                        <input type="radio" name="q${{currentQuestion}}" value="${{index}}" 
                            ${{isSelected ? 'checked' : ''}} style="margin-right: 10px;">
                        ${{String.fromCharCode(65 + index)}}) ${{option}}
                    </label>
                `;
            }});
            
            html += '</div></div>';
            quizContent.innerHTML = html;
            
            // Update navigation buttons
            if (QUIZ_CONFIG.allowReview) {{
                document.getElementById('prevBtn').style.display = currentQuestion > 0 ? 'inline-block' : 'none';
            }}
            document.getElementById('nextBtn').style.display = currentQuestion < quizQuestions.length - 1 ? 'inline-block' : 'none';
            document.getElementById('submitBtn').style.display = currentQuestion === quizQuestions.length - 1 ? 'inline-block' : 'none';
            
            updateProgress();
        }}

        function selectAnswer(index) {{
            userAnswers[currentQuestion] = index;
            const options = document.querySelectorAll('.quiz-option');
            options.forEach((option, i) => {{
                option.classList.toggle('selected', i === index);
            }});
        }}

        function nextQuestion() {{
            if (currentQuestion < quizQuestions.length - 1) {{
                currentQuestion++;
                showQuestion();
            }}
        }}

        function prevQuestion() {{
            if (currentQuestion > 0) {{
                currentQuestion--;
                showQuestion();
            }}
        }}

        function updateProgress() {{
            const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
        }}

        function submitQuiz() {{
            if (!QUIZ_CONFIG.showResults) {{
                alert('Quiz submitted successfully!');
                location.reload();
                return;
            }}
            
            let correct = 0;
            let resultHTML = '<div style="margin-top: 20px;">';
            
            quizQuestions.forEach((question, index) => {{
                const userAnswer = userAnswers[index];
                const isCorrect = userAnswer === question.correct;
                if (isCorrect) correct++;
                
                resultHTML += `
                    <div class="result-item ${{isCorrect ? 'correct' : 'incorrect'}}">
                        <strong>Q${{index + 1}}: ${{isCorrect ? '✓ Correct' : '✗ Incorrect'}}</strong><br>
                        <p style="margin: 10px 0;">${{question.question}}</p>
                        <p style="color: #666;">Your answer: ${{userAnswer !== null ? question.options[userAnswer] : 'Not answered'}}</p>
                        ${{!isCorrect ? `<p style="color: #155724;">Correct answer: ${{question.options[question.correct]}}</p>` : ''}}
                        ${{QUIZ_CONFIG.showExplanations && question.explanation ? `<p style="font-style: italic; margin-top: 10px;">${{question.explanation}}</p>` : ''}}
                    </div>
                `;
            }});
            
            resultHTML += '</div>';
            
            const percentage = Math.round((correct / quizQuestions.length) * 100);
            let feedback = '';
            let color = '';
            
            if (percentage >= 80) {{
                feedback = '🎉 Excellent work!';
                color = '#28a745';
            }} else if (percentage >= 60) {{
                feedback = '👍 Good effort! Review the missed topics.';
                color = '#ffc107';
            }} else {{
                feedback = '📚 Keep studying and try again!';
                color = '#dc3545';
            }}
            
            document.getElementById('quizScore').innerHTML = `
                <div style="font-size: 48px; margin: 20px 0;">${{percentage}}%</div>
                <div>You scored ${{correct}} out of ${{quizQuestions.length}}</div>
                <div style="font-size: 20px; color: ${{color}}; margin-top: 15px;">${{feedback}}</div>
            `;
            document.getElementById('resultDetails').innerHTML = resultHTML;
            
            document.getElementById('quizContent').style.display = 'none';
            document.getElementById('quizResults').style.display = 'block';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'none';
            document.getElementById('prevBtn').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'inline-block';
            
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').textContent = '100%';
        }}

        function restartQuiz() {{
            currentQuestion = 0;
            userAnswers = [];
            document.getElementById('quizContent').style.display = 'block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'none';
            startQuiz();
        }}
    </script>
</body>
</html>'''
            
            # Add image note if images are present
            image_note = ""
            if has_images:
                image_note = f'''<div class="image-note">
            <strong>📌 Image Setup Instructions:</strong><br>
            1. Place your images (1024x1024 recommended) in the same folder as this HTML file<br>
            2. Edit the IMAGE_PATHS section in the HTML source to match your filenames<br>
            3. Images expected: {', '.join(sorted(image_files))}<br>
            4. Images will display inline with questions
        </div>'''
            
            # Format author and company lines
            author_line = f"Created by: {author}" if author else ""
            company_line = f"Organization: {company}" if company else ""
            footer_text = f"©2025 {company}. All rights reserved | Generated with Quiz Generator - Multiaxis Intelligence"
            
            formatted_html = html_template.format(
                title=self.quiz_title,
                description=self.quiz_description,
                author=author,
                company=company,
                author_line=author_line,
                company_line=company_line,
                footer_text=footer_text,
                questions_json=json.dumps(self.questions),
                quiz_config=quiz_config,
                image_section=image_note,
                image_constants=image_constants if has_images else ""
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_html)
            
            return True, f"Generated HTML quiz with {len(self.questions)} questions" + (f" ({len(image_files)} with images)" if has_images else "")
        except Exception as e:
            return False, f"Error generating HTML: {str(e)}"
        """Generate HTML quiz file with image support."""
        if not self.questions:
            return False, "No questions to generate"
        
        try:
            # Check if any questions have images
            has_images = any(q.get('image', '') for q in self.questions)
            
            # Generate image constants section if needed
            image_constants = ""
            if has_images:
                image_constants = """
    <!-- ============================================= -->
    <!-- IMAGE CONFIGURATION SECTION                   -->
    <!-- Edit these paths to match your image files    -->
    <!-- Images should be 1024x1024 for best display   -->
    <!-- Place images in same folder as HTML file      -->
    <!-- ============================================= -->
    <script>
        const IMAGE_PATHS = {
            // Default image paths - edit these to match your files
            // Format: "filename": "path/to/image.png"
            """
                
                # Collect unique image filenames
                image_files = set()
                for i, q in enumerate(self.questions, 1):
                    if q.get('image'):
                        image_files.add(q['image'])
                    elif q.get('image') == "auto":
                        image_files.add(f"q{i}.png")
                
                # Add image path entries
                for img in sorted(image_files):
                    image_constants += f'\n            "{img}": "{img}",  // Question image'
                
                image_constants = image_constants.rstrip(',')
                image_constants += """
            
            // Placeholder image (displays when image not found)
            "placeholder": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'%3E%3Crect width='1024' height='1024' fill='%23f0f0f0'/%3E%3Ctext x='512' y='512' font-family='Arial' font-size='48' fill='%23999' text-anchor='middle' dominant-baseline='middle'%3EImage Placeholder%3C/text%3E%3Ctext x='512' y='570' font-family='Arial' font-size='24' fill='%23999' text-anchor='middle'%3E1024 x 1024%3C/text%3E%3C/svg%3E"
        };
        
        // Function to get image path with fallback
        function getImagePath(filename) {
            return IMAGE_PATHS[filename] || IMAGE_PATHS["placeholder"];
        }
    </script>
"""
            
            html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            min-height: 100vh;
        }}
        .quiz-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px auto;
            max-width: 900px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2C5282;
            text-align: center;
            margin-bottom: 10px;
        }}
        .quiz-description {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .quiz-question {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #5B9BD5;
        }}
        .quiz-question h4 {{
            color: #2C5282;
            margin-bottom: 15px;
        }}
        .question-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            margin: 20px auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .quiz-options {{
            margin: 15px 0;
        }}
        .quiz-option {{
            display: block;
            margin: 10px 0;
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .quiz-option:hover {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            transform: translateX(5px);
        }}
        .quiz-option.selected {{
            background: #f0f4ff;
            border-color: #5B9BD5;
            font-weight: 600;
        }}
        .quiz-button {{
            background: linear-gradient(135deg, #5B9BD5 0%, #2C5282 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            transition: transform 0.2s;
        }}
        .quiz-button:hover {{
            transform: scale(1.05);
        }}
        .quiz-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: scale(1);
        }}
        .quiz-results {{
            padding: 30px;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border-radius: 15px;
            margin: 20px 0;
            display: none;
        }}
        .quiz-score {{
            font-size: 28px;
            color: #2C5282;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .quiz-progress {{
            background: #e2e8f0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .quiz-progress-bar {{
            background: linear-gradient(90deg, #5B9BD5 0%, #2C5282 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .result-item {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
        }}
        .result-item.correct {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .result-item.incorrect {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .image-note {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            margin: 20px 0;
            border-radius: 5px;
            font-size: 14px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="quiz-container">
        <h1>{title}</h1>
        <p class="quiz-description">{description}</p>
        {image_section}
        
        <div class="quiz-progress">
            <div class="quiz-progress-bar" id="progressBar">0%</div>
        </div>

        <div id="quizContent"></div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="quiz-button" id="prevBtn" onclick="prevQuestion()" style="display:none;">← Previous</button>
            <button class="quiz-button" id="nextBtn" onclick="nextQuestion()" style="display:none;">Next →</button>
            <button class="quiz-button" id="startBtn" onclick="startQuiz()">Start Quiz</button>
            <button class="quiz-button" id="submitBtn" onclick="submitQuiz()" style="display:none;">Submit Quiz</button>
            <button class="quiz-button" id="restartBtn" onclick="restartQuiz()" style="display:none;">Restart Quiz</button>
        </div>

        <div class="quiz-results" id="quizResults">
            <h2 style="text-align: center; color: #2C5282;">Quiz Results</h2>
            <div class="quiz-score" id="quizScore"></div>
            <div id="resultDetails"></div>
        </div>
    </div>

    <script>
        const quizQuestions = {questions_json};
        let currentQuestion = 0;
        let userAnswers = [];
        let quizStarted = false;

        function startQuiz() {{
            quizStarted = true;
            currentQuestion = 0;
            userAnswers = new Array(quizQuestions.length).fill(null);
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'inline-block';
            document.getElementById('quizResults').style.display = 'none';
            showQuestion();
        }}

        function showQuestion() {{
            const question = quizQuestions[currentQuestion];
            const quizContent = document.getElementById('quizContent');
            
            let html = `
                <div class="quiz-question">
                    <h4>Question ${{currentQuestion + 1}} of ${{quizQuestions.length}}</h4>
                    <p style="font-size: 18px; margin: 20px 0;">${{question.question}}</p>
            `;
            
            // Add image if present
            if (question.image) {{
                const imagePath = typeof getImagePath === 'function' ? getImagePath(question.image) : question.image;
                html += `<img src="${{imagePath}}" alt="Question ${{currentQuestion + 1}} Image" class="question-image" onerror="this.src='${{typeof getImagePath === 'function' ? getImagePath('placeholder') : ''}}'">`;
            }}
            
            html += '<div class="quiz-options">';
            
            question.options.forEach((option, index) => {{
                const isSelected = userAnswers[currentQuestion] === index;
                html += `
                    <label class="quiz-option ${{isSelected ? 'selected' : ''}}" onclick="selectAnswer(${{index}})">
                        <input type="radio" name="q${{currentQuestion}}" value="${{index}}" 
                            ${{isSelected ? 'checked' : ''}} style="margin-right: 10px;">
                        ${{String.fromCharCode(65 + index)}}) ${{option}}
                    </label>
                `;
            }});
            
            html += '</div></div>';
            quizContent.innerHTML = html;
            
            document.getElementById('prevBtn').style.display = currentQuestion > 0 ? 'inline-block' : 'none';
            document.getElementById('nextBtn').style.display = currentQuestion < quizQuestions.length - 1 ? 'inline-block' : 'none';
            document.getElementById('submitBtn').style.display = currentQuestion === quizQuestions.length - 1 ? 'inline-block' : 'none';
            
            updateProgress();
        }}

        function selectAnswer(index) {{
            userAnswers[currentQuestion] = index;
            const options = document.querySelectorAll('.quiz-option');
            options.forEach((option, i) => {{
                option.classList.toggle('selected', i === index);
            }});
        }}

        function nextQuestion() {{
            if (currentQuestion < quizQuestions.length - 1) {{
                currentQuestion++;
                showQuestion();
            }}
        }}

        function prevQuestion() {{
            if (currentQuestion > 0) {{
                currentQuestion--;
                showQuestion();
            }}
        }}

        function updateProgress() {{
            const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
        }}

        function submitQuiz() {{
            let correct = 0;
            let resultHTML = '<div style="margin-top: 20px;">';
            
            quizQuestions.forEach((question, index) => {{
                const userAnswer = userAnswers[index];
                const isCorrect = userAnswer === question.correct;
                if (isCorrect) correct++;
                
                resultHTML += `
                    <div class="result-item ${{isCorrect ? 'correct' : 'incorrect'}}">
                        <strong>Q${{index + 1}}: ${{isCorrect ? '✓ Correct' : '✗ Incorrect'}}</strong><br>
                        <p style="margin: 10px 0;">${{question.question}}</p>
                        <p style="color: #666;">Your answer: ${{userAnswer !== null ? question.options[userAnswer] : 'Not answered'}}</p>
                        ${{!isCorrect ? `<p style="color: #155724;">Correct answer: ${{question.options[question.correct]}}</p>` : ''}}
                        ${{question.explanation ? `<p style="font-style: italic; margin-top: 10px;">${{question.explanation}}</p>` : ''}}
                    </div>
                `;
            }});
            
            resultHTML += '</div>';
            
            const percentage = Math.round((correct / quizQuestions.length) * 100);
            let feedback = '';
            let color = '';
            
            if (percentage >= 80) {{
                feedback = '🎉 Excellent work!';
                color = '#28a745';
            }} else if (percentage >= 60) {{
                feedback = '👍 Good effort! Review the missed topics.';
                color = '#ffc107';
            }} else {{
                feedback = '📚 Keep studying and try again!';
                color = '#dc3545';
            }}
            
            document.getElementById('quizScore').innerHTML = `
                <div style="font-size: 48px; margin: 20px 0;">${{percentage}}%</div>
                <div>You scored ${{correct}} out of ${{quizQuestions.length}}</div>
                <div style="font-size: 20px; color: ${{color}}; margin-top: 15px;">${{feedback}}</div>
            `;
            document.getElementById('resultDetails').innerHTML = resultHTML;
            
            document.getElementById('quizContent').style.display = 'none';
            document.getElementById('quizResults').style.display = 'block';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'none';
            document.getElementById('prevBtn').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'inline-block';
            
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').textContent = '100%';
        }}

        function restartQuiz() {{
            currentQuestion = 0;
            userAnswers = [];
            document.getElementById('quizContent').style.display = 'block';
            document.getElementById('quizResults').style.display = 'none';
            document.getElementById('restartBtn').style.display = 'none';
            startQuiz();
        }}
    </script>
</body>
</html>'''
            
            # Add image note if images are present
            image_note = ""
            if has_images:
                image_note = f'''<div class="image-note">
            <strong>📌 Image Setup Instructions:</strong><br>
            1. Place your images (1024x1024 recommended) in the same folder as this HTML file<br>
            2. Edit the IMAGE_PATHS section in the HTML source to match your filenames<br>
            3. Images expected: {', '.join(sorted(image_files))}<br>
            4. Images will display inline with questions
        </div>'''
            
            formatted_html = html_template.format(
                title=self.quiz_title,
                description=self.quiz_description,
                questions_json=json.dumps(self.questions),
                image_section=image_constants + image_note if has_images else ""
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_html)
            
            return True, f"Generated HTML quiz with {len(self.questions)} questions" + (f" ({len(image_files)} with images)" if has_images else "")
        except Exception as e:
            return False, f"Error generating HTML: {str(e)}"


    def generate_markdown(self, output_file: str):
        """Generate markdown answer file with image instructions."""
        try:
            # Get settings
            author = getattr(self, 'author', '')
            company = getattr(self, 'company', 'Multiaxis Intelligence')
            
            # Check for images
            image_files = {}
            for i, q in enumerate(self.questions, 1):
                if q.get('image'):
                    image_files[i] = q['image']
            
            md_content = f"# {self.quiz_title}\n\n"
            md_content += f"## {self.quiz_description}\n\n"
            
            # Add metadata
            if author:
                md_content += f"**Author:** {author}\n\n"
            if company:
                md_content += f"**Organization:** {company}\n\n"
            
            md_content += f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            md_content += "---\n\n"
            
            # Add image setup instructions if images are present
            if image_files:
                md_content += "## 📌 Image Setup Instructions\n\n"
                md_content += "This quiz requires the following image files to be placed in the same folder as the HTML file:\n\n"
                md_content += "| Question | Image File | Description |\n"
                md_content += "|----------|------------|-------------|\n"
                
                for q_num, img_file in sorted(image_files.items()):
                    question_text = self.questions[q_num-1]['question'][:50] + "..."
                    md_content += f"| Question {q_num} | `{img_file}` | {question_text} |\n"
                
                md_content += "\n**Image Specifications:**\n"
                md_content += "- Recommended size: 1024x1024 pixels\n"
                md_content += "- Format: PNG or JPG\n"
                md_content += "- Location: Same folder as the HTML quiz file\n\n"
                
                md_content += "**To Update Image Paths:**\n"
                md_content += "1. Open the HTML file in a text editor\n"
                md_content += "2. Find the `IMAGE_PATHS` section near the top\n"
                md_content += "3. Update the paths to match your file locations\n\n"
                md_content += "---\n\n"
            
            # Add questions and answers
            md_content += "## Questions and Answers\n\n"
            
            for i, q in enumerate(self.questions, 1):
                md_content += f"### Question {i}"
                
                # Add difficulty if present
                if q.get('difficulty'):
                    md_content += f" *(Difficulty: {q['difficulty']})*"
                
                # Add image indicator
                if q.get('image'):
                    md_content += f" 🖼️ *[Image: {q['image']}]*"
                
                md_content += "\n"
                md_content += f"**Q:** {q['question']}\n\n"
                md_content += "**Options:**\n"
                
                for j, option in enumerate(q['options']):
                    marker = " ✓" if j == q['correct'] else ""
                    md_content += f"- {chr(65+j)}) {option}{marker}\n"
                
                md_content += f"\n**Answer:** {chr(65+q['correct'])}) {q['options'][q['correct']]}\n\n"
                
                if q['explanation']:
                    md_content += f"**Explanation:** {q['explanation']}\n\n"
                
                md_content += "---\n\n"
            
            # Add scoring guide
            total = len(self.questions)
            md_content += "## Scoring Guide\n\n"
            
            # Check for pass threshold
            pass_threshold = getattr(self, 'pass_threshold', 70)
            
            md_content += f"**Passing Score:** {pass_threshold}%\n\n"
            md_content += f"- **{int(total*0.9)}-{total} correct (90-100%):** Outstanding! Expert level mastery.\n"
            md_content += f"- **{int(total*0.8)}-{int(total*0.9)-1} correct (80-89%):** Excellent! Strong understanding.\n"
            md_content += f"- **{int(total*0.7)}-{int(total*0.8)-1} correct (70-79%):** Good! Meets passing threshold.\n"
            md_content += f"- **{int(total*0.6)}-{int(total*0.7)-1} correct (60-69%):** Fair. Review missed topics.\n"
            md_content += f"- **Below {int(total*0.6)} correct (<60%):** Needs improvement. Study and retake.\n\n"
            
            # Add footer
            md_content += "---\n\n"
            md_content += f"*Generated with Quiz Generator - {company}*\n"
            md_content += f"*©2025 {company}. All rights reserved*\n"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return True, f"Generated markdown answer key with {len(self.questions)} questions"
        except Exception as e:
            return False, f"Error generating markdown: {str(e)}"


    def generate_certificate_html(self, user_name, score_percentage, output_file=None):
        """Generate a standalone certificate HTML file."""

        # Generate more unique certificate ID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_component = secrets.token_hex(4)
        cert_data = f"{user_name}{self.quiz_title}{score_percentage}{timestamp}{random_component}"
        cert_id = hashlib.sha256(cert_data.encode()).hexdigest()[:12].upper()
        
        # Format date
        formatted_date = datetime.now().strftime("%B %d, %Y")
        
        # Try to embed logo as base64
        logo_base64 = ""
        logo_path = resource_path('assets/MultiaxisQuizGenerator_logo.png')
        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                logo_base64 = f"data:image/png;base64,{logo_base64}"
        except:
            # Fallback to SVG placeholder
            logo_base64 = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='80' viewBox='0 0 200 80'%3E%3Crect width='200' height='80' fill='%232C5282'/%3E%3Ctext x='100' y='40' font-family='Arial' font-size='16' fill='white' text-anchor='middle' dominant-baseline='middle'%3EMULTIAXIS%3C/text%3E%3C/svg%3E"
        
        # Performance level and colors
        if score_percentage >= 95:
            performance = "Outstanding Achievement"
            seal_color = "#FFD700"  # Gold
        elif score_percentage >= 90:
            performance = "Excellent Performance"
            seal_color = "#C0C0C0"  # Silver
        elif score_percentage >= 80:
            performance = "Superior Performance"
            seal_color = "#CD7F32"  # Bronze
        else:
            performance = "Successful Completion"
            seal_color = "#5B9BD5"  # Blue
        
        # Get settings
        author = getattr(self, 'author', '')
        company = getattr(self, 'company', 'Multiaxis Intelligence')
        
        cert_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate - {user_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Open+Sans:wght@400;600&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Open Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
            margin: 0;
        }}
        
        .certificate-container {{
            max-width: 1100px;
            width: 95%;
            min-height: 800px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            position: relative;
            margin: 20px auto;
        }}
        
        .certificate-border {{
            position: absolute;
            inset: 20px;
            border: 3px solid {seal_color};
            border-radius: 10px;
            pointer-events: none;
        }}
        
        .certificate-header {{
            background: linear-gradient(135deg, #2C5282 0%, #5B9BD5 100%);
            padding: 40px;
            text-align: center;
            position: relative;
        }}
        
        .logo {{
            max-width: 250px;
            height: auto;
            margin-bottom: 20px;
        }}
        
        .certificate-title {{
            font-family: 'Playfair Display', serif;
            font-size: 42px;
            color: white;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            letter-spacing: 2px;
        }}
        
        .certificate-body {{
            padding: 60px 60px 40px;
            text-align: center;
            background: white;
            position: relative;
        }}
        
        .award-text {{
            font-size: 20px;
            color: #666;
            margin-bottom: 25px;
            font-style: italic;
        }}
        
        .recipient-name {{
            font-family: 'Playfair Display', serif;
            font-size: 56px;
            color: #2C5282;
            margin: 35px 0;
            padding-bottom: 15px;
            border-bottom: 3px solid {seal_color};
            display: inline-block;
            min-width: 400px;
        }}
        
        .achievement-text {{
            font-size: 18px;
            color: #666;
            margin: 25px 0;
            line-height: 1.8;
        }}
        
        .quiz-title {{
            font-size: 28px;
            font-weight: 600;
            color: #2C5282;
            margin: 25px 0;
            font-style: italic;
        }}
        
        .performance-badge {{
            display: inline-block;
            background: linear-gradient(135deg, {seal_color}, {seal_color}dd);
            color: white;
            padding: 12px 40px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 18px;
            margin: 25px 0;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .score {{
            font-size: 48px;
            font-weight: bold;
            color: {seal_color};
            margin: 25px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        
        .certificate-footer {{
            background: #f8f9fa;
            padding: 40px 60px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-top: 2px solid #e2e8f0;
        }}
        
        .signature-block {{
            text-align: center;
            flex: 1;
        }}
        
        .signature-line {{
            width: 200px;
            height: 2px;
            background: #333;
            margin: 50px auto 8px;
        }}
        
        .signature-name {{
            font-size: 14px;
            color: #333;
            font-weight: 600;
            margin-top: 5px;
        }}
        
        .signature-title {{
            font-size: 12px;
            color: #666;
            margin-top: 3px;
        }}
        
        .certificate-meta {{
            background: #2C5282;
            color: white;
            padding: 25px;
            text-align: center;
            font-size: 13px;
            line-height: 1.8;
        }}
        
        .certificate-id {{
            font-family: 'Courier New', monospace;
            font-size: 15px;
            margin-top: 10px;
            background: rgba(255,255,255,0.1);
            padding: 5px 15px;
            border-radius: 5px;
            display: inline-block;
        }}
        
        .seal {{
            position: absolute;
            bottom: 150px;
            right: 80px;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: radial-gradient(circle, {seal_color}, {seal_color}dd);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 
                0 8px 16px rgba(0,0,0,0.3),
                inset 0 2px 4px rgba(255,255,255,0.3);
            transform: rotate(-15deg);
            border: 3px solid {seal_color};
        }}
        
        .seal-text {{
            color: white;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
            transform: rotate(15deg);
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            line-height: 1.4;
        }}
        
        .watermark {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 120px;
            color: rgba(91, 155, 213, 0.05);
            font-weight: bold;
            pointer-events: none;
            z-index: 1;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .certificate-container {{
                box-shadow: none;
                border-radius: 0;
                max-width: 100%;
            }}
            
            .print-button, .download-button {{
                display: none !important;
            }}
        }}
        
        .action-buttons {{
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }}
        
        .action-button {{
            background: #2C5282;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .action-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
            background: #1e3a5f;
        }}
        
        @media print {{
            .action-buttons {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="action-buttons">
        <button class="action-button" onclick="window.print()">
            <span>🖨️</span> Print Certificate
        </button>
        <button class="action-button" onclick="downloadCertificate()">
            <span>💾</span> Save as PDF
        </button>
    </div>
    
    <div class="certificate-container">
        <div class="certificate-border"></div>
        <div class="watermark">CERTIFIED</div>
        
        <div class="certificate-header">
            <img src="{logo_base64}" alt="{company} Logo" class="logo">
            <h1 class="certificate-title">Certificate of Achievement</h1>
        </div>
        
        <div class="certificate-body">
            <p class="award-text">This is to certify that</p>
            
            <h2 class="recipient-name">{user_name}</h2>
            
            <p class="achievement-text">
                has successfully completed the professional assessment
            </p>
            
            <div class="quiz-title">"{self.quiz_title}"</div>
            
            <div class="performance-badge">{performance}</div>
            
            <div class="score">{score_percentage}%</div>
            
            <p class="achievement-text">
                demonstrating exceptional knowledge and understanding<br>
                of the subject matter and meeting all requirements<br>
                for professional certification.
            </p>
            
            <div class="seal">
                <div class="seal-text">
                    CERTIFIED<br>
                    PROFESSIONAL<br>
                    {score_percentage}%
                </div>
            </div>
        </div>
        
        <div class="certificate-footer">
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-name">{author if author else "Course Instructor"}</div>
                <div class="signature-title">Instructor / Examiner</div>
            </div>
            
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-name">{formatted_date}</div>
                <div class="signature-title">Date of Completion</div>
            </div>
            
            <div class="signature-block">
                <div class="signature-line"></div>
                <div class="signature-name">Michael Kaminski</div>
                <div class="signature-title">CodeEO, Multiaxis LLC</div>
            </div>
        </div>
        
        <div class="certificate-meta">
            <div style="font-weight: 600; font-size: 14px;">©2025 {company}. All rights reserved.</div>
            <div>The Power of MULTIAXIS® with the Intelligence of ARLO™</div>
            <div class="certificate-id">Certificate ID: {cert_id}</div>
            <div style="margin-top: 10px; font-size: 12px;">
                This certificate can be verified at www.multiaxis.ai/verify<br>
                Valid for professional development and training documentation purposes
            </div>
        </div>
    </div>
    
    <script>
        // Certificate metadata
        const certificateData = {{
            id: "{cert_id}",
            recipient: "{user_name}",
            quiz: "{self.quiz_title}",
            score: {score_percentage},
            date: "{formatted_date}",
            issuer: "{company}",
            instructor: "{author if author else 'Not specified'}"
        }};
        
        // Download as PDF instruction
        function downloadCertificate() {{
            alert('To save as PDF:\\n\\n1. Press Ctrl+P (or Cmd+P on Mac)\\n2. Select "Save as PDF" as the destination\\n3. Click "Save"\\n\\nThe certificate is optimized for PDF export.');
            window.print();
        }}
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.ctrlKey && e.key === 'p') {{
                e.preventDefault();
                window.print();
            }}
        }});
        
        // Log certificate generation
        console.log('Certificate generated:', certificateData);
    </script>
</body>
</html>'''
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cert_html)
            return True, f"Certificate generated: {output_file}"
        
        return cert_html


# --- Quiz Generator App ---


class QuizGeneratorApp:
    def __init__(self, root):
        logging.info("Initializing Quiz Generator App")
        
        self.root = root
        self.root.title("Quiz Generator - Multiaxis Intelligence")
        
        # Store paths
        self.log_file = LOG_FILE
        self.settings_file = os.path.join(APP_DATA_FOLDER, 'settings', 'quiz_settings.json')
        
        # Hide window initially to prevent flash
        self.root.withdraw()
        
        # Set window size
        self.root.geometry("820x850")
        
        # Set window icon (taskbar and title bar)
        try:
            # Use resource_path for icon location
            icon_path = resource_path('assets/MultiaxisQuizGenerator.png')
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
                logging.info(f"Icon loaded successfully from: {icon_path}")
            else:
                logging.warning(f"Icon file not found at: {icon_path}")
        except Exception as e:
            logging.warning(f"Could not load icon: {e}")
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Initialize quiz generator
        self.quiz_gen = QuizGenerator()
        logging.info("Quiz generator initialized")
        
        # Initialize current question index for navigation
        self.current_question_index = -1
        
        # Initialize settings
        self.load_settings()
        
        # Create GUI
        try:
            self.create_widgets()
            logging.info("GUI widgets created successfully")
        except Exception as e:
            logging.error(f"Error creating widgets: {e}")
            logging.error(traceback.format_exc())
            messagebox.showerror("Initialization Error", 
                               f"Error creating interface: {e}\n\nCheck log file: {self.log_file}")
            raise
        
        # Create notification system
        self.create_notification_system()
        
        # Center window after everything is created
        self.center_and_show()
        
        logging.info("App initialization complete")


    def make_themed_toplevel(self, title, size):
        win = tk.Toplevel(self.root)
        win.title(title); win.geometry(size)
        style = self.style
        bg = style.lookup("TFrame", "background") or "#fff"
        win.configure(bg=bg)
        container = ttk.Frame(win, padding=10)
        container.grid(sticky="nsew")
        win.columnconfigure(0, weight=1); win.rowconfigure(0, weight=1)
        return win, container, bg, style.lookup("TEntry", "fieldbackground") or "#fff"


    def create_notification_system(self):
        """Create a toast notification system."""
        self.notification_frame = tk.Frame(self.root, bg='#2C5282', relief=tk.RAISED, borderwidth=2)
        self.notification_label = tk.Label(
            self.notification_frame, 
            text="", 
            bg='#2C5282', 
            fg='white', 
            font=('Arial', 11, 'bold'),
            padx=20, 
            pady=10
        )
        self.notification_label.pack()


    def show_notification(self, message, notification_type="info", duration=3000):
        """Show a temporary toast notification.
        
        Args:
            message: The message to display
            notification_type: 'success', 'error', 'warning', or 'info'
            duration: How long to show in milliseconds
        """
        # Set colors based on type
        colors = {
            'success': ('#28a745', 'white'),  # Green
            'error': ('#dc3545', 'white'),    # Red
            'warning': ('#ffc107', 'black'),  # Yellow
            'info': ('#5B9BD5', 'white')      # Blue
        }
        
        bg_color, fg_color = colors.get(notification_type, colors['info'])
        
        # Add icon based on type
        icons = {
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ'
        }
        icon = icons.get(notification_type, '')
        
        # Update notification
        self.notification_frame.config(bg=bg_color)
        self.notification_label.config(
            text=f"{icon}  {message}",
            bg=bg_color,
            fg=fg_color
        )
        
        # Position at top center of window
        self.notification_frame.place(
            relx=0.5,
            y=10,
            anchor='n'
        )
        
        # Auto-hide after duration
        self.root.after(duration, lambda: self.notification_frame.place_forget())


    def load_settings(self):
        """Load saved settings or use defaults."""
        self.settings = {
            'company_name': 'Arlo Industries',
            'author': 'ARLO AI Assistant',
            'copyright': '©2025 Multiaxis LLC. All rights reserved',
            'show_results': True,
            'show_explanations': True,
            'allow_review': True,
            'randomize': False,
            'timer_minutes': 0,
            'pass_threshold': 70,
            'enable_certificate': False
        }
        
        # Try to load from AppData settings file first
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                    logging.info(f"Settings loaded from: {self.settings_file}")
            else:
                # Try legacy location for migration
                legacy_settings = 'quiz_settings.json'
                if os.path.exists(legacy_settings):
                    with open(legacy_settings, 'r') as f:
                        saved_settings = json.load(f)
                        self.settings.update(saved_settings)
                    # Save to new location
                    self.save_settings()
                    logging.info("Migrated settings from legacy location")
                    # Optionally remove old file
                    try:
                        os.remove(legacy_settings)
                    except:
                        pass
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
    

    def save_settings(self):
        """Save current settings to AppData location."""
        try:
            # Ensure settings directory exists
            settings_dir = os.path.dirname(self.settings_file)
            os.makedirs(settings_dir, exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logging.info(f"Settings saved to: {self.settings_file}")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")


    def open_app_data_folder(self):
        """Open the application data folder in file explorer."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(APP_DATA_FOLDER)
            logging.info(f"Opened AppData folder: {APP_DATA_FOLDER}")
        except Exception as e:
            logging.error(f"Error opening AppData folder: {e}")
            self.show_notification(f"Error opening folder: {e}", "error")


    def center_and_show(self):
        """Center the window on screen and show it."""
        self.root.update_idletasks()
        
        # Get window size
        width = 820
        height = 850
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Set position and size
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Now show the window
        self.root.deiconify()


    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title Section with Settings
        title_frame = ttk.LabelFrame(main_frame, text="Quiz Information", padding="10")
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Row 1: Title and Description
        ttk.Label(title_frame, text="Quiz Title:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.title_var = tk.StringVar(value="Multiaxis Intelligence - Interactive Knowledge Quiz")
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Label(title_frame, text="Description:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.desc_var = tk.StringVar(value="Test your knowledge with this interactive quiz.")
        self.desc_entry = ttk.Entry(title_frame, textvariable=self.desc_var, width=40)
        self.desc_entry.grid(row=0, column=3, padx=5, sticky=(tk.W, tk.E))
        
        # Row 2: Author and Company
        ttk.Label(title_frame, text="Author:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.author_var = tk.StringVar(value=self.settings.get('author', ''))
        self.author_entry = ttk.Entry(title_frame, textvariable=self.author_var, width=40)
        self.author_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(title_frame, text="Company:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.company_var = tk.StringVar(value=self.settings.get('company_name', 'Multiaxis Intelligence'))
        self.company_entry = ttk.Entry(title_frame, textvariable=self.company_var, width=40)
        self.company_entry.grid(row=1, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Row 3: Quiz Options
        options_frame = ttk.Frame(title_frame)
        options_frame.grid(row=2, column=0, columnspan=4, pady=5)
        
        self.show_results_var = tk.BooleanVar(value=self.settings.get('show_results', True))
        ttk.Checkbutton(options_frame, text="Show Results", variable=self.show_results_var).grid(row=0, column=0, padx=10)
        
        self.show_explanations_var = tk.BooleanVar(value=self.settings.get('show_explanations', True))
        ttk.Checkbutton(options_frame, text="Show Explanations", variable=self.show_explanations_var).grid(row=0, column=1, padx=10)
        
        self.allow_review_var = tk.BooleanVar(value=self.settings.get('allow_review', True))
        ttk.Checkbutton(options_frame, text="Allow Review", variable=self.allow_review_var).grid(row=0, column=2, padx=10)
        
        self.randomize_var = tk.BooleanVar(value=self.settings.get('randomize', False))
        ttk.Checkbutton(options_frame, text="Randomize Questions", variable=self.randomize_var).grid(row=0, column=3, padx=10)
        
        self.enable_certificate_var = tk.BooleanVar(value=self.settings.get('enable_certificate', False))
        ttk.Checkbutton(options_frame, text="Enable Certificate", variable=self.enable_certificate_var).grid(row=0, column=4, padx=10)
        
        # Row 4: Timer and Pass Threshold
        settings_frame = ttk.Frame(title_frame)
        settings_frame.grid(row=3, column=0, columnspan=4, pady=5)
        
        ttk.Label(settings_frame, text="Timer (minutes, 0=off):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.timer_var = tk.IntVar(value=self.settings.get('timer_minutes', 0))
        timer_spin = ttk.Spinbox(settings_frame, from_=0, to=180, textvariable=self.timer_var, width=10)
        timer_spin.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Pass Threshold (%):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.pass_threshold_var = tk.IntVar(value=self.settings.get('pass_threshold', 70))
        threshold_spin = ttk.Spinbox(settings_frame, from_=50, to=100, textvariable=self.pass_threshold_var, width=10)
        threshold_spin.grid(row=0, column=3, padx=5)
        
        ttk.Button(settings_frame, text="Save Settings", command=self.save_current_settings).grid(row=0, column=4, padx=20)
        
        title_frame.columnconfigure(1, weight=1)
        title_frame.columnconfigure(3, weight=1)
        
        # Load Section
        load_frame = ttk.LabelFrame(main_frame, text="Load Questions", padding="10")
        load_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(load_frame, text="Load from CSV", command=self.load_csv).grid(row=0, column=0, padx=5)
        ttk.Button(load_frame, text="Load from JSON", command=self.load_json).grid(row=0, column=1, padx=5)
        ttk.Button(load_frame, text="Load from Text File", command=self.load_text_file).grid(row=0, column=2, padx=5)
        ttk.Button(load_frame, text="Paste Text", command=self.paste_text).grid(row=0, column=3, padx=5)
        
        # Sample Quizzes Section
        ttk.Separator(load_frame, orient='vertical').grid(row=0, column=4, sticky='ns', padx=10)
        ttk.Label(load_frame, text="Sample:").grid(row=0, column=5)
        
        # Create dropdown for sample quizzes
        self.sample_var = tk.StringVar()
        sample_names = list(SAMPLE_QUIZZES.keys())
        self.sample_dropdown = ttk.Combobox(load_frame, textvariable=self.sample_var, 
                                           values=sample_names, state="readonly", width=25)
        self.sample_dropdown.grid(row=0, column=6, padx=5)
        self.sample_dropdown.set("Select a sample quiz...")
        
        ttk.Button(load_frame, text="Load Sample", command=self.load_sample_quiz).grid(row=0, column=7, padx=5)
        
        # Question Management Section
        manage_frame = ttk.LabelFrame(main_frame, text="Question Management", padding="10")
        manage_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Management buttons
        button_row = ttk.Frame(manage_frame)
        button_row.grid(row=0, column=0, columnspan=3, pady=5)
        
        ttk.Button(button_row, text="➕ Add Question", command=self.show_add_question_dialog).grid(row=0, column=0, padx=5)
        ttk.Button(button_row, text="✏️ Edit", command=self.edit_question).grid(row=0, column=1, padx=5)
        ttk.Button(button_row, text="🗑️ Delete", command=self.delete_question).grid(row=0, column=2, padx=5)
        ttk.Button(button_row, text="👁️ Preview", command=self.preview_current_question).grid(row=0, column=3, padx=5)
        ttk.Button(button_row, text="📋 Preview All", command=self.preview_questions).grid(row=0, column=4, padx=5)
        ttk.Button(button_row, text="🗑️ Clear All", command=self.clear_all).grid(row=0, column=5, padx=5)
        
        # Navigation row
        nav_frame = ttk.Frame(manage_frame)
        nav_frame.grid(row=1, column=0, columnspan=3, pady=5)
        
        ttk.Button(nav_frame, text="◀ Previous", command=self.prev_question_nav).grid(row=0, column=0, padx=5)
        
        self.current_question_var = tk.StringVar(value="No questions")
        self.question_selector = ttk.Combobox(nav_frame, textvariable=self.current_question_var, 
                                             state="readonly", width=50)
        self.question_selector.grid(row=0, column=1, padx=10)
        self.question_selector.bind('<<ComboboxSelected>>', self.on_question_selected)
        
        ttk.Button(nav_frame, text="Next ▶", command=self.next_question_nav).grid(row=0, column=2, padx=5)
        
        self.question_count_label = ttk.Label(nav_frame, text="Total: 0 questions")
        self.question_count_label.grid(row=0, column=3, padx=20)
        
        # Question Preview Area
        preview_frame = ttk.LabelFrame(main_frame, text="Question Preview", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure grid weight for preview
        main_frame.rowconfigure(3, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Preview text widget
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=12, width=80)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.preview_text.config(state=tk.DISABLED)
        
        # Set initial preview
        self.update_preview()
        
        # Export Section
        export_frame = ttk.LabelFrame(main_frame, text="Export Quiz", padding="10")
        export_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(export_frame, text="Generate HTML Quiz + Answer Key", command=self.generate_html, 
                  style="Accent.TButton").grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(export_frame, text="Save to CSV", command=self.save_csv).grid(row=0, column=1, padx=5)
        ttk.Button(export_frame, text="Save to JSON", command=self.save_json).grid(row=0, column=2, padx=5)
        ttk.Button(export_frame, text="Generate Answer Key Only", command=self.generate_markdown_only).grid(row=0, column=3, padx=5)
        
        # Second row for certificate tools
        ttk.Button(export_frame, text="Generate Sample Certificate", command=self.generate_sample_certificate).grid(row=0, column=4, padx=5)

        # Help Section
        help_frame = ttk.Frame(main_frame)
        help_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(help_frame, text="Help", command=self.show_help).grid(row=0, column=0, padx=5)
        ttk.Button(help_frame, text="About", command=self.show_about).grid(row=0, column=1, padx=5)
        ttk.Button(help_frame, text="View Log", command=self.view_log).grid(row=0, column=2, padx=5)
        
        # Copyright notice
        copyright_text = "©2025 Multiaxis LLC. All rights reserved | The Power of MULTIAXIS® with the Intelligence of ARLO™"
        ttk.Label(help_frame, text=copyright_text, foreground="gray", font=("Arial", 8)).grid(row=1, column=0, columnspan=3, pady=5)


    def update_status(self):
        """Update status labels and question navigator."""
        count = self.quiz_gen.get_question_count()
        if count > 0:
            self.status_label.config(text=f"✓ Questions loaded successfully", foreground="green")
            self.question_count_label.config(text=f"Total: {count} questions")
            
            # Update question selector dropdown
            question_list = []
            for i, q in enumerate(self.quiz_gen.questions, 1):
                # Truncate long questions for display
                q_text = q['question'][:50] + "..." if len(q['question']) > 50 else q['question']
                difficulty = f"[{q.get('difficulty', 'Medium')}]" if q.get('difficulty') else ""
                image = "🖼️" if q.get('image') else ""
                question_list.append(f"Q{i}: {q_text} {difficulty} {image}")
            
            self.question_selector['values'] = question_list
            if question_list:
                self.question_selector.set(question_list[0])
                self.current_question_index = 0
        else:
            self.status_label.config(text="No questions loaded", foreground="gray")
            self.question_count_label.config(text="Total: 0 questions")
            self.question_selector['values'] = []
            self.question_selector.set("No questions")
            self.current_question_index = -1


    def on_question_selected(self, event):
        """Handle question selection from dropdown."""
        selection = self.question_selector.get()
        if selection and selection != "No questions":
            # Extract question number from selection
            try:
                q_num = int(selection.split(":")[0][1:]) - 1
                self.current_question_index = q_num
            except:
                pass


    def prev_question_nav(self):
        """Navigate to previous question."""
        if self.quiz_gen.get_question_count() > 0 and self.current_question_index > 0:
            self.current_question_index -= 1
            question_list = self.question_selector['values']
            if question_list:
                self.question_selector.set(question_list[self.current_question_index])
                self.update_preview()  # Update preview immediately


    def next_question_nav(self):
        """Navigate to next question."""
        if self.quiz_gen.get_question_count() > 0 and self.current_question_index < self.quiz_gen.get_question_count() - 1:
            self.current_question_index += 1
            question_list = self.question_selector['values']
            if question_list:
                self.question_selector.set(question_list[self.current_question_index])
                self.update_preview()  # Update preview immediately


    def edit_question(self):
        """Edit the selected question (ttk-themed)."""
        if self.current_question_index < 0 or self.current_question_index >= self.quiz_gen.get_question_count():
            messagebox.showwarning("No Selection", "Please select a question to edit")
            return

        qd = self.quiz_gen.questions[self.current_question_index]

        # Themed toplevel + container (from your helper)
        edit_window, container, frame_bg, field_bg = self.make_themed_toplevel(
            f"Edit Question {self.current_question_index + 1}",
            "625x425"
        )

        # Optional: center the window after geometry is applied
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - 312
        y = (edit_window.winfo_screenheight() // 2) - 212
        edit_window.geometry(f"+{x}+{y}")

        # Grid weights
        for c in range(3):
            container.columnconfigure(c, weight=1)

        # --- Question
        ttk.Label(container, text="Question:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        q_text = tk.Text(container, height=3, width=60, bg=field_bg, relief="solid", borderwidth=1)
        q_text.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        q_text.insert("1.0", qd["question"])

        # --- Options
        option_vars = []
        for i, opt_label in enumerate(["A", "B", "C", "D"], start=1):
            ttk.Label(container, text=f"Option {opt_label}:").grid(row=i, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=qd["options"][i-1] if i-1 < len(qd["options"]) else "")
            ttk.Entry(container, textvariable=var, width=60).grid(row=i, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
            option_vars.append(var)

        # --- Correct answer
        ttk.Label(container, text="Correct Answer:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        correct_var = tk.StringVar(value=chr(65 + qd["correct"]))
        rb_frame = ttk.Frame(container)
        rb_frame.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        for i, letter in enumerate(["A", "B", "C", "D"]):
            ttk.Radiobutton(rb_frame, text=letter, variable=correct_var, value=letter).grid(row=0, column=i, padx=5)

        # --- Explanation
        ttk.Label(container, text="Explanation:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        exp_text = tk.Text(container, height=3, width=60, bg=field_bg, relief="solid", borderwidth=1)
        exp_text.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        exp_text.insert("1.0", qd.get("explanation", ""))

        # --- Image
        ttk.Label(container, text="Image filename:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        image_var = tk.StringVar(value=qd.get("image", ""))
        ttk.Entry(container, textvariable=image_var, width=60).grid(row=7, column=1, padx=10, pady=5, sticky="ew")

        # --- Difficulty
        ttk.Label(container, text="Difficulty:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        diff_var = tk.StringVar(value=qd.get("difficulty", "Medium"))
        ttk.Combobox(container, textvariable=diff_var, values=["Easy", "Medium", "Hard"],
                     state="readonly", width=20).grid(row=8, column=1, sticky="w", padx=10, pady=5)

        def save_changes():
            new_question = q_text.get("1.0", tk.END).strip()
            new_options = [v.get().strip() for v in option_vars if v.get().strip()]

            if not new_question:
                messagebox.showerror("Error", "Question cannot be empty"); return
            if len(new_options) < 2:
                messagebox.showerror("Error", "At least 2 options required"); return

            self.quiz_gen.questions[self.current_question_index] = {
                "question": new_question,
                "options": new_options,
                "correct": ord(correct_var.get()) - ord("A"),
                "explanation": exp_text.get("1.0", tk.END).strip(),
                "image": image_var.get().strip(),
                "difficulty": diff_var.get()
            }

            self.update_status()
            self.show_notification("Question updated successfully", "success")
            edit_window.destroy()

        # --- Buttons
        btns = ttk.Frame(container)
        btns.grid(row=9, column=0, columnspan=3, pady=20)
        ttk.Button(btns, text="Save Changes", command=save_changes).grid(row=0, column=0, padx=10)
        ttk.Button(btns, text="Cancel", command=edit_window.destroy).grid(row=0, column=1, padx=10)

        # Accessibility niceties
        q_text.focus_set()
        edit_window.bind("<Escape>", lambda e: edit_window.destroy())


    def delete_question(self):
        """Delete the selected question."""
        if self.current_question_index < 0 or self.current_question_index >= self.quiz_gen.get_question_count():
            messagebox.showwarning("No Selection", "Please select a question to delete")
            return
        
        question = self.quiz_gen.questions[self.current_question_index]['question']
        if len(question) > 100:
            question = question[:100] + "..."
        
        if messagebox.askyesno("Confirm Delete", f"Delete Question {self.current_question_index + 1}?\n\n{question}"):
            del self.quiz_gen.questions[self.current_question_index]
            
            # Adjust current index if needed
            if self.current_question_index >= self.quiz_gen.get_question_count() and self.current_question_index > 0:
                self.current_question_index -= 1
            
            self.update_status()
            messagebox.showinfo("Deleted", "Question deleted successfully")


    def load_csv(self):
        """Load questions from CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.quiz_gen.quiz_title = self.title_var.get()
            self.quiz_gen.quiz_description = self.desc_var.get()
            success, message = self.quiz_gen.load_from_csv(filename)
            if success:
                self.show_notification(message, "success")
                self.update_status()
            else:
                self.show_notification(message, "error", 4000)


    def load_json(self):
        """Load questions from JSON file."""
        filename = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            success, message = self.quiz_gen.load_from_json(filename)
            if success:
                self.title_var.set(self.quiz_gen.quiz_title)
                self.desc_var.set(self.quiz_gen.quiz_description)
                self.show_notification(message, "success")
                self.update_status()
            else:
                self.show_notification(message, "error", 4000)


    def load_text_file(self):
        """Load questions from text file."""
        filename = filedialog.askopenfilename(
            title="Select text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.quiz_gen.quiz_title = self.title_var.get()
            self.quiz_gen.quiz_description = self.desc_var.get()
            success, message = self.quiz_gen.load_from_text(content)
            if success:
                self.show_notification(message, "success")
                self.update_status()
            else:
                self.show_notification(message, "error", 4000)


    def load_sample_quiz(self):
        """Load a sample quiz from the embedded samples."""
        selected = self.sample_var.get()
        
        if selected == "Select a sample quiz..." or selected not in SAMPLE_QUIZZES:
            self.show_notification("Please select a sample quiz from the dropdown", "warning")
            return
        
        # Ask user if they want to replace or append
        if self.quiz_gen.get_question_count() > 0:
            result = messagebox.askyesnocancel(
                "Existing Questions",
                "You have existing questions. Do you want to:\n\n" +
                "Yes - Replace existing questions\n" +
                "No - Add to existing questions\n" +
                "Cancel - Do nothing"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Replace
                self.quiz_gen.clear_questions()
        
        # Load the sample quiz
        sample_data = SAMPLE_QUIZZES[selected]
        
        # Update title and description
        self.title_var.set(selected)
        self.desc_var.set(sample_data["description"])
        
        # Add questions
        for q in sample_data["questions"]:
            self.quiz_gen.add_question(
                question=q["question"],
                options=q["options"],
                correct_index=q["correct"],
                explanation=q.get("explanation", "")
            )
        
        # Update status
        self.update_status()
        self.show_notification(f"Loaded '{selected}' with {len(sample_data['questions'])} questions", "success")
        
        # Reset dropdown
        self.sample_dropdown.set("Select a sample quiz...")


    def paste_text(self):
        """Open dialog to paste formatted text (ttk-themed)."""
        # Themed toplevel + container
        dialog, container, frame_bg, field_bg = self.make_themed_toplevel(
            "Paste Quiz Questions", "600x440"
        )

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 300
        y = (dialog.winfo_screenheight() // 2) - 215
        dialog.geometry(f"+{x}+{y}")

        # Label
        ttk.Label(
            container,
            text="Paste formatted questions (use --- to separate questions):"
        ).pack(pady=5)

        # Text + Scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        text_widget = tk.Text(
            text_frame,
            height=20,
            width=70,
            wrap="word",
            bg=field_bg,
            relief="solid",
            borderwidth=1
        )
        text_widget.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        sb.pack(side="right", fill="y")
        text_widget.configure(yscrollcommand=sb.set)

        # Add sample format
        sample = """Q: What is Python?
A: A snake
B: A programming language
C: A movie
D: A game
Correct: B
Explanation: Python is a programming language.
---
Q: Next question here..."""
        text_widget.insert("1.0", sample)

        # Process function
        def process_text():
            content = text_widget.get("1.0", tk.END)
            self.quiz_gen.quiz_title = self.title_var.get()
            self.quiz_gen.quiz_description = self.desc_var.get()
            success, message = self.quiz_gen.load_from_text(content)
            if success:
                self.show_notification(message, "success")
                self.update_status()
                dialog.destroy()
            else:
                self.show_notification(message, "error", 4000)

        # Buttons
        btns = ttk.Frame(container)
        btns.pack(pady=10)
        ttk.Button(btns, text="Process Text", command=process_text).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

        # UX niceties
        text_widget.focus_set()
        dialog.bind("<Escape>", lambda e: dialog.destroy())


    def save_current_settings(self):
        """Save current settings from UI."""
        self.settings['author'] = self.author_var.get()
        self.settings['company_name'] = self.company_var.get()
        self.settings['show_results'] = self.show_results_var.get()
        self.settings['show_explanations'] = self.show_explanations_var.get()
        self.settings['allow_review'] = self.allow_review_var.get()
        self.settings['randomize'] = self.randomize_var.get()
        self.settings['enable_certificate'] = self.enable_certificate_var.get()
        self.settings['timer_minutes'] = self.timer_var.get()
        self.settings['pass_threshold'] = self.pass_threshold_var.get()
        self.save_settings()
        self.show_notification("Settings saved successfully", "success")


    def update_preview(self):
        """Update the preview text area with current question."""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete('1.0', tk.END)
    
        if self.current_question_index >= 0 and self.current_question_index < self.quiz_gen.get_question_count():
            q = self.quiz_gen.questions[self.current_question_index]
        
            preview = f"QUESTION {self.current_question_index + 1} OF {self.quiz_gen.get_question_count()}\n"
            preview += "=" * 60 + "\n\n"
        
            # Difficulty badge
            if q.get('difficulty'):
                preview += f"Difficulty: {q['difficulty']}\n"
        
            # Image indicator
            if q.get('image'):
                preview += f"Image: {q['image']} 🖼️\n"
        
            preview += "\n"
        
            # Question - unescape HTML entities
            preview += f"Question:\n{html.unescape(q['question'])}\n\n"
        
            # Options - unescape HTML entities
            preview += "Options:\n"
            for i, option in enumerate(q['options']):
                marker = " ✓ (CORRECT)" if i == q['correct'] else ""
                preview += f"  {chr(65+i)}) {html.unescape(option)}{marker}\n"
        
            # Explanation - unescape HTML entities
            if q.get('explanation'):
                preview += f"\nExplanation:\n{html.unescape(q['explanation'])}\n"
        
            self.preview_text.insert('1.0', preview)
        else:
            if self.quiz_gen.get_question_count() == 0:
                self.preview_text.insert('1.0', "No questions in quiz.\n\nClick '➕ Add Question' to create your first question.")
            else:
                self.preview_text.insert('1.0', "Select a question from the dropdown to preview.")
        
        self.preview_text.config(state=tk.DISABLED)


    def update_status(self):
        """Update status labels and question navigator."""
        count = self.quiz_gen.get_question_count()
        if count > 0:
            self.question_count_label.config(text=f"Total: {count} questions")
            
            # Update question selector dropdown
            question_list = []
            for i, q in enumerate(self.quiz_gen.questions, 1):
                # Truncate long questions for display
                q_text = q['question'][:50] + "..." if len(q['question']) > 50 else q['question']
                difficulty = f"[{q.get('difficulty', 'Medium')}]" if q.get('difficulty') else ""
                image = "🖼️" if q.get('image') else ""
                question_list.append(f"Q{i}: {q_text} {difficulty} {image}")
            
            self.question_selector['values'] = question_list
            if question_list:
                # Maintain current selection if valid
                if self.current_question_index < 0 or self.current_question_index >= count:
                    self.current_question_index = 0
                self.question_selector.set(question_list[self.current_question_index])
        else:
            self.question_count_label.config(text="Total: 0 questions")
            self.question_selector['values'] = []
            self.question_selector.set("No questions")
            self.current_question_index = -1
        
        # Update preview
        self.update_preview()


    def on_question_selected(self, event):
        """Handle question selection from dropdown."""
        selection = self.question_selector.get()
        if selection and selection != "No questions":
            # Extract question number from selection
            try:
                q_num = int(selection.split(":")[0][1:]) - 1
                self.current_question_index = q_num
                self.update_preview()
            except:
                pass


    def preview_current_question(self):
        """Preview the currently selected question."""
        if self.current_question_index < 0 or self.current_question_index >= self.quiz_gen.get_question_count():
            self.show_notification("Please select a question to preview", "warning")
            return
    
        # Preview is already shown in main window, just highlight it
        self.update_preview()
        self.show_notification(f"Previewing Question {self.current_question_index + 1}", "info", 2000)


    def show_add_question_dialog(self):
        """Show dialog to add a new question (ttk-themed)."""
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Question")
        add_window.geometry("760x450")

        # Center the window
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - 350
        y = (add_window.winfo_screenheight() // 2) - 300
        add_window.geometry(f"+{x}+{y}")

        # Use themed colors
        style = self.style if hasattr(self, "style") else ttk.Style()
        frame_bg = style.lookup("TFrame", "background") or "#ffffff"
        field_bg = style.lookup("TEntry", "fieldbackground") or "#ffffff"
        add_window.configure(bg=frame_bg)  # make the Toplevel match the theme

        # Container frame (so ttk draws the background)
        container = ttk.Frame(add_window, padding=10)
        container.grid(sticky="nsew")
        add_window.columnconfigure(0, weight=1)
        add_window.rowconfigure(0, weight=1)
        for c in range(3):
            container.columnconfigure(c, weight=1)

        # Question
        ttk.Label(container, text="Question:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        q_text = tk.Text(container, height=3, width=60, bg=field_bg, relief="solid", borderwidth=1)
        q_text.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Options
        option_vars = []
        for i, opt_label in enumerate(["A", "B", "C", "D"], start=1):
            ttk.Label(container, text=f"Option {opt_label}:").grid(row=i, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar()
            ttk.Entry(container, textvariable=var, width=60).grid(row=i, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
            option_vars.append(var)

        # Correct answer
        ttk.Label(container, text="Correct Answer:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        correct_var = tk.StringVar(value="A")
        rb_frame = ttk.Frame(container)
        rb_frame.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        for i, letter in enumerate(["A", "B", "C", "D"]):
            ttk.Radiobutton(rb_frame, text=letter, variable=correct_var, value=letter).grid(row=0, column=i, padx=5)

        # Explanation
        ttk.Label(container, text="Explanation:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        exp_text = tk.Text(container, height=3, width=60, bg=field_bg, relief="solid", borderwidth=1)
        exp_text.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Image
        ttk.Label(container, text="Image filename:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        image_var = tk.StringVar()
        ttk.Entry(container, textvariable=image_var, width=60).grid(row=7, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(container, text="(Optional - e.g., Q1.png)").grid(row=7, column=2, sticky="w", padx=5)

        # Auto-suggest name
        suggested_name = f"q{self.quiz_gen.get_question_count() + 1}.png"
        ttk.Label(container, text=f"Suggested: {suggested_name}").grid(row=8, column=1, sticky="w", padx=10)

        # Difficulty
        ttk.Label(container, text="Difficulty:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        diff_var = tk.StringVar(value="Medium")
        ttk.Combobox(container, textvariable=diff_var, values=["Easy", "Medium", "Hard"],
                      state="readonly", width=20).grid(row=9, column=1, sticky="w", padx=10, pady=5)

        def add_question():
            question = q_text.get("1.0", tk.END).strip()
            options = [v.get().strip() for v in option_vars if v.get().strip()]
            if not question:
                self.show_notification("Please enter a question", "error"); return
            if len(options) < 2:
                self.show_notification("Please enter at least 2 options", "error"); return

            self.quiz_gen.questions.append({
                "question": question,
                "options": options,
                "correct": ord(correct_var.get()) - ord("A"),
                "explanation": exp_text.get("1.0", tk.END).strip(),
                "image": image_var.get().strip(),
                "difficulty": diff_var.get()
            })
            self.current_question_index = self.quiz_gen.get_question_count() - 1
            self.update_status()
            self.show_notification(f"Question {self.quiz_gen.get_question_count()} added ({diff_var.get()})"
                                   + (" with image" if image_var.get().strip() else ""), "success")
            add_window.destroy()

        # Buttons
        btns = ttk.Frame(container)
        btns.grid(row=10, column=0, columnspan=3, pady=20)
        ttk.Button(btns, text="Add Question", command=add_question).grid(row=0, column=0, padx=10)
        ttk.Button(btns, text="Cancel", command=add_window.destroy).grid(row=0, column=1, padx=10)


    def toggle_image_entry(self):
        """This method is no longer needed but kept for compatibility."""
        pass


    def add_question(self):
        """Redirect to show dialog."""
        self.show_add_question_dialog()


    def preview_questions(self):
        """Preview all questions (ttk-themed)."""
        if self.quiz_gen.get_question_count() == 0:
            self.show_notification("No questions to preview", "warning")
            return

        # Themed toplevel + container
        preview, container, frame_bg, field_bg = self.make_themed_toplevel(
            "Preview Questions", "700x500"
        )

        # Center
        preview.update_idletasks()
        x = (preview.winfo_screenwidth() // 2) - 350
        y = (preview.winfo_screenheight() // 2) - 250
        preview.geometry(f"+{x}+{y}")

        # Layout
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Text + themed scrollbar (ttk)
        text_frame = ttk.Frame(container)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        txt = tk.Text(
            text_frame,
            wrap="word",
            bg=field_bg,            # match entry field background
            relief="solid",
            borderwidth=1
        )
        txt.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(text_frame, orient="vertical", command=txt.yview)
        sb.grid(row=0, column=1, sticky="ns")
        txt.configure(yscrollcommand=sb.set)

        # Fill content
        for i, q in enumerate(self.quiz_gen.questions, 1):
            txt.insert("end", f"QUESTION {i}\n", "heading")
            txt.insert("end", f"{html.unescape(q['question'])}\n\n")

            for j, option in enumerate(q['options']):
                marker = " ✓ (CORRECT)" if j == q['correct'] else ""
                txt.insert("end", f"  {chr(65+j)}) {html.unescape(option)}{marker}\n")

            if q.get('explanation'):
                txt.insert("end", f"\nExplanation: {html.unescape(q['explanation'])}\n")

            txt.insert("end", "\n" + ("=" * 54) + "\n\n")

        # Styling for headings
        txt.tag_config("heading", font=("Arial", 12, "bold"))

        # Read-only
        txt.config(state="disabled")

        # Buttons
        btns = ttk.Frame(container)
        btns.grid(row=1, column=0, pady=(0, 10))
        ttk.Button(btns, text="Close", command=preview.destroy).grid(row=0, column=0, padx=6)

        # UX niceties
        preview.bind("<Escape>", lambda e: preview.destroy())


    def clear_all(self):
        """Clear all questions."""
        if self.quiz_gen.get_question_count() > 0:
            if messagebox.askyesno("Confirm", "Clear all questions?"):
                self.quiz_gen.clear_questions()
                self.update_status()
                self.show_notification("All questions cleared", "success")


    def generate_html(self):
        """Generate HTML quiz file."""
        logging.info("Generate HTML button clicked")
        
        if self.quiz_gen.get_question_count() == 0:
            logging.warning("No questions to generate")
            self.show_notification("No questions to generate", "error")
            return
        
        try:
            # Create default filename from quiz title
            default_name = self.title_var.get().replace(" ", "_").lower()
            default_name = re.sub(r'[^\w\-_]', '', default_name)  # Remove special characters
            if not default_name:
                default_name = "quiz"
            default_name = f"{default_name}.html"
            
            logging.info(f"Default filename: {default_name}")
            
            filename = filedialog.asksaveasfilename(
                title="Save HTML Quiz",
                defaultextension=".html",
                initialfile=default_name,
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
            )
            
            if filename:
                logging.info(f"User selected filename: {filename}")
                
                # Set quiz metadata
                self.quiz_gen.quiz_title = self.title_var.get()
                self.quiz_gen.quiz_description = self.desc_var.get()
                
                # Pass all settings to quiz generator
                self.quiz_gen.author = self.author_var.get()
                self.quiz_gen.company = self.company_var.get()
                self.quiz_gen.show_results = self.show_results_var.get()
                self.quiz_gen.show_explanations = self.show_explanations_var.get()
                self.quiz_gen.allow_review = self.allow_review_var.get()
                self.quiz_gen.randomize = self.randomize_var.get()
                self.quiz_gen.enable_certificate = self.enable_certificate_var.get()
                self.quiz_gen.timer_minutes = self.timer_var.get()
                self.quiz_gen.pass_threshold = self.pass_threshold_var.get()
                
                logging.info("Settings passed to quiz generator")
                logging.debug(f"Questions before generation: {len(self.quiz_gen.questions)}")
                
                success, message = self.quiz_gen.generate_html(filename)
                
                if success:
                    logging.info("HTML generation successful")
                    
                    # Automatically generate markdown answer file
                    md_filename = filename.replace('.html', '_answers.md')
                    logging.info(f"Generating markdown file: {md_filename}")
                    
                    md_success, md_message = self.quiz_gen.generate_markdown(md_filename)
                    
                    if md_success:
                        logging.info("Markdown generation successful")
                        self.show_notification(f"Quiz generated: {os.path.basename(filename)}", "success", 4000)
                        
                        if messagebox.askyesno("Open Files", "Open the generated files?"):
                            logging.info("Opening generated files")
                            # Open HTML in browser
                            webbrowser.open(f"file://{os.path.abspath(filename)}")
                            # Open markdown in default editor
                            if os.name == 'nt':  # Windows
                                os.startfile(md_filename)
                            elif os.name == 'posix':  # macOS/Linux
                                os.system(f'open "{md_filename}"' if sys.platform == 'darwin' else f'xdg-open "{md_filename}"')
                    else:
                        logging.warning(f"Markdown generation failed: {md_message}")
                        self.show_notification(f"Quiz generated but answer key failed: {md_message}", "warning", 4000)
                else:
                    logging.error(f"HTML generation failed: {message}")
                    self.show_notification(message, "error", 4000)
            else:
                logging.info("User cancelled file save dialog")
                
        except Exception as e:
            error_msg = f"Unexpected error in generate_html: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.show_notification("Error generating quiz - check log file", "error", 5000)


    def save_csv(self):
        """Save questions to CSV."""
        if self.quiz_gen.get_question_count() == 0:
            self.show_notification("No questions to save", "error")
            return
        
        # Create default filename from quiz title
        default_name = self.title_var.get().replace(" ", "_").lower()
        default_name = re.sub(r'[^\w\-_]', '', default_name)
        if not default_name:
            default_name = "quiz_questions"
        default_name = f"{default_name}.csv"
        
        filename = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            success, message = self.quiz_gen.save_to_csv(filename)
            if success:
                self.show_notification(message, "success")
            else:
                self.show_notification(message, "error", 4000)


    def save_json(self):
        """Save questions to JSON."""
        if self.quiz_gen.get_question_count() == 0:
            self.show_notification("No questions to save", "error")
            return
        
        # Create default filename from quiz title
        default_name = self.title_var.get().replace(" ", "_").lower()
        default_name = re.sub(r'[^\w\-_]', '', default_name)
        if not default_name:
            default_name = "quiz_data"
        default_name = f"{default_name}.json"
        
        filename = filedialog.asksaveasfilename(
            title="Save JSON",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.quiz_gen.quiz_title = self.title_var.get()
            self.quiz_gen.quiz_description = self.desc_var.get()
            success, message = self.quiz_gen.save_to_json(filename)
            if success:
                self.show_notification(message, "success")
            else:
                self.show_notification(message, "error", 4000)


    def generate_markdown_only(self):
        """Generate only the markdown answer file."""
        if self.quiz_gen.get_question_count() == 0:
            self.show_notification("No questions to generate", "error")
            return
        
        # Create default filename from quiz title
        default_name = self.title_var.get().replace(" ", "_").lower()
        default_name = re.sub(r'[^\w\-_]', '', default_name)
        if not default_name:
            default_name = "quiz"
        default_name = f"{default_name}_answers.md"
        
        filename = filedialog.asksaveasfilename(
            title="Save Markdown Answer Key",
            defaultextension=".md",
            initialfile=default_name,
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        
        if filename:
            self.quiz_gen.quiz_title = self.title_var.get()
            self.quiz_gen.quiz_description = self.desc_var.get()
            success, message = self.quiz_gen.generate_markdown(filename)
            
            if success:
                self.show_notification(message, "success")
                if messagebox.askyesno("Open File", "Open the markdown file?"):
                    if os.name == 'nt':  # Windows
                        os.startfile(filename)
                    elif os.name == 'posix':  # macOS/Linux
                        os.system(f'open "{filename}"' if sys.platform == 'darwin' else f'xdg-open "{filename}"')
            else:
                self.show_notification(message, "error", 4000)


    def view_log(self):
        """Open and display the current log file (ttk-themed)."""
        try:
            # Themed toplevel + container
            log_window, container, frame_bg, field_bg = self.make_themed_toplevel(
                f"Log File - {os.path.basename(self.log_file)}", "1200x600"
            )

            # Center
            log_window.update_idletasks()
            x = (log_window.winfo_screenwidth() // 2) - 600
            y = (log_window.winfo_screenheight() // 2) - 300
            log_window.geometry(f"+{x}+{y}")

            # Toolbar
            toolbar = ttk.Frame(container)
            toolbar.pack(side="top", fill="x", padx=5, pady=5)

            ttk.Label(toolbar, text=f"Log file: {self.log_file}").pack(side="left", padx=5)

            # Text + Scrollbar
            text_frame = ttk.Frame(container)
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)

            text_widget = tk.Text(
                text_frame,
                wrap="word",
                bg=field_bg,
                relief="solid",
                borderwidth=1
            )
            text_widget.pack(side="left", fill="both", expand=True)

            sb = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            sb.pack(side="right", fill="y")
            text_widget.configure(yscrollcommand=sb.set)

            def refresh_log():
                """Refresh log content."""
                text_widget.config(state="normal")
                text_widget.delete("1.0", tk.END)
                try:
                    with open(self.log_file, "r") as f:
                        content = f.read()
                    text_widget.insert("1.0", content)
                    text_widget.see(tk.END)  # scroll to bottom
                except Exception as e:
                    text_widget.insert("1.0", f"Error reading log file: {e}")
                text_widget.config(state="disabled")

            def open_log_folder():
                """Open the logs folder in file explorer."""
                log_dir = os.path.dirname(self.log_file)
                if os.name == "nt":  # Windows only
                    os.startfile(log_dir)

            def open_app_data():
                """Open the AppData folder."""
                if os.name == "nt":
                    os.startfile(APP_DATA_FOLDER)

            # Toolbar buttons
            ttk.Button(toolbar, text="Refresh", command=refresh_log).pack(side="right", padx=5)
            ttk.Button(toolbar, text="Open Log Folder", command=open_log_folder).pack(side="right", padx=5)
            ttk.Button(toolbar, text="Open AppData", command=open_app_data).pack(side="right", padx=5)

            # Initial load
            refresh_log()

            # UX niceties
            log_window.bind("<Escape>", lambda e: log_window.destroy())

        except Exception as e:
            logging.error(f"Error opening log viewer: {e}")
            self.show_notification(f"Error opening log: {e}", "error")

    
    def show_help(self):
        """Show help information (ttk-themed)."""
        help_text = """Quiz Generator Help

LOADING QUESTIONS:
- CSV: Load from spreadsheet (Excel/Google Sheets export)
- JSON: Load from JSON file with quiz data
- Text File: Load from formatted text file
- Paste Text: Paste formatted questions directly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILE FORMAT SPECIFICATIONS:

CSV FORMAT:
question,option_a,option_b,option_c,option_d,correct_answer,explanation
"What is Python?","A snake","A programming language","A movie","A game","B","Python is a high-level programming language"
"What is 2+2?","3","4","5","6","B","Basic arithmetic"

Notes: 
- First row must be headers
- Use quotes for text with commas
- correct_answer can be: A, B, C, D (or 1, 2, 3, 4)
- explanation is optional

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JSON FORMAT:
{
  "title": "My Quiz Title",
  "description": "Quiz description here",
  "questions": [
    {
      "question": "What is Python?",
      "options": ["A snake", "A programming language", "A movie", "A game"],
      "correct": 1,
      "explanation": "Python is a programming language"
    },
    {
      "question": "What is 2+2?",
      "options": ["3", "4", "5", "6"],
      "correct": 1,
      "explanation": "Basic arithmetic"
    }
  ]
}

Notes:
- "correct" is 0-based index (0=A, 1=B, 2=C, 3=D)
- "explanation" is optional
- "title" and "description" are optional

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEXT FORMAT:
Q: What is Python?
A: A snake
B: A programming language
C: A movie
D: A game
Correct: B
Explanation: Python is a programming language
---
Q: What is 2+2?
A: 3
B: 4
C: 5
D: 6
Correct: B
Explanation: Basic arithmetic
---

Notes:
- Use --- to separate questions
- Each line starts with its label (Q:, A:, B:, etc.)
- Explanation is optional
- Correct answer: use letter (A-D)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARLO AI PROMPT FOR GENERATING FILES:

For CSV:
"Generate a CSV file with 10 quiz questions about [TOPIC]. 
Use this exact format: question,option_a,option_b,option_c,option_d,correct_answer,explanation
Make sure correct_answer is A, B, C, or D."

For JSON:
"Generate a JSON file with 10 quiz questions about [TOPIC].
Use this exact structure: {"questions": [{"question": "...", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "..."}]}
Note: correct is 0-based index (0=A, 1=B, 2=C, 3=D)"

For Text:
"Generate 10 quiz questions about [TOPIC] in this format:
Q: [question]
A: [option]
B: [option]
C: [option]
D: [option]
Correct: [letter]
Explanation: [explanation]
---
(Separate each question with ---)"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MANUAL ENTRY:
Fill in all fields and click "Add Question"

EXPORTING:
- HTML: Creates interactive web-based quiz
- CSV: For editing in spreadsheet software
- JSON: For programmatic use
- Markdown: Answer key with explanations

For more information, visit:
www.multiaxis.ai"""

        # Themed toplevel + container
        help_window, container, frame_bg, field_bg = self.make_themed_toplevel(
            "Help - Quiz Generator", "700x600"
        )

        # Center
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - 350
        y = (help_window.winfo_screenheight() // 2) - 300
        help_window.geometry(f"+{x}+{y}")

        # Text + Scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        txt = tk.Text(
            text_frame,
            wrap="word",
            width=80,
            height=35,
            bg=field_bg,
            relief="solid",
            borderwidth=1
        )
        txt.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(text_frame, orient="vertical", command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.configure(yscrollcommand=sb.set)

        # Insert text
        txt.insert("1.0", help_text)
        txt.config(state="disabled")

        # Buttons
        btns = ttk.Frame(container)
        btns.pack(pady=10)
        ttk.Button(btns, text="Close", command=help_window.destroy).pack(side="left", padx=5)

        # UX niceties
        help_window.bind("<Escape>", lambda e: help_window.destroy())
        txt.focus_set()


    def generate_sample_certificate(self):
        """Generate a sample certificate for preview/testing."""
        if self.quiz_gen.get_question_count() == 0:
            self.show_notification("Please add questions first to generate a certificate", "warning")
            return
  
        # Create dialog for sample certificate
        cert_dialog = tk.Toplevel(self.root)
        cert_dialog.title("Generate Sample Certificate")
        cert_dialog.geometry("400x300")
        
        # Center the dialog
        cert_dialog.update_idletasks()
        x = (cert_dialog.winfo_screenwidth() // 2) - (200)
        y = (cert_dialog.winfo_screenheight() // 2) - (150)
        cert_dialog.geometry(f'+{x}+{y}')
        
        # Use tk.Label instead of ttk.Label to avoid background discoloration
        tk.Label(cert_dialog, text="Generate Sample Certificate", 
                font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        tk.Label(cert_dialog, text="Recipient Name:").grid(row=1, column=0, sticky=tk.W, padx=20, pady=10)
        name_var = tk.StringVar(value="Dick Johnson")
        ttk.Entry(cert_dialog, textvariable=name_var, width=30).grid(row=1, column=1, padx=20, pady=10)
        
        tk.Label(cert_dialog, text="Score (%):").grid(row=2, column=0, sticky=tk.W, padx=20, pady=10)
        score_var = tk.IntVar(value=92)
        score_spin = ttk.Spinbox(cert_dialog, from_=0, to=100, textvariable=score_var, width=30)
        score_spin.grid(row=2, column=1, padx=20, pady=10)
        
        # Use tk.Label with explicit background color to avoid discoloration
        tk.Label(cert_dialog, text="Performance Level:", fg="gray").grid(row=3, column=0, columnspan=2, pady=5)
        performance_label = tk.Label(cert_dialog, text="", font=("Arial", 11, "bold"))
        performance_label.grid(row=4, column=0, columnspan=2)
        
        def update_performance(*args):
            score = score_var.get()
            if score >= 95:
                performance_label.config(text="🏆 Outstanding Achievement (Gold)", fg="#B8860B")
            elif score >= 90:
                performance_label.config(text="⭐ Excellent Performance (Silver)", fg="#696969")
            elif score >= 80:
                performance_label.config(text="🎖️ Superior Performance (Bronze)", fg="#8B4513")
            else:
                performance_label.config(text="✓ Successful Completion", fg="#5B9BD5")
        
        score_var.trace('w', update_performance)
        update_performance()
        
        def generate():
            name = name_var.get().strip()
            if not name:
                self.show_notification("Please enter a recipient name", "error")
                return
            
            # Create filename
            filename = filedialog.asksaveasfilename(
                title="Save Sample Certificate",
                defaultextension=".html",
                initialfile=f"certificate_{name.replace(' ', '_').lower()}_sample.html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
            )
            
            if filename:
                # Set quiz metadata
                self.quiz_gen.quiz_title = self.title_var.get()
                self.quiz_gen.quiz_description = self.desc_var.get()
                self.quiz_gen.author = self.author_var.get()
                self.quiz_gen.company = self.company_var.get()
                
                # Generate certificate
                result = self.quiz_gen.generate_certificate_html(
                    user_name=name,
                    score_percentage=score_var.get(),
                    output_file=filename
                )

                # Check if it returned a success tuple or just wrote the file
                if isinstance(result, tuple):
                    success, message = result
                    if success:
                        self.show_notification(message, "success")
                        cert_dialog.destroy()
                        if messagebox.askyesno("Open Certificate", "Open the certificate in your browser?"):
                            webbrowser.open(f"file://{os.path.abspath(filename)}")
                    else:
                        self.show_notification(message, "error")
                else:
                    # File was written directly
                    self.show_notification(f"Certificate generated: {os.path.basename(filename)}", "success")
                    cert_dialog.destroy()
                    if messagebox.askyesno("Open Certificate", "Open the certificate in your browser?"):
                        webbrowser.open(f"file://{os.path.abspath(filename)}")
        
        # Buttons - use tk.Frame to avoid background discoloration
        button_frame = tk.Frame(cert_dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Generate Certificate", command=generate).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Cancel", command=cert_dialog.destroy).grid(row=0, column=1, padx=10)


    def save_certificate_record(self, cert_id, user_name, score_percentage):
        """Save certificate data to JSON file for verification."""
        cert_record = {
            'id': cert_id,
            'recipient': user_name,
            'quiz': self.quiz_title,
            'score': score_percentage,
            'date': datetime.now().strftime('%B %d, %Y'),
            'instructor': self.author if hasattr(self, 'author') and self.author else 'Technical Training Team',
            'company': self.company if hasattr(self, 'company') and self.company else 'Multiaxis Intelligence',
            'timestamp': datetime.now().isoformat()
        }
    
        # Determine performance level
        if score_percentage >= 95:
            cert_record['performance'] = 'Outstanding Achievement'
        elif score_percentage >= 90:
            cert_record['performance'] = 'Excellent Performance'
        elif score_percentage >= 80:
            cert_record['performance'] = 'Superior Performance'
        else:
            cert_record['performance'] = 'Successful Completion'
    
        # Load existing certificates or create new file
        cert_file = 'certificates.json'
        try:
            with open(cert_file, 'r') as f:
                certificates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            certificates = {}
    
        # Add new certificate
        certificates[cert_id] = cert_record
    
        # Save back to file
        try:
            with open(cert_file, 'w') as f:
                json.dump(certificates, f, indent=2)
            logging.info(f"Certificate record saved: {cert_id}")
        except Exception as e:
            logging.error(f"Failed to save certificate record: {e}")


    def show_about(self):
        """Show about information (ttk-themed)."""
        about_text = f"""Quiz Generator
Version {CURRENT_VERSION}
Build Date: {BUILD_DATE}
Status: {STATUS}

Created for Multiaxis Intelligence Community
www.multiaxis.ai

Developed by:
Michael Kaminski
Multiaxis LLC

Assistance by:
ARLO AI

©2025 Multiaxis LLC. All rights reserved
The Power of MULTIAXIS® with the Intelligence of ARLO™

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPEN SOURCE ACKNOWLEDGMENTS

This application uses the following technologies:

Python 3.x
- Created by Guido van Rossum
- Python Software Foundation License
- www.python.org

Tkinter
- Python's standard GUI library
- Based on Tcl/Tk by John Ousterhout
- PSF License

JSON (JavaScript Object Notation)
- Created by Douglas Crockford
- Open standard (ECMA-404)

CSV Format
- Comma-Separated Values
- RFC 4180 standard

HTML5/CSS3/JavaScript
- W3C Standards
- Open web technologies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM INFORMATION

Application Data: {APP_DATA_FOLDER}
Settings File: {os.path.join(APP_DATA_FOLDER, 'settings', 'quiz_settings.json')}
Log Location: {os.path.join(APP_DATA_FOLDER, 'logs')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SPECIAL THANKS

- The Python community for excellent documentation
- Stack Overflow contributors for problem-solving insights
- GitHub for hosting open source projects
- All beta testers and users providing feedback

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This software is provided as-is for educational and
training purposes. For commercial licensing inquiries,
please contact: support@multiaxis.llc

A powerful tool for creating interactive
knowledge assessments and training materials."""

        # Themed toplevel + container
        about_window, container, frame_bg, field_bg = self.make_themed_toplevel(
            "About Quiz Generator", "600x750"
        )

        # Center
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - 300
        y = (about_window.winfo_screenheight() // 2) - 375
        about_window.geometry(f"+{x}+{y}")

        # Text + Scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        txt = tk.Text(
            text_frame,
            wrap="word",
            width=70,
            height=38,
            bg=field_bg,
            relief="solid",
            borderwidth=1
        )
        txt.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(text_frame, orient="vertical", command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.configure(yscrollcommand=sb.set)

        # Insert text
        txt.insert("1.0", about_text)
        txt.config(state="disabled")

        # Buttons
        btns = ttk.Frame(container)
        btns.pack(pady=5)
        ttk.Button(
            btns,
            text="Open AppData Folder",
            command=lambda: os.startfile(APP_DATA_FOLDER) if os.name == "nt" else None
        ).pack(side="left", padx=5)
        ttk.Button(btns, text="Close", command=about_window.destroy).pack(side="left", padx=5)

        # UX niceties
        about_window.bind("<Escape>", lambda e: about_window.destroy())


# --- Main ---


def main():
    """Main entry point with error handling and single instance check."""
    try:
        # Check for single instance
        if not create_app_mutex():
            # Another instance is running
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning(
                    "Quiz Generator Already Running",
                    "Another instance of Quiz Generator is already running.\n"
                    "Please check your taskbar or system tray."
                )
            except:
                print("Another instance of Quiz Generator is already running.")
            
            sys.exit(0)
        
        logging.info("Starting main application")
        root = tk.Tk()
        app = QuizGeneratorApp(root)
        logging.info("Entering main loop")
        root.mainloop()
        
    except Exception as e:
        logging.critical(f"Critical error in main: {e}")
        logging.critical(traceback.format_exc())
        
        # Try to show error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Critical Error", 
                               f"Application failed to start:\n{e}\n\n"
                               f"Check log file:\n{LOG_FILE}")
        except:
            print(f"CRITICAL ERROR: {e}")
            print(f"Check log file: {LOG_FILE}")
        
        sys.exit(1)


if __name__ == "__main__":
    print("="*60)
    print("Quiz Generator - Multiaxis Intelligence")
    print("="*60)
    print(f"Log file: {LOG_FILE}")
    print("Starting GUI application...")
    print("\nFeatures:")
    print("• Load questions from CSV, JSON, or text files")
    print("• Add questions manually")
    print("• Generate interactive HTML quizzes")
    print("• Export to various formats")
    print("\nWindow should open momentarily...")
    print("="*60)
    
    main()
