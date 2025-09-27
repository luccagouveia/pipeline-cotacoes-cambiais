"""
Script Principal - Pipeline de Cotações Cambiais com Python + LLM
MBA em Data Engineering - Projeto Final

Este é o ponto de entrada principal do pipeline de dados.
Orquestra todas as etapas: ingestão, transformação, carga e geração de insights.

Uso:
    python main.py                    # Executa pipeline completo
    python main.py --stage ingest     # Executa apenas ingestão
    python main.py --date 2024-01-15  # Executa para data específica
    python main.py --help             # Mostra ajuda
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.logging_config import setup_logging, get_logger
from src.ingest.exchange_api import DataIngester


def parse_arguments():
    """
    Processa argumentos da linha de comando
    
    Returns:
        Namespace com argumentos processados
    """
    parser = argparse.ArgumentParser(
        description='Pipeline de Cotações Cambiais com Python + LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                           # Pipeline completo para hoje
  python main.py --stage ingest            # Apenas ingestão
  python main.py --date 2024-01-15         # Data específica
  python main.py --currency EUR            # Moeda base diferente
  python main.py --log-level DEBUG         # Mais detalhes nos logs
        """
    )
    
    parser.add_argument(
        '--stage',
        choices=['ingest', 'transform', 'load', 'llm', 'all'],
        default='all',
        help='Estágio específico para executar (default: all)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Data para processamento (formato: YYYY-MM-DD). Default: hoje'
    )
    
    parser.add_argument(
        '--currency',
        type=str,
        default='USD',
        help='Moeda base para cotações (default: USD)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nível de logging (default: INFO)'
    )
    
    parser.add_argument(
        '--log-format',
        choices=['console', 'json'],
        default='console',
        help='Formato dos logs (default: console)'
    )
    
    parser.add_argument(
        '--output-path',
        type=str,
        default='data',
        help='Caminho base para dados (default: data)'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """
    Valida argumentos fornecidos
    
    Args:
        args: Argumentos processados
        
    Raises:
        ValueError: Se argumentos forem inválidos
    """
    # Validar data se fornecida
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Data inválida: {args.date}. Use formato YYYY-MM-DD")
    
    # Validar moeda
    if len(args.currency) != 3 or not args.currency.isalpha():
        raise ValueError(f"Código de moeda inválido: {args.currency}. Use formato de 3 letras (ex: USD)")
    
    # Validar caminho de output
    if not args.output_path:
        raise ValueError("Caminho de output não pode estar vazio")


def setup_environment(args):
    """
    Configura ambiente de execução
    
    Args:
        args: Argumentos processados
    """
    # Configurar logging
    setup_logging(
        log_level=args.log_level,
        log_format=args.log_format,
        log_file_path='logs'
    )
    
    # Criar diretórios necessários
    base_path = Path(args.output_path)
    for subdir in ['raw', 'silver', 'gold']:
        (base_path / subdir).mkdir(parents=True, exist_ok=True)
    
    Path('logs').mkdir(exist_ok=True)
    Path('outputs/reports').mkdir(parents=True, exist_ok=True)


def run_ingest_stage(args, logger):
    """
    Executa etapa de ingestão
    
    Args:
        args: Argumentos processados
        logger: Logger configurado
        
    Returns:
        str: Caminho do arquivo gerado
    """
    logger.info("=== INICIANDO ETAPA DE INGESTÃO ===")
    
    try:
        # Determinar data alvo
        target_date = date.fromisoformat(args.date) if args.date else date.today()
        
        # Inicializar ingester
        raw_path = Path(args.output_path) / 'raw'
        ingester = DataIngester(raw_data_path=str(raw_path))
        
        # Coletar e salvar dados
        output_file = ingester.collect_and_save_daily_rates(
            base_currency=args.currency.upper(),
            target_date=target_date
        )
        
        logger.info(
            "Etapa de ingestão concluída com sucesso",
            output_file=output_file,
            target_date=target_date.isoformat(),
            base_currency=args.currency.upper()
        )
        
        return output_file
        
    except Exception as e:
        logger.error(
            "Falha na etapa de ingestão",
            error=str(e),
            error_type=type(e).__name__,
            target_date=args.date or "hoje",
            base_currency=args.currency
        )
        raise


def run_transform_stage(args, logger, input_file=None):
    """
    Executa etapa de transformação
    
    Args:
        args: Argumentos processados
        logger: Logger configurado
        input_file: Arquivo de entrada (opcional)
        
    Returns:
        str: Caminho do arquivo transformado
    """
    logger.info("=== INICIANDO ETAPA DE TRANSFORMAÇÃO ===")
    
    try:
        from src.transform.data_processor import DataTransformer
        
        # Determinar data alvo
        target_date = date.fromisoformat(args.date) if args.date else date.today()
        
        # Inicializar transformer
        raw_path = Path(args.output_path) / 'raw'
        silver_path = Path(args.output_path) / 'silver'
        
        transformer = DataTransformer(
            raw_data_path=str(raw_path),
            silver_data_path=str(silver_path)
        )
        
        # Processar transformação
        report = transformer.process_date(target_date)
        
        if report['status'] == 'success':
            logger.info(
                "Etapa de transformação concluída com sucesso",
                output_file=report['output']['silver_file'],
                target_date=target_date.isoformat(),
                final_records=report['output']['final_records'],
                quality_score=report['quality']['overall_quality_score'],
                execution_time=report['execution_time_seconds']
            )
            
            return report['output']['silver_file']
        else:
            logger.error(
                "Falha na etapa de transformação",
                error=report['error'],
                target_date=target_date.isoformat()
            )
            raise Exception(f"Transformação falhou: {report['error']}")
        
    except Exception as e:
        logger.error(
            "Erro na etapa de transformação",
            error=str(e),
            error_type=type(e).__name__,
            target_date=args.date or "hoje"
        )
        raise


def run_load_stage(args, logger, input_file=None):
    """
    Executa etapa de carga
    
    Args:
        args: Argumentos processados
        logger: Logger configurado
        input_file: Arquivo de entrada (opcional)
        
    Returns:
        str: Caminho do arquivo final
    """
    logger.info("=== ETAPA DE CARGA (PLACEHOLDER) ===")
    logger.info("Esta etapa será implementada na Fase 4")
    return None


def run_llm_stage(args, logger, input_file=None):
    """
    Executa etapa de insights com LLM
    
    Args:
        args: Argumentos processados
        logger: Logger configurado
        input_file: Arquivo de entrada (opcional)
        
    Returns:
        str: Caminho do relatório gerado
    """
    logger.info("=== ETAPA DE INSIGHTS LLM (PLACEHOLDER) ===")
    logger.info("Esta etapa será implementada na Fase 5")
    return None


def main():
    """
    Função principal do pipeline
    """
    try:
        # Processar argumentos
        args = parse_arguments()
        validate_arguments(args)
        
        # Configurar ambiente
        setup_environment(args)
        
        # Obter logger
        logger = get_logger("main")
        
        # Log de início
        logger.info(
            "=== INICIANDO PIPELINE DE COTAÇÕES CAMBIAIS ===",
            stage=args.stage,
            date=args.date or "hoje",
            currency=args.currency,
            log_level=args.log_level,
            timestamp=datetime.now().isoformat()
        )
        
        # Variáveis para rastrear arquivos entre estágios
        output_file = None
        
        # Executar estágios baseado na seleção
        if args.stage in ['ingest', 'all']:
            output_file = run_ingest_stage(args, logger)
        
        if args.stage in ['transform', 'all']:
            output_file = run_transform_stage(args, logger, output_file)
        
        if args.stage in ['load', 'all']:
            output_file = run_load_stage(args, logger, output_file)
        
        if args.stage in ['llm', 'all']:
            run_llm_stage(args, logger, output_file)
        
        # Log de conclusão
        logger.info(
            "=== PIPELINE CONCLUÍDO COM SUCESSO ===",
            stage=args.stage,
            execution_time=(datetime.now()).isoformat(),
            final_output=output_file
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrompido pelo usuário")
        return 130
        
    except Exception as e:
        # Logger pode não estar configurado ainda
        try:
            logger = get_logger("main")
            logger.error(
                "Pipeline falhou com erro crítico",
                error=str(e),
                error_type=type(e).__name__
            )
        except:
            print(f"❌ ERRO CRÍTICO: {e}")
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)