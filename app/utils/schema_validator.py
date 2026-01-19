from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeMeta
from typing import Type, List

def compare_model_and_schema(sqlalchemy_model: Type[DeclarativeMeta], pydantic_schema: Type[BaseModel]) -> None:
    """
    Compara un modelo SQLAlchemy y un esquema Pydantic y muestra diferencias
    en los nombres de campos.
    """
    # Campos del modelo SQLAlchemy
    model_fields = {col.name for col in sqlalchemy_model.__table__.columns}
    
    # Campos del schema Pydantic
    schema_fields = set(pydantic_schema.model_fields.keys())
    
    # Detectar diferencias
    missing_in_model = schema_fields - model_fields
    missing_in_schema = model_fields - schema_fields
    
    print(f"\n🔍 Comparando {sqlalchemy_model.__name__} ↔ {pydantic_schema.__name__}")
    if not missing_in_model and not missing_in_schema:
        print("✅ Todo está sincronizado entre modelo y schema.")
    else:
        if missing_in_model:
            print(f"⚠️ Campos en el schema pero NO en el modelo SQLAlchemy: {missing_in_model}")
        if missing_in_schema:
            print(f"⚠️ Campos en el modelo SQLAlchemy pero NO en el schema: {missing_in_schema}")
