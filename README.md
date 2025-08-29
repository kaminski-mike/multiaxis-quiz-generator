# Quiz Generator

A professional quiz generation system with GUI interface for creating interactive HTML quizzes, developed for Multiaxis Intelligence.

![Quiz Generator Logo](quiz_generator_app_logo.png)

## Overview

Quiz Generator is a comprehensive Python application that allows users to create, manage, and export interactive quizzes. It features a user-friendly GUI interface and generates professional HTML quizzes with automatic scoring, certificates, and detailed answer keys.

## Features

### Core Functionality
- **Multiple Import Formats**: Load questions from CSV, JSON, or formatted text files
- **Manual Question Entry**: Add and edit questions directly through the GUI
- **Interactive HTML Export**: Generate fully functional web-based quizzes
- **Answer Key Generation**: Automatic markdown answer keys with explanations
- **Professional Certificates**: Generate certificates for successful quiz completion

### Quiz Features
- Multiple choice questions (up to 4 options)
- Explanations for each answer
- Image support for questions
- Difficulty levels (Easy, Medium, Hard)
- Timer functionality
- Pass/fail thresholds
- Question randomization
- Review mode

### Export Options
- Interactive HTML quiz files
- CSV format for spreadsheet editing
- JSON format for programmatic use
- Markdown answer keys
- Professional completion certificates

## Installation

### Prerequisites
- Python 3.8 or higher
- tkinter (usually included with Python)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/quiz-generator.git

# Navigate to the project directory
cd quiz-generator

# Run the application
python quiz_generator_app.py
```

## Usage

### Quick Start
1. Launch the application: `python quiz_generator_app.py`
2. Load questions using one of these methods:
   - Click "Load from CSV" to import from spreadsheet
   - Click "Load Sample" to use built-in examples
   - Click "Add Question" to create manually
3. Configure quiz settings (title, author, options)
4. Click "Generate HTML Quiz + Answer Key"
5. Open the generated HTML file in any web browser

### File Format Specifications

#### CSV Format
```csv
question,option_a,option_b,option_c,option_d,correct_answer,explanation
"What is Python?","A snake","A programming language","A movie","A game","B","Python is a high-level programming language"
```

#### JSON Format
```json
{
  "title": "My Quiz",
  "description": "Quiz description",
  "questions": [
    {
      "question": "What is Python?",
      "options": ["A snake", "A programming language", "A movie", "A game"],
      "correct": 1,
      "explanation": "Python is a programming language"
    }
  ]
}
```

#### Text Format
```
Q: What is Python?
A: A snake
B: A programming language
C: A movie
D: A game
Correct: B
Explanation: Python is a programming language
---
```

## Configuration Options

### Quiz Settings
- **Show Results**: Display score and answers after completion
- **Show Explanations**: Include explanations in results
- **Allow Review**: Enable navigation between questions
- **Randomize Questions**: Shuffle question order
- **Enable Certificate**: Generate completion certificates
- **Timer**: Set time limit (0 = unlimited)
- **Pass Threshold**: Minimum score to pass (%)

## Sample Quizzes Included

- CNC Manufacturing Fundamentals
- Project Management Essentials
- Safety Protocols Quiz
- Basic Python Programming

## File Structure

```
quiz-generator/
│
├── quiz_generator_app.py      # Main application file
├── quiz_generator_app_logo.png # Application logo
├── README.md                   # This file
├── LICENSE                     # MIT License
│
├── logs/                       # Application logs (created automatically)
│   └── quiz_generator_*.log
│
└── output/                     # Generated quiz files (user created)
    ├── *.html                  # Interactive quizzes
    └── *_answers.md            # Answer keys
```

## Troubleshooting

### Common Issues

**Application won't start**
- Ensure Python 3.8+ is installed
- Check that tkinter is available: `python -m tkinter`
- Review log files in the `logs/` directory

**Images not displaying in quiz**
- Place image files in the same directory as the HTML file
- Use supported formats (PNG, JPG)
- Check image filenames match those specified in questions

**CSV import fails**
- Ensure proper CSV formatting with headers
- Use quotes for text containing commas
- Check correct_answer values (A, B, C, or D)

## Development

### Requirements
- Python 3.8+
- tkinter (standard library)
- Standard Python libraries: json, csv, logging, pathlib

### Logging
The application creates detailed logs in the `logs/` directory with timestamps. Use "View Log" button in the application to review.

## Company Information

**Developed for:** Multiaxis Intelligence (www.multiaxis.ai)

**Created by:** Michael H. Kaminski Jr., CEO of Multiaxis LLC (www.multiaxis.llc)

**Advisory:** Methods Machine Tools (www.methodsmachine.com)

## License

MIT License

Copyright (c) 2025 Multiaxis LLC. All rights reserved | The Power of MULTIAXIS (R) with the Intelligence of ARLO (TM)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

For support, feature requests, or bug reports:
- Email: support@multiaxis.llc
- Website: www.multiaxis.ai

## Acknowledgments

- Python Software Foundation for Python and tkinter
- The open source community for inspiration and support
- Beta testers and users for valuable feedback

---

*The Power of MULTIAXIS® with the Intelligence of ARLO™*

*©2025 Multiaxis LLC. All rights reserved.*
