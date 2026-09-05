"""
CLI Inference Script for AI Fake News Detection
Predicts whether a given news article is Fake or Real using saved Classical ML models.
"""

import sys
import argparse
from src.preprocessing import TextPreprocessor
from src.train_pipeline import ModelTrainer


def predict_news(text: str, model_name: str = "Linear SVM", models_dir: str = "models"):
    """
    Cleans input news text, transforms with TF-IDF, and returns classification prediction.
    """
    preprocessor = TextPreprocessor()
    clean_text = preprocessor.clean_text(text)

    if not clean_text.strip():
        return {"error": "Cleaned text is empty after preprocessing."}

    try:
        vectorizer, loaded_models = ModelTrainer.load_artifacts(models_dir=models_dir)
    except FileNotFoundError as e:
        return {"error": f"Model files missing. Please run 'python train.py' first. ({e})"}

    if model_name not in loaded_models:
        model_name = list(loaded_models.keys())[0]

    model = loaded_models[model_name]
    vec_input = vectorizer.transform([clean_text])

    prediction = model.predict(vec_input)[0]
    verdict = "REAL" if prediction == 1 else "FAKE"

    confidence = 50.0
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(vec_input)[0]
        confidence = round(float(probs[prediction]) * 100, 2)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "model_used": model_name,
        "cleaned_snippet": clean_text[:150] + "..." if len(clean_text) > 150 else clean_text
    }


def main():
    parser = argparse.ArgumentParser(description="AI Fake News Detection CLI Classifier")
    parser.add_argument("--text", type=str, help="Raw full-article text string")
    parser.add_argument("--file", type=str, help="Path to text file containing news article")
    parser.add_argument(
        "--model",
        type=str,
        default="Linear SVM",
        choices=["Linear SVM", "Logistic Regression", "Naive Bayes"],
        help="Classifier model to use"
    )

    args = parser.parse_args()

    input_text = ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            input_text = f.read()
    elif args.text:
        input_text = args.text
    else:
        print("Usage Example:")
        print("  python predict.py --text \"Federal Reserve announces new fiscal policy standard...\"")
        print("  python predict.py --file article.txt --model \"Logistic Regression\"")
        sys.exit(0)

    result = predict_news(input_text, model_name=args.model)

    print("\n" + "=" * 50)
    print("AI Fake News Detection Result")
    print("=" * 50)
    if "error" in result:
        print(f"[ERROR] {result['error']}")
    else:
        print(f"  Verdict     : {result['verdict']}")
        print(f"  Confidence  : {result['confidence']}%")
        print(f"  Model       : {result['model_used']}")
        print(f"  Clean Text  : {result['cleaned_snippet']}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
