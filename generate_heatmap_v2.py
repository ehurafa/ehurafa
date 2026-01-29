#!/usr/bin/env python3
"""
GitHub Contribution Heatmap Generator - Versão Melhorada
Gera um heatmap SVG com suas contribuições reais do GitHub
"""

import requests
from datetime import datetime, timedelta
import json
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()

# Tenta pegar o username na seguinte ordem:
# 1. GITHUB_USERNAME (definido no .env ou manualmente)
# 2. GITHUB_ACTOR (definido automaticamente pelo GitHub Actions)
# 3. USERNAME (usuário do sistema - fallback para testar localmente, mas cuidado no Windows)
USERNAME = os.environ.get('GITHUB_USERNAME') or os.environ.get('GITHUB_ACTOR') or os.environ.get('USERNAME', 'ehurafa')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Cores personalizadas (seus 8 níveis)
COLORS = {
    0: "#1a1e2e",           # Sem commits
    1: "rgb(255,255,255)",  # 1-2 commits - Branco
    2: "#ffff3e",           # 3-4 commits - Amarelo vibrante
    3: "#FFD700",           # 5 commits - Dourado
    4: "rgb(255,160,90)",   # 6 commits - Laranja claro
    5: "rgb(255,130,60)",   # 7 commits - Laranja
    6: "rgb(255,100,40)",   # 8 commits - Laranja avermelhado
    7: "rgb(255,60,30)",    # 9 commits - Vermelho alaranjado
    8: "rgb(255,0,0)",      # 10+ commits - Vermelho
}

def get_level(count):
    """Converte número de commits em nível de cor"""
    if count == 0: return 0
    if count >= 10: return 8
    if count == 9: return 7
    if count == 8: return 6
    if count == 7: return 5
    if count == 6: return 4
    if count == 5: return 3
    if count >= 3: return 2
    return 1

def fetch_contributions_graphql(username, token):
    """Busca contribuições via GraphQL API"""
    url = "https://api.github.com/graphql"
    
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {
        "query": query,
        "variables": {"username": username}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        
        if "errors" in data:
            print(f"⚠️  Erro GraphQL: {data['errors']}")
            return None
            
        if "data" in data and data["data"]["user"]:
            return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        
        return None
    except Exception as e:
        print(f"⚠️  Erro ao buscar via GraphQL: {e}")
        return None

def fetch_contributions_rest(username, token):
    """Busca contribuições via REST API (fallback)"""
    print("🔄 Tentando método alternativo (REST API)...")
    
    # Busca eventos dos últimos 365 dias
    contributions_by_date = {}
    today = datetime.now()
    
    # Inicializa últimos 365 dias com 0
    for i in range(365):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        contributions_by_date[date] = 0
    
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        # Busca eventos públicos do usuário
        page = 1
        while page <= 3:  # Limita a 3 páginas para não demorar muito
            url = f"https://api.github.com/users/{username}/events/public?per_page=100&page={page}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  Status code: {response.status_code}")
                break
            
            events = response.json()
            if not events:
                break
            
            for event in events:
                if event['type'] in ['PushEvent', 'PullRequestEvent', 'IssuesEvent', 
                                     'CreateEvent', 'DeleteEvent', 'CommitCommentEvent']:
                    date = event['created_at'][:10]  # YYYY-MM-DD
                    if date in contributions_by_date:
                        contributions_by_date[date] += 1
            
            page += 1
        
        # Converte para formato esperado
        total = sum(contributions_by_date.values())
        
        if total == 0:
            print("⚠️  Nenhuma contribuição pública encontrada nos últimos meses")
            return None
        
        # Organiza por semanas
        weeks = []
        current_week = []
        
        # Começa no domingo mais recente
        start_date = today
        while start_date.weekday() != 6:  # 6 = domingo
            start_date -= timedelta(days=1)
        
        for i in range(365):
            date = start_date - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            day_data = {
                "contributionCount": contributions_by_date.get(date_str, 0),
                "date": date_str
            }
            
            current_week.insert(0, day_data)
            
            if date.weekday() == 6 or i == 364:  # Domingo ou último dia
                weeks.insert(0, {"contributionDays": current_week})
                current_week = []
        
        return {
            "totalContributions": total,
            "weeks": weeks
        }
        
    except Exception as e:
        print(f"⚠️  Erro REST API: {e}")
        return None

def generate_fake_data():
    """Gera dados de exemplo para demonstração"""
    print("⚠️  Gerando dados de exemplo para demonstração...")
    
    import random
    contributions_by_date = {}
    today = datetime.now()
    total = 0
    
    for i in range(365):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        # Gera dados aleatórios
        if random.random() < 0.7:  # 70% de chance de ter commits
            count = random.choices(
                [0, 1, 2, 3, 5, 7, 10, 15],
                weights=[30, 25, 20, 10, 7, 5, 2, 1]
            )[0]
            contributions_by_date[date] = count
            total += count
        else:
            contributions_by_date[date] = 0
    
    # Organiza por semanas
    weeks = []
    current_week = []
    
    start_date = today
    while start_date.weekday() != 6:
        start_date -= timedelta(days=1)
    
    for i in range(365):
        date = start_date - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        day_data = {
            "contributionCount": contributions_by_date.get(date_str, 0),
            "date": date_str
        }
        
        current_week.insert(0, day_data)
        
        if date.weekday() == 6 or i == 364:
            weeks.insert(0, {"contributionDays": current_week})
            current_week = []
    
    return {
        "totalContributions": total,
        "weeks": weeks
    }

def generate_svg_heatmap(contributions_data):
    """Gera o SVG do heatmap"""
    
    cell_size = 12
    cell_gap = 4
    total_cell = cell_size + cell_gap
    
    weeks = contributions_data["weeks"][-52:]  # Últimas 52 semanas
    
    width = len(weeks) * total_cell + 40
    height = 7 * total_cell + 60
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .day {{ rx: 2; ry: 2; transition: all 0.2s; }}
        .day:hover {{ stroke: #ff6b00; stroke-width: 2; }}
        text {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: #8b949e; }}
        .fire {{ animation: burn 1.5s ease-in-out infinite; }}
        @keyframes burn {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
    </style>
    <rect width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Título -->
    <text x="10" y="20" fill="#c9d1d9" font-size="14" font-weight="600">
        <tspan fill="#ff6b00">{contributions_data["totalContributions"]}</tspan> contributions in the last year
    </text>
    
    <!-- Labels dos dias -->
'''
    
    days_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, label in enumerate(days_labels):
        if label:
            svg += f'    <text x="5" y="{50 + i * total_cell}" text-anchor="end">{label}</text>\n'
    
    # Meses
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_month = -1
    
    # Grid de contribuições
    for week_idx, week in enumerate(weeks):
        x = 40 + week_idx * total_cell
        
        for day_idx, day in enumerate(week["contributionDays"]):
            y = 40 + day_idx * total_cell
            count = day["contributionCount"]
            level = get_level(count)
            color = COLORS[level]
            
            # Label do mês
            date = datetime.fromisoformat(day["date"])
            if date.month != current_month and day_idx == 0:
                current_month = date.month
                svg += f'    <text x="{x}" y="35">{months[current_month - 1]}</text>\n'
            
            # Quadrado com animação para nível 8
            class_name = "day fire" if level == 8 else "day"
            fill = "url(#fireGradient)" if level == 8 else color
            
            svg += f'    <rect class="{class_name}" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}"/>\n'
    
    # Gradiente de fogo
    svg += '''
    <defs>
        <linearGradient id="fireGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:rgb(255,0,0);stop-opacity:1">
                <animate attributeName="stop-color" values="rgb(255,0,0);rgb(255,50,0);rgb(255,0,0)" dur="1.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="50%" style="stop-color:rgb(255,30,15);stop-opacity:1"/>
            <stop offset="100%" style="stop-color:rgb(255,60,30);stop-opacity:1">
                <animate attributeName="stop-color" values="rgb(255,60,30);rgb(255,100,50);rgb(255,60,30)" dur="1.5s" repeatCount="indefinite"/>
            </stop>
        </linearGradient>
    </defs>
    
    <!-- Legenda -->
    <g transform="translate(10, ''' + str(height - 25) + ''')">
        <text y="12">Less</text>
'''
    
    legend_x = 50
    for level in range(9):
        svg += f'        <rect x="{legend_x + level * (cell_size + 2)}" width="{cell_size}" height="{cell_size}" fill="{COLORS[level]}" rx="2"/>\n'
    
    svg += f'''        <text x="{legend_x + 9 * (cell_size + 2) + 10}" y="12">More 🔥</text>
    </g>
</svg>'''
    
    return svg

def main():
    print(f"🔥 GitHub Heatmap Generator")
    print(f"📊 Buscando contribuições de @{USERNAME}...\n")
    
    contributions = None
    
    # Tenta GraphQL primeiro
    if GITHUB_TOKEN:
        print("🔑 Token encontrado, usando GraphQL API...")
        contributions = fetch_contributions_graphql(USERNAME, GITHUB_TOKEN)
    else:
        print("⚠️  Nenhum token fornecido")
    
    # Fallback para REST API
    if not contributions or contributions["totalContributions"] == 0:
        contributions = fetch_contributions_rest(USERNAME, GITHUB_TOKEN)
    
    # Se ainda não tiver dados, gera exemplos
    if not contributions or contributions["totalContributions"] == 0:
        print("\n" + "="*60)
        print("⚠️  NÃO FOI POSSÍVEL BUSCAR SEUS DADOS REAIS")
        print("="*60)
        print("\n💡 Para usar seus dados reais:")
        print("1. Crie um token: https://github.com/settings/tokens")
        print("2. Marque a permissão: read:user")
        print("3. Execute:")
        print(f"   export GITHUB_TOKEN='seu_token_aqui'")
        print(f"   python generate_heatmap.py")
        print("\n📝 Por enquanto, gerando dados de exemplo...\n")
        contributions = generate_fake_data()
    
    # Gera o SVG
    svg_content = generate_svg_heatmap(contributions)
    
    # Salva
    output_file = "github-heatmap.svg"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"\n✅ Heatmap gerado: {output_file}")
    print(f"📊 Total: {contributions['totalContributions']} contribuições")
    print(f"\n🎯 Adicione ao README:")
    print(f"   ![GitHub Heatmap](./github-heatmap.svg)\n")

if __name__ == "__main__":
    main()
