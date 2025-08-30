# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r examples/requirements.txt

# Set up PYTHONPATH
export PYTHONPATH=$PWD  # Linux/Mac
$Env:PYTHONPATH=$PWD    # Windows PowerShell
```

### Environment Variables
Create a `.env` file in `env_configs/` directory with the following format:

**For Azure OpenAI Client:**
```ini
OPENAI_API_TYPE = "azure"
AZURE_OPENAI_ENDPOINT = "https://xxx.openai.azure.com/"
OPENAI_API_VERSION = "2024-08-01-preview"
AZURE_OPENAI_API_KEY = "YOUR-API-KEY"
```

**For Azure Meta LLaMA Client:**
```ini
LLAMA_ENDPOINT = "YOUR-LLAMA-ENDPOINT"
LLAMA_API_KEY = "YOUR-API-KEY"
```

## Common Commands

### Running Pre-built Workflows
```bash
# Document chunking
python examples/chunking.py PATH-TO-YAML-CONFIG

# Semantic tagging and atomic question generation
python examples/tagging.py PATH-TO-YAML-CONFIG

# Complete QA testing pipeline
python examples/qa.py PATH-TO-YAML-CONFIG

# Evaluation workflow
python examples/evaluate.py PATH-TO-YAML-CONFIG
```

### Working with Specific Datasets
```bash
# MuSiQue dataset examples
python examples/qa.py examples/musique/configs/atomic_decompose.yml
python examples/qa.py examples/musique/configs/self_ask.yml

# HotpotQA dataset examples  
python examples/qa.py examples/hotpotqa/configs/ircot.yml
python examples/qa.py examples/hotpotqa/configs/iter_retgen.yml
```

## Code Architecture

PIKE-RAG is a modular RAG framework with the following key architectural components:

### Core Framework Structure
- **`pikerag/`** - Main package containing all framework components
- **`examples/`** - Pre-built workflow scripts and configuration examples
- **`data_process/`** - Utilities for benchmark dataset processing

### Key Architectural Components

**LLM Clients (`pikerag/llm_client/`)**
- `BaseLLMClient` - Abstract base class with caching and retry logic
- `AzureOpenAIClient` - Azure OpenAI integration
- `AzureMetaLlamaClient` - Azure Meta LLaMA integration  
- `StandardOpenAIClient` - Standard OpenAI API client

**Knowledge Retrievers (`pikerag/knowledge_retrievers/`)**
- `BaseQaRetriever` - Abstract base for retrieval components
- `ChromaQaRetriever` - ChromaDB vector store integration
- `BM25Retriever` - BM25 keyword-based retrieval
- `ChunkAtomRetriever` - Atomic chunk retrieval for multi-hop reasoning

**Document Processing (`pikerag/document_transformers/`)**
- **Splitters**: LLM-powered and sentence-based document chunking
- **Taggers**: Domain-specific semantic tagging and atomic question generation
- **Filters**: LLM-powered content filtering

**Prompt Management (`pikerag/prompts/`)**
- Structured prompt templates for different reasoning strategies
- **Decomposition**: Atomic question decomposition for multi-hop reasoning
- **Self-Ask**: Self-questioning reasoning chain prompts
- **IRCOT**: Interleaving retrieval with chain-of-thought reasoning

**Workflows (`pikerag/workflows/`)**
- `QaWorkflow` - Main QA testing pipeline with parallel execution support
- `ChunkingWorkflow` - Document chunking and processing workflow
- **Evaluation**: Comprehensive metrics (EM, F1, ROUGE, LLM-based evaluation)

### Configuration System

All workflows are driven by YAML configuration files with the following structure:

```yaml
# Logging and experiment tracking
experiment_name: your_experiment_name
log_root_dir: logs/your_domain/
test_rounds: 3

# LLM client configuration
llm_client:
  module_path: pikerag.llm_client
  class_name: AzureOpenAIClient  # or AzureMetaLlamaClient
  llm_config:
    model: gpt-4  # or meta-llama-3-70b-instruct-4
    temperature: 0

# Retriever configuration
retriever:
  module_path: pikerag.knowledge_retrievers
  class_name: QaChunkRetriever
  args:
    retrieve_k: 16
    retrieve_score_threshold: 0.2

# Protocol for LLM communication
qa_protocol:
  module_path: pikerag.prompts.qa
  attr_name: multiple_choice_qa_with_reference_protocol
```

### Dynamic Loading System

The framework uses extensive dynamic loading through `pikerag/utils/config_loader.py`:
- `load_class()` - Dynamically load classes with type checking
- `load_protocol()` - Load and configure communication protocols
- `load_embedding_func()` - Load embedding models with defaults

### Multi-Threading and Caching

- **Parallel Execution**: `QaWorkflow` supports multi-threaded question answering via `num_parallel` setting
- **LLM Response Caching**: All LLM clients use PickleDB for response caching with automatic cache key generation
- **Exponential Backoff**: Configurable retry logic with exponential backoff for API failures

### Reasoning Strategies

The framework implements several advanced RAG reasoning patterns:

- **Atomic Decomposition**: Break complex questions into atomic sub-questions
- **Self-Ask**: Self-questioning reasoning chains for step-by-step problem solving  
- **IRCOT**: Interleave retrieval steps with chain-of-thought reasoning
- **Iterative Retrieval-Generation**: Iteratively refine answers through multiple retrieval rounds

### Dataset Integration

Built-in support for multi-hop QA datasets:
- **MuSiQue, HotpotQA, 2WikiMultiHopQA**: Multi-hop reasoning benchmarks
- **Natural Questions, TriviaQA**: Single-hop factual QA
- Custom dataset loaders in `data_process/open_benchmarks/`