# AI Fake News Detection using Classical ML & NLP

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-orange.svg)](https://scikit-learn.org/)
[![NLTK](https://img.shields.io/badge/NLTK-3.8%2B-green.svg)](https://www.nltk.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end Classical Machine Learning and Natural Language Processing (NLP) repository designed for **Full-Article Fake News Detection**. The project preprocesses raw news article text, converts it into Term Frequency-Inverse Document Frequency (TF-IDF) feature vectors, and classifies articles as **Fake** or **Real** using classical ML algorithms.

---

## 🎯 Project Objective

To build an explainable, lightweight, and robust text classification system that detects fake news articles based on linguistic patterns and statistical term frequencies—without relying on heavy deep learning models, LLMs, or external third-party fact-checking APIs.

---

## 🧠 System Architecture & Pipeline

```
Full Article Input
       │
       ▼
NLTK NLP Preprocessing
(Lowercasing, URL & HTML stripping, Regex cleaning, Stopwords removal, Porter stemming)
       │
       ▼
TF-IDF Feature Extraction
(Unigrams & Bigrams, Sublinear TF scaling, fitted strictly on training split)
       │
       ▼
Classical ML Classification
(Multinomial Naive Bayes, Logistic Regression, Calibrated Linear SVM)
       │
       ▼
Fake / Real Output
(Classification prediction + Model probability + Top TF-IDF term weights)
```

---

## 📊 Dataset & Model Evaluation

### Primary Dataset: WELFake Dataset
- **Source**: [Kaggle - WELFake Dataset](https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification)
- **Dataset File**: `data/news_dataset.csv` or `data/WELFake_Dataset.csv`
- **Schema**: `title`, `text`, `label` (`0 = Fake`, `1 = Real`)
- **Full Article Construction**: Concatenates `title` and `text` into a single body for text classification.

### Model Evaluation
Actual evaluation metrics are generated when running `python train.py`. Metrics are computed on holdout test data using Stratified 80/20 train/test splits and saved to `models/metrics.json`:
- **Accuracy**
- **Precision**
- **Recall**
- **F1-Score**
- **Confusion Matrix**

---

## 📂 Repository Structure

```
AI-Fake-News-Detection-ML-NLP/
├── .gitignore             # Git ignore rules
├── README.md              # Project documentation
├── requirements.txt        # Minimal Python dependencies
├── app.py                 # Interactive Streamlit web interface
├── train.py               # End-to-end model training & evaluation script
├── predict.py             # Command-line interface (CLI) prediction tool
├── data/
│   └── README.md          # Dataset documentation & WELFake schema
├── notebooks/
│   └── fake_news_detection_walkthrough.ipynb  # Reproducible EDA & ML walkthrough
├── models/
│   └── README.md          # Guide on saved model binaries (.joblib) & metrics.json
└── src/
    ├── __init__.py        # Package initializer
    ├── preprocessing.py   # TextPreprocessor class (NLTK cleaning & Porter stemming)
    ├── train_pipeline.py  # ModelTrainer class (TF-IDF, CV, GridSearchCV, Joblib)
    └── evaluator.py       # ModelEvaluator class (Accuracy, F1, Confusion Matrix)
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Dp8453/AI-Fake-News-Detection-ML-NLP.git
cd AI-Fake-News-Detection-ML-NLP
```

### 2. Create & Activate Virtual Environment
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
Place `news_dataset.csv` in `data/` and run:

```bash
python train.py
```

### 2. Command Line Predictions (`predict.py`)
```bash
python predict.py --text "Federal Reserve announces interest rate policy decisions after quarterly economic review."
```

### 3. Launch Streamlit Application (`app.py`)
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

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
