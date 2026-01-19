"""
Constantes y enumeraciones para la aplicación
"""

from enum import Enum


class PermitStatus(int, Enum):
    """Estados posibles para los permisos de datos"""
    PENDING = 0
    INICIATED = 1
    SUBMITTED = 2
    REJECTED = 3
    GRANTED = 4
    EXPIRED = 5


class DataAccessStatus(int, Enum):
    """Estados posibles para el acceso a datos en un workspace"""
    PENDING = 0
    INICIATED = 1
    SUBMITTED = 2
    GRANTED = 3
    REJECTED = 4
    EXPIRED = 5

class CohortStatus(int, Enum):
    """Estados posibles para un cohort"""
    CREATED = 0
    EXECUTED = 1
    ERROR = 2

class MetadataStatus(int, Enum):
    """Estados posibles para los metadatos de datos"""
    PENDING = 0
    INITIATED = 1
    COMPLETED = 2