"""
Intercepta os headers de Authorization reais que o SPA envia
analisando os cookies e o JS bundle para descobrir a API real.
"""
import requests
import re
import json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# --- Login ---
session.get('https://focusconcursos.com.br/login/')
session.post('https://focusconcursos.com.br/login/',
    data={'email': 'gor461@gmail.com', 'password': 'Senha012'},
    headers={'Content-Type': 'application/x-www-form-urlencoded',
             'Referer': 'https://focusconcursos.com.br/login/'})
session.get('https://lms.focusconcursos.com.br/')

print("[1] Cookies:", list(session.cookies.keys()))

# --- Analisar o index.html do LMS para encontrar pistas da API ---
print("\n[2] Analisando o JS do LMS...")
lms_html = session.get("https://lms.focusconcursos.com.br/").text

# Procura URLs de API no HTML
api_patterns = re.findall(r'https?://[a-zA-Z0-9\-\.]+/api[\'"\s/]', lms_html)
print("  APIs encontradas no HTML:", set(api_patterns))

# Procura scripts JS
scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', lms_html)
print(f"  Scripts encontrados: {len(scripts)}")

# Analisa o maior JS bundle
for script_url in scripts[:5]:
    if not script_url.startswith('http'):
        script_url = 'https://lms.focusconcursos.com.br' + script_url
    try:
        js = session.get(script_url, timeout=10).text
        # Procura padrões de URL de API no JS
        api_urls = re.findall(r'["\'](/api/[a-zA-Z0-9\-_/{}]+)["\']', js)
        base_urls = re.findall(r'baseURL["\s]*[:=]["\s]*["\']([^"\']+)["\']', js)
        api_endpoint = re.findall(r'apiUrl["\s]*[:=]["\s]*["\']([^"\']+)["\']', js)
        
        if api_urls or base_urls or api_endpoint:
            print(f"\n  Script: {script_url[:80]}")
            if base_urls:
                print(f"  baseURL: {base_urls[:5]}")
            if api_endpoint:
                print(f"  apiUrl: {api_endpoint[:5]}")
            if api_urls:
                print(f"  Rotas API: {set(api_urls[:20])}")
    except Exception as e:
        print(f"  Erro no script: {e}")

# --- Tentar via Hotmart / EAD (plataformas comuns de LMS no Brasil) ---
print("\n[3] Procurando metadados da sessão...")
# O appToken é um JWT - vamos decodificar para ver payload
app_token = session.cookies.get('@focusconcursos:appToken', '')
if app_token:
    # Decodifica a parte do payload (sem verificação de assinatura)
    parts = app_token.split('.')
    if len(parts) >= 2:
        import base64
        payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
        try:
            payload = json.loads(base64.b64decode(payload_b64))
            print(f"  Token payload: {payload}")
        except:
            print(f"  Token base64 payload (raw): {payload_b64[:100]}")

# Query Params cookie decode
query_params = session.cookies.get('@focusconcursos:queryParams', '')
if query_params and query_params.startswith('v2.'):
    try:
        decoded = base64.b64decode(query_params[3:] + '==').decode()
        print(f"  queryParams: {decoded}")
    except:
        print(f"  queryParams (raw): {query_params[:100]}")
