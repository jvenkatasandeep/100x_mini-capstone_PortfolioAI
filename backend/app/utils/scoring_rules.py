"""
Scoring rules for resume optimization and ATS scoring.
"""
from typing import Dict, List, Tuple
import re
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_keywords(text: str) -> Dict[str, int]:
    """Extract keywords and their frequencies from text.
    
    Args:
        text: Input text to extract keywords from
        
    Returns:
        Dictionary of keywords and their frequencies
    """
    # Simple word frequency counter (can be enhanced with NLP techniques)
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = defaultdict(int)
    for word in words:
        if len(word) > 2:  # Ignore very short words
            word_freq[word] += 1
    return dict(word_freq)

def calculate_ats_score(resume_text: str, job_description: str) -> Tuple[float, Dict]:
    """Calculate ATS score for a resume based on job description.
    
    Args:
        resume_text: Text content of the resume
        job_description: Job description text
        
    Returns:
        Tuple of (score, details) where details contains match information
    """
    try:
        # Extract keywords from resume and job description
        resume_keywords = extract_keywords(resume_text)
        job_keywords = extract_keywords(job_description)
        
        # Calculate match score (simple implementation)
        total_keywords = sum(job_keywords.values())
        if total_keywords == 0:
            return 0.0, {"matches": {}, "missing_keywords": [], "total_keywords": 0}
            
        matched_keywords = {}
        missing_keywords = []
        
        # Check for matches
        for keyword, count in job_keywords.items():
            if keyword in resume_keywords:
                matched_keywords[keyword] = {
                    'count': resume_keywords[keyword],
                    'expected': count
                }
            else:
                missing_keywords.append(keyword)
        
        # Calculate score (percentage of keywords matched)
        matched_count = sum(v['count'] for v in matched_keywords.values())
        score = min(100.0, (matched_count / total_keywords) * 100)
        
        return score, {
            'matches': matched_keywords,
            'missing_keywords': missing_keywords,
            'total_keywords': total_keywords
        }
        
    except Exception as e:
        logger.error(f"Error calculating ATS score: {str(e)}")
        return 0.0, {"error": str(e)}

def get_optimization_suggestions(resume_text: str, job_description: str) -> List[str]:
    """Generate optimization suggestions for a resume based on job description.
    
    Args:
        resume_text: Text content of the resume
        job_description: Job description text
        
    Returns:
        List of optimization suggestions
    """
    suggestions = []
    
    # Check for missing contact information
    contact_patterns = [
        r'\b(phone|mobile|tel|email|e-mail|linkedin|github)\b',
        r'\b@\w+(\.\w+)+\.\w+\b',  # Email pattern
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Phone number pattern
    ]
    
    has_contact = any(re.search(pattern, resume_text, re.IGNORECASE) 
                      for pattern in contact_patterns)
    if not has_contact:
        suggestions.append("Add contact information (phone, email, LinkedIn)")
    
    # Check for key sections
    sections = [
        (r'\b(experience|work\s*history|employment)\b', "Work Experience"),
        (r'\b(education|academic|degrees?)\b', "Education"),
        (r'\b(skills|technical\s*skills|programming\s*languages?)\b', "Skills"),
        (r'\b(projects|portfolio)\b', "Projects"),
    ]
    
    for pattern, section_name in sections:
        if not re.search(pattern, resume_text, re.IGNORECASE):
            suggestions.append(f"Consider adding a '{section_name}' section")
    
    # Check for action verbs (weak vs strong)
    weak_verbs = ['helped', 'tried', 'hoped', 'wanted', 'needed', 'worked on']
    strong_verbs = [
        'achieved', 'managed', 'created', 'designed', 'developed', 
        'implemented', 'improved', 'increased', 'led', 'optimized'
    ]
    
    found_weak = any(verb in resume_text.lower() for verb in weak_verbs)
    found_strong = any(verb in resume_text.lower() for verb in strong_verbs)
    
    if found_weak and not found_strong:
        suggestions.append("Use more action verbs to describe your experience")
    
    return suggestions

def score_resume(resume_text: str, job_description: str) -> Dict:
    """Score a resume against a job description.
    
    Args:
        resume_text: Text content of the resume
        job_description: Job description text
        
    Returns:
        Dictionary containing score and optimization suggestions
    """
    score, details = calculate_ats_score(resume_text, job_description)
    suggestions = get_optimization_suggestions(resume_text, job_description)
    
    return {
        'score': round(score, 1),
        'suggestions': suggestions,
        'details': details
    }
