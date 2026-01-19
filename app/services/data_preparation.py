"""
Servicio para operaciones con workspaces
"""
import base64
import json
import requests
import time

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.data_preparation import DataPreparationRequest, V6TaskResult, V6RunResult
#from vantage6.client import UserClient

class DataPreparationService: 

    IMAGE = "harbor2.vantage6.ai/idea4rc/analytics:latest"
    METHOD = "summary"

    # VARIABLES y NUMERIC_VARIABLES también fijas "de momento"
    VARIABLES = [
        "age", "tumor_size", "histology", "sex",
        "fnclcc_grade", "multifocality", "completeness_of_resection",
        "tumor_rupture", "pre_operative_chemo", "post_operative_chemo",
        "pre_operative_radio", "post_operative_radio",
        "local_recurrence", "distant_metastasis", "status"
    ]

    NUMERIC_VARIABLES = ["age", "tumor_size"]

    API_BASE = "https://vantage6-core.orchestrator.idea.lst.tfo.upm.es/server"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJncG4zend5TUJzeE42QnhPREp1QWN6dDRuVE5WM1RwY095VGZ5VFlfWE5ZIn0.eyJleHAiOjE3NjQyOTk3MjQsImlhdCI6MTc2NDI1NjUyNSwiYXV0aF90aW1lIjoxNzY0MjU2NTI0LCJqdGkiOiJvbnJ0YWM6OWYzZDU4ZWMtNDc4NC00ZGVmLWFiMDctNzkwZDY3MjkyMDg0IiwiaXNzIjoiaHR0cHM6Ly92YW50YWdlNi1hdXRoLm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzL3JlYWxtcy92YW50YWdlNiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI5ZGFjYWJiZi1lMzE4LTQzYzgtODY4MC0wM2FkM2JhNzA4MzYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwdWJsaWNfY2xpZW50Iiwic2lkIjoiMWRjNmRmMWMtNzIzOS00YjUxLWJkZTAtNTdhMDc5MTVmYTJhIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL3ZhbnRhZ2U2LWF1dGgub3JjaGVzdHJhdG9yLmlkZWEubHN0LnRmby51cG0uZXMiLCJodHRwOi8vbG9jYWxob3N0Ojc2ODEiLCJodHRwczovL3ZhbnRhZ2U2Lm9yY2hlc3RyYXRvci5pZGVhLmxzdC50Zm8udXBtLmVzIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXZhbnRhZ2U2Iiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInZhbnRhZ2U2X2NsaWVudF90eXBlIjoidXNlciIsIm5hbWUiOiJGcmFuayBNYXJ0aW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbiIsImdpdmVuX25hbWUiOiJGcmFuayIsImZhbWlseV9uYW1lIjoiTWFydGluIiwiZW1haWwiOiJmLm1hcnRpbkBpa25sLm5sIn0.KELYY7JqWf84RukEgfKOK5ZmXm9Hpv5BoE9MY3P4i3tQZh2OZSb3b9NaLru-1_HWz0p9eiifBMUL0CSwLuKuiF18RidxWCBNaJw8wTOJOmkQVQdAY4t-yKffNNt7q6vhIAf3rfrOXukUWXRkdRP_nZ6EfgvGoa2waA-J6O94JHj2-sauF1oMepuGFmliqNGPc1bqEPh8HzATbCgA-GgF6f8aF-BJNmvP9Mpkd_aOUadzehhaqYOaZIcaOfKzfNXRgKQOm3QZj5mLporJ7rJUWUarCSm10dcE4I7WkV47qeahuYptrDe7UR14kpYZLxxTPJsT5KBJog73z7j9tzHC1Q"
    def __init__(self):
        # import os
       
        

        # Creamos cliente autenticado
        # self.client = UserClient(
        #     "https://vantage6-core.orchestrator.idea.lst.tfo.upm.es:443/server",
        #     auth_url="https://vantage6-auth.orchestrator.idea.lst.tfo.upm.es:443",
        #     auth_client="public_client",
        #     auth_realm="vantage6",
        #     log_level="INFO"
        # )
        # self.client.authenticate(username=username, password=password)

        # Header dinámico
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    # def refresh_token_if_needed(self):
    #     # Si API devuelve 401 → reautenticar y actualizar header
    #     try:
    #         self.client.whoami()
    #     except Exception:
    #         self.client.authenticate()
    #         self.headers["Authorization"] = f"Bearer {self.client._access_token}"


    """
    Service for handling data preparation operations
    """

    def _get_org_ids(self, session_id: int, study_id: int) -> list[int]:
        """
        Simulación: Obtiene las organizaciones asociadas a un estudio.
        En producción → consultar la BBDD.
        """
        # Simulación
        return [3, 1]  # UPM y IKNL

    def _get_dataframe_ids(self, session_id: int, study_id: int) -> list[int]:
        """
        Simulación: Obtiene los IDs de dataframes asociados.
        En producción → consultar la BBDD.
        """
        # Simulación
        pelvis = 76
        rps_pelvis = 77
        rps = 78
        return [pelvis, rps_pelvis, rps]
    
    def _build_payload(self, req: DataPreparationRequest) -> dict:

        org_ids = self._get_org_ids(req.session_id, req.study_id)
        dataframe_ids = self._get_dataframe_ids(req.session_id, req.study_id)

        # argumentos para el algoritmo (en base64)
        algorithm_args = base64.b64encode(
            json.dumps({
                "columns": self.VARIABLES,
                "numeric_columns": self.NUMERIC_VARIABLES,
                "organizations_to_include": org_ids
            }).encode("utf-8")
        ).decode("utf-8")

        org_input = [{
            "id": org_ids[0],   # El central task se ejecuta por la primera org
            "arguments": algorithm_args
        }]

        payload = {
            "name": "Human-readable name of the task",
            "image": self.IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": self.METHOD,
            "organizations": org_input,
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": req.session_id,
            "study_id": req.study_id
        }

        return payload
    
    def create_v6_task(self, req: DataPreparationRequest) -> V6TaskResult:

        payload = self._build_payload(req)

        url = f"{self.API_BASE}/task"
        response = requests.post(
           url,
            headers=self.headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()
        return V6TaskResult(task_id=data["id"])
        
        

    #return V6TaskResult(, job_id=data["job_id"])


# Este metodo hay que ejecutarlo en bucle cada 5 segundos hasta que el estado sea "completed"
    def run_v6_task (self, task_id) -> V6RunResult:
        """
        Check the status of a vantage6 task
        """

        if isinstance(task_id, V6TaskResult):
            task_id = task_id.task_id

        url = f"{self.API_BASE}/run?task_id={task_id}"
        # Poll until the (central) task is finished. We do not concern about the subtasks in
        # this instance. We could consider including them in the future as well?
        
        response = requests.get(
            url,
            headers=self.headers,
        )
        # Since it is a central task we can obtain the [0]th element of the data list as it
        # always should be a single element in a list. Wait until the status returns
        # "completed".
        
       
        try:
            json_data = response.json()
        except Exception:
            raise Exception(
                f"[run_v6_task] Invalid JSON from server.\n"
                f"Status code: {response.status_code}\n"
                f"URL: {url}\n"
                f"Response text: {response.text}"
            )

        if "data" not in json_data:
            raise Exception(
                f"[run_v6_task] API error.\n"
                f"Status code: {response.status_code}\n"
                f"URL: {url}\n"
                f"Response JSON: {json_data}"
            )

        status = json_data["data"][0]["status"]
        return V6RunResult(status=status)

    
    # ESTOOOO ES LO QUE DEVUELVE LOS RESULTADOS FINALES
    def results_v6_task (self, task_id):
        """
        Retrieve the results of a vantage6 task
        """
        # TODO: Make dynamic
        headers = {
            "Authorization": f"Bearer {self.client._access_token}"
        }
       # Get the results of the (central) task, thus the *global* summary statistics.
        response = requests.get(
            f"https://vantage6-core.orchestrator.idea.lst.tfo.upm.es/server/result?task_id={task_id}",
            headers=headers,
        )
        # Again, since it is a central task we can obtain the [0]th element of the data list
        
        try:
            json_data = response.json()
        except Exception:
            raise Exception(f"Invalid JSON from results_v6_task: {response.text}")

        if "data" not in json_data:
            raise Exception(f"API error in results_v6_task: {json_data}")

        try:
            raw = json_data["data"][0]["result"]
            decoded = base64.b64decode(raw).decode("UTF-8")
            return json.loads(decoded)
        except Exception as e:
            raise Exception(f"Error decoding result: {e}, data={json_data}")
        return json.loads(base64.b64decode(response.json()["data"][0]["result"]).decode("UTF-8"))


