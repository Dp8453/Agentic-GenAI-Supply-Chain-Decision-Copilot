"""
AI Fake News Detection - Classical Machine Learning & Natural Language Processing Suite.
"""

from .preprocessing import TextPreprocessor
from .train_pipeline import ModelTrainer
from .evaluator import ModelEvaluator

__all__ = ["TextPreprocessor", "ModelTrainer", "ModelEvaluator"]
