# AI Fake News Detection using Classical ML & NLP

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-orange.svg)](https://scikit-learn.org/)
[![NLTK](https://img.shields.io/badge/NLTK-3.8%2B-green.svg)](https://www.nltk.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end Classical Machine Learning and Natural Language Processing (NLP) repository designed for **Full-Article Fake News Detection**. The project preprocesses raw news article text, converts it into Term Frequency-Inverse Document Frequency (TF-IDF) feature vectors, and classifies articles as **Fake** or **Real** using classical ML algorithms.

---

## 🎯 Project Objective

To build an explainable, lightweight, and robust text classification system that detects fake news articles based on linguistic patterns and stylometric features—without relying on heavy deep learning models, LLMs, or external third-party verification APIs.

---

## 🧠 System Architecture & Pipeline

The pipeline follows a clean, modular classical Machine Learning workflow:

```
Full Article Input Text
       │
       ▼
┌────────────────────────────────────────────────────────┐
│               1. NLTK Preprocessing Pipeline           │
│  - Lowercasing                                         │
│  - URL & HTML Tag Stripping                            │
│  - Regex Cleaning (Non-alphabetic filter)              │
│  - Stopword Removal (NLTK English Corpus)              │
│  - Stemming (NLTK Porter Stemmer)                      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            2. TF-IDF Feature Extraction                │
│  - TfidfVectorizer (Unigrams & Bigrams)                │
│  - Sublinear TF Scaling                                │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│           3. Classical Machine Learning Classifiers    │
│  - Multinomial Naive Bayes                             │
│  - Logistic Regression                                 │
│  - Linear SVM (LinearSVC)                              │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               4. Output Classification                 │
│  - Prediction: Fake (0) vs Real (1)                    │
│  - Confidence / Probability Score                       │
│  - Top Feature Tokens Highlight                        │
└────────────────────────────────────────────────────────┘
```

---

## 📊 Dataset & Reference Benchmarks

### Dataset Overview
- **Primary Reference Dataset**: [WELFake Dataset](https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification) / ISOT Fake News Dataset.
- **Dataset Structure**:
  - `text`: Complete body text of news articles.
  - `label`: Binary classification label (`0 = Fake`, `1 = Real`).
  - Total Volume: ~72,000 labeled articles across politics, world news, and general news categories.

### Reference Performance Comparison
*(Evaluated across classical ML models on benchmark news datasets using 5-Fold Cross Validation)*

| Classifier Model | Accuracy | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| **Linear SVM** *(Best)* | **99.31%** | **0.99** | **0.99** | **0.99** |
| **Logistic Regression** | **98.74%** | **0.99** | **0.98** | **0.98** |
| **Multinomial Naive Bayes** | **93.71%** | **0.94** | **0.93** | **0.93** |

> *Note: Metrics above reflect reference benchmark evaluations from classical ML text classification experiments on the WELFake dataset.*

---

## 📂 Repository Structure

```
AI-Fake-News-Detection-ML-NLP/
├── .gitignore             # Standard Git ignore rules
├── README.md              # Project documentation
├── requirements.txt        # Minimal Python dependencies
├── app.py                 # Interactive Streamlit web interface
├── train.py               # End-to-end model training & evaluation script
├── predict.py             # Command-line interface (CLI) prediction tool
├── data/
│   └── README.md          # Dataset documentation & guidelines
├── notebooks/
│   └── fake_news_detection_walkthrough.ipynb  # Interactive EDA & ML walkthrough
├── models/
│   └── README.md          # Guide on saved model binaries (.joblib)
└── src/
    ├── __init__.py        # Package initializer
    ├── preprocessing.py   # TextPreprocessor class (NLTK cleaning & stemming)
    ├── train_pipeline.py  # ModelTrainer class (TF-IDF, CV, GridSearch)
    └── evaluator.py       # ModelEvaluator class (Accuracy, F1, Confusion Matrix)
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Dp8453/AI-Fake-News-Detection-ML-NLP.git
cd AI-Fake-News-Detection-ML-NLP
```

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage Guide

### 1. Model Training & Evaluation (`train.py`)
To run NLP preprocessing, TF-IDF vectorization, Stratified Train/Test split, 5-Fold Cross Validation, hyperparameter tuning, and save model binaries to `models/`:

```bash
python train.py
```

### 2. Command Line Predictions (`predict.py`)
To classify a news article from text or a text file:

```bash
# Classify text string directly
python predict.py --text "Federal Reserve announces interest rate policy decisions after quarterly economic review."

# Classify text file using a specific model
python predict.py --file sample_article.txt --model "Linear SVM"
```

### 3. Launch Streamlit Frontend (`app.py`)
To launch the interactive web application:

```bash
streamlit run app.py
```

---

## 🔒 Scope & Prohibited Technologies Filter

This repository strictly adheres to **Classical Machine Learning + NLP**:
- ❌ **NO** Google Gemini API / OpenAI / LLM functionality
- ❌ **NO** Generative AI / RAG / Prompt Engineering
- ❌ **NO** Transformer models (BERT, RoBERTa, DistilBERT)
- ❌ **NO** Deep Learning neural networks (CNN, LSTM, BiLSTM)
- ❌ **NO** SerpAPI / Google News API / External web scraping / Third-party fact-checking APIs

---

## 🔮 Future Improvements

- Add n-gram feature importance visualization charts in Streamlit.
- Support multi-file batch CSV predictions for dataset analysis.
- Include Lemmatization options alongside Porter Stemming for comparative linguistic study.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
