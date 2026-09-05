import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


class ModelEvaluator:
    """
    Evaluation metrics calculator for classical text classification models.
    Provides Accuracy, Precision, Recall, F1-score, Confusion Matrix, and Classification Reports.
    """

    @staticmethod
    def evaluate_model(model, X_test, y_test):
        """
        Computes standard performance metrics for a trained classifier.
        """
        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        cm = confusion_matrix(y_test, y_pred)
        clf_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "confusion_matrix": cm.tolist(),
            "classification_report": clf_report
        }

    @staticmethod
    def compare_models(trained_models_dict: dict, X_test, y_test) -> pd.DataFrame:
        """
        Compares multiple trained models side-by-side in a summary DataFrame.
        """
        records = []
        for name, model in trained_models_dict.items():
            metrics = ModelEvaluator.evaluate_model(model, X_test, y_test)
            records.append({
                "Model": name,
                "Accuracy": round(metrics["accuracy"], 4),
                "Precision": round(metrics["precision"], 4),
                "Recall": round(metrics["recall"], 4),
                "F1-Score": round(metrics["f1_score"], 4)
            })

        df = pd.DataFrame(records)
        return df.sort_values(by="F1-Score", ascending=False).reset_index(drop=True)
