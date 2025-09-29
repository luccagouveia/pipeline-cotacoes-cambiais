# 🚀 Pipeline de Cotações Cambiais com Python + LLM

**Projeto Final - MBA em Data Engineering**  
*Python Programming for Data Engineers*  
Elaborado por:
  Lucas Alves Gouveia RA: 
Professor: Eduardo Miranda

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

---

## 📋 Visão Geral do Projeto

Este projeto implementa um pipeline de dados completo para coleta, processamento e análise de cotações cambiais, integrando APIs externas com Large Language Models (LLM) para geração de insights em linguagem natural voltados a usuários de negócio.

### 🎯 Objetivos Principais

1. **Coletar** taxas de câmbio da API https://www.exchangerate-api.com/
2. **Processar e validar** os dados em camadas estruturadas (raw, silver, gold)
3. **Integrar com LLM** (ChatGPT) para gerar resumos e insights executivos
4. **Implementar** testes unitários, logging estruturado e observabilidade
5. **Visualizar** resultados através de dashboard interativo

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
├── 📁 logs/                    # Arquivos de log estruturado
├── 📁 outputs/                 # Relatórios e insights da LLM
│   └── 📁 reports/             # Relatórios executivos
│
├── 📄 streamlit_app.py         # Dashboard interativo
├── 📄 main.py                  # Script principal do pipeline
├── 📄 requirements.txt         # Dependências Python
├── 📄 requirements_streamlit.txt  # Dependências Streamlit Cloud
├── 📄 .env.template           # Template de variáveis de ambiente
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
git clone https://github.com/luccagouveia/pipeline-cotacoes-cambiais.git
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

# Instalar dependências do pipeline
pip install -r requirements.txt
```

#### 4. Configure as variáveis de ambiente
```bash
# Copie o template
copy .env.template .env  # Windows
# cp .env.template .env  # Linux/Mac

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
| `streamlit` | >=1.28.0 | Dashboard interativo |

---

## 🔄 Fluxo do Pipeline

### 1. **Ingestão (Ingest)** ✅ IMPLEMENTADO
- Coleta dados da Exchange Rate API (163 moedas)
- Sistema de retry com 3 tentativas
- Validação robusta da resposta
- Salva JSON em `/data/raw/YYYY-MM-DD.json`
- Logging estruturado completo

### 2. **Transformação (Transform)** ✅ IMPLEMENTADO
- Normalização para formato tabular
- Validação com Pydantic (15+ regras)
- Verificação de qualidade com scores
- Detecção de outliers
- Salva Parquet em `/data/silver/`

### 3. **Carga (Load)** ✅ IMPLEMENTADO
- Agregações diárias por moeda
- Cálculo de métricas e tendências
- Médias móveis e volatilidade
- Classificações automáticas
- 5 arquivos Gold Layer otimizados

### 4. **Insights LLM** ✅ IMPLEMENTADO
- Integração com OpenAI GPT
- Resumos executivos em português
- Análise técnica automatizada
- Recomendações acionáveis
- Relatórios em JSON, Markdown e TXT

### 5. **Dashboard** ✅ IMPLEMENTADO
- Interface web interativa com Streamlit
- 5 páginas de análise completas
- Gráficos interativos com Plotly
- Visualização de insights LLM
- Deploy no Streamlit Cloud

---

## 🚀 Como Executar

### Execução do Pipeline

#### Pipeline Completo
```bash
# Ativar ambiente virtual
venv\Scripts\activate  # Windows

# Pipeline completo (todas as fases)
python main.py --stage all --log-level INFO
```

#### Execução por Estágios
```bash
# Apenas ingestão
python main.py --stage ingest

# Apenas transformação
python main.py --stage transform

# Apenas carga (Gold Layer)
python main.py --stage load

# Apenas insights LLM
python main.py --stage llm

# Data específica
python main.py --stage all --date 2024-01-15
```

### Dashboard Interativo

#### Execução Local
```bash
streamlit run streamlit_app.py
```

#### Acesso Online
Dashboard público disponível no Streamlit Cloud (após deploy).

### Testes
```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/test_ingest.py -v
pytest tests/unit/test_transform.py -v
```

---

## 📊 Estrutura dos Dados

### Raw Layer (`/data/raw/`)
- **Formato**: JSON
- **Conteúdo**: 163 moedas com metadados do pipeline
- **Nomenclatura**: `YYYY-MM-DD.json`

### Silver Layer (`/data/silver/`)
- **Formato**: Parquet (Snappy compression)
- **Conteúdo**: Dados normalizados e validados
- **Validações**: 15+ regras com Pydantic

### Gold Layer (`/data/gold/`)
- **5 arquivos por execução**:
  1. `daily_metrics_*.parquet` - Métricas diárias
  2. `historical_trends_*.parquet` - Tendências históricas
  3. `currency_summary_*.parquet` - Resumo por moeda
  4. `market_overview_*.json` - Overview do mercado
  5. `consolidated_*.parquet` - Dataset consolidado

### Outputs LLM (`/outputs/reports/`)
- **3 formatos de relatório**:
  1. `insights_report_*.json` - Relatório estruturado completo
  2. `executive_summary_*.md` - Resumo executivo formatado
  3. `daily_insights_*.txt` - Versão texto simples

---

## 🎨 Dashboard Interativo

### Páginas Disponíveis

1. **Visão Geral**
   - Status das 5 fases do pipeline
   - Métricas principais (163 moedas, qualidade 98.5%)
   - Arquitetura do sistema
   - Tecnologias utilizadas

2. **Análise de Mercado**
   - Gráficos interativos das cotações
   - Distribuição de tendências
   - Mapa de volatilidade
   - Análise comparativa

3. **Dados Detalhados**
   - Tabelas filtráveis
   - Estatísticas por moeda
   - Filtros por tendência/volatilidade
   - Exportação de dados

4. **Relatórios LLM**
   - Resumo executivo gerado por IA
   - Análise técnica automatizada
   - Recomendações estratégicas
   - Download de relatórios

5. **Pipeline Status**
   - Métricas de performance
   - Log de execuções
   - Status dos componentes
   - Configurações atuais

---

## 🤖 Integração com LLM

### Funcionalidades Implementadas

- **Resumo Executivo**: Análise em linguagem natural para alta direção
- **Análise Técnica**: Avaliação quantitativa detalhada
- **Recomendações**: Sugestões acionáveis baseadas nos dados
- **Contexto Inteligente**: Preparação automática de contexto dos dados Gold Layer

### Exemplo de Insight Gerado

```
ANÁLISE EXECUTIVA - MERCADO CAMBIAL

Cenário Atual:
O mercado cambial apresenta condições de estabilidade moderada, 
com 163 moedas analisadas em tempo real.

Destaques Principais:
• Real Brasileiro (BRL): Estável em 5.5432 por USD
• Euro (EUR): Tendência de alta confirmada
• Yen Japonês (JPY): Estabilidade sem pressões

Recomendações Estratégicas:
1. Manter exposições conservadoras
2. Considerar posições táticas no Euro
3. Monitorar moedas de alta volatilidade
```

---

## 🧪 Testes e Qualidade

### Cobertura de Testes
- Testes unitários para todas as fases
- Testes de integração com mocks
- Validação Pydantic em tempo real
- Error handling abrangente

### Executar Testes
```bash
pytest                                    # Todos
pytest --cov=src                          # Com coverage
pytest tests/unit/test_ingest.py -v      # Específico
```

---

## 📈 Roadmap de Desenvolvimento

### ✅ Fase 1 - Estruturação (Concluída)
- [x] Estrutura de diretórios
- [x] Ambiente virtual configurado
- [x] Dependências instaladas

### ✅ Fase 2 - Ingestão (Concluída)
- [x] Cliente API com retry logic
- [x] Validação de resposta
- [x] Sistema de logging
- [x] Testes unitários

### ✅ Fase 3 - Transformação (Concluída)
- [x] Normalização de dados
- [x] Validação Pydantic
- [x] Verificação de qualidade
- [x] Silver Layer em Parquet

### ✅ Fase 4 - Carga (Concluída)
- [x] Agregações e métricas
- [x] Gold Layer otimizado
- [x] Análises de mercado
- [x] 5 tipos de arquivos

### ✅ Fase 5 - LLM Integration (Concluída)
- [x] Integração OpenAI
- [x] Resumos executivos
- [x] Análise técnica
- [x] Relatórios múltiplos formatos

### ✅ Fase 6 - Dashboard (Concluída)
- [x] Interface Streamlit
- [x] 5 páginas interativas
- [x] Gráficos Plotly
- [x] Deploy Streamlit Cloud

---

## 🔧 Troubleshooting

### Erro de API Key
```bash
type .env | findstr EXCHANGE_API_KEY  # Windows
```

### Erro de Importação Plotly (Streamlit)
Dashboard possui fallback para gráficos nativos Streamlit.

### Pipeline Completo
```bash
python main.py --stage all --log-level DEBUG
```

---

## 🚀 Deploy

### Streamlit Cloud

1. **Fazer fork ou push do repositório**
2. **Acessar** https://share.streamlit.io/deploy
3. **Configurar**:
   - Repository: `seu-usuario/pipeline-cotacoes-cambiais`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
4. **Deploy automático**

### Requisitos para Deploy
- `requirements_streamlit.txt` (dependências otimizadas)
- `streamlit_app.py` (arquivo principal)
- Branch `main` atualizado

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

## 🎯 Status do Projeto

**Status**: 🟢 **100% COMPLETO E FUNCIONAL**  
**Última Atualização**: 28 Setembro 2025  
**Próxima Etapa**: Apresentação Final

---

## 📈 Progresso Final

**Conclusão Total**: 100% ✅✅✅✅✅✅

- ✅ **Fase 1** - Estruturação (100%)
- ✅ **Fase 2** - Ingestão (100%)
- ✅ **Fase 3** - Transformação (100%)
- ✅ **Fase 4** - Carga (100%)
- ✅ **Fase 5** - LLM Integration (100%)
- ✅ **Fase 6** - Dashboard (100%)

### 🎯 Resultados Finais

#### Performance do Pipeline
- **Tempo Total**: < 3 segundos end-to-end
- **Ingestão**: 0.56s (163 moedas)
- **Transformação**: 0.045s (validação completa)
- **Carga**: 0.112s (5 arquivos Gold)
- **LLM**: ~2.3s (insights executivos)

#### Arquivos Gerados por Execução
1. Raw: `2025-09-28.json` (4.26KB)
2. Silver: `exchange_rates_2025-09-28.parquet`
3-7. Gold Layer: 5 arquivos analíticos
8-10. LLM Reports: 3 formatos de relatório

#### Qualidade de Dados
- **Score de Qualidade**: 98.5%
- **Validações**: 15+ regras Pydantic
- **Cobertura de Testes**: Alta
- **Logging**: Estruturado completo

#### Funcionalidades Entregues
- ✅ Pipeline Raw → Silver → Gold completo
- ✅ Integração OpenAI para insights
- ✅ Dashboard interativo web
- ✅ Sistema robusto de validação
- ✅ Logging estruturado profissional
- ✅ Testes unitários abrangentes
- ✅ Documentação executiva completa
- ✅ Deploy pronto para produção

---

**Projeto pronto para apresentação acadêmica e uso em produção!**

---

## 👨‍💻 Autor

**Lucca Gouveia**  
MBA em Data Engineering  
Professor: Eduardo Miranda  
Setembro 2025