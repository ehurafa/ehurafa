#!/usr/bin/env python3
"""
GitHub Contribution Heatmap Generator - Versão 4 (Fogo Azul com Fagulhas)
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
MONTHS_TO_SHOW = int(os.environ.get('MONTHS_TO_SHOW', 6)) # Default: 6 meses
THEME = os.environ.get('THEME', 'light') # 'light' or 'dark'

# Configuração de Temas
THEMES = {
    "dark": {
        "bg": "#0d1117",
        "text": "#8b949e",
        "empty": "#1a1e2e",
        "title": "#c9d1d9"
    },
    "light": {
        "bg": "#ffffff",
        "text": "#24292f",
        "empty": "#ebedf0",
        "title": "#24292f"
    }
}

current_theme = THEMES.get(THEME, THEMES["dark"])

# Cores personalizadas (9 níveis - incluindo fogo azul)
COLORS = {
    0: current_theme["empty"],           # Sem commits
    1: "hsl(60, 100%, 92%)",  # 1-2 commits - Amarelo muito claro
    2: "#ffff3e",           # 3-4 commits - Amarelo vibrante
    3: "#FFD700",           # 5 commits - Dourado
    4: "rgb(255,160,90)",   # 6 commits - Laranja claro
    5: "rgb(255,130,60)",   # 7 commits - Laranja
    6: "rgb(255,100,40)",   # 8 commits - Laranja avermelhado
    7: "rgb(255,60,30)",    # 9 commits - Vermelho alaranjado
    8: "rgb(255,0,0)",      # 10 commits - Fogo Vermelho
    9: "#00EEFF",           # 12+ commits - Fogo Azul (Super Intenso)
}

def get_level(count):
    """Converte número de commits em nível de cor"""
    if count == 0: return 0
    if count >= 12: return 9  # Fogo Azul (Super Intenso)
    if count >= 10: return 8  # Fogo Vermelho
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
    
    cell_size = 22
    cell_gap = 4
    total_cell = cell_size + cell_gap
    
    # Calcula semanas baseado nos meses (aprox 4.33 semanas por mês)
    weeks_to_show = int(MONTHS_TO_SHOW * 4.33)
    weeks = contributions_data["weeks"][-weeks_to_show:]
    
    width = len(weeks) * total_cell + 80  # Espaço à direita para brilho
    height = 7 * total_cell + 120  # Espaço para legenda e brilho
    
    svg = f'''<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .day {{ rx: 2; ry: 2; transition: all 0.2s; }}
        .day:hover {{ stroke: #ff6b00; stroke-width: 2; }}
        text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"; font-size: 10px; fill: {current_theme["text"]}; }}
        
        /* Fogo Vermelho (Nível 8) - Intensidade Reduzida */
        .fire-red {{ 
            rx: 2;
            animation: pulseFireRed 2s ease-in-out infinite;
            filter: drop-shadow(0 0 6px rgba(255, 100, 0, 0.6));
        }}
        
        @keyframes pulseFireRed {{
            0% {{ 
                filter: 
                    drop-shadow(0 -3px 6px rgba(255, 0, 0, 0.8))
                    drop-shadow(0 -6px 12px rgba(255, 100, 0, 0.6))
                    drop-shadow(0 -10px 18px rgba(255, 150, 0, 0.4));
            }}
            50% {{ 
                filter: 
                    drop-shadow(0 -5px 10px rgba(255, 0, 0, 0.9))
                    drop-shadow(0 -10px 20px rgba(255, 100, 0, 0.7))
                    drop-shadow(0 -15px 28px rgba(255, 200, 0, 0.5));
            }}
            100% {{ 
                filter: 
                    drop-shadow(0 -3px 6px rgba(255, 0, 0, 0.8))
                    drop-shadow(0 -6px 12px rgba(255, 100, 0, 0.6))
                    drop-shadow(0 -10px 18px rgba(255, 150, 0, 0.4));
            }}
        }}
        
        /* Fogo Azul (Nível 9) - Super Intenso com Alto Contraste */
        .fire-blue {{ 
            rx: 2;
            animation: pulseFireBlue 1.5s ease-in-out infinite;
            filter: drop-shadow(0 0 15px rgba(0, 150, 255, 1));
        }}
        
        @keyframes pulseFireBlue {{
            0% {{ 
                filter: 
                    drop-shadow(0 -6px 12px rgba(0, 50, 200, 1))
                    drop-shadow(0 -12px 24px rgba(0, 150, 255, 1))
                    drop-shadow(0 -20px 40px rgba(100, 220, 255, 0.9));
            }}
            50% {{ 
                filter: 
                    drop-shadow(0 -10px 20px rgba(0, 30, 180, 1))
                    drop-shadow(0 -20px 40px rgba(0, 180, 255, 1))
                    drop-shadow(0 -30px 60px rgba(150, 240, 255, 1));
            }}
            100% {{ 
                filter: 
                    drop-shadow(0 -6px 12px rgba(0, 50, 200, 1))
                    drop-shadow(0 -12px 24px rgba(0, 150, 255, 1))
                    drop-shadow(0 -20px 40px rgba(100, 220, 255, 0.9));
            }}
        }}
        
        /* Fagulhas Vermelhas (Fogo Vermelho) */
        .spark-red {{
            fill: #ffaa00;
            opacity: 0;
            animation: sparkFlyRed 1.5s ease-out infinite;
        }}
        
        @keyframes sparkFlyRed {{
            0% {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
            50% {{
                opacity: 0.7;
            }}
            100% {{
                opacity: 0;
                transform: translateY(var(--ty)) scale(0.2);
            }}
        }}
        
        /* Fagulhas Azuis (Fogo Azul) - Pequenas e Dispersas */
        .spark-blue {{
            opacity: 0;
            animation: sparkFlyBlue 1.5s ease-out infinite;
        }}
        
        @keyframes sparkFlyBlue {{
            0% {{
                opacity: 0.9;
                transform: translate(0, 0) scale(1);
                fill: #66AAFF;
            }}
            30% {{
                opacity: 0.8;
                fill: #44CCFF;
            }}
            70% {{
                opacity: 0.4;
                fill: #88EEFF;
            }}
            100% {{
                opacity: 0;
                transform: translate(var(--tx), var(--ty)) scale(0.3);
                fill: #CCFFFF;
            }}
        }}
    </style>
    <rect width="{width}" height="{height}" fill="{current_theme["bg"]}" rx="6"/>
    
    <!-- Título -->
    <text x="15" y="25" fill="{current_theme["title"]}" font-size="12" font-weight="400">
        <tspan fill="#ff6b00" font-weight="600">{contributions_data["totalContributions"]}</tspan> contribuições nos últimos {MONTHS_TO_SHOW} meses
    </text>
    
    <!-- Labels dos dias -->
'''
    
    days_labels = ["", "Seg", "", "Qua", "", "Sex", ""]
    for i, label in enumerate(days_labels):
        if label:
            # Centraliza o texto verticalmente na célula (approx)
            svg += f'    <text x="25" y="{56 + i * total_cell}" text-anchor="end">{label}</text>\n'
    
    # Meses
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    current_month = -1
    
    # Grid de contribuições
    fire_cells = []
    normal_cells = []

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
            
            # Separar células normais das de fogo para renderizar fogo por cima (z-index)
            if level == 9:  # Fogo Azul (Super Intenso)
                class_name = "day fire-blue"
                fill = "url(#fireGradientBlue)"
                rect_content = f'    <rect class="{class_name}" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}"/>\n'
                fire_cells.append(rect_content)
                
                # Adiciona 12 fagulhas azuis pequenas e dispersas
                import random
                for i in range(12):  # Mais fagulhas, menores
                    cx = x + cell_size / 2 + random.uniform(-8, 8)  # Mais disperso horizontalmente
                    cy = y + cell_size / 2 + random.uniform(-4, 4)  # Pequena variação vertical
                    
                    # Movimento mais suave e disperso
                    tx = random.uniform(-15, 15)  # Movimento horizontal
                    ty = random.uniform(-40, -15)  # Movimento vertical
                    delay = random.uniform(0, 1.5)
                    
                    spark = f'    <circle class="spark-blue" cx="{cx}" cy="{cy}" r="0.8" style="--tx: {tx}px; --ty: {ty}px; animation-delay: {delay}s;"/>\n'
                    fire_cells.append(spark)
                    
            elif level == 8:  # Fogo Vermelho (sem fagulhas)
                class_name = "day fire-red"
                fill = "url(#fireGradientRed)"
                rect_content = f'    <rect class="{class_name}" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}"/>\n'
                fire_cells.append(rect_content)
            else:
                class_name = "day"
                fill = color
                rect_content = f'    <rect class="{class_name}" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}"/>\n'
                normal_cells.append(rect_content)

    # Renderiza primeiro as normais, depois as de fogo (para ficarem por cima)
    svg += "".join(normal_cells)
    svg += "".join(fire_cells)
    
    # Gradientes de fogo com animação
    svg += '''
    <defs>
        <!-- Gradiente Fogo Vermelho -->
        <linearGradient id="fireGradientRed" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff0000;stop-opacity:1">
                <animate attributeName="stop-color" values="#ff0000;#cc0000;#ff0000" dur="2s" repeatCount="indefinite"/>
            </stop>
            <stop offset="40%" style="stop-color:#ff4400;stop-opacity:1">
                <animate attributeName="stop-color" values="#ff4400;#ff6600;#ff4400" dur="2s" repeatCount="indefinite"/>
            </stop>
            <stop offset="70%" style="stop-color:#ff8800;stop-opacity:1">
                <animate attributeName="stop-color" values="#ff8800;#ffaa00;#ff8800" dur="2s" repeatCount="indefinite"/>
            </stop>
            <stop offset="100%" style="stop-color:#ffff00;stop-opacity:1">
                <animate attributeName="stop-color" values="#ffff00;#ffcc00;#ffff00" dur="2s" repeatCount="indefinite"/>
            </stop>
        </linearGradient>
        
        
        <!-- Gradiente Fogo Azul (Alto Contraste) -->
        <linearGradient id="fireGradientBlue" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#001a80;stop-opacity:1">
                <animate attributeName="stop-color" values="#001a80;#002266;#001a80" dur="1.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="30%" style="stop-color:#0055cc;stop-opacity:1">
                <animate attributeName="stop-color" values="#0055cc;#0066ff;#0055cc" dur="1.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="60%" style="stop-color:#0099ff;stop-opacity:1">
                <animate attributeName="stop-color" values="#0099ff;#00ccff;#0099ff" dur="1.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="100%" style="stop-color:#66ffff;stop-opacity:1">
                <animate attributeName="stop-color" values="#66ffff;#ccffff;#66ffff" dur="1.5s" repeatCount="indefinite"/>
            </stop>
        </linearGradient>
    </defs>
    
    <!-- Legenda -->
    <g transform="translate(40, ''' + str(height - 50) + ''')">
        <text y="15">Menos</text>
'''
    
    legend_x = 40 # Ajuste fino para "Menos" não colar
    for level in range(10):  # Agora vai até 9 (10 níveis: 0-9)
        if level == 9:  # Fogo Azul
            svg += f'        <rect class="day fire-blue" x="{legend_x + level * (cell_size + 2)}" width="{cell_size}" height="{cell_size}" fill="url(#fireGradientBlue)" rx="2"/>\n'
        elif level == 8:  # Fogo Vermelho
            svg += f'        <rect class="day fire-red" x="{legend_x + level * (cell_size + 2)}" width="{cell_size}" height="{cell_size}" fill="url(#fireGradientRed)" rx="2"/>\n'
        else:
            svg += f'        <rect x="{legend_x + level * (cell_size + 2)}" width="{cell_size}" height="{cell_size}" fill="{COLORS[level]}" rx="2"/>\n'
    
    svg += f'''        <text x="{legend_x + 10 * (cell_size + 2) + 10}" y="15">Mais 🔥💙</text>
    </g>
</svg>'''
    
    return svg

def main():
    print(f"🔥 GitHub Heatmap Generator v4 - Fogo Azul com Fagulhas")
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
        print(f"   python generate_heatmap_v4.py")
        print("\n📋 Por enquanto, gerando dados de exemplo...\n")
        contributions = generate_fake_data()
    
    # Gera o SVG
    svg_content = generate_svg_heatmap(contributions)
    
    # Salva
    output_file = "github-heatmap-v4.svg"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"\n✅ Heatmap gerado: {output_file}")
    print(f"📊 Total: {contributions['totalContributions']} contribuições")
    print(f"\n🎯 Adicione ao README:")
    print(f"   ![GitHub Heatmap](./github-heatmap-v4.svg)\n")

if __name__ == "__main__":
    main()
