import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from .preprocessing import TextPreprocessor


class ModelTrainer:
    """
    End-to-end Classical ML training pipeline for fake news text classification.
    Supports TF-IDF vectorization, Stratified Train/Test split, K-Fold Cross Validation,
    Hyperparameter Tuning (GridSearchCV), and artifact saving/loading.
    """

    def __init__(self, max_features: int = 5000, ngram_range: tuple = (1, 2)):
        self.preprocessor = TextPreprocessor(use_stemming=True)
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True
        )
        self.models = {
            "Naive Bayes": MultinomialNB(),
            "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0, random_state=42),
            "Linear SVM": CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, dual="auto"))
        }
        self.trained_models = {}

    def fit_vectorizer(self, X_clean: list[str]):
        """
        Fit and transform text data into TF-IDF feature matrix.
        """
        return self.vectorizer.fit_transform(X_clean)

    def transform_text(self, X_clean: list[str]):
        """
        Transform cleaned text data using fitted vectorizer.
        """
        return self.vectorizer.transform(X_clean)

    def train_and_evaluate_all(self, X_matrix, y_labels, cv_folds: int = 5):
        """
        Train Naive Bayes, Logistic Regression, and Linear SVM classifiers.
        Performs Cross-Validation and stores fitted model instances.
        """
        cv_results = {}

        for name, model in self.models.items():
            # Stratified Cross-validation on training matrix
            scores = cross_val_score(model, X_matrix, y_labels, cv=cv_folds, scoring="accuracy")
            
            # Fit model on full training matrix
            model.fit(X_matrix, y_labels)
            self.trained_models[name] = model

            cv_results[name] = {
                "cv_mean_accuracy": float(scores.mean()),
                "cv_std_accuracy": float(scores.std())
            }

        return cv_results

    def tune_hyperparameters(self, X_matrix, y_labels):
        """
        Hyperparameter tuning using GridSearchCV for Logistic Regression.
        Sets the best estimator as the final model instance for evaluation and export.
        """
        param_grid = {
            "C": [0.1, 1.0, 10.0],
            "solver": ["liblinear", "lbfgs"]
        }
        grid_search = GridSearchCV(
            estimator=LogisticRegression(max_iter=1000, random_state=42),
            param_grid=param_grid,
            cv=3,
            scoring="accuracy",
            n_jobs=-1
        )
        grid_search.fit(X_matrix, y_labels)
        
        # Assign best tuned estimator as the final Logistic Regression model
        self.trained_models["Logistic Regression"] = grid_search.best_estimator_
        
        return grid_search.best_params_, grid_search.best_score_

    def save_artifacts(self, output_dir: str = "models"):
        """
        Serialize vectorizer and trained ML model binaries to disk.
        """
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(self.vectorizer, os.path.join(output_dir, "tfidf_vectorizer.joblib"))

        for name, model in self.trained_models.items():
            filename = name.lower().replace(" ", "_") + ".joblib"
            joblib.dump(model, os.path.join(output_dir, filename))

    @staticmethod
    def load_artifacts(models_dir: str = "models"):
        """
        Load vectorizer and saved ML models from disk.
        """
        vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.joblib")
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Vectorizer file not found at {vectorizer_path}")

        vectorizer = joblib.load(vectorizer_path)
        loaded_models = {}

        model_files = {
            "Naive Bayes": "naive_bayes.joblib",
            "Logistic Regression": "logistic_regression.joblib",
            "Linear SVM": "linear_svm.joblib"
        }

        for name, filename in model_files.items():
            path = os.path.join(models_dir, filename)
            if os.path.exists(path):
                loaded_models[name] = joblib.load(path)

        return vectorizer, loaded_models
