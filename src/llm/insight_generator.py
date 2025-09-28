"""
Insight Generator - Integração LLM para Análise de Cotações
Pipeline de Cotações Cambiais - MBA Data Engineering

Este módulo é responsável por:
1. Carregar dados do Gold Layer
2. Preparar contexto para LLM
3. Gerar insights executivos em português
4. Salvar relatórios estruturados
"""

import json
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog
from openai import OpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = structlog.get_logger()


class InsightGenerator:
    """
    Gerador de insights executivos usando LLM
    """
    
    def __init__(self, gold_path: str = 'data/gold', outputs_path: str = 'outputs/reports'):
        """
        Inicializa o gerador de insights
        
        Args:
            gold_path: Caminho dos dados Gold Layer
            outputs_path: Caminho para relatórios gerados
        """
        self.gold_path = Path(gold_path)
        self.outputs_path = Path(outputs_path)
        
        # Criar diretório de outputs se não existir
        self.outputs_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar cliente OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
            
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        logger.info(
            "InsightGenerator inicializado",
            gold_path=str(self.gold_path),
            outputs_path=str(self.outputs_path),
            model=self.model
        )
    
    def load_gold_data(self, target_date: date) -> Dict[str, Any]:
        """
        Carrega dados do Gold Layer para análise
        
        Args:
            target_date: Data de referência
            
        Returns:
            Dicionário com dados carregados
        """
        date_str = target_date.strftime('%Y-%m-%d')
        
        logger.info("Carregando dados Gold Layer para análise", date=date_str)
        
        data = {}
        
        try:
            # 1. Resumo por moeda
            summary_file = self.gold_path / f"currency_summary_{date_str}.parquet"
            if summary_file.exists():
                data['currency_summary'] = pd.read_parquet(summary_file)
                logger.debug(f"Carregado currency_summary: {len(data['currency_summary'])} moedas")
            
            # 2. Overview do mercado
            overview_file = self.gold_path / f"market_overview_{date_str}.json"
            if overview_file.exists():
                with open(overview_file, 'r', encoding='utf-8') as f:
                    data['market_overview'] = json.load(f)
                logger.debug("Carregado market_overview")
            
            # 3. Consolidado
            consolidated_file = self.gold_path / f"consolidated_{date_str}.parquet"
            if consolidated_file.exists():
                data['consolidated'] = pd.read_parquet(consolidated_file)
                logger.debug(f"Carregado consolidated: {len(data['consolidated'])} registros")
            
            if not data:
                raise FileNotFoundError(f"Nenhum arquivo Gold Layer encontrado para {date_str}")
                
            logger.info(
                "Dados Gold Layer carregados com sucesso",
                files_loaded=len(data),
                date=date_str
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados Gold Layer: {str(e)}")
            raise
    
    def prepare_market_context(self, data: Dict[str, Any]) -> str:
        """
        Prepara contexto estruturado para envio ao LLM
        
        Args:
            data: Dados carregados do Gold Layer
            
        Returns:
            Contexto formatado em texto
        """
        logger.info("Preparando contexto para análise LLM")
        
        context_parts = []
        
        # Informações gerais do mercado
        if 'market_overview' in data:
            overview = data['market_overview']
            context_parts.append("=== VISÃO GERAL DO MERCADO ===")
            context_parts.append(f"Data da análise: {overview.get('timestamp', 'N/A')}")
            context_parts.append(f"Total de moedas analisadas: {overview.get('total_currencies', 0)}")
            context_parts.append(f"Período analisado: {overview.get('days_analyzed', 1)} dia(s)")
            
            if 'rate_statistics' in overview:
                stats = overview['rate_statistics']
                context_parts.append(f"Taxa mínima: {stats.get('min_rate', 0):.6f}")
                context_parts.append(f"Taxa máxima: {stats.get('max_rate', 0):.4f}")
                context_parts.append(f"Taxa média: {stats.get('avg_rate', 0):.4f}")
            
            context_parts.append("")
        
        # Top 15 moedas mais importantes
        if 'currency_summary' in data:
            df = data['currency_summary'].head(15)
            context_parts.append("=== TOP 15 MOEDAS MAIS IMPORTANTES ===")
            
            for _, row in df.iterrows():
                currency = row['currency']
                rate = row['current_rate']
                trend = row.get('trend_class', 'N/A')
                volatility = row.get('volatility_class', 'N/A')
                obs = row.get('total_observations', 0)
                
                context_parts.append(
                    f"{currency}: Taxa={rate:.4f}, Tendência={trend}, "
                    f"Volatilidade={volatility}, Observações={obs}"
                )
            
            context_parts.append("")
        
        # Moedas de maior interesse para Brasil
        if 'currency_summary' in data:
            brazilian_interest = ['BRL', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY']
            df = data['currency_summary']
            
            context_parts.append("=== MOEDAS DE INTERESSE PARA O BRASIL ===")
            
            for currency in brazilian_interest:
                currency_data = df[df['currency'] == currency]
                if not currency_data.empty:
                    row = currency_data.iloc[0]
                    rate = row['current_rate']
                    trend = row.get('trend_class', 'Estável')
                    
                    if currency == 'BRL':
                        context_parts.append(f"Real Brasileiro (BRL): 1 USD = {rate:.4f} BRL - {trend}")
                    else:
                        context_parts.append(f"{currency}: {rate:.4f} - {trend}")
            
            context_parts.append("")
        
        # Distribuição de tendências
        if 'currency_summary' in data:
            df = data['currency_summary']
            if 'trend_class' in df.columns:
                trend_counts = df['trend_class'].value_counts()
                context_parts.append("=== DISTRIBUIÇÃO DE TENDÊNCIAS ===")
                
                for trend, count in trend_counts.items():
                    percentage = (count / len(df)) * 100
                    context_parts.append(f"{trend}: {count} moedas ({percentage:.1f}%)")
                
                context_parts.append("")
        
        # Distribuição de volatilidade
        if 'currency_summary' in data:
            df = data['currency_summary']
            if 'volatility_class' in df.columns:
                vol_counts = df['volatility_class'].value_counts()
                context_parts.append("=== DISTRIBUIÇÃO DE VOLATILIDADE ===")
                
                for vol, count in vol_counts.items():
                    percentage = (count / len(df)) * 100
                    context_parts.append(f"{vol}: {count} moedas ({percentage:.1f}%)")
        
        context = "\n".join(context_parts)
        
        logger.info(
            "Contexto preparado",
            context_length=len(context),
            sections=4 if 'currency_summary' in data else 1
        )
        
        return context
    
    def generate_executive_summary(self, context: str) -> str:
        """
        Gera resumo executivo usando LLM
        
        Args:
            context: Contexto estruturado dos dados
            
        Returns:
            Resumo executivo em português
        """
        logger.info("Gerando resumo executivo com LLM")
        
        system_prompt = """Você é um analista financeiro sênior especializado em mercados cambiais. 
        Sua função é analisar dados de cotações e criar resumos executivos claros e acionáveis para alta gerência.
        
        INSTRUÇÕES:
        1. Escreva em português brasileiro formal mas acessível
        2. Foque em insights práticos para tomada de decisão
        3. Use linguagem executiva (direta, objetiva, sem jargão técnico)
        4. Estruture com títulos claros
        5. Inclua recomendações quando apropriado
        6. Mantenha tom profissional mas não acadêmico
        
        O relatório deve ter aproximadamente 300-500 palavras."""
        
        user_prompt = f"""Com base nos dados de cotações cambiais abaixo, crie um resumo executivo para a alta direção.

        {context}
        
        Por favor, analise estes dados e forneça:
        1. Visão geral do cenário cambial atual
        2. Principais destaques e movimentações
        3. Moedas que merecem atenção especial
        4. Contexto para decisões de negócio
        5. Recomendações ou alertas importantes
        
        Lembre-se: este relatório será lido por executivos que precisam de insights claros e acionáveis."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            summary = response.choices[0].message.content
            
            # Log das interações (sem expor API key)
            logger.info(
                "Resumo executivo gerado",
                model=self.model,
                summary_length=len(summary),
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo executivo: {str(e)}")
            return self._generate_fallback_summary(context)
    
    def generate_technical_analysis(self, context: str) -> str:
        """
        Gera análise técnica detalhada
        
        Args:
            context: Contexto dos dados
            
        Returns:
            Análise técnica detalhada
        """
        logger.info("Gerando análise técnica detalhada")
        
        system_prompt = """Você é um analista quantitativo especializado em análise técnica de mercados cambiais.
        Crie uma análise técnica detalhada baseada nos dados fornecidos.
        
        FOQUE EM:
        1. Padrões identificados nos dados
        2. Níveis de suporte e resistência (quando aplicável)
        3. Sinais de volatilidade e estabilidade
        4. Correlações entre moedas principais
        5. Indicadores técnicos relevantes
        
        Use linguagem técnica apropriada mas explicativa."""
        
        user_prompt = f"""Analise tecnicamente os dados cambiais abaixo:

        {context}
        
        Forneça uma análise técnica detalhada incluindo:
        1. Análise de volatilidade atual
        2. Identificação de padrões ou anomalias
        3. Avaliação de estabilidade por moeda
        4. Recomendações técnicas para trading/hedging
        5. Métricas de risco relevantes"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            logger.info(
                "Análise técnica gerada",
                analysis_length=len(analysis)
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao gerar análise técnica: {str(e)}")
            return "Análise técnica não disponível devido a limitações de API."
    
    def _generate_fallback_summary(self, context: str) -> str:
        """
        Gera resumo alternativo sem LLM em caso de falha
        """
        logger.warning("Gerando resumo alternativo (sem LLM)")
        
        return f"""RESUMO EXECUTIVO - COTAÇÕES CAMBIAIS
        
        **VISÃO GERAL**
        Este relatório apresenta a análise das cotações cambiais processadas pelo sistema.
        
        **DADOS PROCESSADOS**
        {context[:500]}...
        
        **LIMITAÇÕES**
        Este é um resumo automático gerado devido a indisponibilidade temporária do serviço de análise avançada.
        Para insights detalhados, recomenda-se análise manual dos dados ou nova tentativa posterior.
        
        **PRÓXIMOS PASSOS**
        - Revisar dados detalhados nos arquivos Gold Layer
        - Consultar analista financeiro para interpretação especializada
        - Monitorar tendências nas próximas atualizações
        """
    
    def save_insights_report(self, summary: str, technical_analysis: str, 
                           context: str, target_date: date) -> Dict[str, str]:
        """
        Salva relatório completo de insights
        
        Args:
            summary: Resumo executivo
            technical_analysis: Análise técnica
            context: Contexto original
            target_date: Data de referência
            
        Returns:
            Dicionário com caminhos dos arquivos salvos
        """
        logger.info("Salvando relatório de insights")
        
        date_str = target_date.strftime('%Y-%m-%d')
        timestamp = datetime.now().isoformat()
        
        # Estrutura completa do relatório
        report = {
            'metadata': {
                'generated_at': timestamp,
                'target_date': date_str,
                'model_used': self.model,
                'pipeline_version': '1.0.0'
            },
            'executive_summary': summary,
            'technical_analysis': technical_analysis,
            'data_context': context,
            'recommendations': {
                'immediate_actions': [
                    "Revisar exposição cambial nas moedas de maior volatilidade",
                    "Monitorar tendências identificadas nas próximas atualizações",
                    "Considerar estratégias de hedge para moedas em alta volatilidade"
                ],
                'monitoring_points': [
                    "Acompanhar mudanças nas classificações de tendência",
                    "Observar variações significativas nas taxas principais",
                    "Avaliar impacto em operações internacionais"
                ]
            }
        }
        
        files_created = {}
        
        # 1. Relatório completo em JSON
        json_file = self.outputs_path / f"insights_report_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        files_created['json_report'] = str(json_file)
        
        # 2. Resumo executivo em markdown
        md_file = self.outputs_path / f"executive_summary_{date_str}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Resumo Executivo - Cotações Cambiais\n\n")
            f.write(f"**Data:** {target_date.strftime('%d/%m/%Y')}\n")
            f.write(f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(summary)
            f.write("\n\n---\n\n")
            f.write("## Análise Técnica\n\n")
            f.write(technical_analysis)
        files_created['markdown_summary'] = str(md_file)
        
        # 3. Relatório executivo simplificado em texto
        txt_file = self.outputs_path / f"daily_insights_{date_str}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DIÁRIO - COTAÇÕES CAMBIAIS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Data: {target_date.strftime('%d/%m/%Y')}\n")
            f.write(f"Gerado: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n")
            f.write(summary)
        files_created['text_summary'] = str(txt_file)
        
        # Calcular tamanhos
        total_size_kb = sum(Path(path).stat().st_size for path in files_created.values()) / 1024
        
        logger.info(
            "Relatório de insights salvo",
            files_created=len(files_created),
            total_size_kb=round(total_size_kb, 2),
            date=date_str
        )
        
        return files_created
    
    def process_insights(self, target_date: date) -> Dict[str, Any]:
        """
        Processo principal de geração de insights
        
        Args:
            target_date: Data para análise
            
        Returns:
            Relatório do processamento
        """
        start_time = datetime.now()
        
        logger.info(
            "=== INICIANDO GERAÇÃO DE INSIGHTS LLM ===",
            target_date=target_date.isoformat(),
            start_time=start_time.isoformat()
        )
        
        try:
            # 1. Carregar dados Gold Layer
            data = self.load_gold_data(target_date)
            
            # 2. Preparar contexto
            context = self.prepare_market_context(data)
            
            # 3. Gerar resumo executivo
            summary = self.generate_executive_summary(context)
            
            # 4. Gerar análise técnica
            technical_analysis = self.generate_technical_analysis(context)
            
            # 5. Salvar relatórios
            files_created = self.save_insights_report(summary, technical_analysis, 
                                                    context, target_date)
            
            # Calcular tempo de execução
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Relatório final
            report = {
                'status': 'success',
                'target_date': target_date.isoformat(),
                'execution_time_seconds': execution_time,
                'processing': {
                    'gold_files_loaded': len(data),
                    'context_length': len(context),
                    'summary_length': len(summary),
                    'analysis_length': len(technical_analysis)
                },
                'output': {
                    'files_created': files_created,
                    'total_files': len(files_created)
                },
                'insights_preview': {
                    'summary_preview': summary[:200] + "..." if len(summary) > 200 else summary,
                    'model_used': self.model
                }
            }
            
            logger.info(
                "=== INSIGHTS LLM GERADOS COM SUCESSO ===",
                target_date=target_date.isoformat(),
                execution_time_seconds=execution_time,
                files_created=len(files_created),
                model=self.model
            )
            
            return report
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(
                "=== GERAÇÃO DE INSIGHTS FALHOU ===",
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


def main():
    """
    Função principal para executar geração de insights
    """
    logger.info("=== INICIANDO PIPELINE DE INSIGHTS LLM ===")
    
    try:
        # Inicializar generator
        generator = InsightGenerator()
        
        # Processar para hoje
        today = date.today()
        report = generator.process_insights(today)
        
        if report['status'] == 'success':
            logger.info(
                "Pipeline de insights concluído com sucesso",
                files_created=report['output']['total_files'],
                model=report['insights_preview']['model_used']
            )
        else:
            logger.error(
                "Pipeline de insights falhou",
                error=report['error']
            )
            
    except Exception as e:
        logger.error(
            "Erro crítico no pipeline de insights",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


if __name__ == "__main__":
    main()