"""
Constantes y enumeraciones para la aplicación
"""

from enum import Enum


class PermitStatus(int, Enum):
    """Estados posibles para los permisos de datos"""
    PENDING = 0
    INICIATED = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4


class DataAccessStatus(int, Enum):
    """Estados posibles para el acceso a datos en un workspace"""
    PENDING = 0
    INICIATED = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4