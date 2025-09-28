"""
Gold Layer Processor - Pipeline de Cotações Cambiais
MBA em Data Engineering

Este módulo é responsável por:
1. Consolidar dados do Silver Layer
2. Calcular métricas e agregações
3. Gerar análises históricas
4. Criar Gold Layer otimizado para análise
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import structlog
import json

logger = structlog.get_logger()


class GoldLayerProcessor:
    """
    Processador principal do Gold Layer
    """
    
    def __init__(self, silver_path: str = 'data/silver', gold_path: str = 'data/gold'):
        """
        Inicializa o processador do Gold Layer
        
        Args:
            silver_path: Caminho dos dados Silver
            gold_path: Caminho para Gold Layer
        """
        self.silver_path = Path(silver_path)
        self.gold_path = Path(gold_path)
        
        # Criar diretório gold se não existir
        self.gold_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "GoldLayerProcessor inicializado",
            silver_path=str(self.silver_path),
            gold_path=str(self.gold_path)
        )
    
    def load_silver_data(self, start_date: date, end_date: date = None) -> pd.DataFrame:
        """
        Carrega dados do Silver Layer para período específico
        
        Args:
            start_date: Data inicial
            end_date: Data final (se None, usa apenas start_date)
            
        Returns:
            DataFrame consolidado do Silver Layer
        """
        if end_date is None:
            end_date = start_date
            
        logger.info(
            "Carregando dados Silver Layer",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        dataframes = []
        current_date = start_date
        
        while current_date <= end_date:
            file_path = self.silver_path / f"exchange_rates_{current_date.strftime('%Y-%m-%d')}.parquet"
            
            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    dataframes.append(df)
                    logger.debug(f"Carregado {len(df)} registros de {current_date}")
                except Exception as e:
                    logger.warning(f"Erro ao carregar {file_path}: {str(e)}")
            else:
                logger.warning(f"Arquivo não encontrado: {file_path}")
                
            current_date += timedelta(days=1)
        
        if not dataframes:
            raise ValueError(f"Nenhum dado encontrado para o período {start_date} a {end_date}")
        
        # Consolidar todos os DataFrames
        consolidated_df = pd.concat(dataframes, ignore_index=True)
        
        logger.info(
            "Dados Silver consolidados",
            total_records=len(consolidated_df),
            date_range=f"{start_date} a {end_date}",
            unique_dates=consolidated_df['collection_date'].nunique(),
            unique_currencies=consolidated_df['target_currency'].nunique()
        )
        
        return consolidated_df
    
    def calculate_daily_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula métricas diárias por moeda
        
        Args:
            df: DataFrame com dados Silver
            
        Returns:
            DataFrame com métricas diárias agregadas
        """
        logger.info("Calculando métricas diárias")
        
        # Agrupar por data e moeda
        daily_metrics = df.groupby(['collection_date', 'target_currency']).agg({
            'exchange_rate': ['mean', 'std', 'min', 'max', 'count'],
            'collection_timestamp': 'max'  # Último timestamp do dia
        }).reset_index()
        
        # Flatten column names
        daily_metrics.columns = [
            'date', 'currency', 'rate_mean', 'rate_std', 'rate_min', 
            'rate_max', 'observations', 'last_update'
        ]
        
        # Calcular métricas adicionais
        daily_metrics['rate_range'] = daily_metrics['rate_max'] - daily_metrics['rate_min']
        daily_metrics['rate_cv'] = daily_metrics['rate_std'] / daily_metrics['rate_mean']  # Coeficiente de variação
        daily_metrics['rate_cv'] = daily_metrics['rate_cv'].fillna(0)
        
        # Ordenar por data e moeda
        daily_metrics = daily_metrics.sort_values(['date', 'currency']).reset_index(drop=True)
        
        logger.info(
            "Métricas diárias calculadas",
            total_records=len(daily_metrics),
            date_range=f"{daily_metrics['date'].min()} a {daily_metrics['date'].max()}",
            currencies=daily_metrics['currency'].nunique()
        )
        
        return daily_metrics
    
    def calculate_historical_trends(self, daily_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula tendências históricas e variações
        
        Args:
            daily_metrics: DataFrame com métricas diárias
            
        Returns:
            DataFrame enriquecido com tendências
        """
        logger.info("Calculando tendências históricas")
        
        # Criar cópia para não modificar original
        trends_df = daily_metrics.copy()
        
        # Ordenar por moeda e data
        trends_df = trends_df.sort_values(['currency', 'date']).reset_index(drop=True)
        
        # Calcular variações por moeda
        for currency in trends_df['currency'].unique():
            mask = trends_df['currency'] == currency
            currency_data = trends_df[mask].copy()
            
            # Verificar se há dados suficientes
            if len(currency_data) < 2:
                # Se só há 1 dia de dados, preencher com zeros
                currency_data['daily_change'] = 0.0
                currency_data['cumulative_change'] = 0.0
                currency_data['volatility_7d'] = 0.0
            else:
                # Variação diária (%)
                currency_data['daily_change'] = currency_data['rate_mean'].pct_change() * 100
                
                # Primeira linha será NaN, preencher com 0
                currency_data['daily_change'] = currency_data['daily_change'].fillna(0)
                
                # Variação acumulada desde o primeiro dia (%)
                first_rate = currency_data['rate_mean'].iloc[0]
                currency_data['cumulative_change'] = ((currency_data['rate_mean'] / first_rate) - 1) * 100
                
                # Volatilidade 7 dias
                currency_data['volatility_7d'] = currency_data['daily_change'].rolling(window=7, min_periods=1).std()
                currency_data['volatility_7d'] = currency_data['volatility_7d'].fillna(0)
            
            # Média móvel 7 dias
            currency_data['ma_7d'] = currency_data['rate_mean'].rolling(window=7, min_periods=1).mean()
            
            # Máxima e mínima dos últimos 30 dias
            currency_data['max_30d'] = currency_data['rate_mean'].rolling(window=30, min_periods=1).max()
            currency_data['min_30d'] = currency_data['rate_mean'].rolling(window=30, min_periods=1).min()
            
            # Posição relativa
            range_30d = currency_data['max_30d'] - currency_data['min_30d']
            currency_data['relative_position'] = np.where(
                range_30d > 0,
                (currency_data['rate_mean'] - currency_data['min_30d']) / range_30d * 100,
                50.0  # Default se não há variação
            )
            
            # Atualizar no DataFrame principal
            trends_df.loc[mask] = currency_data
        
        # Preencher NaN com 0 para variações
        trends_df['daily_change'] = trends_df['daily_change'].fillna(0)
        trends_df['volatility_7d'] = trends_df['volatility_7d'].fillna(0)
        
        logger.info(
            "Tendências históricas calculadas",
            currencies_processed=trends_df['currency'].nunique(),
            metrics_added=6  # daily_change, cumulative_change, ma_7d, etc.
        )
        
        return trends_df
    
    def create_currency_summary(self, trends_df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria resumo consolidado por moeda
        
        Args:
            trends_df: DataFrame com tendências
            
        Returns:
            DataFrame com resumo por moeda
        """
        logger.info("Criando resumo por moeda")
        
        # Pegar dados mais recentes de cada moeda
        latest_data = trends_df.groupby('currency').last().reset_index()
        
        # Garantir que daily_change existe
        if 'daily_change' not in latest_data.columns:
            latest_data['daily_change'] = 0.0
        if 'cumulative_change' not in latest_data.columns:
            latest_data['cumulative_change'] = 0.0
            
        # Dados históricos por moeda - processamento seguro
        agg_dict = {
            'rate_mean': ['min', 'max', 'mean'],
            'volatility_7d': 'mean',
            'date': ['min', 'max', 'count']
        }
        
        # Só incluir daily_change se existir
        if 'daily_change' in trends_df.columns:
            daily_change_stats = trends_df.groupby('currency')['daily_change'].agg(['std', 'min', 'max']).reset_index()
            daily_change_stats = daily_change_stats.fillna(0)
        else:
            daily_change_stats = pd.DataFrame({
                'currency': trends_df['currency'].unique(),
                'std': 0.0, 'min': 0.0, 'max': 0.0
            })
        
        historical_stats = trends_df.groupby('currency').agg(agg_dict).reset_index()
        
        # Flatten columns
        historical_stats.columns = [
            'currency', 'historical_min', 'historical_max', 'historical_avg',
            'avg_volatility_7d', 'first_date', 'last_date', 'total_observations'
        ]
        
        # Merge com estatísticas de daily_change
        historical_stats = historical_stats.merge(daily_change_stats, on='currency')
        historical_stats = historical_stats.rename(columns={
            'std': 'avg_daily_volatility',
            'min': 'max_daily_drop', 
            'max': 'max_daily_gain'
        })
        
        # Merge com dados mais recentes - apenas colunas que existem
        merge_columns = ['currency', 'rate_mean', 'ma_7d', 'volatility_7d', 'relative_position', 'last_update']
        if 'daily_change' in latest_data.columns:
            merge_columns.append('daily_change')
        if 'cumulative_change' in latest_data.columns:
            merge_columns.append('cumulative_change')
            
        summary = latest_data[merge_columns].merge(historical_stats, on='currency')
        
        # Renomear colunas
        rename_dict = {
            'rate_mean': 'current_rate'
        }
        if 'daily_change' in summary.columns:
            rename_dict['daily_change'] = 'last_daily_change'
        if 'cumulative_change' in summary.columns:
            rename_dict['cumulative_change'] = 'total_change_pct'
            
        summary = summary.rename(columns=rename_dict)
        
        # Garantir que colunas necessárias existem
        if 'last_daily_change' not in summary.columns:
            summary['last_daily_change'] = 0.0
        if 'total_change_pct' not in summary.columns:
            summary['total_change_pct'] = 0.0
        
        # Classificações
        summary['volatility_class'] = pd.cut(
            summary['avg_volatility_7d'], 
            bins=[0, 1, 2, 5, float('inf')], 
            labels=['Baixa', 'Moderada', 'Alta', 'Muito Alta']
        )
        
        summary['trend_class'] = summary['last_daily_change'].apply(
            lambda x: 'Forte Alta' if x > 2 else
                     'Alta' if x > 0.5 else
                     'Estável' if -0.5 <= x <= 0.5 else
                     'Baixa' if x > -2 else
                     'Forte Baixa'
        )
        
        # Ordenar por importância
        summary = summary.sort_values(['total_observations', 'avg_volatility_7d'], 
                                    ascending=[False, True]).reset_index(drop=True)
        
        logger.info(
            "Resumo por moeda criado",
            currencies=len(summary),
            date_range=f"{summary['first_date'].min()} a {summary['last_date'].max()}"
        )
        
        return summary
    
    def create_market_overview(self, summary_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Cria overview geral do mercado
        
        Args:
            summary_df: DataFrame com resumo por moeda
            
        Returns:
            Dicionário com overview do mercado
        """
        logger.info("Criando overview do mercado")
        
        # Moedas principais (as 10 mais observadas)
        major_currencies = summary_df.head(10)
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'total_currencies': len(summary_df),
            'observation_period': {
                'start': summary_df['first_date'].min().isoformat(),
                'end': summary_df['last_date'].max().isoformat(),
                'total_days': (summary_df['last_date'].max() - summary_df['first_date'].min()).days + 1
            },
            'market_sentiment': {
                'currencies_up': len(summary_df[summary_df['last_daily_change'] > 0]),
                'currencies_down': len(summary_df[summary_df['last_daily_change'] < 0]),
                'currencies_stable': len(summary_df[summary_df['last_daily_change'].abs() <= 0.1])
            },
            'volatility_distribution': {
                'low': len(summary_df[summary_df['volatility_class'] == 'Baixa']),
                'moderate': len(summary_df[summary_df['volatility_class'] == 'Moderada']),
                'high': len(summary_df[summary_df['volatility_class'] == 'Alta']),
                'very_high': len(summary_df[summary_df['volatility_class'] == 'Muito Alta'])
            },
            'top_performers': {
                'biggest_gainer': {
                    'currency': summary_df.loc[summary_df['total_change_pct'].idxmax(), 'currency'],
                    'change_pct': float(summary_df['total_change_pct'].max())
                },
                'biggest_loser': {
                    'currency': summary_df.loc[summary_df['total_change_pct'].idxmin(), 'currency'],
                    'change_pct': float(summary_df['total_change_pct'].min())
                },
                'most_volatile': {
                    'currency': summary_df.loc[summary_df['avg_volatility_7d'].idxmax(), 'currency'],
                    'volatility': float(summary_df['avg_volatility_7d'].max())
                },
                'most_stable': {
                    'currency': summary_df.loc[summary_df['avg_volatility_7d'].idxmin(), 'currency'],
                    'volatility': float(summary_df['avg_volatility_7d'].min())
                }
            },
            'major_currencies_summary': major_currencies[['currency', 'current_rate', 'last_daily_change', 
                                                        'total_change_pct', 'volatility_class', 'trend_class']].to_dict('records')
        }
        
        logger.info(
            "Overview do mercado criado",
            currencies_up=overview['market_sentiment']['currencies_up'],
            currencies_down=overview['market_sentiment']['currencies_down'],
            biggest_gainer=overview['top_performers']['biggest_gainer']['currency'],
            biggest_loser=overview['top_performers']['biggest_loser']['currency']
        )
        
        return overview
    
    def save_gold_layer(self, daily_metrics: pd.DataFrame, trends_df: pd.DataFrame, 
                       summary_df: pd.DataFrame, overview: Dict[str, Any],
                       target_date: date) -> Dict[str, str]:
        """
        Salva todos os dados do Gold Layer
        
        Args:
            daily_metrics: Métricas diárias
            trends_df: Dados com tendências
            summary_df: Resumo por moeda
            overview: Overview do mercado
            target_date: Data de referência
            
        Returns:
            Dicionário com caminhos dos arquivos salvos
        """
        logger.info("Salvando Gold Layer")
        
        date_str = target_date.strftime('%Y-%m-%d')
        files_created = {}
        
        # 1. Métricas diárias
        daily_file = self.gold_path / f"daily_metrics_{date_str}.parquet"
        daily_metrics.to_parquet(daily_file, compression='snappy', index=False)
        files_created['daily_metrics'] = str(daily_file)
        
        # 2. Tendências históricas
        trends_file = self.gold_path / f"historical_trends_{date_str}.parquet"
        trends_df.to_parquet(trends_file, compression='snappy', index=False)
        files_created['historical_trends'] = str(trends_file)
        
        # 3. Resumo por moeda
        summary_file = self.gold_path / f"currency_summary_{date_str}.parquet"
        summary_df.to_parquet(summary_file, compression='snappy', index=False)
        files_created['currency_summary'] = str(summary_file)
        
        # 4. Overview do mercado (JSON)
        overview_file = self.gold_path / f"market_overview_{date_str}.json"
        with open(overview_file, 'w', encoding='utf-8') as f:
            json.dump(overview, f, indent=2, ensure_ascii=False)
        files_created['market_overview'] = str(overview_file)
        
        # 5. Consolidado final (dados mais importantes)
        consolidated = summary_df[['currency', 'current_rate', 'last_daily_change', 
                                  'total_change_pct', 'ma_7d', 'volatility_7d', 
                                  'trend_class', 'volatility_class']].copy()
        
        consolidated_file = self.gold_path / f"consolidated_{date_str}.parquet"
        consolidated.to_parquet(consolidated_file, compression='snappy', index=False)
        files_created['consolidated'] = str(consolidated_file)
        
        # Calcular tamanhos dos arquivos
        total_size_kb = sum(Path(path).stat().st_size for path in files_created.values()) / 1024
        
        logger.info(
            "Gold Layer salvo com sucesso",
            files_created=len(files_created),
            total_size_kb=round(total_size_kb, 2),
            target_date=date_str
        )
        
        return files_created
    
    def process_gold_layer(self, target_date: date, days_back: int = 7) -> Dict[str, Any]:
        """
        Processo principal do Gold Layer
        
        Args:
            target_date: Data de referência
            days_back: Quantos dias históricos incluir (reduzido para 7)
            
        Returns:
            Relatório do processamento
        """
        start_time = datetime.now()
        
        logger.info(
            "=== INICIANDO PROCESSAMENTO GOLD LAYER ===",
            target_date=target_date.isoformat(),
            days_back=days_back,
            start_time=start_time.isoformat()
        )
        
        try:
            # 1. Tentar carregar apenas o dia atual primeiro
            try:
                silver_df = self.load_silver_data(target_date, target_date)
                logger.info("Usando apenas dados do dia atual")
                start_date = target_date
                actual_days = 1
            except ValueError:
                # Se não há dados do dia atual, tentar buscar dias anteriores
                logger.info("Tentando buscar dados históricos")
                start_date = target_date - timedelta(days=days_back-1)
                silver_df = self.load_silver_data(start_date, target_date)
                actual_days = (target_date - start_date).days + 1
            
            # 2. Calcular métricas diárias
            daily_metrics = self.calculate_daily_metrics(silver_df)
            
            # 3. Calcular tendências históricas (adaptado para poucos dados)
            trends_df = self.calculate_historical_trends_simple(daily_metrics)
            
            # 4. Criar resumo por moeda
            summary_df = self.create_currency_summary_simple(trends_df)
            
            # 5. Criar overview do mercado
            overview = self.create_market_overview_simple(summary_df, actual_days)
            
            # 6. Salvar Gold Layer
            files_created = self.save_gold_layer(daily_metrics, trends_df, summary_df, 
                                               overview, target_date)
            
            # Calcular tempo de execução
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Relatório final
            report = {
                'status': 'success',
                'target_date': target_date.isoformat(),
                'execution_time_seconds': execution_time,
                'processing': {
                    'period_analyzed': f"{start_date} to {target_date}",
                    'days_included': actual_days,
                    'silver_records_processed': len(silver_df),
                    'daily_metrics_calculated': len(daily_metrics),
                    'currencies_analyzed': len(summary_df)
                },
                'output': {
                    'files_created': files_created,
                    'total_files': len(files_created)
                },
                'insights': {
                    'market_overview': overview,
                    'top_currencies': summary_df.head(5)[['currency', 'current_rate', 
                                                        'trend_class']].to_dict('records')
                }
            }
            
            logger.info(
                "=== GOLD LAYER PROCESSADO COM SUCESSO ===",
                target_date=target_date.isoformat(),
                execution_time_seconds=execution_time,
                files_created=len(files_created),
                currencies_analyzed=len(summary_df)
            )
            
            return report
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(
                "=== PROCESSAMENTO GOLD LAYER FALHOU ===",
                target_date=target_date.isoformat(),
                execution_time_seconds=execution_time,
                error=str(e),
                error_type=type(e).__name__
            )
            
            return {
                'status': 'error',
                'target_date': target_date.isoformat(),
                'execution_time_seconds': execution_time,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def calculate_historical_trends_simple(self, daily_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Versão simplificada para poucos dados
        """
        logger.info("Calculando tendências (versão simplificada)")
        
        trends_df = daily_metrics.copy()
        trends_df = trends_df.sort_values(['currency', 'date']).reset_index(drop=True)
        
        # Adicionar colunas básicas com valores padrão seguros
        trends_df['daily_change'] = 0.0
        trends_df['cumulative_change'] = 0.0
        trends_df['ma_7d'] = trends_df['rate_mean']  # Média móvel = valor atual se só há 1 dia
        trends_df['volatility_7d'] = 0.0
        trends_df['max_30d'] = trends_df['rate_mean']
        trends_df['min_30d'] = trends_df['rate_mean']
        trends_df['relative_position'] = 50.0  # Posição neutra
        
        return trends_df
    
    def create_currency_summary_simple(self, trends_df: pd.DataFrame) -> pd.DataFrame:
        """
        Versão simplificada do resumo
        """
        logger.info("Criando resumo por moeda (versão simplificada)")
        
        # Usar dados mais recentes
        summary = trends_df.groupby('currency').last().reset_index()
        
        # Adicionar colunas necessárias
        summary['current_rate'] = summary['rate_mean']
        summary['last_daily_change'] = 0.0
        summary['total_change_pct'] = 0.0
        summary['historical_min'] = summary['rate_min']
        summary['historical_max'] = summary['rate_max']
        summary['historical_avg'] = summary['rate_mean']
        summary['avg_daily_volatility'] = summary['rate_std']
        summary['max_daily_drop'] = 0.0
        summary['max_daily_gain'] = 0.0
        summary['avg_volatility_7d'] = summary['rate_std']
        summary['first_date'] = summary['date']
        summary['last_date'] = summary['date']
        summary['total_observations'] = summary['observations']
        
        # Classificações baseadas em dados disponíveis
        summary['volatility_class'] = 'Baixa'  # Default para dados limitados
        summary['trend_class'] = 'Estável'     # Default para dados limitados
        
        # Ordenar por número de observações
        summary = summary.sort_values('total_observations', ascending=False).reset_index(drop=True)
        
        logger.info(f"Resumo criado para {len(summary)} moedas")
        
        return summary
    
    def create_market_overview_simple(self, summary_df: pd.DataFrame, days_analyzed: int) -> Dict[str, Any]:
        """
        Versão simplificada do overview
        """
        logger.info("Criando overview do mercado (versão simplificada)")
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'total_currencies': len(summary_df),
            'days_analyzed': days_analyzed,
            'observation_period': {
                'start': summary_df['first_date'].min().isoformat(),
                'end': summary_df['last_date'].max().isoformat(),
                'total_days': days_analyzed
            },
            'market_sentiment': {
                'currencies_analyzed': len(summary_df),
                'data_quality': 'Limited historical data - single day analysis'
            },
            'currency_distribution': {
                'total': len(summary_df),
                'with_valid_rates': len(summary_df[summary_df['current_rate'] > 0])
            },
            'rate_statistics': {
                'min_rate': float(summary_df['current_rate'].min()),
                'max_rate': float(summary_df['current_rate'].max()),
                'avg_rate': float(summary_df['current_rate'].mean())
            }
        }
        
        return overview


def main():
    """
    Função principal para executar Gold Layer
    """
    logger.info("=== INICIANDO PIPELINE GOLD LAYER ===")
    
    try:
        # Inicializar processor
        processor = GoldLayerProcessor()
        
        # Processar para hoje
        today = date.today()
        report = processor.process_gold_layer(today, days_back=30)
        
        if report['status'] == 'success':
            logger.info(
                "Pipeline Gold Layer concluído com sucesso",
                files_created=report['output']['total_files'],
                currencies_analyzed=report['processing']['currencies_analyzed']
            )
        else:
            logger.error(
                "Pipeline Gold Layer falhou",
                error=report['error']
            )
            
    except Exception as e:
        logger.error(
            "Erro crítico no pipeline Gold Layer",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


if __name__ == "__main__":
    main()