#!/usr/bin/env python3

import requests
import sys
import time
from urllib.parse import urljoin

# Configuración
DOMAIN = "https://orchestrator.idea.lst.tfo.upm.es"
ENDPOINTS = [
    "/",
    "/health",
    "/api/v1/health",
    "/docs"
]

def check_endpoint(base_url, endpoint):
    """Verificar un endpoint específico"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(url, timeout=10, verify=False)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {endpoint} - {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - Error: {e}")
        return False

def main():
    print("🏥 Health Check - RAVEN API")
    print("=" * 40)
    print(f"🌐 Verificando: {DOMAIN}")
    print()
    
    success_count = 0
    total_count = len(ENDPOINTS)
    
    for endpoint in ENDPOINTS:
        if check_endpoint(DOMAIN, endpoint):
            success_count += 1
        time.sleep(0.5)
    
    print()
    print(f"📊 Resultado: {success_count}/{total_count} endpoints funcionando")
    
    if success_count == total_count:
        print("✅ Todos los endpoints están funcionando correctamente")
        sys.exit(0)
    else:
        print("❌ Algunos endpoints tienen problemas")
        sys.exit(1)

if __name__ == "__main__":
    main()