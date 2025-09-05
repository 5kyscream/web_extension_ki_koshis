# Internship Recommendation System

An intelligent internship recommendation engine built with Flask, MySQL, and NLP techniques. It parses student resumes, matches them against internship listings, and ranks results using a multi-factor scoring system.

![Workflow](https://github.com/pranavkr1005/prototype_O/blob/main/workflow_for_backend.png)

---

##  How It Works

The system follows a structured backend pipeline:

1. **Input Collection**
   - Internship listings with metadata (skills, stipend, rating, prestige, etc.)
   - Student resume uploaded as PDF

2. **Text Preprocessing**
   - Lowercasing, tokenization, stopword removal, lemmatization, punctuation cleanup

3. **Vectorization**
   - TF-IDF with n-gram support and vocabulary filtering

4. **Similarity Calculation**
   - Cosine similarity between student profile and internship descriptions

5. **Multi-Factor Scoring**
   - Weighted score based on:
     - Similarity (40%)
     - Popularity (20%)
     - Stipend (20%)
     - Rating (10%)
     - Prestige (10%)

6. **Ranking & Output**
   - Top N internships returned with explanations and contributing terms

---

##  Features

- Resume parsing via PyPDF2
- NLP preprocessing pipeline
- TF-IDF vectorization
- Cosine similarity computation
- Multi-factor scoring logic
- Cold start handling
- Explanation generation for recommendations
-  Dashboard with internship stats

---

## Tech Stack

| Layer        | Tools Used                          |
|--------------|-------------------------------------|
| Backend      | Flask, MySQL, PyPDF2                |
| NLP          | Custom preprocessing, TF-IDF        |
| Database     | MySQL with auto-init and sample data|
| Frontend     | HTML templates (`index`, `upload`, `dashboard`) |

---

##  API Endpoints

### `GET /`
- Renders homepage

### `GET /upload`
- Resume upload interface

### `GET /dashboard`
- Internship stats and recent entries

### `POST /add_internship`
- Add internship via JSON payload

### `POST /recommend`
- Upload resume (PDF) and receive top 5 recommendations





```bash
git clone https://github.com/pranavkr1005/prototype_O.git
cd prototype_O
