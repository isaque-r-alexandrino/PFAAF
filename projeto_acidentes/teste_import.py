# teste_import.py
import sys
import os

print("="*60)
print("🔍 DIAGNÓSTICO DE IMPORTAÇÃO")
print("="*60)

# 1. Verifica se o arquivo existe
print("\n1. Verificando arquivo...")
if os.path.exists('src/data_generator.py'):
    print("✅ src/data_generator.py existe")
else:
    print("❌ src/data_generator.py NÃO encontrado")
    sys.exit(1)

# 2. Tenta importar o módulo
print("\n2. Tentando importar o módulo...")
try:
    import src.data_generator as module
    print(f"✅ Módulo importado: {module}")
    print(f"📄 Atributos disponíveis: {[x for x in dir(module) if not x.startswith('_')]}")
except Exception as e:
    print(f"❌ Erro ao importar módulo: {e}")
    sys.exit(1)

# 3. Tenta importar a classe
print("\n3. Tentando importar DataGenerator...")
try:
    from src.data_generator import DataGenerator
    print("✅ DataGenerator importado com sucesso!")
    print(f"📄 DataGenerator: {DataGenerator}")
except ImportError as e:
    print(f"❌ Erro ao importar DataGenerator: {e}")
    
    # Verifica se a classe existe no módulo
    if hasattr(module, 'DataGenerator'):
        print("✅ A classe DataGenerator existe no módulo")
    elif hasattr(module, 'data_generator'):
        print("⚠️ Encontrei 'data_generator' (minúsculo) em vez de 'DataGenerator'")
    else:
        print("❌ A classe DataGenerator NÃO existe no módulo")
        print(f"📄 Conteúdo do módulo: {dir(module)}")

# 4. Verifica o conteúdo do arquivo
print("\n4. Verificando conteúdo do arquivo...")
with open('src/data_generator.py', 'r', encoding='utf-8') as f:
    linhas = f.readlines()
    print(f"📄 Total de linhas: {len(linhas)}")
    
    # Mostra as primeiras 10 linhas
    print("\n📄 Primeiras 10 linhas:")
    for i, linha in enumerate(linhas[:10], 1):
        print(f"   {i}: {linha.rstrip()}")
    
    # Verifica se tem 'class DataGenerator'
    tem_classe = any('class DataGenerator' in linha for linha in linhas)
    print(f"\n🔍 'class DataGenerator' encontrado? {tem_classe}")

print("\n" + "="*60)