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

TOKEN_V6= "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJncG4zend5TUJzeE42QnhPREp1QWN6dDRuVE5WM1RwY095VGZ5VFlfWE5ZIn0.eyJleHAiOjE3NzAyODk0NzMsImlhdCI6MTc2OTE2NjI3MywiYXV0aF90aW1lIjoxNzY5MTY2MjU2LCJqdGkiOiJvbnJ0YWM6YzhhMjIxNWEtMGQwMS00MTM3LWJmYzItY2E4OWFiMDZjM2UyIiwiaXNzIjoiaHR0cHM6Ly92YW50YWdlNi1hdXRoLm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzL3JlYWxtcy92YW50YWdlNiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI5ZGFjYWJiZi1lMzE4LTQzYzgtODY4MC0wM2FkM2JhNzA4MzYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwdWJsaWNfY2xpZW50Iiwic2lkIjoiNjZhYjUzZDktOWMxMy00MWYwLTgyYzYtNDQ1YThkMTQxZjVkIiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3ZhbnRhZ2U2LWF1dGgub3JjaGVzdHJhdG9yLmlkZWEubHN0LnRmby51cG0uZXMiLCJodHRwOi8vbG9jYWxob3N0Ojc2ODEiLCJodHRwczovL3ZhbnRhZ2U2Lm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXZhbnRhZ2U2Iiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInZhbnRhZ2U2X2NsaWVudF90eXBlIjoidXNlciIsIm5hbWUiOiJGcmFuayBNYXJ0aW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbiIsImdpdmVuX25hbWUiOiJGcmFuayIsImZhbWlseV9uYW1lIjoiTWFydGluIiwiZW1haWwiOiJmLm1hcnRpbkBpa25sLm5sIn0.I4xNBBfztMJ5f-in_9Nl9XA4vFhEq2oU4SCn9Bl16rulQeMD6fi9jRCZqbApcNSLgC1RRR8lw8_L6OATLzkPRqBaxbJ2ilKYNSZMtbEwUY8mtQnmN8_0EhZwzKQ0I5FFtn8bUhwiTSdc_BfYH-JkcLpKun179xxq4H0zNy2KK-E6nmsAsoxIY9CYFaDL0GI_Z8HPe7MlMlEq0c3nBPwiiiouKdft31wwx6YZ5sjjtaHwWnrFLBZzRCFq3Jdu8GMj1urvOn4C7YL-3tpbVT2fhkhbCj7qii_abFHgqmam7JUXhym-niJLJPp_udDswq6rkgV1kEL2GzquuOiaMEd53w"


API_BASE = "https://vantage6-core.orchestrator.idea.lst.tfo.upm.es/server"

COLLABORATION_ID = 2