# Data Directory

This directory stores the training dataset for the AI Fake News Detection project.

## Primary Dataset: WELFake Dataset
- **Source**: [Kaggle - WELFake Dataset](https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification)
- **File Name**: `data/news_dataset.csv` or `data/WELFake_Dataset.csv`
- **Volume**: Over 72,000 labeled fake and real news articles.

## Dataset Schema
The pipeline expects a CSV file containing the following columns:
- `title`: Headline of the news article (String)
- `text`: Body text content of the news article (String)
- `label`: Binary classification target (`0 = Fake News`, `1 = Real News`)

## Pipeline Data Handling
When `python train.py` is executed, the pipeline automatically:
1. Concatenates `title` and `text` to form `full_text` for complete article classification.
2. Removes rows with missing text content or target labels.
3. Applies NLTK NLP preprocessing (lowercasing, regex cleaning, stopword filtering, Porter stemming).
4. Executes a Stratified 80/20 train/test split.
5. Fits the `TfidfVectorizer` exclusively on the training split to prevent data leakage.
