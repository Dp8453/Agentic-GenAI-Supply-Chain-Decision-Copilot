# Data Directory

This directory stores the training dataset for the AI Fake News Detection project.

## Primary Dataset: WELFake Dataset
- **Official Source**: [Zenodo Repository (DOI: 10.5281/zenodo.4561253)](https://zenodo.org/record/4561253)
- **Direct Download Link**: `https://zenodo.org/record/4561253/files/WELFake_Dataset.csv?download=1`
- **Hugging Face Hub Mirror**: [davanstrien/WELFake](https://huggingface.co/datasets/davanstrien/WELFake)
- **Dataset File Path**: `data/WELFake_Dataset.csv`
- **Dataset Version**: 1.0 (Published Feb 2021)
- **Original Research Reference**: 
  > Shahane, S., Doke, A. et al. *WELFake: Word Embedding Over Linguistic Features for Fake News Detection*. IEEE Transactions on Computational Social Systems.

## Dataset Schema & Specifications
The pipeline expects a CSV file containing the following columns:
- `title`: Headline of the news article (String)
- `text`: Body text content of the news article (String)
- `label`: Binary classification target (`0 = Fake News`, `1 = Real News`)

## Pipeline Data Handling
When `python train.py` is executed, the pipeline automatically:
1. Concatenates `title` and `text` to form `full_text` for complete article classification.
2. Removes rows with missing text content or target labels.
3. Checks for and removes exact duplicate `full_text` articles before dataset splitting.
4. Applies NLTK NLP preprocessing (lowercasing, regex cleaning, stopword filtering, Porter stemming).
5. Executes a Stratified 80/20 train/test split (`random_state=42`).
6. Fits the `TfidfVectorizer` exclusively on the training split (`X_train`) to prevent data leakage.

## Reproducible Download Instructions
To download and place the official dataset locally:
```bash
python -c "import urllib.request; urllib.request.urlretrieve('https://zenodo.org/record/4561253/files/WELFake_Dataset.csv?download=1', 'data/WELFake_Dataset.csv')"
```
*Note: `data/WELFake_Dataset.csv` is added to `.gitignore` to prevent large binary files from clogging Git repository history.*
