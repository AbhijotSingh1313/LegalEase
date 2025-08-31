import os
import re
import torch
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

# Import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentProcessor:
    def __init__(self):
        """Initialize InLegalBERT and Google Gemini"""
        logger.info("Loading InLegalBERT model...")
        self.model_name = "law-ai/InLegalBERT"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            
            # Initialize Google Gemini client
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("Gemini API key not found. Q&A feature will not work.")
                self.gemini_model = None
            else:
                if GEMINI_AVAILABLE:
                    try:
                        genai.configure(api_key=api_key)
                        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                        logger.info("Google Gemini initialized successfully!")
                    except Exception as gemini_error:
                        logger.error(f"Failed to initialize Gemini: {gemini_error}")
                        self.gemini_model = None
                else:
                    logger.error("google-generativeai package not installed. Install with: pip install google-generativeai")
                    self.gemini_model = None
            
            logger.info("InLegalBERT model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def extract_legal_terms_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract actual legal terms from the contract text with their meanings"""
        
        legal_term_definitions = {
            "whereas": "since; considering that",
            "hereby": "by this document",
            "herein": "in this document",
            "hereinafter": "from now on in this document",
            "heretofore": "before this time",
            "thereafter": "after that time",
            "notwithstanding": "despite; in spite of",
            "pursuant to": "according to; in accordance with",
            "in consideration of": "in exchange for",
            "covenant": "legally binding promise",
            "indemnify": "protect from loss or damage",
            "liquidated damages": "predetermined compensation for breach",
            "force majeure": "unforeseeable circumstances beyond control",
            "breach": "violation of contract terms",
            "cure": "fix or remedy a problem",
            "default": "failure to meet obligations",
            "termination": "ending of the contract",
            "void": "having no legal effect",
            "voidable": "can be made void under certain conditions",
            "severability": "if one part is invalid, the rest remains valid",
            "waiver": "giving up a right voluntarily",
            "assignment": "transfer of rights to another party",
            "novation": "replacement of a contract with a new one",
            "rescission": "cancellation of a contract",
            "specific performance": "court order to fulfill contract exactly",
            "injunctive relief": "court order to do or stop doing something",
            "damages": "monetary compensation for loss",
            "consequential damages": "indirect losses resulting from breach",
            "incidental damages": "additional costs due to breach",
            "punitive damages": "punishment damages beyond actual loss",
            "mitigation": "reducing the amount of damages",
            "material breach": "serious violation affecting the contract's essence",
            "anticipatory breach": "indication that breach will occur in future",
            "substantial performance": "performance that meets essential requirements",
            "conditions precedent": "events that must occur before obligations arise",
            "conditions subsequent": "events that end existing obligations",
            "representations": "statements of fact made to induce contract formation",
            "warranties": "promises about the quality or condition of something",
            "indemnification": "compensation for harm or loss",
            "hold harmless": "agreement not to hold someone responsible",
            "liability": "legal responsibility for damages",
            "limitation of liability": "restriction on the amount of responsibility",
            "arbitration": "dispute resolution outside of court",
            "mediation": "assisted negotiation to resolve disputes",
            "jurisdiction": "authority of a court to hear a case",
            "governing law": "which state or country's laws apply",
            "venue": "location where legal proceedings take place",
            "statute of limitations": "time limit for bringing legal action",
            "confidentiality": "obligation to keep information secret",
            "non-disclosure": "agreement not to reveal information",
            "proprietary": "privately owned or exclusive",
            "intellectual property": "creations of the mind (patents, trademarks, etc.)",
            "trade secret": "confidential business information",
            "non-compete": "agreement not to compete with former employer",
            "non-solicitation": "agreement not to recruit employees or customers",
            "exclusivity": "sole rights to something",
            "royalty": "payment for use of property or rights",
            "escrow": "third party holds money/documents until conditions are met",
            "fiduciary": "relationship of trust and confidence",
            "due diligence": "reasonable investigation or care",
            "good faith": "honest intention and fair dealing",
            "best efforts": "maximum effort reasonably possible",
            "reasonable efforts": "efforts that a reasonable person would make",
            "time is of the essence": "deadlines are critically important"
        }
        
        found_terms = []
        text_lower = text.lower()
        
        for term, definition in legal_term_definitions.items():
            if term.lower() in text_lower:
                context = self._extract_context_around_phrase(text, term, 80)
                found_terms.append({
                    "term": term.title(),
                    "definition": definition,
                    "context": context
                })
        
        # Ensure we have at least some terms, add defaults if none found
        if not found_terms:
            default_terms = [
                {
                    "term": "Agreement",
                    "definition": "A mutual understanding between parties",
                    "context": "This agreement establishes terms and conditions"
                },
                {
                    "term": "Party",
                    "definition": "An individual or entity entering into a contract",
                    "context": "Each party has rights and obligations"
                },
                {
                    "term": "Terms",
                    "definition": "Conditions and provisions of a contract",
                    "context": "The terms of this contract are binding"
                }
            ]
            found_terms = default_terms
        
        return found_terms[:15]

    def _extract_context_around_phrase(self, text: str, phrase: str, context_length: int = 100) -> str:
        """Extract context around a specific phrase"""
        text_lower = text.lower()
        phrase_lower = phrase.lower()
        
        index = text_lower.find(phrase_lower)
        if index == -1:
            return f"The term '{phrase}' appears in the contract"
        
        start = max(0, index - context_length)
        end = min(len(text), index + len(phrase) + context_length)
        
        context = text[start:end].strip()
        return context[:200] + "..." if len(context) > 200 else context

    def _determine_contract_type(self, text: str) -> str:
        """Determine the type of contract"""
        text_lower = text.lower()
        
        contract_types = {
            "service agreement": ["service", "services", "provide", "perform", "consulting"],
            "employment contract": ["employment", "employee", "employer", "salary", "benefits", "job"],
            "lease agreement": ["lease", "rent", "tenant", "landlord", "property", "premises"],
            "purchase agreement": ["purchase", "buy", "sell", "goods", "product", "merchandise"],
            "license agreement": ["license", "licensing", "intellectual property", "software", "patent"],
            "partnership agreement": ["partnership", "partner", "joint venture", "collaborate"],
            "non-disclosure agreement": ["confidential", "non-disclosure", "nda", "proprietary"],
            "loan agreement": ["loan", "lend", "borrow", "credit", "debt", "principal"],
            "construction contract": ["construction", "build", "contractor", "materials", "project"],
            "supply agreement": ["supply", "supplier", "deliver", "goods", "materials"]
        }
        
        scores = {}
        for contract_type, keywords in contract_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[contract_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "general agreement"

    def _extract_main_subject(self, text: str, contract_type: str) -> str:
        """Extract the main subject matter of the contract"""
        
        subject_patterns = [
            r'(?:for the|regarding the|concerning the|related to the)\s+([^.]{10,50})',
            r'(?:provision of|supply of|delivery of|performance of)\s+([^.]{10,50})',
            r'this agreement covers\s+([^.]{10,50})',
            r'the purpose of this agreement is\s+([^.]{10,50})'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                return subject[:100] + "..." if len(subject) > 100 else subject
        
        # Fallback based on contract type
        type_subjects = {
            "service agreement": "professional services and consulting",
            "employment contract": "employment relationship and duties",
            "lease agreement": "property rental and occupancy",
            "purchase agreement": "goods purchase and delivery",
            "license agreement": "intellectual property licensing",
            "partnership agreement": "business partnership and collaboration",
            "non-disclosure agreement": "confidential information protection",
            "loan agreement": "financial lending and repayment",
            "construction contract": "construction project and specifications",
            "supply agreement": "goods supply and delivery"
        }
        
        return type_subjects.get(contract_type, "business relationship and obligations")

    def generate_executive_summary(self, text: str, sections: Dict, financial_terms: Dict, risk: Dict) -> str:
        """Generate a comprehensive executive summary"""
        
        contract_type = self._determine_contract_type(text)
        main_subject = self._extract_main_subject(text, contract_type)
        
        section_count = len([s for s in sections.values() if s])
        amount_count = len(financial_terms.get('amounts', []))
        
        summary_parts = [
            f"This is a {contract_type} focusing on {main_subject}."
        ]
        
        if amount_count > 0:
            amounts = financial_terms.get('amounts', [])
            summary_parts.append(f"The contract involves financial obligations including {', '.join(amounts[:3])}.")
        
        summary_parts.append(f"Risk analysis indicates a {risk['risk_level']} risk level with {len(risk['reasons'])} identified risk factors.")
        
        if section_count > 0:
            summary_parts.append(f"The contract is structured into {section_count} main sections covering various legal and business aspects.")
        
        timeline = self.extract_timeline(text)
        if timeline:
            summary_parts.append(f"Important dates include {len(timeline)} scheduled events or milestones.")
        
        return " ".join(summary_parts)

    def extract_precise_obligations(self, text: str) -> Dict[str, List[str]]:
        """Extract precise and detailed obligations from the contract"""
        
        obligations = {
            "all_obligations": [],
            "critical_obligations": [],
            "payment_obligations": [],
            "performance_obligations": []
        }
        
        obligation_keywords = [
            "shall", "must", "will", "agrees to", "undertakes to", "commits to",
            "responsible for", "liable for", "duty to", "obligation to",
            "required to", "bound to", "covenant to"
        ]
        
        critical_keywords = ['payment', 'deliver', 'complete', 'maintain', 'comply', 'perform', 'provide']
        payment_keywords = ['pay', 'payment', 'remit', 'compensation', 'fee', 'amount', 'invoice']
        performance_keywords = ['deliver', 'perform', 'complete', 'execute', 'provide', 'supply']
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            sentence_lower = sentence.lower()
            
            is_obligation = any(
                keyword in sentence_lower 
                for keyword in obligation_keywords
            )
            
            if is_obligation:
                clean_obligation = sentence[:300] + "..." if len(sentence) > 300 else sentence
                obligations["all_obligations"].append(clean_obligation)
                
                if any(keyword in sentence_lower for keyword in critical_keywords):
                    obligations["critical_obligations"].append(clean_obligation)
                
                if any(keyword in sentence_lower for keyword in payment_keywords):
                    obligations["payment_obligations"].append(clean_obligation)
                
                if any(keyword in sentence_lower for keyword in performance_keywords):
                    obligations["performance_obligations"].append(clean_obligation)
        
        # Ensure we have at least some obligations
        for key in obligations:
            if not obligations[key]:
                obligations[key] = ["No specific obligations identified in this category"]
            else:
                obligations[key] = list(dict.fromkeys(obligations[key]))[:10]
        
        return obligations

    def assess_contract_risks(self, text: str) -> Dict[str, Any]:
        """Enhanced risk assessment based on actual contract content"""
        
        risk_indicators = {
            "high": {
                "unlimited liability": 3,
                "personal guarantee": 3,
                "liquidated damages": 3,
                "specific performance": 3,
                "criminal liability": 4,
                "punitive damages": 3,
                "indemnify": 2,
                "hold harmless": 2,
                "strict liability": 3,
                "immediate termination": 2,
                "no cure period": 3,
                "forfeiture": 3
            },
            "medium": {
                "limitation of liability": -1,
                "material breach": 2,
                "cure period": -1,
                "force majeure": -1,
                "reasonable efforts": 1,
                "best efforts": 2,
                "consequential damages": 2,
                "indirect damages": 2,
                "arbitration": -1,
                "mediation": -1
            },
            "low": {
                "mutual": -1,
                "standard terms": -1,
                "industry standard": -1,
                "reasonable": -1,
                "good faith": -1,
                "fair dealing": -1,
                "customary": -1,
                "typical": -1
            }
        }
        
        text_lower = text.lower()
        risk_score = 0
        risk_reasons = []
        detailed_analysis = []
        
        for risk_level, indicators in risk_indicators.items():
            for indicator, points in indicators.items():
                if indicator in text_lower:
                    risk_score += points
                    context = self._extract_context_around_phrase(text, indicator, 100)
                    
                    risk_type = "increases" if points > 0 else "reduces"
                    risk_reasons.append(f"Found '{indicator}' which {risk_type} risk")
                    
                    detailed_analysis.append({
                        "factor": indicator,
                        "impact": f"{risk_type} risk by {abs(points)} points",
                        "context": context[:150] + "..." if len(context) > 150 else context
                    })
        
        # Additional risk factors
        if "without limitation" in text_lower:
            risk_score += 2
            risk_reasons.append("Broad liability clause without limitations")
            detailed_analysis.append({
                "factor": "without limitation",
                "impact": "increases risk by 2 points",
                "context": "Broad liability exposure identified"
            })
        
        if "at will" in text_lower:
            risk_score += 1
            risk_reasons.append("At-will provisions increase uncertainty")
        
        if len(re.findall(r'\b(?:penalty|penalties)\b', text_lower)) > 2:
            risk_score += 2
            risk_reasons.append("Multiple penalty clauses identified")
        
        # Determine overall risk level
        if risk_score >= 8:
            overall_risk = "HIGH"
        elif risk_score >= 4:
            overall_risk = "MEDIUM"
        elif risk_score >= 0:
            overall_risk = "LOW"
        else:
            overall_risk = "VERY LOW"
        
        # Ensure we have at least some analysis
        if not risk_reasons:
            risk_reasons = ["Standard contract terms with typical risk level"]
        
        if not detailed_analysis:
            detailed_analysis = [{
                "factor": "general terms",
                "impact": "standard risk level",
                "context": "No specific high-risk factors identified"
            }]
        
        return {
            "risk_level": overall_risk,
            "risk_score": max(0, risk_score),
            "reasons": risk_reasons[:10],
            "detailed_analysis": detailed_analysis[:8]
        }

    def identify_contract_sections(self, text: str) -> Dict[str, List[str]]:
        """Enhanced section identification"""
        keywords = {
            "payment_terms": [
                "payment", "fee", "cost", "amount", "invoice", "billing", 
                "due", "remuneration", "compensation", "salary", "wage", 
                "price", "consideration", "installment", "deposit"
            ],
            "termination_clauses": [
                "termination", "terminate", "expire", "expiration", "end", 
                "conclude", "dissolution", "cancellation", "breach", "default",
                "notice period", "wind up"
            ],
            "liability_limitations": [
                "liability", "damages", "limitation", "limit", "responsible", 
                "accountable", "indemnify", "indemnification", "harm", 
                "loss", "consequential", "indirect"
            ],
            "warranty_disclaimers": [
                "warranty", "guarantee", "assurance", "as is", "disclaim", 
                "merchantability", "fitness", "defect", "condition",
                "representation"
            ],
            "confidentiality": [
                "confidential", "non-disclosure", "nda", "proprietary", 
                "trade secret", "classified", "private", "sensitive"
            ],
            "intellectual_property": [
                "intellectual property", "copyright", "patent", "trademark", 
                "trade secret", "proprietary", "ownership", "license",
                "derivative works"
            ],
            "dispute_resolution": [
                "dispute", "arbitration", "mediation", "jurisdiction", 
                "governing law", "venue", "litigation", "court"
            ],
            "general_terms": []
        }
        
        sections = {k: [] for k in keywords}
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip() and len(p.strip()) > 50]
        
        if not paragraphs:
            # Fallback: split by sentences if no clear paragraphs
            paragraphs = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 100]
        
        for paragraph in paragraphs:
            para_lower = paragraph.lower()
            classified = False
            best_match = ("general_terms", 0)
            
            for section_type, section_keywords in keywords.items():
                if section_type == "general_terms":
                    continue
                    
                keyword_matches = sum(1 for kw in section_keywords if kw in para_lower)
                if keyword_matches > best_match[1]:
                    best_match = (section_type, keyword_matches)
            
            if best_match[1] > 0:
                sections[best_match[0]].append(paragraph)
                classified = True
            
            if not classified:
                sections["general_terms"].append(paragraph)
        
        return sections

    def extract_key_entities(self, text: str) -> Dict[str, List[str]]:
        """Enhanced entity extraction"""
        patterns = {
            "amounts": r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|\$)',
            "dates": r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+\w+\s+\d{4})',
            "percentages": r'\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s*percent',
            "timeframes": r'\b\d+\s*(?:days?|weeks?|months?|years?|hours?)\b',
            "addresses": r'\b\d+\s+[A-Z][a-zA-Z\s]+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Lane|Ln\.?)',
            "phone_numbers": r'\b(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b',
            "email_addresses": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        entities = {}
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities[entity_type] = list(set(matches))[:10]
        
        return entities

    def extract_financial_terms(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive financial information"""
        financial_info = {
            "amounts": [],
            "payment_schedule": [],
            "penalties": [],
            "interest_rates": [],
            "currencies": [],
            "payment_methods": []
        }
        
        # Enhanced amount extraction
        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?',
            r'\b\d+(?:,\d{3})*\s*USD'
        ]
        
        for pattern in amount_patterns:
            amounts = re.findall(pattern, text, re.IGNORECASE)
            financial_info["amounts"].extend(amounts)
        
        # Payment schedule extraction
        payment_patterns = [
            r'(?:within|due\s+in|payable\s+in|paid\s+within)\s+(\d+)\s*(?:days?|weeks?|months?)',
            r'net\s+(\d+)',
            r'(\d+)\s*(?:days?|weeks?|months?)\s*(?:after|from|following)',
            r'(?:monthly|quarterly|annually|weekly)\s+payments?'
        ]
        
        for pattern in payment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                financial_info["payment_schedule"].append(str(match))
        
        # Interest rate extraction
        interest_patterns = [
            r'(\d+(?:\.\d+)?)\s*%\s*(?:interest|rate|annual|per\s+annum)',
            r'interest.*?(\d+(?:\.\d+)?)\s*(?:percent|%)'
        ]
        
        for pattern in interest_patterns:
            rates = re.findall(pattern, text, re.IGNORECASE)
            financial_info["interest_rates"].extend([f"{rate}%" for rate in rates])
        
        # Payment methods
        payment_method_patterns = [
            r'\b(?:wire transfer|check|cash|credit card|bank transfer|ACH|electronic transfer)\b'
        ]
        
        for pattern in payment_method_patterns:
            methods = re.findall(pattern, text, re.IGNORECASE)
            financial_info["payment_methods"].extend(methods)
        
        # Remove duplicates and limit
        for key in financial_info:
            financial_info[key] = list(dict.fromkeys(financial_info[key]))[:10]
        
        return financial_info

    def extract_timeline(self, text: str) -> List[Dict[str, str]]:
        """Extract timeline information"""
        timeline = []
        
        date_patterns = [
            (r'(?:effective|commence|start|begin|execution).*?(\w+\s+\d{1,2},?\s+\d{4})', "Contract Start"),
            (r'(?:expire|end|terminate|conclusion|completion).*?(\w+\s+\d{1,2},?\s+\d{4})', "Contract End"),
            (r'(?:due|payable|payment).*?(\w+\s+\d{1,2},?\s+\d{4})', "Payment Due"),
            (r'(?:delivery|deliver|provided).*?(\w+\s+\d{1,2},?\s+\d{4})', "Delivery Date"),
            (r'(?:review|evaluation|assessment).*?(\w+\s+\d{1,2},?\s+\d{4})', "Review Date")
        ]
        
        for pattern, event_type in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                timeline.append({
                    "date": match,
                    "event": event_type,
                    "type": "milestone"
                })
        
        return timeline[:12]

    def simplify_legal_language(self, text: str) -> str:
        """Enhanced legal language simplification"""
        simplifications = {
            "hereinafter": "from now on",
            "heretofore": "before this",
            "whereas": "since",
            "hereby": "by this document",
            "thereof": "of that",
            "wherein": "in which",
            "notwithstanding": "despite",
            "pursuant to": "according to",
            "in consideration of": "in exchange for",
            "force majeure": "unforeseeable circumstances",
            "liquidated damages": "pre-agreed compensation",
            "indemnify": "protect from loss",
            "hold harmless": "not hold responsible",
            "covenant": "promise",
            "assign": "transfer",
            "breach": "break the agreement",
            "cure": "fix the problem",
            "default": "fail to meet obligations",
            "remedy": "solution",
            "waiver": "giving up a right",
            "perpetuity": "forever",
            "forthwith": "immediately",
            "inter alia": "among other things",
            "shall": "must",
            "shall not": "must not"
        }
        
        result = text
        for legal_term, simple_term in simplifications.items():
            pattern = re.compile(re.escape(legal_term), re.IGNORECASE)
            result = pattern.sub(simple_term, result)
        
        return result
    async def ask_openai_question(self, question: str, context: str) -> Dict[str, Any]:
        """Q&A using Google Gemini with concise responses"""
        if not self.gemini_model:
            return self.ask_keyword_question(question, context)

        try:
            prompt = f"""You are a legal analyst. Provide a **concise** answer (max 3 sentences) to the user’s question based solely on the contract excerpt below.

CONTRACT CONTEXT:
{context[:2000]}  # shorter context for brevity

USER QUESTION: {question}

Answer concisely:"""

            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200,   # reduced token limit
                    candidate_count=1
                )
            )

            answer = response.text.strip()

            return {
                "answer": answer,
                "relevant_clauses": self._extract_relevant_clauses(context, question),
                "confidence": 0.9,
                "follow_up_suggestions": self._generate_follow_up_questions(question, context)
            }

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self.ask_keyword_question(question, context)
        
    def ask_keyword_question(self, question: str, context: str) -> Dict[str, Any]:
        """Fallback keyword-based Q&A when Gemini is not available"""
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["payment", "pay", "cost", "fee", "money", "amount"]):
            # Find payment-related sections
            payment_info = []
            for section in context.split('\n'):
                if any(word in section.lower() for word in ["payment", "pay", "fee", "cost", "$", "amount"]):
                    payment_info.append(section.strip())
            
            if payment_info:
                answer = "Based on the contract, here are the payment-related terms:\n\n" + "\n\n".join(payment_info[:3])
            else:
                answer = "No specific payment terms found in this contract."
        
        elif any(word in question_lower for word in ["terminate", "end", "cancel", "termination"]):
            termination_info = []
            for section in context.split('\n'):
                if any(word in section.lower() for word in ["terminate", "termination", "end", "cancel", "expire"]):
                    termination_info.append(section.strip())
            
            if termination_info:
                answer = "Regarding termination, the contract states:\n\n" + "\n\n".join(termination_info[:3])
            else:
                answer = "No specific termination clauses found in this contract."
        
        elif any(word in question_lower for word in ["risk", "liability", "damage", "harm"]):
            risk_info = []
            for section in context.split('\n'):
                if any(word in section.lower() for word in ["liability", "damage", "risk", "harm", "loss", "indemnify"]):
                    risk_info.append(section.strip())
            
            if risk_info:
                answer = "Regarding risks and liability:\n\n" + "\n\n".join(risk_info[:3])
            else:
                answer = "No specific liability or risk clauses found."
        
        elif any(word in question_lower for word in ["obligation", "duty", "must", "shall", "required"]):
            obligations_info = []
            for section in context.split('\n'):
                if any(word in section.lower() for word in ["shall", "must", "obligation", "duty", "required", "responsible"]):
                    obligations_info.append(section.strip())
            
            if obligations_info:
                answer = "The contract establishes these obligations:\n\n" + "\n\n".join(obligations_info[:3])
            else:
                answer = "No specific obligations found."
        
        else:
            # Generic response - find most relevant sentences
            question_words = set(question_lower.split())
            relevant_sentences = []
            
            for sentence in context.split('.'):
                if len(sentence.strip()) < 20:
                    continue
                sentence_words = set(sentence.lower().split())
                overlap = len(question_words.intersection(sentence_words))
                if overlap >= 2:
                    relevant_sentences.append((overlap, sentence.strip()))
            
            if relevant_sentences:
                # Sort by relevance and take top 3
                relevant_sentences.sort(reverse=True, key=lambda x: x[0])
                answer = "Based on your question, here are the most relevant parts of the contract:\n\n"
                answer += "\n\n".join([sent[1] for sent in relevant_sentences[:3]])
            else:
                answer = "I couldn't find specific information related to your question in this contract. Please try asking about payment terms, termination conditions, obligations, or liability provisions."
        
        return {
            "answer": answer,
            "relevant_clauses": self._extract_relevant_clauses(context, question),
            "confidence": 0.7,
            "follow_up_suggestions": [
                "What are the payment terms?",
                "How can this contract be terminated?",
                "What are the main obligations?",
                "What are the liability provisions?"
            ]
        }

    def _extract_relevant_clauses(self, context: str, question: str) -> List[str]:
        """Extract clauses relevant to the question"""
        question_words = set(question.lower().split())
        relevant_clauses = []
        
        sentences = re.split(r'[.!?]+', context)
        
        for sentence in sentences:
            if not sentence.strip() or len(sentence.strip()) < 30:
                continue
                
            sentence_words = set(sentence.lower().split())
            overlap = len(question_words.intersection(sentence_words))
            
            if overlap >= 2:
                clause = sentence.strip()
                if len(clause) > 50:
                    relevant_clauses.append(clause[:250] + "..." if len(clause) > 250 else clause)
        
        return relevant_clauses[:5]

    def _generate_follow_up_questions(self, original_question: str, context: str) -> List[str]:
        """Generate relevant follow-up questions"""
        base_questions = [
            "What are the key payment obligations?",
            "How can this contract be terminated?",
            "What happens if there's a breach of contract?",
            "Are there any liability limitations?",
            "What are the warranty provisions?",
            "How are disputes resolved?",
            "What are the renewal terms?",
            "What are the confidentiality requirements?",
            "What intellectual property rights are involved?",
            "What are the performance standards?"
        ]
        
        # Filter out questions too similar to the original
        original_words = set(original_question.lower().split())
        filtered_questions = []
        
        for q in base_questions:
            q_words = set(q.lower().split())
            if len(original_words.intersection(q_words)) < 3:
                filtered_questions.append(q)
        
        return filtered_questions[:6]

    def process_contract(self, text: str) -> Dict[str, Any]:
        """Main contract processing with comprehensive analysis"""
        try:
            logger.info(f"Processing contract of {len(text)} characters")
            
            # Extract all components
            sections = self.identify_contract_sections(text)
            entities = self.extract_key_entities(text)
            financial_terms = self.extract_financial_terms(text)
            timeline = self.extract_timeline(text)
            risk = self.assess_contract_risks(text)
            simplified_text = self.simplify_legal_language(text)
            key_terms = self.extract_legal_terms_from_text(text)
            obligations = self.extract_precise_obligations(text)
            
            # Generate contract type and subject (REQUIRED FIELDS)
            contract_type = self._determine_contract_type(text)
            main_subject = self._extract_main_subject(text, contract_type)
            
            # Generate executive summary
            executive_summary = self.generate_executive_summary(text, sections, financial_terms, risk)
            
            # Build response with ALL required fields
            response = {
                "processing_status": "success",
                "detailed_summary": {
                    "executive_summary": executive_summary,
                    "key_points": [
                        f"Contract type: {contract_type}",
                        f"Main subject: {main_subject}",
                        f"Risk level: {risk['risk_level']}",
                        f"Total obligations: {len(obligations['all_obligations'])}",
                        f"Financial terms: {len(financial_terms['amounts'])} amounts identified"
                    ],
                    "financial_terms": financial_terms,
                    "timeline": timeline,
                    "contract_type": contract_type,  # REQUIRED
                    "main_subject": main_subject     # REQUIRED
                },
                "key_terms": key_terms,  # Each item has term, definition, context
                "obligations": obligations,
                "risk_assessment": risk,
                "sections": sections,
                "entities": entities,
                "simplified_text": simplified_text
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in contract processing: {e}")
            return {
                "processing_status": "failed",
                "error": f"Contract processing failed: {str(e)}"
            }


# Singleton factory
processor: Optional[LegalDocumentProcessor] = None

def get_processor() -> LegalDocumentProcessor:
    """Get or create the legal processor instance"""
    global processor
    if processor is None:
        processor = LegalDocumentProcessor()
    return processor
