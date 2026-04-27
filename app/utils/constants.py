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


TOKEN_V6 = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJncG4zend5TUJzeE42QnhPREp1QWN6dDRuVE5WM1RwY095VGZ5VFlfWE5ZIn0.eyJleHAiOjE4MDQ4NDI0MTMsImlhdCI6MTc3MzMwNjQ1NSwiYXV0aF90aW1lIjoxNzczMzA2NDEzLCJqdGkiOiJvbnJ0YWM6YWE5Y2Q1MGEtZjg4MS00MTRjLWE2NTQtZjc0NmE4OGVlYzY3IiwiaXNzIjoiaHR0cHM6Ly92YW50YWdlNi1hdXRoLm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzL3JlYWxtcy92YW50YWdlNiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI5ZGFjYWJiZi1lMzE4LTQzYzgtODY4MC0wM2FkM2JhNzA4MzYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwdWJsaWNfY2xpZW50Iiwic2lkIjoiMDA4YWZmODEtZjViMC00ZWU0LThiN2QtYTc1ZjIyOTA5MDQ1IiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3ZhbnRhZ2U2LWF1dGgub3JjaGVzdHJhdG9yLmlkZWEubHN0LnRmby51cG0uZXMiLCJodHRwOi8vbG9jYWxob3N0Ojc2ODEiLCJodHRwczovL3ZhbnRhZ2U2Lm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXZhbnRhZ2U2Iiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInZhbnRhZ2U2X2NsaWVudF90eXBlIjoidXNlciIsIm5hbWUiOiJGcmFuayBNYXJ0aW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbiIsImdpdmVuX25hbWUiOiJGcmFuayIsImZhbWlseV9uYW1lIjoiTWFydGluIiwiZW1haWwiOiJmLm1hcnRpbkBpa25sLm5sIn0.e67r2eOhcScXH_j7rVR8R-g7vjbhF6slKmnv7cru2BE0Kixbm2tl-kJ7EoNodJJmRVvAi4Jq5PERR6CVDu3mZ35chvzVjaIpjITTaGtiiUFXRl4AOi8SN45LJjT3qP0Hi5cxbhk_Yyda5VeCF5VF35yRrtmeV2IAsaiiVsCwVCC4rlJg_lAx_y27ZaH3m4BfghbYOqNrhjX7S2xyxLuW5v_0mEdJYAzMzHH093gKZTec02QpJUQEEDdYQTJUApnMsXJ5_jvm92n-8PvErI9IvkCYi-1SxwiYaAD7-oqS1OBW6-gbp6BnClA10FZatJllMdGpFILSz88U-LS72dKdnw"

API_BASE = "https://vantage6-core.orchestrator.idea.lst.tfo.upm.es/server"

COLLABORATION_ID = 3

ORGANIZATION_IDS = {1, 4, 5, 9}


class typeOfDiseases(Enum):
    """Tipos de enfermedades"""

    SARCOMA = "sarc"
    HAndN = "head_and_neck"


class ALGORITHMS(str, Enum):

    CROSSTABULATION = "crosstabulation"
    TTEST = "t-test"
    CHI_SQUARED = "chi-squared"
    KAPLAN_MEIER = "kaplan-meier"
    LOG_RANK_TEST = "log-rank-test"
    GLM = "glm"
    TIME_DELTA = "time-delta"
    TABLE1 = "table1"
    BASIC_ARITHMETIC = "basic_arithmetic"
    SUMMARY = "summary"
    COXPH = "cox-ph"


class ORGANIZATION_TYPES(int, Enum):
    """Tipos de organizaciones"""

    HOSPITAL = 1
    OTHER = 2


class ORGANIZATION_DATA_AVAILABILITY(int, Enum):
    """Disponibilidad de datos en las organizaciones"""

    AVAILABLE = True
    NOT_AVAILABLE = False
