from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ContractAnalysisRequest(BaseModel):
    """What data we expect when someone sends us a contract to analyze"""
    contract_text: str
    analysis_options: Optional[Dict[str, bool]] = {
        "extract_entities": True,
        "assess_risk": True,
        "simplify_language": True,
        "identify_sections": True
    }

class FileUploadRequest(BaseModel):
    """For file upload analysis"""
    analysis_options: Optional[Dict[str, bool]] = {
        "extract_entities": True,
        "assess_risk": True,
        "simplify_language": True,
        "identify_sections": True
    }

class QuestionRequest(BaseModel):
    """For asking follow-up questions"""
    question: str
    contract_context: str

class KeyTerm(BaseModel):
    """Structure for key terms and their definitions"""
    term: str
    definition: str
    context: str

class RiskAssessment(BaseModel):
    """Structure for risk assessment results"""
    risk_level: str
    risk_score: int
    reasons: List[str]
    detailed_analysis: List[Dict[str, str]]

class Obligations(BaseModel):
    """Structure for contract obligations"""
    all_obligations: List[str]
    critical_obligations: List[str]
    payment_obligations: List[str]
    performance_obligations: List[str]

class DetailedSummary(BaseModel):
    """Enhanced summary structure"""
    executive_summary: str
    key_points: List[str]
    financial_terms: Dict[str, Any]
    timeline: List[Dict[str, str]]
    contract_type: str
    main_subject: str

class ContractAnalysisResponse(BaseModel):
    """What data we send back after analyzing a contract"""
    detailed_summary: DetailedSummary
    key_terms: List[KeyTerm]
    obligations: Obligations
    risk_assessment: RiskAssessment
    sections: Dict[str, List[str]]
    entities: Dict[str, List[str]]
    simplified_text: str
    processing_status: str

class QuestionResponse(BaseModel):
    """Response for follow-up questions"""
    answer: str
    relevant_clauses: List[str]
    confidence: float
    follow_up_suggestions: List[str]

class ErrorResponse(BaseModel):
    """What we send back if something goes wrong"""
    error: str
    processing_status: str
