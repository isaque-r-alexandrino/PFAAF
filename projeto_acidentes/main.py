"""
Sistema de Análise de Acidentes em Rodovias Federais
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
import os
import json
import logging
import sys
from pathlib import Path
import traceback

# Importar módulos do projeto
from src.data_generator import DataGenerator
from src.data_processor import DataProcessor
from src.visualizer import Visualizer
from src.analyzer import Analyzer

# Configuração
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analise.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class SistemaAnaliseAcidentes:
    """
    Sistema principal para análise de acidentes
    
    Attributes:
        config: Dicionário com configurações
        data_generator: Gerador de dados
        data_processor: Processador de dados
        visualizer: Visualizador de dados
        analyzer: Analisador de dados
    """
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Inicializa o sistema
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config = self._carregar_config(config_path)
        self.timestamp_inicio = datetime.now()
        
        # Inicializar componentes
        self.data_generator = DataGenerator(self.config)
        self.data_processor = DataProcessor(self.config)
        self.visualizer = Visualizer(self.config)
        self.analyzer = Analyzer(self.config)
        
        # Dados
        self.acidentes = None
        self.infracoes = None
        self.estatisticas = None
        self.kpis = None
        self.insights = None
        
        self._mostrar_boas_vindas()
    
    def _carregar_config(self, config_path: str) -> dict:
        """
        Carrega configurações do arquivo JSON
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Dicionário com configurações
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f" Configurações carregadas de {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Arquivo {config_path} não encontrado. Usando configurações padrão.")
            return self._config_padrao()
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            return self._config_padrao()
    
    def _config_padrao(self) -> dict:
        """Retorna configurações padrão"""
        return {
            "PERIOD": {
                "START_DATE": "2025-01-01",
                "END_DATE": "2026-02-28"
            },
            "DATA": {
                "SEED": 42,
                "ACIDENTES_BASE_LAMBDA": 45,
                "TAXA_MORTE_BASE": 0.08
            },
            "COSTS": {
                "CUSTO_POR_MORTE": 350000,
                "CUSTO_POR_FERIDO": 50000
            }
        }
    
    def _mostrar_boas_vindas(self):
        """Mostra mensagem de boas-vindas"""
        print("\n" + "="*80)
        print(" ANÁLISE DE ACIDENTES EM RODOVIAS FEDERAIS")
        print("="*80)
        print(f" Período: {self.config['PERIOD']['START_DATE']} a {self.config['PERIOD']['END_DATE']}")
        print(f" Seed: {self.config['DATA'].get('SEED', 42)}")
        print(f" Início: {self.timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def executar(self) -> bool:
        """
        Executa o pipeline completo de análise
        
        Returns:
            True se bem sucedido, False caso contrário
        """
        try:
            logger.info(" Iniciando pipeline de análise...")
            
            # 1. Gerar dados
            logger.info("\n 1. GERANDO DADOS")
            dados = self.data_generator.gerar_todos_dados()
            self.acidentes = dados['acidentes']
            self.infracoes = dados['infracoes']
            self.estatisticas = dados['estatisticas']
            
            # 2. Processar dados
            logger.info("\n🔧 2. PROCESSANDO DADOS")
            self.acidentes = self.data_processor.processar_acidentes(self.acidentes)
            self.infracoes = self.data_processor.processar_infracoes(self.infracoes)
            
            # 3. Calcular KPIs
            logger.info("\n 3. CALCULANDO KPIS")
            self.kpis = self.data_processor.calcular_kpis(self.acidentes)
            
            # 4. Criar visualizações
            logger.info("\n 4. CRIANDO VISUALIZAÇÕES")
            self.visualizer.criar_dashboard(
                self.acidentes, 
                self.infracoes, 
                self.kpis,
                output_dir='resultados'
            )
            self.visualizer.criar_graficos_kpis(self.kpis, output_dir='resultados')
            
            # 5. Gerar insights
            logger.info("\n 5. GERANDO INSIGHTS")
            self.insights = self.analyzer.gerar_insights(self.acidentes)
            self.analyzer.imprimir_insights()
            self.analyzer.exportar_insights(output_dir='resultados')
            
            # 6. Exportar resultados
            logger.info("\n 6. EXPORTANDO RESULTADOS")
            self._exportar_resultados()
            
            # 7. Resumo final
            self._mostrar_resumo()
            
            return True
            
        except Exception as e:
            logger.error(f" Erro na execução: {str(e)}")
            traceback.print_exc()
            return False
    
    def _exportar_resultados(self):
        """Exporta todos os resultados"""
        output_dir = 'resultados'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Exportar dados
        self.acidentes.to_csv(f'{output_dir}/acidentes_tratados.csv', index=False, encoding='utf-8-sig')
        self.infracoes.to_csv(f'{output_dir}/infracoes_tratadas.csv', index=False, encoding='utf-8-sig')
        self.estatisticas.to_csv(f'{output_dir}/estatisticas_uf.csv', index=False, encoding='utf-8-sig')
        
        # Exportar KPIs
        if self.kpis:
            kpis_df = pd.DataFrame([self.kpis])
            kpis_df.to_csv(f'{output_dir}/kpis_gerais.csv', index=False, encoding='utf-8-sig')
        
        # Exportar resumo
        resumo = pd.DataFrame({
            'Métrica': [
                'Total Acidentes', 'Total Mortes', 'Total Feridos',
                'Taxa Mortalidade Média', 'Período Início', 'Período Fim',
                'Custo Social Estimado', 'Índice de Risco Médio'
            ],
            'Valor': [
                f"{self.acidentes['total_acidentes'].sum():,}",
                f"{self.acidentes['mortes'].sum():.0f}",
                f"{self.acidentes['feridos'].sum():.0f}",
                f"{self.acidentes['taxa_mortalidade'].mean():.2f}%",
                self.config['PERIOD']['START_DATE'],
                self.config['PERIOD']['END_DATE'],
                f"R$ {self.kpis['custo_social_estimado']:,.2f}" if self.kpis else "N/A",
                f"{self.acidentes['indice_risco'].mean():.3f}"
            ]
        })
        resumo.to_csv(f'{output_dir}/resumo_geral.csv', index=False, encoding='utf-8-sig')
        
        logger.info(f" Resultados salvos em {output_dir}/")
    
    def _mostrar_resumo(self):
        """Mostra resumo final da execução"""
        tempo = (datetime.now() - self.timestamp_inicio).total_seconds()
        
        print("\n" + "="*80)
        print(" ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print(f"\n RESUMO FINAL:")
        print(f"   • Acidentes analisados: {self.acidentes['total_acidentes'].sum():,}")
        print(f"   • Mortes registradas: {self.acidentes['mortes'].sum():.0f}")
        print(f"   • Feridos registrados: {self.acidentes['feridos'].sum():.0f}")
        print(f"   • Insights gerados: {len(self.insights) if self.insights else 0}")
        print(f"   • Tempo de execução: {tempo:.2f} segundos")
        
        if self.kpis:
            print(f"\n IMPACTO SOCIAL:")
            print(f"   • Custo estimado: {self.kpis.get('custo_social_formatado', 'N/A')}")
            print(f"   • Severidade média: {self.kpis.get('severidade_media', 0)} mortes/acidente")
        
        print(f"\n Resultados salvos em: 'resultados/'")
        print("\n Arquivos gerados:")
        print("   ✓ acidentes_tratados.csv")
        print("   ✓ infracoes_tratadas.csv")
        print("   ✓ estatisticas_uf.csv")
        print("   ✓ kpis_gerais.csv")
        print("   ✓ resumo_geral.csv")
        print("   ✓ dashboard_completo.png")
        print("   ✓ kpis_graficos.png")
        print("   ✓ insights.json")
        print("   ✓ insights.txt")
        print("   ✓ analise.log")
        print("="*80)


def main():
    """Função principal"""
    try:
        sistema = SistemaAnaliseAcidentes('config.json')
        sucesso = sistema.executar()
        return sucesso
    except KeyboardInterrupt:
        print("\n Execução interrompida pelo usuário")
        return False
    except Exception as e:
        logger.error(f" Erro fatal: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)