"""
Módulo para geração de dados realistas
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
import json
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)


class DataGenerator:
    """
    Gerador de dados realistas para análise de acidentes
    """
    
    def __init__(self, config: Dict, seed: Optional[int] = None):
        """
        Inicializa o gerador de dados
        
        Args:
            config: Dicionário com configurações
            seed: Semente para reprodutibilidade (opcional)
        """
        self.config = config
        self.seed = seed or config.get('DATA', {}).get('SEED', 42)
        self.acidentes = None
        self.infracoes = None
        self.estatisticas = None
        
        # Configurar seed
        np.random.seed(self.seed)
        
        # Configurar dias da semana em português
        self.dias_semana = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        logger.info(f"DataGenerator inicializado com seed {self.seed}")
    
    def _gerar_horas(self, n: int) -> np.ndarray:
        """
        Gera horários realistas para acidentes
        
        Args:
            n: Número de horas a gerar
            
        Returns:
            Array com horários
        """
        horas = []
        for _ in range(n):
            rand = np.random.random()
            if rand < 0.25:  # Pico noturno (17-20h)
                hora = np.random.choice([17, 18, 19, 20], p=[0.2, 0.4, 0.3, 0.1])
            elif rand < 0.45:  # Pico matutino (6-9h)
                hora = np.random.choice([6, 7, 8, 9], p=[0.2, 0.4, 0.3, 0.1])
            elif rand < 0.60:  # Almoço (11-14h)
                hora = np.random.choice([11, 12, 13, 14], p=[0.2, 0.4, 0.3, 0.1])
            else:
                hora = np.random.randint(0, 24)
            horas.append(hora)
        return np.array(horas)
    
    def _calcular_feriados(self, datas: pd.DatetimeIndex) -> np.ndarray:
        """
        Identifica feriados e períodos especiais
        
        Args:
            datas: Índice de datas
            
        Returns:
            Array com flags de feriados
        """
        feriados = np.zeros(len(datas), dtype=bool)
        
        # Períodos especiais
        mask_ano_novo = (datas >= '2025-12-31') | (datas <= '2026-01-01')
        mask_carnaval = (datas >= '2025-03-02') & (datas <= '2025-03-05')
        mask_pascoa = (datas >= '2025-04-18') & (datas <= '2025-04-21')
        
        feriados = mask_ano_novo | mask_carnaval | mask_pascoa
        return feriados
    
    def gerar_acidentes(self) -> pd.DataFrame:
        """
        Gera dados de acidentes com padrões realistas
        
        Returns:
            DataFrame com dados de acidentes
        """
        try:
            logger.info("Gerando dados de acidentes...")
            
            # Configurações
            start_date = self.config['PERIOD']['START_DATE']
            end_date = self.config['PERIOD']['END_DATE']
            data_config = self.config.get('DATA', {})
            
            # Gerar datas
            datas = pd.date_range(start=start_date, end=end_date, freq='D')
            n_dias = len(datas)
            
            # Características temporais
            dias_semana = datas.dayofweek
            meses = datas.month
            
            # Base de acidentes (Poisson)
            lambda_base = data_config.get('ACIDENTES_BASE_LAMBDA', 45)
            acidentes_base = np.random.poisson(lam=lambda_base, size=n_dias)
            acidentes_base = np.maximum(acidentes_base, 20)
            
            # Fatores sazonais
            fator_fim_semana = np.where(dias_semana >= 5, 
                                       data_config.get('FATOR_FIM_SEMANA', 1.3), 1.0)
            fator_ferias = np.where((meses == 12) | (meses == 1) | (meses == 7),
                                   data_config.get('FATOR_FERIAS', 1.2), 1.0)
            fator_feriados = self._calcular_feriados(datas) * 0.3 + 1.0
            
            # Ajuste final
            acidentes_ajustados = (acidentes_base * fator_fim_semana * 
                                  fator_ferias * fator_feriados).astype(int)
            acidentes_ajustados = np.maximum(acidentes_ajustados, 20)
            
            # Mortes
            taxa_morte = data_config.get('TAXA_MORTE_BASE', 0.08)
            mortes = np.random.binomial(acidentes_ajustados, taxa_morte)
            
            # Feridos
            feridos = np.random.poisson(lam=acidentes_ajustados * 0.15)
            feridos = np.clip(feridos, acidentes_ajustados * 0.1, 
                             acidentes_ajustados * 0.3).astype(int)
            
            # Regiões
            regioes_config = self.config.get('REGIONS', {})
            if regioes_config:
                regioes = list(regioes_config.keys())
                regioes_probs = [regioes_config[r]['prob'] for r in regioes]
                regioes_nomes = [regioes_config[r]['nome'] for r in regioes]
            else:
                regioes_nomes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
                regioes_probs = [0.08, 0.27, 0.15, 0.35, 0.15]
            
            # Rodovias
            rodovias_config = self.config.get('RODOVIAS', [])
            if rodovias_config:
                rodovias = [r['nome'] for r in rodovias_config]
                rodovias_probs = [r['prob'] for r in rodovias_config]
                pista_map = {r['nome']: r['pista_simples'] for r in rodovias_config}
            else:
                rodovias = ['BR-101', 'BR-116', 'BR-153', 'BR-324', 'BR-040']
                rodovias_probs = [0.25, 0.25, 0.20, 0.15, 0.15]
                pista_map = {r: 0.4 for r in rodovias}
            
            # Selecionar rodovias
            rodovias_dia = np.random.choice(rodovias, n_dias, p=rodovias_probs)
            
            # Pista simples
            pista_simples = np.array([
                np.random.choice([0, 1], p=[1-pista_map[br], pista_map[br]]) 
                for br in rodovias_dia
            ])
            
            # Criar DataFrame
            self.acidentes = pd.DataFrame({
                'data': datas,
                'total_acidentes': acidentes_ajustados,
                'mortes': mortes,
                'feridos': feridos,
                'regiao': np.random.choice(regioes_nomes, n_dias, p=regioes_probs),
                'br': rodovias_dia,
                'teste_alcool': np.random.choice([0, 1], n_dias, p=[0.85, 0.15]),
                'motocicleta': np.random.choice([0, 1], n_dias, p=[0.72, 0.28]),
                'chuva': np.random.choice([0, 1], n_dias, p=[0.70, 0.30]),
                'pista_simples': pista_simples,
                'hora': self._gerar_horas(n_dias)
            })
            
            # Operações especiais
            self.acidentes['operacao'] = 'Normal'
            mask_rodovida = (self.acidentes['data'] >= '2025-12-18') & (self.acidentes['data'] <= '2026-02-28')
            mask_anonovo = (self.acidentes['data'] >= '2025-12-24') & (self.acidentes['data'] <= '2026-01-01')
            self.acidentes.loc[mask_rodovida, 'operacao'] = 'Rodovida 2025/2026'
            self.acidentes.loc[mask_anonovo, 'operacao'] = 'Ano Novo 2025/2026'
            
            logger.info(f"✅ {len(self.acidentes):,} dias de acidentes gerados")
            return self.acidentes
            
        except Exception as e:
            logger.error(f"Erro ao gerar acidentes: {str(e)}")
            traceback.print_exc()
            raise
    
    def gerar_infracoes(self) -> pd.DataFrame:
        """
        Gera dados de infrações
        
        Returns:
            DataFrame com dados de infrações
        """
        try:
            logger.info("Gerando dados de infrações...")
            
            n_infracoes = self.config.get('DATA', {}).get('N_INFRACOES', 60000)
            start_date = self.config['PERIOD']['START_DATE']
            end_date = self.config['PERIOD']['END_DATE']
            
            datas = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Dados das infrações
            infracoes_config = self.config.get('INFRACOES', {})
            if infracoes_config and 'tipos' in infracoes_config:
                tipos = [t['nome'] for t in infracoes_config['tipos']]
                probs = [t['prob'] for t in infracoes_config['tipos']]
                multas = [t['multa'] for t in infracoes_config['tipos']]
                gravidade_map = {t['nome']: t['gravidade'] for t in infracoes_config['tipos']}
            else:
                tipos = ['Excesso de velocidade', 'Ultrapassagem irregular', 'Embriaguez']
                probs = [0.5, 0.3, 0.2]
                multas = [880.41, 2937.70, 2937.70]
                gravidade_map = {
                    'Excesso de velocidade': 'Média',
                    'Ultrapassagem irregular': 'Alta',
                    'Embriaguez': 'Altíssima'
                }
            
            ufs = self.config.get('UFS', ['SP', 'MG', 'RJ', 'BA', 'PR'])
            
            datas_infracoes = np.random.choice(datas, n_infracoes)
            
            self.infracoes = pd.DataFrame({
                'id_infracao': range(1, n_infracoes + 1),
                'tipo': np.random.choice(tipos, n_infracoes, p=probs),
                'valor_multa': np.random.choice(multas, n_infracoes, p=probs),
                'uf': np.random.choice(ufs, n_infracoes),
                'data': datas_infracoes,
                'veiculo_apreendido': np.random.choice([0, 1], n_infracoes, p=[0.95, 0.05]),
                'detido': np.random.choice([0, 1], n_infracoes, p=[0.998, 0.002])
            })
            
            # Adicionar gravidade
            self.infracoes['gravidade'] = self.infracoes['tipo'].map(gravidade_map)
            
            logger.info(f"✅ {len(self.infracoes):,} infrações geradas")
            return self.infracoes
            
        except Exception as e:
            logger.error(f"Erro ao gerar infrações: {str(e)}")
            traceback.print_exc()
            raise
    
    def gerar_estatisticas_uf(self) -> pd.DataFrame:
        """
        Gera estatísticas por UF
        
        Returns:
            DataFrame com estatísticas por UF
        """
        try:
            logger.info("Gerando estatísticas por UF...")
            
            estados_dados = []
            ufs = self.config.get('UFS', ['SP', 'MG', 'RJ', 'BA', 'PR'])
            fatores = self.config.get('FATORES_ESTADUAIS', {})
            
            for uf in ufs:
                for ano in [2025, 2026]:
                    meses = 4 if ano == 2026 else 12
                    fator = fatores.get(uf, 1.0)
                    
                    estados_dados.append({
                        'uf': uf,
                        'ano': ano,
                        'total_acidentes': int(np.random.poisson(lam=800 * fator) * (meses/12)),
                        'total_mortes': int(np.random.poisson(lam=65 * fator) * (meses/12)),
                        'total_feridos': int(np.random.poisson(lam=950 * fator) * (meses/12)),
                        'infracoes_aplicadas': int(np.random.poisson(lam=3000 * fator) * (meses/12)),
                        'valor_arrecadado': float(np.random.uniform(500000, 2000000) * fator * (meses/12))
                    })
            
            self.estatisticas = pd.DataFrame(estados_dados)
            logger.info(f"✅ {len(self.estatisticas):,} registros de estatísticas gerados")
            return self.estatisticas
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {str(e)}")
            traceback.print_exc()
            raise
    
    def gerar_todos_dados(self) -> Dict[str, pd.DataFrame]:
        """
        Gera todos os datasets
        
        Returns:
            Dicionário com todos os DataFrames
        """
        return {
            'acidentes': self.gerar_acidentes(),
            'infracoes': self.gerar_infracoes(),
            'estatisticas': self.gerar_estatisticas_uf()
        }
    
    def salvar_dados(self, output_dir: str = 'dados_brutos'):
        """
        Salva os dados gerados em arquivos
        
        Args:
            output_dir: Diretório de saída
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if self.acidentes is not None:
            self.acidentes.to_csv(f'{output_dir}/acidentes_brutos.csv', index=False)
        
        if self.infracoes is not None:
            self.infracoes.to_csv(f'{output_dir}/infracoes_brutas.csv', index=False)
        
        if self.estatisticas is not None:
            self.estatisticas.to_csv(f'{output_dir}/estatisticas_brutas.csv', index=False)
        
        logger.info(f"✅ Dados salvos em {output_dir}/")
