"""CRUD operations for PortfolioAI."""
from typing import List, Optional, Type, TypeVar, Generic, Any
from sqlalchemy.orm import Session
from ..db import models

ModelType = TypeVar("ModelType", bound=models.Base)

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: str) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: dict
    ) -> ModelType:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: str) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

class CRUDUser(CRUDBase[models.User]):
    def get_by_email(self, db: Session, email: str) -> Optional[models.User]:
        return db.query(self.model).filter(self.model.email == email).first()

class CRUDPortfolio(CRUDBase[models.Portfolio]):
    def get_multi_by_owner(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[models.Portfolio]:
        return (
            db.query(self.model)
            .filter(models.Portfolio.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

class CRUDCV(CRUDBase[models.CV]):
    def get_multi_by_owner(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[models.CV]:
        return (
            db.query(self.model)
            .filter(models.CV.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

# Create instances for each model
user = CRUDUser(models.User)
portfolio = CRUDPortfolio(models.Portfolio)
cv = CRUDCV(models.CV)
api_call = CRUDBase(models.APICall)
