"""Machine Learning API endpoints.

Provides endpoints for:
- Training chiller power models (Gordon-Ng, RLA regression)
- Making predictions with trained models
- Model management (list, versions, delete)
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Path, Query, HTTPException
from pydantic import BaseModel, Field

from app.ml.storage.registry import get_model_registry
from app.ml.training.trainer import ModelTrainer

router = APIRouter()


# ============= Pydantic Schemas =============


class TrainingRequest(BaseModel):
    """Request to train a model."""

    model_type: str = Field(
        ..., description="Model type: 'gordon_ng' or 'rla_regression'"
    )
    equipment_id: str = Field(
        ..., description="Equipment ID (e.g., 'chiller_1' or 'chiller_1+chiller_2')"
    )
    start_date: Optional[date] = Field(None, description="Training data start date")
    end_date: Optional[date] = Field(None, description="Training data end date")
    training_params: Optional[Dict[str, Any]] = Field(
        None, description="Model-specific training parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "gordon_ng",
                "equipment_id": "chiller_1",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
            }
        }


class GordonNgPredictionRequest(BaseModel):
    """Request for Gordon-Ng model prediction."""

    cooling_load_rt: List[float] = Field(..., description="Cooling load in RT")
    evap_temp_f: List[float] = Field(
        ..., description="Evaporator temperature in Fahrenheit"
    )
    cond_temp_f: List[float] = Field(
        ..., description="Condenser temperature in Fahrenheit"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cooling_load_rt": [200, 250, 300],
                "evap_temp_f": [44.0, 44.0, 44.0],
                "cond_temp_f": [85.0, 85.0, 85.0],
            }
        }


class RLAPredictionRequest(BaseModel):
    """Request for RLA regression prediction."""

    percentage_rla: List[float] = Field(..., description="RLA percentage values")
    temperature_f: Optional[List[float]] = Field(
        None, description="Optional temperature values"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "percentage_rla": [50.0, 60.0, 70.0, 80.0],
            }
        }


class PredictionResponse(BaseModel):
    """Prediction response."""

    site_id: str
    equipment_id: str
    model_type: str
    model_version: str
    predictions: List[float]
    units: str = "kW"


# ============= Model Management Endpoints =============


@router.get(
    "/models",
    summary="List all ML models",
)
async def list_models(
    site_id: Optional[str] = Query(None, description="Filter by site"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
) -> Dict:
    """List all trained ML models with optional filtering."""
    registry = get_model_registry()
    models = await registry.list_models(site_id, model_type)
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
    }


@router.get(
    "/models/{site_id}/{model_type}/{equipment_id}",
    summary="Get model details",
)
async def get_model(
    site_id: str = Path(..., description="Site identifier"),
    model_type: str = Path(..., description="Model type"),
    equipment_id: str = Path(..., description="Equipment identifier"),
    version: Optional[str] = Query(None, description="Model version (default: latest)"),
) -> Dict:
    """Get details for a specific model."""
    registry = get_model_registry()
    try:
        model = await registry.load_model(site_id, model_type, equipment_id, version)
        return model.metadata.to_dict()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {site_id}/{model_type}/{equipment_id}",
        )


# ============= Site-Specific Training Endpoints =============


@router.post(
    "/sites/{site_id}/train",
    summary="Train a model for site equipment",
)
async def train_model(
    site_id: str = Path(..., description="Site identifier"),
    request: TrainingRequest = ...,
) -> Dict:
    """Train a model for specific equipment at a site.

    For Gordon-Ng models, trains on cooling load, temperatures, and power data.
    For RLA regression, trains on RLA percentage to power mapping.
    """
    registry = get_model_registry()
    trainer = ModelTrainer(registry)

    try:
        start_dt = (
            datetime.combine(request.start_date, datetime.min.time())
            if request.start_date
            else None
        )
        end_dt = (
            datetime.combine(request.end_date, datetime.max.time())
            if request.end_date
            else None
        )

        metadata = await trainer.train_model(
            site_id=site_id,
            model_type=request.model_type,
            equipment_id=request.equipment_id,
            start_date=start_dt,
            end_date=end_dt,
            training_params=request.training_params,
        )

        return {
            "status": "completed",
            "model": metadata.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post(
    "/sites/{site_id}/train/all-chillers",
    summary="Train models for all chillers at a site",
)
async def train_all_chillers(
    site_id: str = Path(..., description="Site identifier"),
    model_type: str = Query(..., description="Model type to train"),
    start_date: Optional[date] = Query(None, description="Training data start"),
    end_date: Optional[date] = Query(None, description="Training data end"),
) -> Dict:
    """Train models for all chillers discovered at the site."""
    registry = get_model_registry()
    trainer = ModelTrainer(registry)

    try:
        start_dt = (
            datetime.combine(start_date, datetime.min.time()) if start_date else None
        )
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        results = await trainer.train_all_chillers(
            site_id=site_id,
            model_type=model_type,
            start_date=start_dt,
            end_date=end_dt,
        )

        return {
            "status": "completed",
            "models_trained": len(results),
            "models": [m.to_dict() for m in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post(
    "/sites/{site_id}/train/all-combinations",
    summary="Train models for all chiller combinations",
)
async def train_all_combinations(
    site_id: str = Path(..., description="Site identifier"),
    model_type: str = Query(..., description="Model type to train"),
    start_date: Optional[date] = Query(None, description="Training data start"),
    end_date: Optional[date] = Query(None, description="Training data end"),
) -> Dict:
    """Train models for all chiller combinations at the site."""
    registry = get_model_registry()
    trainer = ModelTrainer(registry)

    try:
        start_dt = (
            datetime.combine(start_date, datetime.min.time()) if start_date else None
        )
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        results = await trainer.train_all_combinations(
            site_id=site_id,
            model_type=model_type,
            start_date=start_dt,
            end_date=end_dt,
        )

        return {
            "status": "completed",
            "models_trained": len(results),
            "models": [m.to_dict() for m in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


# ============= Site-Specific Prediction Endpoints =============


@router.post(
    "/sites/{site_id}/predict/gordon-ng/{equipment_id}",
    summary="Predict chiller power using Gordon-Ng model",
    response_model=PredictionResponse,
)
async def predict_gordon_ng(
    site_id: str = Path(..., description="Site identifier"),
    equipment_id: str = Path(..., description="Equipment identifier"),
    request: GordonNgPredictionRequest = ...,
    version: Optional[str] = Query(None, description="Model version (default: latest)"),
) -> PredictionResponse:
    """Predict chiller power consumption using Gordon-Ng thermodynamic model.

    Requires cooling load (RT), evaporator temperature, and condenser temperature.
    """
    registry = get_model_registry()

    try:
        model = await registry.load_model(site_id, "gordon_ng", equipment_id, version)

        import numpy as np

        predictions = model.predict(
            np.array(request.cooling_load_rt),
            np.array(request.evap_temp_f),
            np.array(request.cond_temp_f),
        )

        return PredictionResponse(
            site_id=site_id,
            equipment_id=equipment_id,
            model_type="gordon_ng",
            model_version=model.metadata.version,
            predictions=predictions.tolist(),
            units="kW",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No Gordon-Ng model found for {equipment_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/sites/{site_id}/predict/rla/{equipment_id}",
    summary="Predict chiller power using RLA regression",
    response_model=PredictionResponse,
)
async def predict_rla(
    site_id: str = Path(..., description="Site identifier"),
    equipment_id: str = Path(..., description="Equipment identifier"),
    request: RLAPredictionRequest = ...,
    version: Optional[str] = Query(None, description="Model version (default: latest)"),
) -> PredictionResponse:
    """Predict chiller power consumption from RLA percentage.

    Simple regression model mapping RLA% to power (kW).
    """
    registry = get_model_registry()

    try:
        model = await registry.load_model(
            site_id, "rla_regression", equipment_id, version
        )

        import numpy as np

        predictions = model.predict(
            np.array(request.percentage_rla),
            np.array(request.temperature_f) if request.temperature_f else None,
        )

        return PredictionResponse(
            site_id=site_id,
            equipment_id=equipment_id,
            model_type="rla_regression",
            model_version=model.metadata.version,
            predictions=predictions.tolist(),
            units="kW",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No RLA model found for {equipment_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sites/{site_id}/models",
    summary="List models for a site",
)
async def list_site_models(
    site_id: str = Path(..., description="Site identifier"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
) -> Dict:
    """List all trained models for a specific site."""
    registry = get_model_registry()
    models = await registry.list_models(site_id, model_type)
    return {
        "site_id": site_id,
        "models": [m.to_dict() for m in models],
        "count": len(models),
    }


@router.get(
    "/sites/{site_id}/models/{equipment_id}/versions",
    summary="Get model versions",
)
async def get_model_versions(
    site_id: str = Path(..., description="Site identifier"),
    equipment_id: str = Path(..., description="Equipment identifier"),
    model_type: str = Query(..., description="Model type"),
) -> Dict:
    """Get all versions of a model."""
    registry = get_model_registry()
    versions = await registry.get_model_versions(site_id, model_type, equipment_id)
    return {
        "site_id": site_id,
        "equipment_id": equipment_id,
        "model_type": model_type,
        "versions": versions,
    }


@router.delete(
    "/sites/{site_id}/models/{model_type}/{equipment_id}/{version}",
    summary="Delete a model version",
)
async def delete_model_version(
    site_id: str = Path(..., description="Site identifier"),
    model_type: str = Path(..., description="Model type"),
    equipment_id: str = Path(..., description="Equipment identifier"),
    version: str = Path(..., description="Version to delete"),
) -> Dict:
    """Delete a specific model version."""
    registry = get_model_registry()
    deleted = await registry.delete_model(site_id, model_type, equipment_id, version)

    if not deleted:
        raise HTTPException(status_code=404, detail="Model version not found")

    return {
        "status": "deleted",
        "site_id": site_id,
        "model_type": model_type,
        "equipment_id": equipment_id,
        "version": version,
    }
