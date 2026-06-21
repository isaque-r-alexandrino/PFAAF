"""
Sistema de Análise de Acidentes em Rodovias Federais - VERSÃO SIMPLIFICADA
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
import json
import logging
import sys
from pathlib import Path
import traceback

warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnaliseAcidentes:
    """Classe principal para análise de acidentes"""
    
    def __init__(self, config_path='config.json'):
        """Inicializa o sistema"""
        self.config = self._carregar_config(config_path)
        self.dados = {}
        self.kpis = {}
        self.insights = []
        self.timestamp_inicio = datetime.now()
        
        # Configurar seed
        np.random.seed(self.config.get('DATA', {}).get('SEED', 42))
        
        self._mostrar_boas_vindas()
    
    def _carregar_config(self, config_path):
        """Carrega configurações do JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f" Configurações carregadas")
            return config
        except:
            logger.warning("Usando configurações padrão")
            return {
                "PERIOD": {"START_DATE": "2025-01-01", "END_DATE": "2026-02-28"},
                "DATA": {"SEED": 42, "ACIDENTES_BASE_LAMBDA": 45, "TAXA_MORTE_BASE": 0.08},
                "COSTS": {"CUSTO_POR_MORTE": 350000, "CUSTO_POR_FERIDO": 50000}
            }
    
    def _mostrar_boas_vindas(self):
        """Mostra mensagem inicial"""
        print("\n" + "="*80)
        print(" ANÁLISE DE ACIDENTES EM RODOVIAS FEDERAIS")
        print("="*80)
        print(f" Período: {self.config['PERIOD']['START_DATE']} a {self.config['PERIOD']['END_DATE']}")
        print(f" Início: {self.timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def _gerar_horas(self, n):
        """Gera horários realistas"""
        horas = []
        for _ in range(n):
            rand = np.random.random()
            if rand < 0.25:
                hora = np.random.choice([17, 18, 19, 20], p=[0.2, 0.4, 0.3, 0.1])
            elif rand < 0.45:
                hora = np.random.choice([6, 7, 8, 9], p=[0.2, 0.4, 0.3, 0.1])
            elif rand < 0.60:
                hora = np.random.choice([11, 12, 13, 14], p=[0.2, 0.4, 0.3, 0.1])
            else:
                hora = np.random.randint(0, 24)
            horas.append(hora)
        return np.array(horas)
    
    def gerar_dados(self):
        """Gera todos os dados necessários"""
        try:
            logger.info(" Gerando dados...")
            
            # Datas
            start = self.config['PERIOD']['START_DATE']
            end = self.config['PERIOD']['END_DATE']
            datas = pd.date_range(start=start, end=end, freq='D')
            n_dias = len(datas)
            
            # Acidentes
            lambda_base = self.config['DATA'].get('ACIDENTES_BASE_LAMBDA', 45)
            acidentes = np.random.poisson(lam=lambda_base, size=n_dias)
            acidentes = np.maximum(acidentes, 20)
            
            # Fatores sazonais
            dias_semana = datas.dayofweek
            meses = datas.month
            fator_fim_semana = np.where(dias_semana >= 5, 1.3, 1.0)
            fator_ferias = np.where((meses == 12) | (meses == 1) | (meses == 7), 1.2, 1.0)
            
            # Ajuste
            acidentes = (acidentes * fator_fim_semana * fator_ferias).astype(int)
            acidentes = np.maximum(acidentes, 20)
            
            # Mortes e feridos
            taxa_morte = self.config['DATA'].get('TAXA_MORTE_BASE', 0.08)
            mortes = np.random.binomial(acidentes, taxa_morte)
            feridos = np.random.poisson(lam=acidentes * 0.15)
            feridos = np.clip(feridos, acidentes * 0.1, acidentes * 0.3).astype(int)
            
            # Regiões e rodovias
            regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
            regioes_probs = [0.08, 0.27, 0.15, 0.35, 0.15]
            rodovias = ['BR-101', 'BR-116', 'BR-153', 'BR-324', 'BR-040']
            rodovias_probs = [0.25, 0.25, 0.20, 0.15, 0.15]
            
            # DataFrame de acidentes
            self.dados['acidentes'] = pd.DataFrame({
                'data': datas,
                'total_acidentes': acidentes,
                'mortes': mortes,
                'feridos': feridos,
                'regiao': np.random.choice(regioes, n_dias, p=regioes_probs),
                'br': np.random.choice(rodovias, n_dias, p=rodovias_probs),
                'teste_alcool': np.random.choice([0, 1], n_dias, p=[0.85, 0.15]),
                'motocicleta': np.random.choice([0, 1], n_dias, p=[0.72, 0.28]),
                'chuva': np.random.choice([0, 1], n_dias, p=[0.70, 0.30]),
                'pista_simples': np.random.choice([0, 1], n_dias, p=[0.40, 0.60]),
                'hora': self._gerar_horas(n_dias)
            })
            
            # Operações especiais
            self.dados['acidentes']['operacao'] = 'Normal'
            mask = (self.dados['acidentes']['data'] >= '2025-12-18') & (self.dados['acidentes']['data'] <= '2026-02-28')
            self.dados['acidentes'].loc[mask, 'operacao'] = 'Rodovida 2025/2026'
            
            # Infrações
            n_infracoes = 60000
            tipos = ['Excesso de velocidade', 'Ultrapassagem irregular', 'Embriaguez', 
                    'Sem cinto', 'Uso de celular', 'Recusa ao teste']
            probs = [0.35, 0.20, 0.12, 0.12, 0.11, 0.10]
            multas = [880.41, 2937.70, 2937.70, 195.23, 2937.70, 2937.70]
            ufs = ['SP', 'MG', 'RJ', 'BA', 'PR', 'RS', 'SC', 'GO', 'PE', 'CE']
            
            self.dados['infracoes'] = pd.DataFrame({
                'id': range(1, n_infracoes + 1),
                'tipo': np.random.choice(tipos, n_infracoes, p=probs),
                'valor_multa': np.random.choice(multas, n_infracoes, p=probs),
                'uf': np.random.choice(ufs, n_infracoes),
                'data': np.random.choice(datas, n_infracoes)
            })
            
            # Estatísticas por UF
            estados = []
            for uf in ufs[:5]:
                for ano in [2025, 2026]:
                    meses = 4 if ano == 2026 else 12
                    estados.append({
                        'uf': uf,
                        'ano': ano,
                        'total_acidentes': np.random.randint(500, 1500),
                        'total_mortes': np.random.randint(40, 100),
                        'total_feridos': np.random.randint(500, 1500)
                    })
            self.dados['estatisticas'] = pd.DataFrame(estados)
            
            logger.info(f" {len(self.dados['acidentes'])} dias de dados gerados")
            return True
            
        except Exception as e:
            logger.error(f" Erro ao gerar dados: {str(e)}")
            return False
    
    def processar_dados(self):
        """Processa e enriquece os dados"""
        try:
            logger.info("🔧 Processando dados...")
            
            df = self.dados['acidentes'].copy()
            
            # Features temporais
            df['data'] = pd.to_datetime(df['data'])
            df['ano'] = df['data'].dt.year
            df['mes'] = df['data'].dt.month
            df['dia_semana'] = df['data'].dt.day_name()
            
            # Taxa de mortalidade
            df['taxa_mortalidade'] = (df['mortes'] / df['total_acidentes'] * 100).round(2)
            
            # Classificação de risco
            df['classificacao_risco'] = np.where(
                (df['teste_alcool'] == 1) & (df['motocicleta'] == 1), 'CRÍTICO',
                np.where(df['teste_alcool'] == 1, 'ALTO',
                np.where(df['motocicleta'] == 1, 'MÉDIO', 'BAIXO'))
            )
            
            # Índice de risco
            df['indice_risco'] = (
                df['teste_alcool'] * 0.4 +
                df['motocicleta'] * 0.3 +
                df['pista_simples'] * 0.2 +
                df['chuva'] * 0.1
            ).round(3)
            
            self.dados['acidentes'] = df
            logger.info(" Dados processados com sucesso")
            return True
            
        except Exception as e:
            logger.error(f" Erro no processamento: {str(e)}")
            return False
    
    def calcular_kpis(self):
        """Calcula KPIs"""
        try:
            logger.info(" Calculando KPIs...")
            
            df = self.dados['acidentes']
            
            total_acidentes = df['total_acidentes'].sum()
            total_mortes = df['mortes'].sum()
            total_feridos = df['feridos'].sum()
            
            custo_morte = self.config['COSTS'].get('CUSTO_POR_MORTE', 350000)
            custo_ferido = self.config['COSTS'].get('CUSTO_POR_FERIDO', 50000)
            
            self.kpis = {
                'total_acidentes': int(total_acidentes),
                'total_mortes': int(total_mortes),
                'total_feridos': int(total_feridos),
                'severidade_media': round(df['mortes'].mean(), 2),
                'taxa_mortalidade': round(df['taxa_mortalidade'].mean(), 2),
                'risco_medio': round(df['indice_risco'].mean(), 3),
                'percentual_alcool': round((df['teste_alcool'].sum() / len(df)) * 100, 2),
                'percentual_moto': round((df['motocicleta'].sum() / len(df)) * 100, 2),
                'custo_social': total_mortes * custo_morte + total_feridos * custo_ferido
            }
            self.kpis['custo_formatado'] = f"R$ {self.kpis['custo_social']:,.2f}"
            
            logger.info(" KPIs calculados")
            return True
            
        except Exception as e:
            logger.error(f" Erro nos KPIs: {str(e)}")
            return False
    
    def gerar_graficos(self):
        """Gera gráficos"""
        try:
            logger.info(" Gerando gráficos...")
            
            df = self.dados['acidentes']
            
            fig = plt.figure(figsize=(18, 20))
            
            # 1. Acidentes por Região
            ax1 = fig.add_subplot(3, 3, 1)
            data = df.groupby('regiao')['total_acidentes'].sum().sort_values(ascending=False)
            ax1.bar(data.index, data.values, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7'])
            ax1.set_title('Acidentes por Região', fontweight='bold')
            ax1.set_ylabel('Total')
            for i, v in enumerate(data.values):
                ax1.text(i, v + 100, f'{int(v):,}', ha='center', fontweight='bold', fontsize=9)
            
            # 2. Evolução Mensal
            ax2 = fig.add_subplot(3, 3, 2)
            mensal = df.groupby(df['data'].dt.to_period('M')).agg({
                'total_acidentes': 'sum',
                'mortes': 'sum'
            }).reset_index()
            mensal['data'] = mensal['data'].astype(str)
            ax2.plot(mensal['data'], mensal['total_acidentes'], marker='o', label='Acidentes', linewidth=2)
            ax2.plot(mensal['data'], mensal['mortes'], marker='s', label='Mortes', linewidth=2)
            ax2.set_title('Evolução Mensal', fontweight='bold')
            ax2.legend()
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. Top Rodovias
            ax3 = fig.add_subplot(3, 3, 3)
            data = df.groupby('br')['mortes'].sum().sort_values(ascending=False).head(8)
            ax3.barh(range(len(data)), data.values, color='#d62728')
            ax3.set_yticks(range(len(data)))
            ax3.set_yticklabels(data.index)
            ax3.set_title('Rodovias com Mais Mortes', fontweight='bold')
            ax3.invert_yaxis()
            
            # 4. Correlação
            ax4 = fig.add_subplot(3, 3, 4)
            cols = ['total_acidentes', 'mortes', 'feridos', 'teste_alcool', 'motocicleta', 'indice_risco']
            corr = df[cols].corr()
            sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax4, square=True)
            ax4.set_title('Matriz de Correlação', fontweight='bold')
            
            # 5. Distribuição por Hora
            ax5 = fig.add_subplot(3, 3, 5)
            data = df.groupby('hora')['total_acidentes'].sum()
            ax5.plot(data.index, data.values, marker='o', color='#17becf', linewidth=2)
            ax5.fill_between(data.index, 0, data.values, alpha=0.3)
            ax5.set_title('Acidentes por Hora', fontweight='bold')
            ax5.set_xlabel('Hora')
            ax5.grid(True, alpha=0.3)
            
            # 6. Classificação de Risco
            ax6 = fig.add_subplot(3, 3, 6)
            data = df['classificacao_risco'].value_counts()
            cores = {'CRÍTICO': '#000000', 'ALTO': '#d62728', 'MÉDIO': '#ff7f0e', 'BAIXO': '#2ca02c'}
            colors = [cores.get(x, '#cccccc') for x in data.index]
            ax6.pie(data.values, labels=data.index, autopct='%1.1f%%', colors=colors, startangle=90)
            ax6.set_title('Classificação de Risco', fontweight='bold')
            
            # 7. Infrações
            ax7 = fig.add_subplot(3, 3, 7)
            data = self.dados['infracoes']['tipo'].value_counts().head(6)
            ax7.bar(data.index, data.values, color='#9467bd')
            ax7.set_title('Principais Infrações', fontweight='bold')
            ax7.tick_params(axis='x', rotation=45)
            
            # 8. Mortes por Dia
            ax8 = fig.add_subplot(3, 3, 8)
            dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            data = df.groupby(df['data'].dt.day_name())['mortes'].mean().reindex(dias)
            cores = ['#ff9896' if d in ['Saturday', 'Sunday'] else '#98df8a' for d in data.index]
            ax8.bar(dias_pt, data.values, color=cores)
            ax8.set_title('Média de Mortes por Dia', fontweight='bold')
            ax8.tick_params(axis='x', rotation=45)
            
            # 9. Operações
            ax9 = fig.add_subplot(3, 3, 9)
            operacoes = df['operacao'].unique()
            dados_box = [df[df['operacao'] == op]['total_acidentes'] for op in operacoes]
            bp = ax9.boxplot(dados_box, labels=operacoes, patch_artist=True)
            for i, patch in enumerate(bp['boxes']):
                patch.set_facecolor(['#2ca02c', '#d62728', '#ff7f0e'][i % 3])
            ax9.set_title('Acidentes por Operação', fontweight='bold')
            ax9.tick_params(axis='x', rotation=45)
            
            plt.suptitle('DASHBOARD - ACIDENTES EM RODOVIAS FEDERAIS 2025-2026',
                        fontsize=16, fontweight='bold', y=0.98)
            plt.tight_layout()
            
            # Salvar
            Path('resultados').mkdir(exist_ok=True)
            plt.savefig('resultados/dashboard.png', dpi=150, bbox_inches='tight')
            plt.show()
            
            logger.info(" Gráficos gerados")
            return True
            
        except Exception as e:
            logger.error(f" Erro nos gráficos: {str(e)}")
            return False
    
    def gerar_insights(self):
        """Gera insights automáticos"""
        try:
            logger.info(" Gerando insights...")
            
            df = self.dados['acidentes']
            
            # 1. Período crítico
            acidentes_op = df.groupby('operacao')['total_acidentes'].mean()
            pior_op = acidentes_op.idxmax()
            melhor_op = acidentes_op.idxmin()
            aumento = ((acidentes_op[pior_op]/acidentes_op[melhor_op])-1)*100
            
            self.insights.append({
                'titulo': ' Período Crítico',
                'descricao': f'Operação {pior_op} tem {aumento:.0f}% mais acidentes',
                'recomendacao': f'Reforçar fiscalização durante {pior_op}'
            })
            
            # 2. Álcool
            taxa_alcool = df[df['teste_alcool']==1]['taxa_mortalidade'].mean()
            taxa_sem = df[df['teste_alcool']==0]['taxa_mortalidade'].mean()
            aumento = ((taxa_alcool/taxa_sem)-1)*100
            
            self.insights.append({
                'titulo': ' Impacto do Álcool',
                'descricao': f'Acidentes com álcool têm {aumento:.0f}% mais mortes',
                'recomendacao': 'Ampliar blitz da Lei Seca em finais de semana'
            })
            
            # 3. Rodovia mais perigosa
            rodovia = df.groupby('br')['taxa_mortalidade'].mean().idxmax()
            taxa = df.groupby('br')['taxa_mortalidade'].mean().max()
            
            self.insights.append({
                'titulo': ' Rodovia Mais Perigosa',
                'descricao': f'{rodovia} tem taxa de mortalidade de {taxa:.2f}%',
                'recomendacao': f'Priorizar investimentos na {rodovia}'
            })
            
            # 4. Motociclistas
            perc_moto = (df['motocicleta'].sum() / len(df)) * 100
            perc_mortes = (df[df['motocicleta']==1]['mortes'].sum() / df['mortes'].sum()) * 100
            
            self.insights.append({
                'titulo': ' Motociclistas',
                'descricao': f'{perc_moto:.1f}% dos acidentes, {perc_mortes:.1f}% das mortes',
                'recomendacao': 'Campanhas educativas e faixas exclusivas para motos'
            })
            
            # 5. Dia de risco
            dias = df.groupby(df['data'].dt.day_name())['mortes'].mean()
            pior_dia = dias.idxmax()
            
            self.insights.append({
                'titulo': ' Dia de Risco',
                'descricao': f'{pior_dia} tem média de {dias[pior_dia]:.2f} mortes',
                'recomendacao': f'Operações especiais nas {pior_dia}s'
            })
            
            # 6. Horário
            hora_data = df.groupby('hora')['total_acidentes'].sum()
            pico = hora_data.idxmax()
            
            self.insights.append({
                'titulo': ' Horário de Pico',
                'descricao': f'{pico}h concentra o maior número de acidentes',
                'recomendacao': 'Reforçar patrulhamento nos horários de pico'
            })
            
            print("\n" + "="*80)
            print("💡 INSIGHTS E RECOMENDAÇÕES")
            print("="*80)
            for i, insight in enumerate(self.insights, 1):
                print(f"\n{i}. {insight['titulo']}")
                print(f"    {insight['descricao']}")
                print(f"    {insight['recomendacao']}")
            
            logger.info(f" {len(self.insights)} insights gerados")
            return True
            
        except Exception as e:
            logger.error(f" Erro nos insights: {str(e)}")
            return False
    
    def exportar_resultados(self):
        """Exporta todos os resultados"""
        try:
            logger.info(" Exportando resultados...")
            
            Path('resultados').mkdir(exist_ok=True)
            
            # Exportar CSVs
            self.dados['acidentes'].to_csv('resultados/acidentes.csv', index=False, encoding='utf-8-sig')
            self.dados['infracoes'].to_csv('resultados/infracoes.csv', index=False, encoding='utf-8-sig')
            self.dados['estatisticas'].to_csv('resultados/estatisticas.csv', index=False, encoding='utf-8-sig')
            
            # KPIs
            pd.DataFrame([self.kpis]).to_csv('resultados/kpis.csv', index=False, encoding='utf-8-sig')
            
            # Insights
            with open('resultados/insights.txt', 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("INSIGHTS E RECOMENDAÇÕES\n")
                f.write("="*80 + "\n\n")
                for i, insight in enumerate(self.insights, 1):
                    f.write(f"{i}. {insight['titulo']}\n")
                    f.write(f"   {insight['descricao']}\n")
                    f.write(f"   Recomendação: {insight['recomendacao']}\n\n")
            
            logger.info(" Resultados exportados")
            return True
            
        except Exception as e:
            logger.error(f" Erro na exportação: {str(e)}")
            return False
    
    def executar(self):
        """Executa todo o pipeline"""
        try:
            print("\n" + "="*50)
            print(" INICIANDO ANÁLISE")
            print("="*50)
            
            # 1. Gerar dados
            if not self.gerar_dados():
                return False
            
            # 2. Processar dados
            if not self.processar_dados():
                return False
            
            # 3. Calcular KPIs
            if not self.calcular_kpis():
                return False
            
            # 4. Gerar gráficos
            if not self.gerar_graficos():
                return False
            
            # 5. Gerar insights
            if not self.gerar_insights():
                return False
            
            # 6. Exportar
            if not self.exportar_resultados():
                return False
            
            # Resumo final
            tempo = (datetime.now() - self.timestamp_inicio).total_seconds()
            
            print("\n" + "="*80)
            print(" ANÁLISE CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print(f"\n RESUMO:")
            print(f"   • Acidentes: {self.kpis['total_acidentes']:,}")
            print(f"   • Mortes: {self.kpis['total_mortes']:.0f}")
            print(f"   • Insights: {len(self.insights)}")
            print(f"   • Custo Social: {self.kpis['custo_formatado']}")
            print(f"   • Tempo: {tempo:.2f} segundos")
            print(f"\n Resultados em: 'resultados/'")
            print("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f" Erro fatal: {str(e)}")
            traceback.print_exc()
            return False


if __name__ == "__main__":
    sistema = AnaliseAcidentes('config.json')
    sucesso = sistema.executar()
    sys.exit(0 if sucesso else 1)