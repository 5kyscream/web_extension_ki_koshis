# generate_data.py
import pandas as pd
import random

print("Generating simulated internship data...")

TITLES_POOL = [
    "AI/ML Development Intern", "Backend Developer (Python)", "Data Science Intern",
    "Web Development with Flask", "AI Research Intern", "Software Engineering Intern",
    "Product Management Intern", "Cybersecurity Analyst Intern", "Cloud Engineering Intern",
    "Frontend Developer (JavaScript)", "Data Analyst Intern", "Machine Learning Engineer"
]
COMPANIES_POOL = [
    "TechNext Solutions", "Innovate AI", "DataWise Inc.", "CyberGuard Systems",
    "CloudSphere Technologies", "CodeCrafters", "Webify Services", "Insight Analytics",
    "QuantumLeap AI", "SecureNet", "LogicLoop", "PixelPerfect"
]
DESCRIPTIONS_POOL = [
    "Develop and implement an AI-based matchmaking engine for efficient internship placement. The project involves data preprocessing, model training, and front-end integration.",
    "Work on a functional prototype of a smart allocation system. Responsibilities include building the recommendation algorithm and demonstrating its effectiveness through a user interface.",
    "This internship focuses on creating a smart automation tool for the PM Internship Scheme. The candidate will be involved in the full development lifecycle, from concept to deployment."
]
SKILLS_POOL = [
    "python, machine learning, flask, scikit-learn", "ai, nlp, python, data science", "flask, javascript, html, css, sqlite"
]

def simulate_ratings_and_prestige(company_name):
    return round(random.uniform(3.8, 4.7), 1), random.randint(5, 8)

internship_data = []
for _ in range(50):
    company = random.choice(COMPANIES_POOL)
    rating, prestige = simulate_ratings_and_prestige(company)
    
    internship_data.append({
        'title': random.choice(TITLES_POOL),
        'company': company,
        'description': random.choice(DESCRIPTIONS_POOL),
        'required_skills': random.choice(SKILLS_POOL),
        'duration': f"{random.randint(2, 6)} months",
        'stipend': random.choice([5000, 10000, 12000, 15000, 20000]),
        'rating': rating,
        'company_prestige': prestige,
        'popularity': random.randint(60, 99),
        # --- THIS IS THE FIX: A placeholder URL is now added ---
        'apply_url': 'https://www.linkedin.com/jobs/search/?keywords=internship'
    })

df = pd.DataFrame(internship_data)
csv_file_path = 'pm_internship_data.csv'
df.to_csv(csv_file_path, index=False)

print(f"✅ Successfully generated {len(internship_data)} sample internships and saved to {csv_file_path}")
print("You can now run your main application with 'python app.py'.")