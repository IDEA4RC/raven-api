from typing import Optional, Dict, Any
import logging

import requests
import json
import base64

from vantage6.client import UserClient

logger = logging.getLogger(__name__)

# def get_vantage_token(
#     username: str,
#     password: str
# ) -> Optional[dict]:
#     """
#     Obtiene un token de acceso para Vantage utilizando las credenciales del usuario.
    
#     Args:
#         username (str): Nombre de usuario.
#         password (str): Contraseña del usuario.
    
#     Returns:
#         Optional[dict]: Diccionario con el token de acceso y otros datos, o None si falla.
#     """
#     auth_response = requests.post(
#         "https://orchestrator.idea.lst.tfo.upm.es/server/token/user",
#         json={
#             "username": username,
#             "password": password
#         }
#     )
#     if auth_response.status_code != 200:
#         logger.error(f"Error obtaining Vantage token: {auth_response.text}")
#         return None
#     return auth_response.json()
#

def create_vantage_client(
    username: str,
    password: str
) -> Optional[Any]:
    try:
        # Import lazily to make this optional
        from vantage.client import Client  # type: ignore
    except Exception:  # pragma: no cover - optional dependency missing
        logger.warning("vantage.client not installed; create_vantage_client is a no-op")
        return None
    try:
        client = Client(
            "https://orchestrator.idea.lst.tfo.upm.es",
            443,
            "/server",
            log_level="INFO",
        )
        client.authenticate(
            username=username,
            password=password
        )
        logger.info("Vantage client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating Vantage client: {e}")
        return None

def create_vantage_user_client(username: str, password: str):
    from vantage6.client import UserClient
    
    client = UserClient(
        host="https://vantage6-core.orchestrator.idea.lst.tfo.upm.es",
        port=443,
        path="/server",
        auth_url="https://vantage6-auth.orchestrator.idea.lst.tfo.upm.es:443",
        auth_client="public_client",
        auth_realm="vantage6",
        log_level="INFO"
    )

    client.authenticate(username=username, password=password)

    return client._access_token

def create_vantage_organization(
    organization_data: Dict[str, Any]
) -> Optional[dict]:
    # Client will be imported in create_vantage_client
    client = create_vantage_client(
        "root",
        "root"
    )
    if not client:
        return None
    try:
        org = client.organizations.create(
            name=organization_data.get("org_name"),
            address1=organization_data.get("org_city"),
            address2="",
            zipcode="",
            country="",
            domain=organization_data.get("org_name"),
        )
        return org
    except Exception as e:
        logger.error(f"Error creating Vantage organization: {e}")
        return None
    
def create_vantage_user(
    user_data: Dict[str, Any]
) -> Optional[dict]:
    # Client will be imported in create_vantage_client
    client = create_vantage_client(
        "root",
        "root"
    )
    if not client:
        return None
    try:
        user = client.users.create(
            username=user_data.get("username"),
            password="root",
            email=user_data.get("email"),
            firstname=user_data.get("first_name"),
            lastname=user_data.get("last_name"),
            organization=user_data.get("organization_id"),
            roles=[6],  
        )
        return user
    except Exception as e:
        logger.error(f"Error creating Vantage user: {e}")
        return None

def algorithm_org_input(
    collaboration_data: Dict[str, Any]
) -> Optional[dict]:
    # Client will be imported in create_vantage_client
    #client = create_vantage_client(        "root",        "root"    )

    STUDY_ID = 3
    #
    # A session that is already part of the study is 2
    SESSION_ID = 2
    #
    # The image to use is the latest version of the sessions algorithm
    IMAGE = "harbor2.vantage6.ai/idea4rc/analytics:latest"
    #
    # The method (that is within this IMAGE) to execute is the summary algorithm
    METHOD = "summary"
    #
    # Organization IDs for UPM and IKNL
    UPM_ORG_ID = 3
    IKNL_ORG_ID = 1
    ORG_IDS = [UPM_ORG_ID, IKNL_ORG_ID]

    # Besides that the vantage6 server expect a certain payload the algorithm also
    # expects certain input:
    #
    # * DATAFRAME_IDS (the IDs of the dataframes to include in the analysis)
    # * VARIABLES (the variables to include in the analysis)
    # * NUMERIC_VARIABLES (the numeric variables that are included in the analysis, should
    #   be a subset of VARIABLES)
    #
    #
    # These dataframes are already created and part of the session/study.
    pelvis = 76 # Pelvis cohort ID
    rps_pelvis = 77 # RPS+Pelvis cohort ID
    rps = 78 # RPS cohort ID
    DATAFRAME_IDS = [pelvis, rps_pelvis, rps]
    #
    # These are the variables that currently exist in the dataframes.
    VARIABLES = [
        "age", # num
        "tumor_size", # num
        "histology", # cat
        "sex", # cat
        "fnclcc_grade", # cat
        "multifocality", # cat
        "completeness_of_resection", # cat
        "tumor_rupture", # cat
        "pre_operative_chemo", # cat
        "post_operative_chemo", # cat
        "pre_operative_radio", # cat
        "post_operative_radio", # cat
        "local_recurrence", # cat
        "distant_metastasis", # cat
        "status", # cat
    ]
    #
    # From these variables, the numeric variables are:
    NUMERIC_VARIABLES = [
        "age",
        "tumor_size"
    ]
    #
    # The input for the central part of the algorithm is the following.
    #
    # * The variables to include in the analysis
    # * The numeric variables to include in the analysis
    # * The organizations to include in the analysis
    #
    # These require to be encoded as follows:
    org_input = [
        {
            "id": UPM_ORG_ID, # Central task is executed by UPM
            "arguments": base64.b64encode(
                json.dumps(
                    {
                        "columns": VARIABLES,
                        "numeric_columns": NUMERIC_VARIABLES,
                        "organizations_to_include": ORG_IDS
                    }
                ).encode("UTF-8")
            ).decode("UTF-8")
        }
    ]

    # Then the full payload of both the server requirements and the algorithm input is:
    payload = {
        "name": "Human-readable name of the task",
        "image": IMAGE,
        "description": "Description of the task",
        "action": "central_compute",
        "method": METHOD,
        "organizations": org_input,
        "databases": [
            [
                {
                    "type": "dataframe",
                    "dataframe_id": df_id
                } for df_id in DATAFRAME_IDS
            ]
        ],
        "session_id": SESSION_ID,
        "study_id": STUDY_ID
    }

    if not client:
        return None
    try:
        collab = client.collaborations.create(
            name=collaboration_data.get("collab_name"),
            description=collaboration_data.get("collab_description"),
            organization=collaboration_data.get("organization_id"),
        )
        return collab
    except Exception as e:
        logger.error(f"Error creating Vantage collaboration: {e}")
        return None