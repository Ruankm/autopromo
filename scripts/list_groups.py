#!/usr/bin/env python3
"""
Lista grupos do WhatsApp conectado via Evolution API.

Uso:
    python scripts/list_groups.py
"""
import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv(".env.evolution")

EVOLUTION_BASE_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8081")
EVOLUTION_API_KEY = os.getenv("AUTHENTICATION_API_KEY", "f708f2fc-471f-4511-83c3-701229e766d5")
INSTANCE_NAME = "Worker01"


def list_all_groups():
    """Lista todos os grupos e destaca os importantes."""
    url = f"{EVOLUTION_BASE_URL}/group/fetchAllGroups/{INSTANCE_NAME}"
    headers = {"apikey": EVOLUTION_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        groups = response.json()
        
        # Filtrar grupos de interesse
        target_keywords = ["escorrega", "autopromo", "preço", "preco"]
        
        print("=" * 80)
        print(" GRUPOS ENCONTRADOS NO WHATSAPP")
        print("=" * 80)
        print()
        
        highlighted = []
        others = []
        
        for group in groups:
            group_id = group.get("id", "")
            group_name = group.get("subject", "Sem nome")
            participants = group.get("size", 0)
            
            # Verificar se é grupo importante
            is_target = any(kw in group_name.lower() for kw in target_keywords)
            
            group_info = {
                "name": group_name,
                "id": group_id,
                "participants": participants
            }
            
            if is_target:
                highlighted.append(group_info)
            else:
                others.append(group_info)
        
        # Mostrar grupos importantes primeiro
        if highlighted:
            print("🎯 GRUPOS IMPORTANTES:")
            print()
            for g in highlighted:
                print(f"  📌 {g['name']}")
                print(f"     ID: {g['id']}")
                print(f"     Participantes: {g['participants']}")
                print()
        
        # Mostrar outros grupos
        if others:
            print("\n📋 OUTROS GRUPOS:")
            print()
            for g in others[:10]:  # Limitar a 10 para não poluir
                print(f"  - {g['name']}")
                print(f"    ID: {g['id']}")
                print()
        
        if len(others) > 10:
            print(f"  ... e mais {len(others) - 10} grupos")
        
        print()
        print("=" * 80)
        print(" COPIE OS IDs ACIMA PARA USAR NO SETUP DO BANCO")
        print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar grupos: {e}")
        print(f"   URL: {url}")
        print(f"   Verifique se Evolution API está rodando")


if __name__ == "__main__":
    list_all_groups()
