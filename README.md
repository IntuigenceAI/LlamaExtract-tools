# LlamaExtract Tools

This repository provides utilities for working with PDF documents using [LlamaExtract](https://docs.llamaindex.ai/llama-cloud/llama-extract/).  

The main workflow is:

1. Split large PDFs into smaller ones by chapters.  
2. Run the LlamaExtract scripts to extract structured information.  

---

## Setup

### 1. Clone this repository
### 2. Install dependencies
    pip install python-dotenv PyPDF2
### 3. Set up your API key
    Create a .env file in the root of the project with the following content:
    LLAMA_CLOUD_API_KEY=your_api_key_here

