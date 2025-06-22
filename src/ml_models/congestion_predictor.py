"""
Port congestion prediction model using machine learning
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import structlog

logger = structlog.get_logger(__name__)


class CongestionPredictor:
    """Machine learning model for predicting port congestion levels"""
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'vessels_waiting', 'vessels_at_berth', 'vessels_arrived_24h',
            'average_wait_time', 'berth_utilization', 'throughput_24h',
            'weather_impact', 'hour_of_day', 'day_of_week', 'month',
            'seasonal_factor', 'historical_avg_congestion'
        ]
        self.is_trained = False
        
        # Initialize model based on type
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def prepare_features(self, congestion_data: List[Dict]) -> pd.DataFrame:
        """Prepare features for training or prediction"""
        df = pd.DataFrame(congestion_data)
        
        # Convert timestamp to datetime features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # Calculate seasonal factor (higher in winter months for northern ports)
        df['seasonal_factor'] = np.sin(2 * np.pi * df['month'] / 12)
        
        # Calculate historical average congestion for the same time period
        df['historical_avg_congestion'] = df.groupby(['hour_of_day', 'day_of_week'])['congestion_score'].transform('mean')
        
        # Fill missing values
        for col in self.feature_columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = 0.0
        
        return df[self.feature_columns]
    
    def train(self, training_data: List[Dict], target_column: str = 'congestion_score') -> Dict[str, float]:
        """Train the congestion prediction model"""
        logger.info(f"Training congestion predictor with {len(training_data)} samples")
        
        # Prepare features and target
        X = self.prepare_features(training_data)
        df = pd.DataFrame(training_data)
        y = df[target_column].fillna(0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate training metrics
        y_pred = self.model.predict(X_scaled)
        metrics = {
            'mae': mean_absolute_error(y, y_pred),
            'mse': mean_squared_error(y, y_pred),
            'rmse': np.sqrt(mean_squared_error(y, y_pred))
        }
        
        logger.info(f"Training completed. MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
        return metrics
    
    def predict(self, input_data: List[Dict]) -> List[float]:
        """Predict congestion levels for given input data"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X = self.prepare_features(input_data)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        # Ensure predictions are within valid range [0, 1]
        predictions = np.clip(predictions, 0.0, 1.0)
        
        return predictions.tolist()
    
    def predict_future_congestion(self, port_id: str, hours_ahead: int = 24) -> List[Dict]:
        """Predict congestion for the next N hours"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = []
        current_time = datetime.utcnow()
        
        for hour in range(hours_ahead):
            future_time = current_time + timedelta(hours=hour)
            
            # Create input data for this time point
            input_data = [{
                'port_id': port_id,
                'timestamp': future_time,
                'vessels_waiting': 0,  # These would be populated from current data
                'vessels_at_berth': 0,
                'vessels_arrived_24h': 0,
                'average_wait_time': 0,
                'berth_utilization': 0.7,  # Default assumption
                'throughput_24h': 0,
                'weather_impact': 0.1,  # Default good weather
                'historical_avg_congestion': 0.5  # Default
            }]
            
            congestion_score = self.predict(input_data)[0]
            
            predictions.append({
                'timestamp': future_time,
                'predicted_congestion': congestion_score,
                'confidence': self._calculate_confidence(congestion_score)
            })
        
        return predictions
    
    def _calculate_confidence(self, prediction: float) -> float:
        """Calculate confidence score for prediction"""
        # Simple confidence calculation based on prediction value
        # More sophisticated methods could use prediction intervals
        if hasattr(self.model, 'predict_proba'):
            return 0.8  # Placeholder for probabilistic models
        else:
            # For regression models, use distance from extremes
            return min(prediction, 1 - prediction) * 2
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.is_trained:
            raise ValueError("Model must be trained to get feature importance")
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_columns, importance))
        else:
            return {}
    
    def save_model(self, filepath: str):
        """Save the trained model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model from file"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {filepath}")
    
    def evaluate(self, test_data: List[Dict], target_column: str = 'congestion_score') -> Dict[str, float]:
        """Evaluate model performance on test data"""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        X = self.prepare_features(test_data)
        df = pd.DataFrame(test_data)
        y_true = df[target_column].fillna(0.0)
        
        X_scaled = self.scaler.transform(X)
        y_pred = self.model.predict(X_scaled)
        
        # Clip predictions to valid range
        y_pred = np.clip(y_pred, 0.0, 1.0)
        
        metrics = {
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'accuracy_within_10pct': np.mean(np.abs(y_true - y_pred) < 0.1),
            'accuracy_within_20pct': np.mean(np.abs(y_true - y_pred) < 0.2)
        }
        
        return metrics
    
    def detect_congestion_anomalies(self, current_data: Dict, threshold: float = 0.3) -> Dict[str, any]:
        """Detect unusual congestion patterns"""
        if not self.is_trained:
            return {'anomaly_detected': False, 'reason': 'Model not trained'}
        
        predicted_congestion = self.predict([current_data])[0]
        actual_congestion = current_data.get('congestion_score', 0)
        
        anomaly_score = abs(predicted_congestion - actual_congestion)
        is_anomaly = anomaly_score > threshold
        
        return {
            'anomaly_detected': is_anomaly,
            'anomaly_score': anomaly_score,
            'predicted_congestion': predicted_congestion,
            'actual_congestion': actual_congestion,
            'threshold': threshold,
            'severity': 'high' if anomaly_score > 0.5 else 'medium' if anomaly_score > 0.3 else 'low'
        } 