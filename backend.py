# backend.py
import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import string, random

# Ensure required nltk resources are available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading required NLTK data...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)

# ---------------- Preprocessing ---------------- #
def preprocess(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    # Remove stopwords, numbers, punctuation, and very short tokens
    filtered_tokens = [
        lemmatizer.lemmatize(word)
        for word in tokens
        if word.isalnum()
        and word not in stop_words
        and not word.isdigit()
        and len(word) > 2
    ]
    return ' '.join(filtered_tokens)

# ---------------- Term Contribution Helper ---------------- #
def get_top_contributing_terms(query_vec, doc_vec, feature_names, top_n=3):
    contributions = query_vec.toarray()[0] * doc_vec.toarray()[0]
    top_indices = np.argsort(contributions)[::-1]
    top_terms = [feature_names[i] for i in top_indices if contributions[i] > 0][:top_n]
    return top_terms

# ---------------- Recommendation Engine ---------------- #
def recommendInternship(student, internships, top_n=5):
    if not internships:
        return []

    # Combine resume skills + interests
    query_raw = student.get("skills", "") + " " + student.get("interests", "")
    query = preprocess(query_raw)

    # Preprocess internship docs
    docs = [
        preprocess(f'{i["title"]} {i["description"]} {i["required_skills"]}')
        for i in internships
    ]

    # Fallback: no useful resume text
    if not query.strip():
        scores = []
        for intern in internships:
            score = (
                (intern.get("popularity", 0) / 100) * 0.5 +
                (intern.get("rating", 0) / 5) * 0.3 +
                (intern.get("company_prestige", 0) / 10) * 0.2
            )
            scores.append((score, intern, "Recommended based on general popularity and ratings."))
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_n]

    # TF-IDF with filtering to remove noise
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,  # ignore words that appear only once
    )
    tfidf_matrix = vectorizer.fit_transform(docs + [query])
    query_vec = tfidf_matrix[-1]
    doc_vecs = tfidf_matrix[:-1]
    similarities = cosine_similarity(query_vec, doc_vecs)[0]

    # Normalize stipend
    all_stipends = [intern.get("stipend", 0) for intern in internships]
    max_stipend = max(all_stipends) if all_stipends else 1
    if max_stipend == 0:
        max_stipend = 1

    scores = []
    feature_names = vectorizer.get_feature_names_out()

    for i, intern in enumerate(internships):
        sim = similarities[i]

        # Weighted scoring system
        score = (
            sim * 0.55 +
            (intern.get("popularity", 0) / 100) * 0.15 +
            min(intern.get("stipend", 0) / max_stipend, 1) * 0.15 +
            (intern.get("rating", 0) / 5) * 0.10 +
            (intern.get("company_prestige", 0) / 10) * 0.05
        )

        # Build explanation
        top_terms = get_top_contributing_terms(query_vec, doc_vecs[i], feature_names)
        explanation_lines = []
        if sim > 0.05 and top_terms:
            explanation_lines.append(f"• Keyword Match: {', '.join(top_terms)}")
        elif sim > 0.05:
            explanation_lines.append("• General textual match with your resume.")
        else:
            explanation_lines.append("• No strong skill match, ranked by popularity and ratings.")

        explanation_lines.append(f"• Similarity Score: {sim:.3f}")
        explanation_lines.append(f"• Popularity Score: {intern.get('popularity', 0)}/100")
        explanation_lines.append(f"• Prestige Score: {intern.get('company_prestige', 0)}/10")

        explanation = "\n".join(explanation_lines)
        scores.append((score, intern, explanation))

    # Sort by score, add slight randomness to break ties
    scores = sorted(scores, key=lambda x: (x[0], random.random()), reverse=True)
    return scores[:top_n]
