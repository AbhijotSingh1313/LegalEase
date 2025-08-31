from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import docx
import io
import logging
from typing import Optional

from models import (
    ContractAnalysisRequest,
    ContractAnalysisResponse,
    QuestionRequest,
    QuestionResponse,
)
from legal_processor import get_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Contract Simplifier API",
    description="AI-powered legal contract analysis using InLegalBERT with OpenAI integration",
    version="2.0.0"
)

# Enable CORS for all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(content: bytes) -> str:
    """Enhanced PDF text extraction"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {e}")

def extract_text_from_docx(content: bytes) -> str:
    """Enhanced DOCX text extraction"""
    try:
        doc = docx.Document(io.BytesIO(content))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {e}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Legal Contract Simplifier API v2.0",
        "status": "active",
        "features": [
            "Text Analysis with InLegalBERT",
            "File Upload (PDF/DOCX/TXT)",
            "Legal Term Extraction",
            "OpenAI Q&A Integration",
            "Risk Assessment",
            "Contract Simplification"
        ],
        "endpoints": {
            "health": "GET /health",
            "analyze_text": "POST /analyze-text",
            "upload_file": "POST /upload-file",
            "ask_question": "POST /ask-question",
            "model_info": "GET /model-info"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        processor = get_processor()
        return {
            "status": "healthy",
            "model_loaded": True,
            "message": "All systems operational",
            "model_info": "InLegalBERT loaded successfully"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "error": str(e)
        }

@app.post("/analyze-text", response_model=ContractAnalysisResponse)
async def analyze_contract_text(request: ContractAnalysisRequest):
    """Analyze contract text using InLegalBERT"""
    if not request.contract_text.strip():
        raise HTTPException(status_code=400, detail="Contract text cannot be empty")
    
    if len(request.contract_text) < 100:
        raise HTTPException(status_code=400, detail="Contract text too short for meaningful analysis")
    
    try:
        processor = get_processor()
        result = processor.process_contract(request.contract_text)
        
        if result.get("processing_status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        logger.info(f"Successfully analyzed contract with {len(request.contract_text)} characters")
        return ContractAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_contract_text: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/upload-file", response_model=ContractAnalysisResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and analyze contract file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Validate file extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported types: PDF, DOCX, TXT"
        )
    
    try:
        # Extract text based on file type
        if ext == "pdf":
            text = extract_text_from_pdf(content)
        elif ext == "docx":
            text = extract_text_from_docx(content)
        else:  # txt
            text = content.decode("utf-8", errors="ignore")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file")
        
        if len(text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Extracted text too short for analysis")
        
        # Process the contract
        processor = get_processor()
        result = processor.process_contract(text)
        
        if result.get("processing_status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        logger.info(f"Successfully processed {ext.upper()} file: {file.filename}")
        return ContractAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.post("/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask questions about the contract using OpenAI"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not request.contract_context.strip():
        raise HTTPException(status_code=400, detail="Contract context is required")
    
    if len(request.question) > 500:
        raise HTTPException(status_code=400, detail="Question too long. Maximum 500 characters")
    
    try:
        processor = get_processor()
        answer_data = await processor.ask_openai_question(
            request.question,
            request.contract_context
        )
        
        logger.info(f"Successfully answered question: {request.question[:50]}...")
        return QuestionResponse(**answer_data)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")

@app.get("/model-info")
async def model_info():
    """Get information about the models and capabilities"""
    return {
        "primary_model": {
            "name": "InLegalBERT",
            "parameters": "110M",
            "training_data": "5.4M Indian legal documents (1950-2019)",
            "capabilities": [
                "Legal text understanding",
                "Contract section identification",
                "Entity extraction",
                "Risk assessment"
            ]
        },
        "qa_model": {
            "name": "OpenAI GPT-3.5-turbo",
            "capabilities": [
                "Question answering",
                "Legal interpretation",
                "Contextual analysis"
            ]
        },
        "features": [
            "Text & File Upload Analysis",
            "Legal Term Extraction from Contract",
            "Detailed Contract Summaries",
            "Risk & Obligation Assessment",
            "Interactive Q&A",
            "Legal Language Simplification"
        ],
        "supported_formats": ["PDF", "DOCX", "TXT"],
        "max_file_size": "10MB",
        "api_version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Legal Contract Simplifier API v2.0...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
