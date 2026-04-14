"""
Focus Concursos API Scraper v2
Usa o appToken já descoberto para chamar a API e extrair todos os links.
"""
import requests
import json
import sqlite3
import base64

APP_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbnN0aXR1dGlvbiI6NCwiaWF0IjoxNTE2MjM5MDIyfQ.mn0-q3vdGWFm_XnUpiQr2-WsfMbrKiKMnxaPmyYHe3E"
EMAIL = "gor461@gmail.com"
PASSWORD = "Senha012"
COURSE_ID = "1313054044"
DB_PATH = "tjsc_plan.db"

def get_real_token(session, app_token):
    """Obtém token real de usuário autenticado."""
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://lms.focusconcursos.com.br",
        "Referer": "https://lms.focusconcursos.com.br/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    
    login_payloads = [
        {"email": EMAIL, "password": PASSWORD},
        {"email": EMAIL, "senha": PASSWORD},
        {"login": EMAIL, "password": PASSWORD},
        {"login": EMAIL, "senha": PASSWORD},
        {"username": EMAIL, "password": PASSWORD},
    ]
    
    lms_login_endpoints = [
        "https://lms.focusconcursos.com.br/api/login",
        "https://lms.focusconcursos.com.br/api/v1/login",
        "https://lms.focusconcursos.com.br/api/auth",
        "https://lms.focusconcursos.com.br/login",
        "https://lms.focusconcursos.com.br/api/v1/auth/login",
        "https://lms.focusconcursos.com.br/api/usuario/login",
        "https://lms.focusconcursos.com.br/api/user/login",
    ]
    
    for endpoint in lms_login_endpoints:
        for payload in login_payloads[:2]:  # Test only first 2 payloads per endpoint
            try:
                resp = session.post(endpoint, json=payload, headers=headers, timeout=8)
                print(f"  {endpoint}: {resp.status_code}", end="")
                if resp.status_code == 200 and len(resp.text) > 10:
                    try:
                        data = resp.json()
                        print(f" -> {str(data)[:100]}")
                        token = (data.get('token') or data.get('access_token') or 
                                data.get('data', {}).get('token'))
                        if token:
                            return token, data
                    except:
                        print(f" -> HTML (not JSON)")
                else:
                    print()
            except Exception as e:
                print(f"  {endpoint}: ERR {str(e)[:50]}")
    
    return None, None

def probe_course_api(session, token=None):
    """Tenta descobrir a API de cursos."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://lms.focusconcursos.com.br",
        "Referer": f"https://lms.focusconcursos.com.br/#/curso/{COURSE_ID}",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    endpoints = [
        f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}",
        f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}/subjects",
        f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}/lessons",
        f"https://lms.focusconcursos.com.br/api/courses/{COURSE_ID}",
        f"https://lms.focusconcursos.com.br/api/courses/{COURSE_ID}/subjects",
        f"https://lms.focusconcursos.com.br/api/courses/{COURSE_ID}/lessons",
        f"https://lms.focusconcursos.com.br/api/cursos/{COURSE_ID}",
        f"https://lms.focusconcursos.com.br/api/course/{COURSE_ID}",
        f"https://lms.focusconcursos.com.br/api/v2/cursos/{COURSE_ID}",
        f"https://lms.focusconcursos.com.br/api/v1/subscriptions",
        f"https://lms.focusconcursos.com.br/api/v1/enrollment",
        f"https://lms.focusconcursos.com.br/api/v1/user/courses",
        f"https://lms.focusconcursos.com.br/api/v1/subjects?course={COURSE_ID}",
    ]
    
    results = []
    for ep in endpoints:
        try:
            resp = session.get(ep, headers=headers, timeout=8)
            if resp.status_code not in [404, 405]:
                content_type = resp.headers.get('Content-Type', '')
                is_json = 'json' in content_type
                print(f"  [{resp.status_code}] {ep}")
                if resp.status_code == 200 and is_json:
                    data = resp.json()
                    print(f"       JSON: {str(data)[:200]}")
                    results.append((ep, data))
        except Exception as e:
            pass
    
    return results

def update_db_with_video_links(conn, lessons):
    """Atualiza o banco de dados com os links de vídeo."""
    cursor = conn.cursor()
    updated = 0
    
    for lesson in lessons:
        title = lesson.get('title', '')
        link = lesson.get('link', '')
        
        if title and link:
            # Match flexível
            cursor.execute('''
                UPDATE classes SET video_link = ? 
                WHERE LOWER(REPLACE(REPLACE(title, '|', '-'), '  ', ' ')) 
                    LIKE LOWER(REPLACE(?)
            ''', (link, f"%{title[:30]}%"))
            if cursor.rowcount > 0:
                updated += 1
    
    conn.commit()
    return updated

def check_lms_graphql(session):
    """Verifica se o LMS usa GraphQL."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://lms.focusconcursos.com.br",
    }
    
    query = {"query": "{ __typename }"}
    graphql_endpoints = [
        "https://lms.focusconcursos.com.br/graphql",
        "https://lms.focusconcursos.com.br/api/graphql",
        "https://lms.focusconcursos.com.br/api/v1/graphql",
    ]
    
    print("\n[GraphQL Check]")
    for ep in graphql_endpoints:
        try:
            resp = session.post(ep, json=query, headers=headers, timeout=5)
            print(f"  {ep}: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  -> GRAPHQL! {resp.text[:200]}")
        except Exception as e:
            print(f"  {ep}: {str(e)[:50]}")

def setup_video_link_column():
    """Garante que a coluna video_link existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE classes ADD COLUMN video_link TEXT')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    return conn

def main():
    print("=" * 60)
    print("Focus API Scraper v2 - Encontrando API real")
    print("=" * 60)
    
    conn = setup_video_link_column()
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    # 1. Autenticar via site para obter cookies de sessão
    print("\n[STEP 1] Login web...")
    login_page = session.get("https://focusconcursos.com.br/login/")
    session.post(
        "https://focusconcursos.com.br/login/",
        data={"email": EMAIL, "password": PASSWORD, "action": "login"},
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Referer": "https://focusconcursos.com.br/login/"},
        allow_redirects=True
    )
    print(f"   Cookies: {list(session.cookies.keys())}")

    # 2. Acessar LMS para pegar cookies de sessão  
    print("\n[STEP 2] Acessando LMS...")
    session.get("https://lms.focusconcursos.com.br/")
    print(f"   Cookies: {list(session.cookies.keys())}")
    
    # 3. Tentar obter token real
    print("\n[STEP 3] Tentando obter token autenticado...")
    user_token, auth_data = get_real_token(session, APP_TOKEN)
    
    # 4. Probe endpoints
    print("\n[STEP 4] Explorando endpoints da API...")
    results = probe_course_api(session, user_token or APP_TOKEN)
    
    # 5. Check GraphQL
    check_lms_graphql(session)
    
    # 6. Tentar acessar endpoints de aula diretos conhecidos
    print("\n[STEP 5] Tentando endpoints de aulas conhecidos...")
    known_subject_ids = [
        "69cdc412d18e69e490011aac",  # Língua Portuguesa
        "69cdcac5d18e69e4bb292c86",  # Informática  
        "69cdd11ad18e69319578b8fa",  # Adm Geral
        "69cdd248d18e6931ba1b1afe",  # Gestão de Pessoas
        "69cdc520d18e69e486550eb8",  # Legislação
    ]
    
    for subj_id in known_subject_ids[:2]:
        ep = f"https://lms.focusconcursos.com.br/api/v1/subjects/{subj_id}/lessons"
        try:
            resp = session.get(ep, timeout=8)
            print(f"  [{resp.status_code}] {ep}")
            if resp.status_code == 200:
                print(f"  -> {resp.text[:200]}")
        except Exception as e:
            print(f"  ERR: {str(e)[:60]}")
    
    print("\n[FIM] Análise completa.")
    
    if results:
        print(f"\nEncontrados {len(results)} endpoints úteis!")
        for ep, data in results:
            print(f"  -> {ep}")
    
    conn.close()

if __name__ == "__main__":
    main()
