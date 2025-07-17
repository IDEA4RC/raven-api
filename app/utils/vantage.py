from vantage.client import Client

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
) -> Optional[Client]:
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

def create_vantage_organization(
    organization_data: str
) -> Optional[dict]:

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
    user_data: dict
) -> Optional[dict]:
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
