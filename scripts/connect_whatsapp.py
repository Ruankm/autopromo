#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Conexao Inteligente WhatsApp - AutoPromo Cloud
=========================================================

Conecta uma instancia WhatsApp usando Evolution API v2.1.0

PRIORIDADE 1: Pairing Code (codigo numerico)
PRIORIDADE 2: QR Code (fallback)

Uso:
    python scripts/connect_whatsapp.py
"""

import requests
import json
import time
import sys
import base64
from pathlib import Path

# ============================================================================
# CONFIGURACAO
# ============================================================================

EVOLUTION_BASE_URL = "http://localhost:8081"
EVOLUTION_API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"
INSTANCE_NAME = "Worker01"
PHONE_NUMBER = "5531998722744"

            url = f"{self.base_url}/instance/delete/{instance_name}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                print(f"[OK] Instancia '{instance_name}' deletada")
                return True
        except Exception as e:
            print(f"[INFO] Instancia nao existia: {e}")
        response = requests.post(url, json=payload, headers=self.headers, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Instancia criada: {data.get('instance', {}).get('status', 'unknown')}")
            return data
        else:
            print(f"[ERRO] Status {response.status_code}: {response.text}")
            return None
    
    def get_pairing_code(self, instance_name: str):
        """Tenta obter Pairing Code"""
        url = f"{self.base_url}/instance/connect/{instance_name}"
        params = {"number": PHONE_NUMBER}
        
        for attempt in range(1, 6):
            print(f"\n[BUSCA] Tentativa {attempt}/5 - Pairing Code...")
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "pairingCode" in data and data["pairingCode"]:
                        return data["pairingCode"]
                    
                    print(f"   Resposta: {json.dumps(data, indent=2)}")
                    
            except Exception as e:
                print(f"   Erro: {e}")
            
            if attempt < 5:
                time.sleep(3)
        
        return None
    
    def get_qr_code(self, instance_name: str):
        """Tenta obter QR Code base64"""
        url = f"{self.base_url}/instance/connect/{instance_name}"
        
        for attempt in range(1, 6):
            print(f"\n[BUSCA] Tentativa {attempt}/5 - QR Code...")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "base64" in data and data["base64"]:
                        return data["base64"]
                    
                    if "code" in data and data["code"]:
                        return data["code"]
                    
                    if "qrcode" in data:
                        qr_data = data["qrcode"]
                        if isinstance(qr_data, dict):
                            if "base64" in qr_data:
                                return qr_data["base64"]
                            if "code" in qr_data:
                                return qr_data["code"]
                    
                    print(f"   Resposta: {json.dumps(data, indent=2)}")
                    
            except Exception as e:
                print(f"   Erro: {e}")
            
            if attempt < 5:
                time.sleep(3)
        
        return None
    
    def get_connection_state(self, instance_name: str):
        """Verifica estado da conexao"""
        try:
            url = f"{self.base_url}/instance/connectionState/{instance_name}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Erro ao verificar estado: {e}")
        return None

# ============================================================================
# FUNCOES AUXILIARES
# ============================================================================

def save_qr_as_image(qr_base64: str):
    """Salva QR Code como imagem"""
    try:
        if "," in qr_base64:
            qr_base64 = qr_base64.split(",")[1]
        
        image_data = base64.b64decode(qr_base64)
        
        output_path = Path("qr_code.png")
        output_path.write_bytes(image_data)
        
        print(f"\n[OK] QR Code salvo em: {output_path.absolute()}")
        print(f"[INFO] Abra o arquivo e escaneie com WhatsApp > Aparelhos Conectados")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Erro ao salvar QR Code: {e}")
        return False

def display_pairing_code(code: str):
    """Exibe Pairing Code de forma destacada"""
    print("\n" + "=" * 60)
    print(">>> PAIRING CODE GERADO COM SUCESSO! <<<")
    print("=" * 60)
    print(f"\n   CODIGO: {code}\n")
    print("[INFO] ABRA O WHATSAPP NO SEU CELULAR:")
    print("  1.  Va em 'Aparelhos Conectados'")
    print("  2. Toque em 'Vincular com numero de telefone'")
    print(f"   3. Digite o codigo: {code}")
    print("\n" + "=" * 60)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("AutoPromo Cloud - Conexao WhatsApp Inteligente")
    print("Evolution API v2.1.0")
    print("=" * 60)
    
    client = EvolutionAPIClient(EVOLUTION_BASE_URL, EVOLUTION_API_KEY)
    
    print(f"\n[LIMPEZA] Removendo instancia antiga '{INSTANCE_NAME}'...")
    client.delete_instance(INSTANCE_NAME)
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("TENTATIVA 1: PAIRING CODE (Prioridade)")
    print("=" * 60)
    
    instance_data = client.create_instance(INSTANCE_NAME, use_pairing=True)
    
    if instance_data:
        time.sleep(3)
        pairing_code = client.get_pairing_code(INSTANCE_NAME)
        
        if pairing_code:
            display_pairing_code(pairing_code)
            
            print("\n[AGUARDANDO] Aguardando voce digitar o codigo...")
            print("   (Pressione Ctrl+C para cancelar)")
            
            for i in range(60):
                time.sleep(2)
                state = client.get_connection_state(INSTANCE_NAME)
                
                if state and state.get("instance", {}).get("state") == "open":
                    print(f"\n[SUCESSO] CONECTADO COM SUCESSO!")
                    print(f"Estado: {json.dumps(state, indent=2)}")
                    return 0
            
            print("\n[TIMEOUT] Tempo esgotado aguardando conexao")
            return 1
    
    print("\n" + "=" * 60)
    print("TENTATIVA 2: QR CODE (Fallback)")
    print("=" * 60)
    print("Pairing Code nao funcionou. Tentando QR Code...")
    
    client.delete_instance(INSTANCE_NAME)
    time.sleep(2)
    
    instance_data = client.create_instance(INSTANCE_NAME, use_pairing=False)
    
    if instance_data:
        time.sleep(3)
        qr_code = client.get_qr_code(INSTANCE_NAME)
        
        if qr_code:
            if save_qr_as_image(qr_code):
                print("\n[AGUARDANDO] Aguardando voce escanear o QR Code...")
                
                for i in range(60):
                    time.sleep(2)
                    state = client.get_connection_state(INSTANCE_NAME)
                    
                    if state and state.get("instance", {}).get("state") == "open":
                        print(f"\n[SUCESSO] CONECTADO COM SUCESSO!")
                        print(f"Estado: {json.dumps(state, indent=2)}")
                        return 0
                
                print("\n[TIMEOUT] Tempo esgotado aguardando conexao")
                return 1
    
    print("\n[ERRO] Falha em ambas tentativas (Pairing Code e QR Code)")
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Cancelado pelo usuario")
        sys.exit(130)
