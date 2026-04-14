import requests

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

# Login para pegar cookies
session.get('https://focusconcursos.com.br/login/')
session.post('https://focusconcursos.com.br/login/',
    data={'email': 'gor461@gmail.com', 'password': 'Senha012'},
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://focusconcursos.com.br/login/'
    })
session.get('https://lms.focusconcursos.com.br/')

print("Cookies:", list(session.cookies.keys()))

COURSE_ID = "1313054044"

# Tenta endpoints que um SPA Vue.js geralmente usa
endpoints = [
    f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}",
    f"https://lms.focusconcursos.com.br/api/v1/courses/{COURSE_ID}",
    f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}/subjects",
    f"https://lms.focusconcursos.com.br/api/v1/cursos/{COURSE_ID}/aulas",
    f"https://lms.focusconcursos.com.br/api/v2/cursos/{COURSE_ID}",
    f"https://lms.focusconcursos.com.br/api/cursos/{COURSE_ID}",
    f"https://lms.focusconcursos.com.br/cursos/{COURSE_ID}/aulas",
    # API alternativa (Hotmart/Eduzz/Vimeo etc.)
    f"https://lms.focusconcursos.com.br/api/v1/subscription/{COURSE_ID}",
    f"https://lms.focusconcursos.com.br/api/v1/enrollment/{COURSE_ID}",
    # Tentar achar endpoint raiz
    "https://lms.focusconcursos.com.br/api/v1/",
    "https://lms.focusconcursos.com.br/api/",
    "https://lms.focusconcursos.com.br/api/v1/user/me", 
    "https://lms.focusconcursos.com.br/api/v1/aluno/me",
    "https://lms.focusconcursos.com.br/api/v1/student/me",
]

for url in endpoints:
    try:
        r = session.get(url, timeout=6)
        status = r.status_code
        content_type = r.headers.get('Content-Type', '')
        preview = r.text[:150].replace('\n', ' ') if status != 404 else ''
        print(f"[{status}] {url}")
        if status == 200 and 'json' in content_type:
            print(f"         JSON -> {preview}")
        elif status not in [404, 405]:
            print(f"         -> {preview}")
    except Exception as e:
        print(f"[ERR] {url}: {str(e)[:60]}")
