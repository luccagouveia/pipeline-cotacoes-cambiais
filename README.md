# 🚀 Pipeline de Cotações Cambiais com Python + LLM

**Projeto Final - MBA em Data Engineering**  
*Python Programming for Data Engineers*  
Professor: Eduardo Miranda

---

## 📋 Visão Geral do Projeto

Este projeto implementa um pipeline de dados completo para coleta, processamento e análise de cotações cambiais, integrando APIs externas com Large Language Models (LLM) para geração de insights em linguagem natural voltados a usuários de negócio.

### 🎯 Objetivos Principais

1. **Coletar** taxas de câmbio da API https://www.exchangerate-api.com/
2. **Processar e validar** os dados em camadas estruturadas (raw, silver, gold)
3. **Integrar com LLM** (ChatGPT) para gerar resumos e insights executivos
4. **Implementar** testes unitários, logging estruturado e observabilidade

---

## 🏗️ Arquitetura do Projeto

### Estrutura de Diretórios

```
pipeline-cotacoes-cambiais/
│
├── 📁 data/                    # Arquitetura Medallion
│   ├── 📁 raw/                 # Dados brutos da API (JSON)
│   ├── 📁 silver/              # Dados limpos e normalizados (Parquet)
│   └── 📁 gold/                # Dados agregados e métricas (Parquet/JSON)
│
├── 📁 src/                     # Código fonte principal
│   ├── 📁 ingest/              # Módulos de ingestão de dados
│   ├── 📁 transform/           # Módulos de transformação
│   ├── 📁 load/                # Módulos de carga Gold Layer
│   ├── 📁 llm/                 # Integração com LLM
│   └── 📁 utils/               # Utilitários e funções auxiliares
│
├── 📁 config/                  # Configurações do pipeline
├── 📁 tests/                   # Testes unitários e integração
│   ├── 📁 unit/                # Testes unitários
│   └── 📁 integration/         # Testes de integração
│
├── 📁 logs/                    # Arquivos de log estruturado
├── 📁 outputs/                 # Relatórios e insights da LLM
│   └── 📁 reports/             # Relatórios executivos
│
├── 📁 docs/                    # Documentação adicional
├── 📁 scripts/                 # Scripts auxiliares e automação
│
├── 📄 requirements.txt         # Dependências Python
├── 📄 .env.template           # Template de variáveis de ambiente
├── 📄 .env                    # Variáveis de ambiente (não versionado)
├── 📄 .gitignore              # Arquivos ignorados pelo Git
└── 📄 README.md               # Esta documentação
```

---

## ⚙️ Configuração do Ambiente

### Pré-requisitos

- Python 3.8+
- Conta na [Exchange Rate API](https://www.exchangerate-api.com/)
- Conta na [OpenAI](https://platform.openai.com/) para acesso ao ChatGPT
- Git para controle de versão

### 🔧 Instalação

#### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd pipeline-cotacoes-cambiais
```

#### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 3. Instale as dependências
```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências principais
pip install requests pandas python-dotenv pyyaml openai structlog pydantic pytest pytest-mock python-dateutil pyarrow
```

#### 4. Configure as variáveis de ambiente
```bash
# Copie o template
copy .env.template .env

# Edite o arquivo .env com suas chaves de API
```

### 🔐 Configuração das APIs

#### Exchange Rate API
1. Acesse https://www.exchangerate-api.com/
2. Crie uma conta gratuita
3. Copie sua API key
4. Adicione no arquivo `.env`:
```bash
EXCHANGE_API_KEY=sua_chave_aqui
```

#### OpenAI API
1. Acesse https://platform.openai.com/
2. Crie uma conta e configure billing
3. Gere uma API key
4. Adicione no arquivo `.env`:
```bash
OPENAI_API_KEY=sua_chave_openai_aqui
```

---

## 📚 Dependências do Projeto

### Bibliotecas Principais

| Biblioteca | Versão | Finalidade |
|------------|--------|------------|
| `requests` | >=2.31.0 | Requisições HTTP para APIs |
| `pandas` | >=2.0.0 | Manipulação e análise de dados |
| `pyarrow` | >=13.0.0 | Processamento de arquivos Parquet |
| `python-dotenv` | >=1.0.0 | Carregamento de variáveis de ambiente |
| `pyyaml` | >=6.0.0 | Processamento de arquivos YAML |
| `openai` | >=1.0.0 | Integração com ChatGPT |
| `structlog` | >=23.0.0 | Logging estruturado |
| `pydantic` | >=2.0.0 | Validação de dados |
| `pytest` | >=7.0.0 | Framework de testes |

---

## 🔄 Fluxo do Pipeline

### 1. **Ingestão (Ingest)** ✅ IMPLEMENTADO
- ✅ Coleta dados da Exchange Rate API
- ✅ Sistema de retry com 3 tentativas e delay configurável
- ✅ Validação robusta da resposta da API
- ✅ Salva resposta JSON bruta em `/data/raw/` com nomenclatura YYYY-MM-DD
- ✅ Logging estruturado com rastreamento completo
- ✅ Configuração via `.env`, sem hardcode de chaves/API
- ✅ Error handling para timeouts, conexão e erros HTTP
- ✅ Metadados do pipeline incluídos nos dados salvos

**Arquivos Gerados:**
- `data/raw/2025-09-28.json` (exemplo real)
- `logs/pipeline_20250928.log`

**Classes Principais:**
- `ExchangeRateAPIClient`: Cliente da API com retry logic
- `DataIngester`: Orquestrador da coleta e armazenamento

### 2. **Transformação (Transform)** ✅ IMPLEMENTADO
- ✅ Leitura de dados JSON da camada Raw
- ✅ Normalização para formato tabular estruturado
- ✅ Validação rigorosa com Pydantic (15+ regras)
- ✅ Verificação de qualidade com métricas e scores
- ✅ Detecção de outliers e anomalias
- ✅ Compatibilidade entre versões do Pydantic
- ✅ Armazenamento em Parquet otimizado (Silver layer)
- ✅ Sistema completo de logging e rastreamento

**Validações Implementadas:**
- Códigos de moeda ISO 4217 (168 moedas válidas)
- Taxas de câmbio entre 0.0001 e 1.000.000
- Timestamps no intervalo 2000-2030
- Consistência entre datas de coleta e atualização
- Detecção de duplicatas e valores nulos

**Arquivos Gerados:**
- `data/silver/exchange_rates_YYYY-MM-DD.parquet`
- Relatórios de qualidade com scores
- Logs estruturados de transformação

### 3. **Carga (Load)** ✅ IMPLEMENTADO
- ✅ Agregações diárias por moeda
- ✅ Cálculo de métricas históricas e tendências
- ✅ Médias móveis e indicadores de volatilidade
- ✅ Análise de performance e classificações
- ✅ Overview consolidado do mercado
- ✅ Múltiplos formatos de saída otimizados
- ✅ Adaptação inteligente para dados limitados

**Métricas Calculadas:**
- Médias, mínimos, máximos por período
- Volatilidade e coeficiente de variação
- Médias móveis (7 dias)
- Posição relativa (percentil)
- Classificações de tendência e volatilidade

**Arquivos Gerados:**
- `data/gold/daily_metrics_YYYY-MM-DD.parquet`
- `data/gold/historical_trends_YYYY-MM-DD.parquet`
- `data/gold/currency_summary_YYYY-MM-DD.parquet`
- `data/gold/market_overview_YYYY-MM-DD.json`
- `data/gold/consolidated_YYYY-MM-DD.parquet`

### 4. **Enriquecimento com LLM** 🔄 FASE 5
Integração planejada com ChatGPT para interpretar as cotações e gerar insights em linguagem natural.

### 5. **Testes e Observabilidade** ✅ IMPLEMENTADO PARCIALMENTE
- ✅ Testes unitários com pytest e mocking
- ✅ Logging estruturado durante todas as etapas com structlog
- ✅ Níveis de log configuráveis (INFO, DEBUG, ERROR)
- ✅ Logs salvos em arquivo com rotação diária
- 🔄 Logging do prompt/response do ChatGPT (Fase 5)

---

## 🚀 Como Executar

### Execução do Pipeline

#### Execução Completa
```bash
# Ativar ambiente virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Pipeline completo Raw → Silver → Gold
python main.py

# Pipeline com logs detalhados
python main.py --log-level DEBUG
```

#### Execução por Estágios
```bash
# Apenas ingestão de dados
python main.py --stage ingest

# Apenas transformação
python main.py --stage transform

# Apenas carga (Gold Layer)
python main.py --stage load

# Para uma data específica
python main.py --stage all --date 2024-01-15

# Com moeda base diferente
python main.py --stage ingest --currency EUR
```

#### Opções de Linha de Comando
```bash
# Ajuda completa
python main.py --help

# Opções disponíveis:
--stage {ingest,transform,load,llm,all}  # Estágio a executar
--date YYYY-MM-DD                       # Data específica
--currency XXX                          # Moeda base (padrão: USD)  
--log-level {DEBUG,INFO,WARNING,ERROR}  # Nível de log
--log-format {console,json}             # Formato dos logs
--output-path PATH                      # Caminho base dos dados
```

### Testes
```bash
# Executar todos os testes
pytest

# Executar com coverage
pytest --cov=src

# Testes específicos por módulo
pytest tests/unit/test_ingest.py -v
pytest tests/unit/test_transform.py -v

# Executar com logs detalhados
pytest tests/unit/ -v -s --log-cli-level=DEBUG
```

---

## 📊 Estrutura dos Dados

### Raw Layer (`/data/raw/`) ✅ IMPLEMENTADO
Estrutura atual dos arquivos salvos:
```json
{
  "pipeline_metadata": {
    "collection_timestamp": "2025-09-28T13:09:11.644833",
    "collection_date": "2025-09-28",
    "base_currency": "USD", 
    "pipeline_version": "1.0.0"
  },
  "api_response": {
    "result": "success",
    "base_code": "USD",
    "conversion_rates": {
      "BRL": 5.5432,
      "EUR": 0.9012,
      "GBP": 0.7634,
      "JPY": 143.21,
      // ... 163 moedas total
    }
  }
}
```

**Características:**
- ✅ **163 moedas** coletadas em tempo real
- ✅ Metadados do pipeline incluídos
- ✅ Timestamp de coleta preciso
- ✅ Resposta original preservada  
- ✅ Nomenclatura padronizada: `YYYY-MM-DD.json`

### Silver Layer (`/data/silver/`) ✅ IMPLEMENTADO
Estrutura após transformação e validação:
```
| base_currency | target_currency | exchange_rate | collection_timestamp    | collection_date | last_update_timestamp   | pipeline_version |
|---------------|-----------------|---------------|-------------------------|-----------------|-------------------------|------------------|
| USD           | BRL             | 5.5432        | 2025-09-28T13:09:11.644 | 2025-09-28      | 2025-09-28T00:00:01.000 | 1.0.0           |
| USD           | EUR             | 0.9012        | 2025-09-28T13:09:11.644 | 2025-09-28      | 2025-09-28T00:00:01.000 | 1.0.0           |
```

**Características do Silver Layer:**
- ✅ **163 registros** normalizados por execução
- ✅ Validação com Pydantic (15+ regras)  
- ✅ Formato Parquet com compressão Snappy
- ✅ Tipos de dados otimizados
- ✅ Score de qualidade calculado

### Gold Layer (`/data/gold/`) ✅ IMPLEMENTADO
Estrutura agregada e métricas calculadas:

#### Resumo por Moeda (`currency_summary_*.parquet`)
```
| currency | current_rate | trend_class | volatility_class | historical_min | historical_max | total_observations |
|----------|--------------|-------------|------------------|----------------|----------------|--------------------|
| BRL      | 5.5432       | Estável     | Baixa           | 5.5432         | 5.5432         | 1                 |
| EUR      | 0.9012       | Estável     | Baixa           | 0.9012         | 0.9012         | 1                 |
```

#### Overview do Mercado (`market_overview_*.json`)
```json
{
  "timestamp": "2025-09-28T13:09:11",
  "total_currencies": 163,
  "days_analyzed": 1,
  "rate_statistics": {
    "min_rate": 0.0001,
    "max_rate": 25000.0,
    "avg_rate": 157.45
  },
  "currency_distribution": {
    "total": 163,
    "with_valid_rates": 163
  }
}
```

**Arquivos Gold Layer:**
- ✅ Métricas diárias consolidadas
- ✅ Tendências históricas quando disponíveis
- ✅ Resumo executivo por moeda
- ✅ Overview completo do mercado em JSON
- ✅ Dataset consolidado otimizado

---

## 🤖 Integração com LLM

### Status: 🔄 FASE 5 - Planejada

### Prompts Configurados
```yaml
# Em config/pipeline_config.yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"  
  temperature: 0.3
  max_tokens: 500
  prompts:
    daily_summary: |
      Você é um analista financeiro experiente. Analise os dados de cotações 
      cambiais fornecidos e crie um resumo executivo conciso em português brasileiro.
      
      Inclua:
      1. Principais movimentações das moedas
      2. Destaques de valorização/desvalorização  
      3. Contexto para decisões de negócio
      4. Alertas importantes
      
      Mantenha linguagem clara e acessível para executivos.
```

### Implementação Futura
- ✅ Configuração OpenAI já preparada no `.env`
- ✅ Dados Gold Layer estruturados para análise LLM
- 🔄 Módulo `src/llm/insight_generator.py` 
- 🔄 Prompts personalizáveis via YAML
- 🔄 Geração de relatórios em `outputs/reports/`

---

## 🧪 Testes e Qualidade

### Cobertura de Testes ✅ IMPLEMENTADO
- ✅ Testes unitários completos para ingestão, transformação e carga
- ✅ Validação de taxas numéricas e estrutura da API
- ✅ Testes de integração com mocks para APIs externas
- ✅ Mocking para chamadas HTTP e sistema de arquivos
- ✅ Testes de cenários de erro (timeout, conexão, HTTP errors)
- ✅ Fixtures para dados de teste padronizados
- ✅ Testes de validação Pydantic e qualidade de dados

### Casos de Teste Implementados
```python
# Módulo de Ingestão
- test_get_latest_rates_success()               # Coleta bem-sucedida
- test_get_latest_rates_retry_on_timeout()      # Sistema de retry
- test_collect_and_save_daily_rates_success()   # Salvamento de dados

# Módulo de Transformação
- test_exchange_rate_record_validation()        # Validação Pydantic
- test_data_quality_checker()                   # Verificações de qualidade
- test_currency_validator()                     # Validação de códigos de moeda

# Módulo de Carga (Gold Layer)
- test_calculate_daily_metrics()                # Agregações diárias
- test_create_currency_summary()                # Resumo por moeda
- test_market_overview_creation()               # Overview do mercado
```

### Executar Testes
```bash
# Todos os testes
pytest

# Testes por módulo
pytest tests/unit/test_ingest.py -v
pytest tests/unit/test_transform.py -v

# Com coverage detalhado
pytest --cov=src --cov-report=html --cov-report=term
```

### Logging Estruturado ✅ IMPLEMENTADO
```python
# Exemplo de logs gerados em todo o pipeline:
{
  "event": "Gold Layer processado com sucesso", 
  "target_date": "2025-09-28",
  "currencies_analyzed": 163,
  "files_created": 5,
  "execution_time_seconds": 0.112,
  "timestamp": "2025-09-28T13:09:11.123456",
  "logger": "GoldLayerProcessor"
}
```

### Validação de Dados ✅ IMPLEMENTADO
```python
class ExchangeRateRecord(BaseModel):
    base_currency: str
    target_currency: str
    exchange_rate: float
    collection_timestamp: datetime
    
    @validator('exchange_rate')
    def rate_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Taxa de câmbio deve ser positiva')
        return v
```

---

## 📈 Roadmap de Desenvolvimento

### ✅ Fase 1 - Estruturação (Concluída)
- [x] Estrutura de diretórios
- [x] Ambiente virtual configurado
- [x] Dependências instaladas
- [x] Arquivos de configuração

### ✅ Fase 2 - Ingestão (Concluída)
- [x] Módulo de coleta da API (`ExchangeRateAPIClient`)
- [x] Sistema de retry e error handling
- [x] Validação de resposta da API
- [x] Armazenamento em JSON com nomenclatura padronizada
- [x] Sistema de logging estruturado
- [x] Testes unitários completos
- [x] Script principal com argumentos CLI
- [x] Integração com variáveis de ambiente

### ✅ Fase 3 - Transformação (Concluída)
- [x] Normalização de dados para formato tabular
- [x] Validações de qualidade com Pydantic
- [x] Verificação de qualidade com métricas
- [x] Processamento para Silver layer em Parquet
- [x] Sistema de detecção de outliers
- [x] Compatibilidade com diferentes versões do Pydantic
- [x] Testes unitários para transformação
- [x] Integração completa Raw → Silver

### ✅ Fase 4 - Carga (Concluída)
- [x] Agregações e métricas calculadas
- [x] Processamento adaptável para dados limitados
- [x] Gold layer com múltiplos formatos
- [x] Análises de mercado e classificações
- [x] Overview consolidado em JSON
- [x] Sistema robusto de error handling
- [x] Pipeline completo Raw → Silver → Gold

### 🔄 Fase 5 - LLM Integration (Próxima)
- [ ] Integração com OpenAI
- [ ] Geração de insights executivos
- [ ] Relatórios em linguagem natural
- [ ] Análises de tendências automáticas

### 🔄 Fase 6 - Observabilidade Final
- [ ] Dashboard interativo
- [ ] Monitoramento automatizado
- [ ] Alertas de qualidade
- [ ] Métricas de performance

---

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro de Instalação do PyArrow
```bash
# Solução alternativa
pip install fastparquet
```

#### Erro de API Key  
```bash
# Verifique se o arquivo .env está configurado
type .env | findstr EXCHANGE_API_KEY  # Windows
# cat .env | grep EXCHANGE_API_KEY    # Linux/Mac
```

#### Erro "daily_change KeyError" (Resolvido)
```bash
# Já corrigido na versão atual
# Gold Layer agora funciona com dados limitados
python main.py --stage load --log-level DEBUG
```

#### Pipeline Completo
```bash
# Para executar todas as fases
python main.py --stage all --log-level INFO
```

---

## 👥 Contribuição

### Padrões de Código
- Formatação: `black`
- Linting: `flake8`
- Documentação: docstrings em português
- Commits: conventional commits

### Estrutura de Branches
- `main`: código de produção
- `develop`: desenvolvimento ativo
- `feature/*`: novas funcionalidades

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `/logs/`
2. Execute os testes: `pytest`
3. Consulte a documentação da API
4. Verifique arquivos gerados em `/data/`

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos como parte do MBA em Data Engineering.

---

**Status do Projeto**: 🟢 **4 Fases Funcionando Perfeitamente!**  
**Última Atualização**: 28 Setembro 2025 - Pipeline Raw → Silver → Gold **COMPLETO E TESTADO**  
**Próxima Fase**: Integração LLM para Insights Executivos

---

## 📈 Progresso do Projeto

**Conclusão Total**: 80% ✅✅✅✅🔄🔄

- ✅ **Fase 1** - Estruturação (100%)
- ✅ **Fase 2** - Ingestão (100%) **TESTADO EM PRODUÇÃO** ⭐
- ✅ **Fase 3** - Transformação (100%) **SILVER LAYER FUNCIONAL** ⭐
- ✅ **Fase 4** - Carga (100%) **GOLD LAYER IMPLEMENTADO** ⭐
- 🔄 **Fase 5** - LLM Integration (0%)  
- 🔄 **Fase 6** - Observabilidade Final (0%)

### 🎯 **RESULTADOS REAIS DA EXECUÇÃO** (28/09/2025)

#### ✅ **Performance Comprovada:**
- ⚡ **Pipeline Completo**: Raw → Silver → Gold em < 2 segundos
- ⚡ **Ingestão**: 163 cotações coletadas em 0.56s
- ⚡ **Transformação**: Validação completa em < 1s
- ⚡ **Carga**: 5 arquivos Gold Layer gerados em 0.11s
- 📊 **Dados processados**: 163 moedas com validação rigorosa
- 💾 **Arquivos gerados**: 7 arquivos otimizados por execução
- 📝 **Logs estruturados**: 30+ eventos rastreados

#### ✅ **Funcionalidades Validadas:**
- 🔄 Pipeline completo Raw → Silver → Gold funcionando
- 🛡️ Sistema de validação rigoroso (Pydantic) 
- 📋 Verificação de qualidade com scores
- 💾 Armazenamento otimizado em Parquet
- 🔍 Agregações e métricas automáticas
- 📈 Análise de mercado e classificações
- ⚙️ Adaptação inteligente para dados limitados
- 🧪 Cobertura completa de testes unitários

#### ✅ **Arquivos de Saída por Execução:**
1. **Raw**: `data/raw/2025-09-28.json` (4.26KB)
2. **Silver**: `data/silver/exchange_rates_2025-09-28.parquet` (otimizado)
3. **Gold Daily**: `data/gold/daily_metrics_2025-09-28.parquet`
4. **Gold Trends**: `data/gold/historical_trends_2025-09-28.parquet`
5. **Gold Summary**: `data/gold/currency_summary_2025-09-28.parquet`
6. **Gold Overview**: `data/gold/market_overview_2025-09-28.json`
7. **Gold Consolidated**: `data/gold/consolidated_2025-09-28.parquet`

**Pipeline pronto para produção e apresentação acadêmica!**