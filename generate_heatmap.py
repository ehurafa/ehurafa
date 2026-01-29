#!/usr/bin/env python3
"""
GitHub Contribution Heatmap Generator
Gera um heatmap SVG com suas contribuições reais do GitHub
"""

import requests
from datetime import datetime, timedelta
import json

USERNAME = "ehurafa"  # Seu username do GitHub

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

def fetch_contributions(username):
    """
    Busca contribuições do GitHub via API GraphQL
    Nota: Você precisará de um token do GitHub para production
    """
    # URL da API GraphQL do GitHub
    url = "https://api.github.com/graphql"
    
    # Query GraphQL para buscar contribuições
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
    
    # Headers (você precisará adicionar seu token aqui)
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer SEU_TOKEN_AQUI"  # Descomente e adicione seu token
    }
    
    payload = {
        "query": query,
        "variables": {"username": username}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if "errors" in data:
            print(f"Erro na API: {data['errors']}")
            return None
            
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None

def generate_svg_heatmap(contributions_data):
    """Gera o SVG do heatmap"""
    
    # Configurações do SVG
    cell_size = 12
    cell_gap = 4
    total_cell = cell_size + cell_gap
    
    # Pega os últimos 365 dias
    weeks = contributions_data["weeks"][-52:]  # Últimas 52 semanas
    
    width = len(weeks) * total_cell + 40
    height = 7 * total_cell + 60
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .day {{ rx: 2; ry: 2; }}
        .day:hover {{ stroke: #ff6b00; stroke-width: 2; }}
        text {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: #8b949e; }}
    </style>
    <rect width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Título -->
    <text x="10" y="20" fill="#c9d1d9" font-size="14">
        {contributions_data["totalContributions"]} contributions in the last year
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
    month_x = 40
    
    # Grid de contribuições
    for week_idx, week in enumerate(weeks):
        x = 40 + week_idx * total_cell
        
        for day_idx, day in enumerate(week["contributionDays"]):
            y = 40 + day_idx * total_cell
            count = day["contributionCount"]
            level = get_level(count)
            color = COLORS[level]
            
            # Adiciona label do mês
            date = datetime.fromisoformat(day["date"].replace("Z", "+00:00"))
            if date.month != current_month and day_idx == 0:
                current_month = date.month
                svg += f'    <text x="{x}" y="35">{months[current_month - 1]}</text>\n'
            
            # Animação especial para nível 8 (fogo)
            if level == 8:
                svg += f'''    <g>
        <rect class="day" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" 
              fill="url(#fireGradient)" data-count="{count}">
            <animate attributeName="opacity" values="1;0.8;1" dur="1.5s" repeatCount="indefinite"/>
        </rect>
    </g>\n'''
            else:
                svg += f'    <rect class="day" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" data-count="{count}"/>\n'
    
    # Gradiente de fogo para nível 8
    svg += '''
    <!-- Gradiente de fogo -->
    <defs>
        <linearGradient id="fireGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
            <stop offset="50%" style="stop-color:rgb(255,30,15);stop-opacity:1" />
            <stop offset="100%" style="stop-color:rgb(255,60,30);stop-opacity:1" />
        </linearGradient>
    </defs>
    
    <!-- Legenda -->
    <text x="10" y="''' + str(height - 20) + '''">Less</text>
'''
    
    legend_x = 50
    for level in range(9):
        svg += f'    <rect x="{legend_x + level * (cell_size + 2)}" y="{height - 30}" width="{cell_size}" height="{cell_size}" fill="{COLORS[level]}" rx="2"/>\n'
    
    svg += f'''    <text x="{legend_x + 9 * (cell_size + 2) + 10}" y="{height - 20}">More 🔥</text>
</svg>'''
    
    return svg

def main():
    print(f"Buscando contribuições de @{USERNAME}...")
    
    # Busca os dados
    contributions = fetch_contributions(USERNAME)
    
    if not contributions:
        print("❌ Não foi possível buscar as contribuições.")
        print("\n⚠️  Para usar em produção, você precisa:")
        print("1. Criar um token no GitHub: https://github.com/settings/tokens")
        print("2. Adicionar o token no código (linha 47)")
        print("3. Dar permissão 'read:user'")
        return
    
    # Gera o SVG
    svg_content = generate_svg_heatmap(contributions)
    
    # Salva o arquivo
    output_file = "github-heatmap.svg"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"✅ Heatmap gerado com sucesso: {output_file}")
    print(f"📊 Total de contribuições: {contributions['totalContributions']}")
    print("\n🎯 Para adicionar ao seu README:")
    print(f"![GitHub Heatmap](./github-heatmap.svg)")

if __name__ == "__main__":
    main()
