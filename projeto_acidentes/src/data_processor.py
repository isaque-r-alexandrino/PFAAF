"""
Módulo para processamento e enriquecimento de dados
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Processador de dados para análise de acidentes
    
    Attributes:
        config: Dicionário com configurações
        acidentes: DataFrame com dados de acidentes
        infracoes: DataFrame com dados de infrações
        estatisticas: DataFrame com estatísticas
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa o processador
        
        Args:
            config: Dicionário com configurações
        """
        self.config = config
        self.acidentes = None
        self.infracoes = None
        self.estatisticas = None
        
        # Mapeamento de dias da semana
        self.dias_semana = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        logger.info("DataProcessor inicializado")
    
    def processar_acidentes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa e enriquece dados de acidentes
        
        Args:
            df: DataFrame com dados brutos
            
        Returns:
            DataFrame processado
        """
        try:
            logger.info("Processando dados de acidentes...")
            
            df = df.copy()
            
            # Converter data
            df['data'] = pd.to_datetime(df['data'])
            
            # Features temporais
            df['ano'] = df['data'].dt.year
            df['mes'] = df['data'].dt.month
            df['dia'] = df['data'].dt.day
            df['dia_semana_en'] = df['data'].dt.day_name()
            df['dia_semana'] = df['dia_semana_en'].map(self.dias_semana)
            df['trimestre'] = df['data'].dt.quarter
            df['semana'] = df['data'].dt.isocalendar().week
            
            # Taxa de mortalidade
            df['taxa_mortalidade'] = (
                df['mortes'] / df['total_acidentes'] * 100
            ).round(2)
            
            # Classificação de risco
            df['classificacao_risco'] = self._classificar_risco(
                df['teste_alcool'].values,
                df['motocicleta'].values
            )
            
            # Índice de risco
            df['indice_risco'] = (
                df['teste_alcool'] * 0.4 +
                df['motocicleta'] * 0.3 +
                df['pista_simples'] * 0.2 +
                df['chuva'] * 0.1
            ).round(3)
            
            # Categoria de acidente
            df['categoria_acidente'] = pd.cut(
                df['total_acidentes'],
                bins=[0, 30, 50, 70, 100],
                labels=['Baixo', 'Médio', 'Alto', 'Crítico']
            )
            
            logger.info(f"✅ {len(df)} registros de acidentes processados")
            self.acidentes = df
            return df
            
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            raise
    
    def _classificar_risco(self, teste_alcool: np.ndarray, 
                          motocicleta: np.ndarray) -> np.ndarray:
        """
        Classifica o risco baseado em fatores
        
        Args:
            teste_alcool: Array com flags de álcool
            motocicleta: Array com flags de motocicleta
            
        Returns:
            Array com classificações
        """
        return np.where(
            (teste_alcool == 1) & (motocicleta == 1), 'CRÍTICO',
            np.where(teste_alcool == 1, 'ALTO',
            np.where(motocicleta == 1, 'MÉDIO', 'BAIXO'))
        )
    
    def processar_infracoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de infrações
        
        Args:
            df: DataFrame com dados brutos
            
        Returns:
            DataFrame processado
        """
        try:
            logger.info("Processando dados de infrações...")
            
            df = df.copy()
            
            # Converter data
            df['data'] = pd.to_datetime(df['data'])
            
            # Features temporais
            df['ano'] = df['data'].dt.year
            df['mes'] = df['data'].dt.month
            df['dia_semana'] = df['data'].dt.day_name()
            
            # Categorizar valor
            df['categoria_valor'] = pd.cut(
                df['valor_multa'],
                bins=[0, 195, 500, 1000, 3000],
                labels=['Baixa', 'Média-Baixa', 'Média', 'Alta']
            )
            
            logger.info(f"✅ {len(df)} registros de infrações processados")
            self.infracoes = df
            return df
            
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            raise
    
    def calcular_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula KPIs a partir dos dados processados
        
        Args:
            df: DataFrame com dados processados
            
        Returns:
            Dicionário com KPIs
        """
        try:
            logger.info("Calculando KPIs...")
            
            total_acidentes = df['total_acidentes'].sum()
            total_mortes = df['mortes'].sum()
            total_feridos = df['feridos'].sum()
            
            custo_morte = self.config.get('COSTS', {}).get('CUSTO_POR_MORTE', 350000)
            custo_ferido = self.config.get('COSTS', {}).get('CUSTO_POR_FERIDO', 50000)
            
            kpis = {
                'total_acidentes': int(total_acidentes),
                'total_mortes': int(total_mortes),
                'total_feridos': int(total_feridos),
                'media_acidentes_dia': round(total_acidentes / len(df), 2),
                'media_mortes_dia': round(total_mortes / len(df), 2),
                'severidade_media': round(df['mortes'].mean(), 2),
                'taxa_letalidade': round(total_mortes / max(total_feridos, 1), 3),
                'taxa_mortalidade_media': round(df['taxa_mortalidade'].mean(), 2),
                'indice_risco_medio': round(df['indice_risco'].mean(), 3),
                'percentual_alcool': round((df['teste_alcool'].sum() / len(df)) * 100, 2),
                'percentual_moto': round((df['motocicleta'].sum() / len(df)) * 100, 2),
                'custo_social_estimado': total_mortes * custo_morte + total_feridos * custo_ferido
            }
            
            # Formatar custo
            kpis['custo_social_formatado'] = f"R$ {kpis['custo_social_estimado']:,.2f}"
            
            logger.info("✅ KPIs calculados com sucesso")
            return kpis
            
        except Exception as e:
            logger.error(f"Erro no cálculo de KPIs: {str(e)}")
            raise
    
    def agregar_por_periodo(self, df: pd.DataFrame, 
                           periodo: str = 'M') -> pd.DataFrame:
        """
        Agrega dados por período
        
        Args:
            df: DataFrame com dados
            periodo: Período de agregação ('D', 'W', 'M', 'Q', 'Y')
            
        Returns:
            DataFrame agregado
        """
        try:
            logger.info(f"Agregando dados por {periodo}...")
            
            df_agregado = df.groupby(pd.Grouper(key='data', freq=periodo)).agg({
                'total_acidentes': 'sum',
                'mortes': 'sum',
                'feridos': 'sum',
                'teste_alcool': 'mean',
                'motocicleta': 'mean'
            }).reset_index()
            
            # Calcular taxas
            df_agregado['taxa_mortalidade'] = (
                df_agregado['mortes'] / df_agregado['total_acidentes'] * 100
            ).round(2)
            
            logger.info(f"✅ Dados agregados: {len(df_agregado)} períodos")
            return df_agregado
            
        except Exception as e:
            logger.error(f"Erro na agregação: {str(e)}")
            raise