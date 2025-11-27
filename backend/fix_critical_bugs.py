"""
Script de correcao automatica dos 3 bugs criticos encontrados.
Execute: python fix_critical_bugs.py
"""
import re
from pathlib import Path

print("=" * 80)
print("CORRECAO AUTOMATICA DE BUGS CRITICOS - AutoPromo Cloud")
print("=" * 80)
print()

bugs_fixed = 0

# BUG 1: WhatsAppInstance.metadata -> extra_data (SQLAlchemy reserved word)
print("[1/3] Corrigindo WhatsAppInstance.metadata...")
whatsapp_instance_file = Path("models/whatsapp_instance.py")
if whatsapp_instance_file.exists():
    content = whatsapp_instance_file.read_text(encoding='utf-8')
    if 'metadata = Column' in content:
        content = content.replace(
            '# Metadados extras\n    metadata = Column(JSON, default={}, nullable=True)',
            '# Metadados extras (renamed from metadata to avoid SQLAlchemy conflict)\n    extra_data = Column(JSON, default={}, nullable=True)'
        )
        whatsapp_instance_file.write_text(content, encoding='utf-8')
        print("  [OK] Fixed: metadata -> extra_data")
        bugs_fixed += 1
    else:
        print("  [INFO] Already fixed or not found")
else:
    print("  [WARN] File not found")

# BUG 2: worker.py extract_url -> extract_urls
print("\n[2/3] Corrigindo worker.py extract_url...")
worker_file = Path("workers/worker.py")
if worker_file.exists():
    content = worker_file.read_text(encoding='utf-8')
    if 'url = extract_url(message.raw_text)' in content:
        # Replace the problematic section
        old_code = '''    # 2. Extrair URL do texto
    url = extract_url(message.raw_text)
    
    if not url:
        logger.info(f"No URL found in message, skipping. Text: {message.raw_text[:50]}...")
        return'''
        
        new_code = '''    # 2. Extrair URLs do texto
    urls = extract_urls(message.raw_text)
    
    if not urls:
        logger.info(f"No URL found in message, skipping. Text: {message.raw_text[:50]}...")
        return
    
    # Pegar primeira URL
    url = urls[0]
    logger.info(f"Extracted URL: {url}")'''
        
        content = content.replace(old_code, new_code)
        worker_file.write_text(content, encoding='utf-8')
        print("  [OK] Fixed: extract_url -> extract_urls")
        bugs_fixed += 1
    else:
        print("  [INFO] Already fixed or not found")
else:
    print("  [WARN] File not found")

# BUG 3: whatsapp_evolution.py syntax error (unterminated string)
print("\n[3/3] Corrigindo whatsapp_evolution.py syntax error...")
whatsapp_evo_file = Path("services/providers/whatsapp_evolution.py")
if whatsapp_evo_file.exists():
    content = whatsapp_evo_file.read_text(encoding='utf-8')
    
    # Check if there's a syntax error
    try:
        compile(content, whatsapp_evo_file.name, 'exec')
        print("  [INFO] No syntax errors found")
    except SyntaxError as e:
        print(f"  [WARN] Syntax error found at line {e.lineno}: {e.msg}")
        print("  [FIX] Attempting to fix...")
        
        # Fix common issue: missing closing quotes
        lines = content.split('\n')
        fixed = False
        for i, line in enumerate(lines):
            if '"""Envia mensagem de texto (metodo legado)."""' in line and not line.strip().endswith('"""'):
                lines[i] = '        """Envia mensagem de texto (metodo legado)."""'
                fixed = True
                break
        
        if fixed:
            content = '\n'.join(lines)
            whatsapp_evo_file.write_text(content, encoding='utf-8')
            print("  [OK] Fixed syntax error")
            bugs_fixed += 1
        else:
            print("  [ERROR] Could not auto-fix, manual intervention needed")
else:
    print("  [WARN] File not found")

print()
print("=" * 80)
print(f"RESULTADO: {bugs_fixed}/3 bugs corrigidos")
print("=" * 80)
print()

if bugs_fixed == 3:
    print("[SUCCESS] Todos os bugs foram corrigidos!")
    print()
    print("Proximos passos:")
    print("1. Reinicie o backend: python -m uvicorn main:app --reload --port 8000")
    print("2. Teste: curl http://localhost:8000/health")
elif bugs_fixed > 0:
    print(f"[PARTIAL] {bugs_fixed} bugs corrigidos, mas alguns podem precisar de correcao manual.")
    print("Verifique os arquivos acima.")
else:
    print("[INFO] Nenhum bug encontrado (ja foram corrigidos anteriormente?)")
