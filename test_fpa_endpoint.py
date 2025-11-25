import requests
import json

# Configuración
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/auth/login'
API_URL = f'{BASE_URL}/tickets/api/calculate-fpa'

# Credenciales (Usuario de Providencia)
USERNAME = 'admin_prov'
PASSWORD = 'password123'

# Datos para el cálculo (ajustar según lo que existe en BD)
PAYLOAD = {
    'surgery_id': 1,              # ID de la cirugía "rodilla"
    'pavilion_end_time': '2025-11-24T22:10',
    'clinic_id': 4                # ID de Clínica RedSalud Providencia
}

def test_endpoint():
    session = requests.Session()
    
    print(f"1. Iniciando sesión como {USERNAME}...")
    try:
        # Primero obtenemos el CSRF token si es necesario (flask-wtf)
        # Pero para login simple a veces basta con post
        login_data = {
            'username': USERNAME,
            'password': PASSWORD
        }
        response = session.post(LOGIN_URL, data=login_data)
        
        if response.status_code != 200 and response.status_code != 302:
            print(f"❌ Error en login: {response.status_code}")
            print(response.text)
            return

        print("✅ Login exitoso (o redirección recibida)")
        
        print(f"\n2. Probando endpoint {API_URL}...")
        print(f"   Enviando datos: {json.dumps(PAYLOAD, indent=2)}")
        
        # Necesitamos el CSRF token para peticiones POST
        # Intentamos obtenerlo de la cookie o header si existe
        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Hacemos la petición
        response = session.post(API_URL, json=PAYLOAD, headers=headers)
        
        print(f"\n3. Resultado:")
        print(f"   Status Code: {response.status_code}")
        
        try:
            json_response = response.json()
            print(f"   Respuesta JSON:\n{json.dumps(json_response, indent=2)}")
        except:
            print(f"   Respuesta Texto:\n{response.text}")
            
    except Exception as e:
        print(f"❌ Error ejecutando prueba: {str(e)}")

if __name__ == '__main__':
    test_endpoint()
