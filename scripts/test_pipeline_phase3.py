"""
Script de Teste para Fase 3 - Transformação
Pipeline de Cotações Cambiais - MBA Data Engineering

Este script testa a funcionalidade completa da Fase 3:
1. Verifica se dados Raw existem
2. Executa transformação para Silver
3. Valida resultados
4. Gera relatório de qualidade
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime
import json

# Adicionar src ao path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir / "src"))

from src.transform.data_processor import DataTransformer
from src.utils.logging_config import setup_logging, get_logger

def check_prerequisites():
    """
    Verifica pré-requisitos para execução dos testes
    """
    logger = get_logger("test_prerequisites")
    
    logger.info("Verificando pré-requisitos...")
    
    # Verificar estrutura de diretórios
    base_path = Path("data")
    raw_path = base_path / "raw"
    silver_path = base_path / "silver"
    
    if not raw_path.exists():
        logger.error("Diretório data/raw não encontrado")
        return False
    
    # Verificar se há dados raw para hoje
    today = date.today()
    today_file = raw_path / f"{today.strftime('%Y-%m-%d')}.json"
    
    if not today_file.exists():
        logger.warning(f"Arquivo de dados para hoje não encontrado: {today_file}")
        # Tentar encontrar arquivo mais recente
        json_files = list(raw_path.glob("*.json"))
        if not json_files:
            logger.error("Nenhum arquivo de dados raw encontrado")
            return False
        else:
            latest_file = max(json_files, key=os.path.getctime)
            logger.info(f"Usando arquivo mais recente: {latest_file}")
    
    logger.info("Pré-requisitos verificados com sucesso")
    return True

def test_single_file_transformation(date_str: str = None):
    """
    Testa transformação de um único arquivo
    """
    logger = get_logger("test_transformation")
    
    if not date_str:
        date_str = date.today().strftime('%Y-%m-%d')
    
    logger.info(f"=== TESTANDO TRANSFORMAÇÃO PARA {date_str} ===")
    
    try:
        # Inicializar transformer
        transformer = DataTransformer()
        
        # Executar transformação
        report = transformer.process_date(date_str)
        
        if report['status'] == 'success':
            logger.info("✅ Transformação executada com sucesso!")
            
            # Exibir métricas
            logger.info("📊 Métricas de Processamento:")
            logger.info(f"  • Tempo de execução: {report['execution_time_seconds']:.2f}s")
            logger.info(f"  • Registros processados: {report['processing']['validated_records']}")
            logger.info(f"  • Taxa de sucesso: {report['processing']['validation_success_rate']:.2%}")
            logger.info(f"  • Score de qualidade: {report['quality']['overall_quality_score']:.2%}")
            logger.info(f"  • Arquivo gerado: {report['output']['silver_file']}")
            
            # Verificar arquivo gerado
            output_path = Path(report['output']['silver_file'])
            if output_path.exists():
                file_size = output_path.stat().st_size / 1024  # KB
                logger.info(f"  • Tamanho do arquivo: {file_size:.2f} KB")
            
            return True, report
            
        else:
            logger.error("❌ Transformação falhou!")
            logger.error(f"Erro: {report['error']}")
            return False, report
            
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {str(e)}")
        return False, {"error": str(e)}

def test_data_quality_checks():
    """
    Testa verificações específicas de qualidade
    """
    logger = get_logger("test_quality")
    
    logger.info("=== TESTANDO VERIFICAÇÕES DE QUALIDADE ===")
    
    try:
        from src.transform.data_processor import DataQualityChecker
        from src.utils.data_validator import CurrencyValidator, ExchangeRateValidator
        import pandas as pd
        
        # Teste do validador de moedas
        logger.info("🔍 Testando validador de moedas...")
        valid_currencies = ['USD', 'BRL', 'EUR', 'GBP', 'JPY']
        invalid_currencies = ['US', 'INVALID', '123', '']
        
        for currency in valid_currencies:
            assert CurrencyValidator.is_valid_currency_code(currency), f"{currency} deveria ser válido"
        
        for currency in invalid_currencies:
            assert not CurrencyValidator.is_valid_currency_code(currency), f"{currency} deveria ser inválido"
        
        logger.info("✅ Validador de moedas funcionando")
        
        # Teste do validador de taxas
        logger.info("🔍 Testando validador de taxas...")
        valid_rates = [0.1, 1.0, 5.5, 100.0]
        invalid_rates = [-1.0, 0.0, float('inf'), 2000000.0]
        
        for rate in valid_rates:
            assert ExchangeRateValidator.is_valid_rate(rate), f"{rate} deveria ser válido"
        
        for rate in invalid_rates:
            assert not ExchangeRateValidator.is_valid_rate(rate), f"{rate} deveria ser inválido"
        
        logger.info("✅ Validador de taxas funcionando")
        
        # Teste do checker de qualidade
        logger.info("🔍 Testando verificador de qualidade...")
        quality_checker = DataQualityChecker()
        
        # Criar DataFrame de teste
        test_df = pd.DataFrame({
            'base_currency': ['USD', 'USD', 'USD'],
            'target_currency': ['BRL', 'EUR', 'GBP'],
            'exchange_rate': [5.5, 0.85, 0.78]
        })
        
        report = quality_checker.generate_quality_report(test_df)
        
        assert 'overall_quality_score' in report
        assert 0 <= report['overall_quality_score'] <= 1
        
        logger.info("✅ Verificador de qualidade funcionando")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes de qualidade: {str(e)}")
        return False

def find_latest_raw_file():
    """
    Encontra o arquivo raw mais recente
    """
    raw_path = Path("data/raw")
    json_files = list(raw_path.glob("*.json"))
    
    if not json_files:
        return None
    
    latest_file = max(json_files, key=os.path.getctime)
    date_str = latest_file.stem  # Nome do arquivo sem extensão
    
    return date_str

def main():
    """
    Função principal de teste
    """
    # Configurar logging
    setup_logging(log_level="INFO", log_format="console")
    logger = get_logger("test_main")
    
    logger.info("🚀 INICIANDO TESTES DA FASE 3 - TRANSFORMAÇÃO")
    
    # 1. Verificar pré-requisitos
    if not check_prerequisites():
        logger.error("❌ Pré-requisitos não atendidos")
        return False
    
    # 2. Testar verificações de qualidade
    if not test_data_quality_checks():
        logger.error("❌ Testes de qualidade falharam")
        return False
    
    # 3. Encontrar arquivo para testar
    date_str = find_latest_raw_file()
    if not date_str:
        logger.error("❌ Nenhum arquivo raw encontrado para teste")
        return False
    
    logger.info(f"📁 Usando arquivo de dados: {date_str}")
    
    # 4. Testar transformação completa
    success, report = test_single_file_transformation(date_str)
    
    if success:
        logger.info("🎉 TODOS OS TESTES DA FASE 3 PASSARAM!")
        logger.info("✨ O módulo de transformação está funcionando corretamente")
        
        # Resumo final
        logger.info("\n📋 RESUMO DOS RESULTADOS:")
        logger.info(f"  • Data processada: {date_str}")
        logger.info(f"  • Registros validados: {report['processing']['validated_records']}")
        logger.info(f"  • Qualidade dos dados: {report['quality']['overall_quality_score']:.1%}")
        logger.info(f"  • Arquivo Parquet: {Path(report['output']['silver_file']).name}")
        
        return True
    else:
        logger.error("❌ TESTES DA FASE 3 FALHARAM!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)