"""
Standalone Training Script for AI Fake News Detection (Classical ML + NLP)
Runs data preprocessing, TF-IDF feature extraction, cross-validation, 
hyperparameter tuning, model evaluation, and saves trained model binaries.
"""

import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split

from src.preprocessing import TextPreprocessor
from src.train_pipeline import ModelTrainer
from src.evaluator import ModelEvaluator


def generate_sample_dataset() -> pd.DataFrame:
    """
    Generates a clean sample dataset of real and fake news articles
    for baseline model training and demonstration purposes.
    """
    fake_samples = [
        "BREAKING: Secret Alien Technology Discovered in Abandoned Warehouse! Government refuses to acknowledge shocking claim.",
        "Miracle Cure Found! Doctors don't want you to know about this simple 2-ingredient secret drink.",
        "Shocking Hoax Exposed: Prominent politician secretly replaced by clone last month, claims viral blogger.",
        "Unbelievable Discovery: Local man finds chest of gold coins in back yard, ancient curse attached.",
        "Banned Video Reveals Shocking Truth About Energy Crisis That Mainstream Media Is Hiding From You!"
    ] * 20

    real_samples = [
        "Federal Reserve Announces Interest Rate Decision Following Quarterly Economic Review and Policy Meeting.",
        "Global Climate Summit Reaches Landmark Accord on Renewable Energy Investments and Carbon Reduction Targets.",
        "Central Bank Reports Stable Growth in Domestic Manufacturing Sector Amid Easing Supply Chain Bottlenecks.",
        "Researchers Publish Peer-Reviewed Study Detailing Breakthrough in Solar Panel Energy Efficiency.",
        "Treasury Department Issues Updated Fiscal Guidelines for International Commercial Trade Agreements."
    ] * 20

    df_fake = pd.DataFrame({"text": fake_samples, "label": 0})  # 0 = Fake
    df_real = pd.DataFrame({"text": real_samples, "label": 1})  # 1 = Real

    df = pd.concat([df_fake, df_real], ignore_index=True)
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)


def main():
    print("=" * 60)
    print("AI Fake News Detection - Classical ML + NLP Training Pipeline")
    print("=" * 60)

    data_dir = "data"
    dataset_path = os.path.join(data_dir, "news_dataset.csv")

    if os.path.exists(dataset_path):
        print(f"[*] Loading dataset from {dataset_path}...")
        df = pd.read_csv(dataset_path)
    else:
        print("[*] Local dataset not found. Generating sample training dataset...")
        df = generate_sample_dataset()
        os.makedirs(data_dir, exist_ok=True)
        df.to_csv(dataset_path, index=False)
        print(f"[+] Created sample dataset at {dataset_path} ({len(df)} samples)")

    # 1. NLP Preprocessing
    print("[*] Running NLTK NLP Preprocessing (cleaning, stopword removal, stemming)...")
    preprocessor = TextPreprocessor(use_stemming=True)
    df["clean_text"] = preprocessor.preprocess_corpus(df["text"].tolist())

    # 2. Train / Test Split
    print("[*] Splitting dataset into train (80%) and test (20%) sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    # 3. Vectorization & Training Pipeline
    trainer = ModelTrainer(max_features=5000)
    print("[*] Fitting TF-IDF Vectorizer...")
    X_train_tfidf = trainer.fit_vectorizer(X_train)
    X_test_tfidf = trainer.transform_text(X_test)

    # 4. Train Models & Perform Cross-Validation
    print("[*] Training Naive Bayes, Logistic Regression, and Linear SVM models...")
    cv_results = trainer.train_and_evaluate_all(X_train_tfidf, y_train, cv_folds=5)

    for model_name, res in cv_results.items():
        print(f"    - {model_name} (5-Fold CV Accuracy): {res['cv_mean_accuracy'] * 100:.2f}% (+/- {res['cv_std_accuracy'] * 100:.2f}%)")

    # 5. Hyperparameter Tuning
    print("[*] Running GridSearchCV Hyperparameter Tuning for Logistic Regression...")
    best_params, best_score = trainer.tune_hyperparameters(X_train_tfidf, y_train)
    print(f"    - Best Params: {best_params}")
    print(f"    - Best CV Accuracy: {best_score * 100:.2f}%")

    # 6. Comprehensive Evaluation
    print("\n" + "=" * 60)
    print("Test Set Evaluation Summary")
    print("=" * 60)
    comparison_df = ModelEvaluator.compare_models(trainer.trained_models, X_test_tfidf, y_test)
    print(comparison_df.to_string(index=False))

    # 7. Save Model Artifacts
    models_dir = "models"
    print(f"\n[*] Saving trained vectorizer and models to {models_dir}/ directory...")
    trainer.save_artifacts(output_dir=models_dir)
    
    # Save evaluation summary JSON
    metrics_path = os.path.join(models_dir, "evaluation_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(comparison_df.to_dict(orient="records"), f, indent=4)
    print(f"[+] Saved evaluation metrics to {metrics_path}")

    print("\n[SUCCESS] Training pipeline completed successfully!")


if __name__ == "__main__":
    main()
