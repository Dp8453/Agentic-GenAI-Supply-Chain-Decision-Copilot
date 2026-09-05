# Data Directory

This directory contains dataset documentation and placeholders for training and evaluation data.

## Recommended Datasets
1. **WELFake Dataset** (Kaggle): Over 72,000 labeled fake and real news articles.
2. **ISOT Fake News Dataset**: Contains real news articles from Reuters and fake news articles from flagged online sources.

## Data Format
CSV files placed in this directory should follow the column schema:
- `text`: Full news article text body (String)
- `label`: Binary classification target (`0` = Fake News, `1` = Real News)

## Data Generation Script
Running `python train.py` will automatically load `data/news_dataset.csv` if present, or generate a baseline training dataset to verify the pipeline end-to-end.
