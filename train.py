"""
Standalone Training Script for AI Fake News Detection (Classical ML + NLP)
Runs data preprocessing, TF-IDF feature extraction, cross-validation, 
hyperparameter tuning, model evaluation, and saves trained model binaries and metrics.json.
Requires WELFake dataset located at data/news_dataset.csv or data/WELFake_Dataset.csv.
"""

import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split

from src.preprocessing import TextPreprocessor
from src.train_pipeline import ModelTrainer
from src.evaluator import ModelEvaluator


def load_welfake_dataset(data_dir: str = "data") -> pd.DataFrame:
    """
    Loads and prepares the WELFake dataset from the data directory.
    Constructs full article text from available 'title' and 'text' columns.
    Raises FileNotFoundError if no dataset file exists.
    """
    possible_paths = [
        os.path.join(data_dir, "news_dataset.csv"),
        os.path.join(data_dir, "WELFake_Dataset.csv")
    ]

    dataset_path = None
    for p in possible_paths:
        if os.path.exists(p):
            dataset_path = p
            break

    if not dataset_path:
        raise FileNotFoundError(
            "Dataset not found at data/news_dataset.csv or data/WELFake_Dataset.csv. "
            "Please place the WELFake dataset CSV file in the 'data/' directory before running training."
        )

    print(f"[*] Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    # Inspect and handle column names for WELFake dataset schema
    # Expected columns: ['title', 'text', 'label']
    if "title" in df.columns and "text" in df.columns:
        print("[*] Combining 'title' and 'text' columns into full article content...")
        df["full_text"] = df["title"].fillna("") + " " + df["text"].fillna("")
    elif "text" in df.columns:
        df["full_text"] = df["text"].fillna("")
    else:
        raise KeyError("Dataset must contain a 'text' or 'title' column.")

    if "label" not in df.columns:
        raise KeyError("Dataset must contain a 'label' target column (0 = Fake, 1 = Real).")

    # Drop rows with missing full_text or label
    df = df.dropna(subset=["full_text", "label"]).reset_index(drop=True)
    df["label"] = df["label"].astype(int)

    print(f"[+] Loaded {len(df)} total articles.")
    print(f"    - Fake articles (0): {(df['label'] == 0).sum()}")
    print(f"    - Real articles (1): {(df['label'] == 1).sum()}")

    return df


def main():
    print("=" * 60)
    print("AI Fake News Detection - Classical ML + NLP Training Pipeline")
    print("=" * 60)

    # 1. Load Dataset (Fails with FileNotFoundError if missing)
    df = load_welfake_dataset(data_dir="data")

    # 2. NLP Preprocessing (explicitly enable Porter stemming)
    print("[*] Running NLTK NLP Preprocessing (lowercasing, cleaning, stopwords, Porter stemming)...")
    preprocessor = TextPreprocessor(use_stemming=True)
    df["clean_text"] = preprocessor.preprocess_corpus(df["full_text"].tolist())

    # 3. Train / Test Split BEFORE TF-IDF fitting (Stratified)
    print("[*] Splitting dataset into train (80%) and test (20%) sets (Stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    # 4. TF-IDF Vectorization (Fitted exclusively on X_train)
    trainer = ModelTrainer(max_features=5000)
    print("[*] Fitting TF-IDF Vectorizer on X_train...")
    X_train_tfidf = trainer.fit_vectorizer(X_train)
    X_test_tfidf = trainer.transform_text(X_test)

    # 5. Train Models & Perform Stratified 5-Fold Cross-Validation
    print("[*] Training Naive Bayes, Logistic Regression, and Linear SVM models...")
    cv_results = trainer.train_and_evaluate_all(X_train_tfidf, y_train, cv_folds=5)

    for model_name, res in cv_results.items():
        print(f"    - {model_name} (5-Fold CV Accuracy): {res['cv_mean_accuracy'] * 100:.2f}% (+/- {res['cv_std_accuracy'] * 100:.2f}%)")

    # 6. Hyperparameter Tuning using GridSearchCV
    print("[*] Running GridSearchCV Hyperparameter Tuning for Logistic Regression...")
    best_params, best_score = trainer.tune_hyperparameters(X_train_tfidf, y_train)
    print(f"    - Best Params: {best_params}")
    print(f"    - Best CV Accuracy: {best_score * 100:.2f}%")
    print("    - Updated Logistic Regression instance with grid.best_estimator_")

    # 7. Evaluation on Test Set
    print("\n" + "=" * 60)
    print("Test Set Evaluation Summary")
    print("=" * 60)
    comparison_df = ModelEvaluator.compare_models(trainer.trained_models, X_test_tfidf, y_test)
    print(comparison_df.to_string(index=False))

    # Save detailed evaluation dictionary for metrics.json
    detailed_metrics = {}
    for name, model in trainer.trained_models.items():
        eval_res = ModelEvaluator.evaluate_model(model, X_test_tfidf, y_test)
        detailed_metrics[name] = {
            "Accuracy": round(eval_res["accuracy"], 4),
            "Precision": round(eval_res["precision"], 4),
            "Recall": round(eval_res["recall"], 4),
            "F1-Score": round(eval_res["f1_score"], 4),
            "Confusion Matrix": eval_res["confusion_matrix"]
        }

    # 8. Save Model Artifacts & metrics.json
    models_dir = "models"
    print(f"\n[*] Saving trained vectorizer and models to {models_dir}/ directory...")
    trainer.save_artifacts(output_dir=models_dir)

    metrics_path = os.path.join(models_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(detailed_metrics, f, indent=4)
    print(f"[+] Saved evaluation metrics to {metrics_path}")

    print("\n[SUCCESS] Training pipeline completed successfully!")


if __name__ == "__main__":
    main()
