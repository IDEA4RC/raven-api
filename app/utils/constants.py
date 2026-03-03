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


TOKEN_V6 = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJncG4zend5TUJzeE42QnhPREp1QWN6dDRuVE5WM1RwY095VGZ5VFlfWE5ZIn0.eyJleHAiOjE3NzI5ODYwNzQsImlhdCI6MTc3MTg2Mjg3NCwiYXV0aF90aW1lIjoxNzcxODYyODY1LCJqdGkiOiJvbnJ0YWM6ZWM1ZTY4Y2MtMTdlNC00YzJmLTg0ZTktZWJjNTBhZDU5NTJmIiwiaXNzIjoiaHR0cHM6Ly92YW50YWdlNi1hdXRoLm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzL3JlYWxtcy92YW50YWdlNiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI5ZGFjYWJiZi1lMzE4LTQzYzgtODY4MC0wM2FkM2JhNzA4MzYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwdWJsaWNfY2xpZW50Iiwic2lkIjoiMjcyOTcxZGUtZGUwNS00ZjY3LWE4ZmYtZDczY2FlNDFlMTRkIiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3ZhbnRhZ2U2LWF1dGgub3JjaGVzdHJhdG9yLmlkZWEubHN0LnRmby51cG0uZXMiLCJodHRwOi8vbG9jYWxob3N0Ojc2ODEiLCJodHRwczovL3ZhbnRhZ2U2Lm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXZhbnRhZ2U2Iiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInZhbnRhZ2U2X2NsaWVudF90eXBlIjoidXNlciIsIm5hbWUiOiJGcmFuayBNYXJ0aW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbiIsImdpdmVuX25hbWUiOiJGcmFuayIsImZhbWlseV9uYW1lIjoiTWFydGluIiwiZW1haWwiOiJmLm1hcnRpbkBpa25sLm5sIn0.Sc3YqZe4C7-wSVaBiZ4nyCx6hywyc_sqk29QKt-doK3MOyBXMPaSsCKD28m4CX9THeUQmQGllswcrO2JpUe4tbyDueu_Ksj3Jz8SEzEqo1luYwFRK350J7ovH99IrL7-MC0R60PU2eBhVMrNDsOFcU0gUMdHaqho8_0X8NW2xixlp0xgqfElY0sqwrS4h6wdyCAjzM1qaw9aczYXPwn7wztTIZEfMB5qXrzRoUaxYu-qiXu0Sb5WKKFxVRpUVx383MO_4v1QsjXO2HhVyXiKDza-WBGK0sxwj8o9bLB3CDZHUHw9V5DPIDpOHF1Jsn1eJpGuLAfndDewtjg1HrO8JQ"

API_BASE = "https://vantage6-core.orchestrator.idea.lst.tfo.upm.es/server"

COLLABORATION_ID = 3

ORGANIZATION_IDS = {1, 4}


class typeOfDiseases(Enum):
    """Tipos de enfermedades"""

    SARCOMA = "sarc"
    HAndN = "head_and_neck"
