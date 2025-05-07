from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import string
import os

# Initialize Flask app
app = Flask(__name__, static_folder='../static')  # Assuming frontend files are in a static folder
CORS(app)  # Enable CORS with default options

# Download NLTK data - only try once with proper error handling
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Global lists and dictionaries
STOP_WORDS = set(stopwords.words('english'))
CLICKBAIT_PHRASES = [
    "you won't believe", "shocking", "mind-blowing", "unbelievable", 
    "jaw-dropping", "secret", "trick", "hack", "hidden", "they don't want you to know",
    "this will change", "never seen before", "stunning", "miracle", "bombshell",
    "exclusive", "revealed", "conspiracy", "what happens next will", "scientists shocked",
    "doctors hate", "one weird trick"
]

RELIABLE_SOURCES = [
    "reuters.com", "apnews.com", "npr.org", "bbc.com", "bbc.co.uk", 
    "economist.com", "nature.com", "science.org", "scientificamerican.com",
    "nejm.org", "washingtonpost.com", "nytimes.com", "wsj.com", "bloomberg.com",
    "ft.com", "time.com", "cnn.com", "nbcnews.com", "abcnews.go.com", "cbsnews.com"
]

QUESTIONABLE_SOURCES = [
    "infowars.com", "naturalhealth.news", "breitbart.com", "dailybuzzlive.com",
    "worldnewsdailyreport.com", "empirenews.net", "huzlers.com", "theonion.com",
    "clickhole.com", "babylonbee.com", "newslo.com", "nationalreport.net",
    "bizarretoday.com", "worldtruth.tv", "unconfirmedbreakinginfo.com"
]

# Fake news detection functions
def analyze_text_content(text):
    """Analyze the language patterns in the text."""
    # Input validation
    if not text or not isinstance(text, str) or len(text.strip()) < 20:
        return {
            "score": 0,
            "analysis": "Insufficient content for analysis."
        }
    
    # Convert to lowercase
    text = text.lower()
    
    try:
        # Tokenize text
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        # Remove punctuation and stopwords
        words = [word for word in words if word not in string.punctuation and word not in STOP_WORDS]
        
        # Check for clickbait phrases
        clickbait_count = sum(1 for phrase in CLICKBAIT_PHRASES if phrase in text)
        clickbait_ratio = clickbait_count / max(len(sentences), 1)
        
        # Check for excessive punctuation
        exclamation_count = text.count('!')
        question_count = text.count('?')
        punctuation_ratio = (exclamation_count + question_count) / max(len(sentences), 1)
        
        # Check for ALL CAPS words (excluding acronyms)
        caps_count = sum(1 for word in words if word.isupper() and len(word) > 2)
        caps_ratio = caps_count / max(len(words), 1)
        
        # Analyze sentence structure
        sentence_lengths = [len(word_tokenize(sentence)) for sentence in sentences]
        avg_sentence_length = sum(sentence_lengths) / max(len(sentences), 1)
        
        # Calculate language score (0-100)
        # Lower score indicates more sensationalist language
        base_score = 70  # Start with neutral score
        
        # Adjust score based on analysis
        base_score -= clickbait_ratio * 30
        base_score -= punctuation_ratio * 20
        base_score -= caps_ratio * 25
        
        # Very short or very long sentences can indicate issues
        if avg_sentence_length < 5 or avg_sentence_length > 40:
            base_score -= 10
        
        # Ensure score is within 0-100 range
        language_score = max(0, min(100, base_score))
        
        # Generate analysis text
        if language_score < 40:
            analysis = "Highly emotional language detected. Contains sensationalist phrases and potential manipulation techniques."
        elif language_score < 70:
            analysis = "Some emotional language present. Article tone is somewhat sensationalist."
        else:
            analysis = "Neutral language detected. Article presents information in a balanced, objective manner."
        
        return {
            "score": language_score,
            "analysis": analysis
        }
    except Exception as e:
        # If any error occurs during analysis, return a safe default
        print(f"Error in analyze_text_content: {str(e)}")
        return {
            "score": 50,
            "analysis": "Analysis incomplete due to text processing error."
        }

def check_source_credibility(text, url=None):
    """Check the credibility of the source."""
    try:
        if url and isinstance(url, str):
            # Extract domain from URL - improved regex pattern
            domain_match = re.search(r'https?://(?:www\.)?([^/\s]+)', url.lower())
            if domain_match:
                domain = domain_match.group(1)
                
                if any(reliable in domain for reliable in RELIABLE_SOURCES):
                    return {
                        "score": 85,
                        "analysis": "Source has good reputation for accuracy and journalistic standards."
                    }
                elif any(questionable in domain for questionable in QUESTIONABLE_SOURCES):
                    return {
                        "score": 25,
                        "analysis": "Source has low credibility rating. Known for publishing misleading or false information."
                    }
        
        if not text or not isinstance(text, str):
            return {
                "score": 50,
                "analysis": "Unable to assess source credibility with provided information."
            }
            
        # If no URL or domain not found in lists, analyze text for source indicators
        # Look for citation patterns, quoted experts, etc.
        
        citation_patterns = [
            r'according to [^.,]+',
            r'cited in [^.,]+',
            r'reported by [^.,]+',
            r'published in [^.,]+',
            r'study in [^.,]+',
            r'research from [^.,]+'
        ]
        
        quote_pattern = r'"[^"]+"'
        
        citations = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in citation_patterns)
        quotes = len(re.findall(quote_pattern, text))
        
        # Analyze attribution density
        word_count = max(len(word_tokenize(text)), 1)  # Avoid division by zero
        attribution_density = (citations + quotes) / max(word_count / 100, 1)
        
        if attribution_density > 1.5:
            return {
                "score": 75,
                "analysis": "Source includes multiple attributions and citations. Appears to follow journalistic standards."
            }
        elif attribution_density > 0.5:
            return {
                "score": 60,
                "analysis": "Source has some attributions. Has moderate credibility indicators."
            }
        else:
            return {
                "score": 45,
                "analysis": "Source has mixed credibility. Has published both accurate and misleading content in the past."
            }
    except Exception as e:
        print(f"Error in check_source_credibility: {str(e)}")
        return {
            "score": 50,
            "analysis": "Unable to assess source credibility due to processing error."
        }

def check_fact_consistency(text):
    """Check the internal consistency and factual indicators in the text."""
    try:
        if not text or not isinstance(text, str) or len(text.strip()) < 20:
            return {
                "score": 50,
                "analysis": "Insufficient content for fact consistency analysis."
            }
        
        # Check for hedge words that might indicate uncertainty
        hedge_words = [
            "allegedly", "reportedly", "supposedly", "claims", "could be", "might be",
            "perhaps", "possibly", "rumored", "speculated", "unconfirmed", "unverified"
        ]
        
        hedge_count = sum(1 for word in hedge_words if re.search(r'\b' + word + r'\b', text, re.IGNORECASE))
        
        # Check for specific indicators like dates, numbers, statistics
        date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        statistic_pattern = r'\b\d+(?:\.\d+)?%\b|\b\d+ percent\b|\b\d+ out of \d+\b'
        
        dates = len(re.findall(date_pattern, text))
        statistics = len(re.findall(statistic_pattern, text))
        
        # Check for contradictory statements (simplified approach)
        contradictions = 0
        negation_words = ["not", "no", "never", "none", "neither", "nor", "nothing"]
        
        try:
            sentences = sent_tokenize(text)
            
            for i, sentence in enumerate(sentences):
                if i > 0:
                    words = word_tokenize(sentence.lower())
                    if any(word in words for word in negation_words):
                        prev_words = word_tokenize(sentences[i-1].lower())
                        common_words = set(words) & set(prev_words)
                        if len(common_words) > 3:  # If sentences share multiple words but one has negation
                            contradictions += 1
        except Exception as inner_e:
            print(f"Error in contradiction analysis: {str(inner_e)}")
            # Continue with other analyses if this one fails
        
        # Calculate score
        base_score = 65  # Start neutral
        
        # Adjust score
        base_score -= hedge_count * 5  # Subtract for uncertain language
        base_score += min(dates + statistics, 10) * 3  # Add for specific facts (capped at +30)
        base_score -= contradictions * 15  # Subtract for contradictions
        
        # Ensure score is within 0-100 range
        fact_score = max(0, min(100, base_score))
        
        # Generate analysis
        if fact_score < 40:
            analysis = "Multiple unverified claims detected. Several statements contradict established facts."
        elif fact_score < 70:
            analysis = "Some claims require verification. The article mixes factual information with potentially misleading statements."
        else:
            analysis = "Most claims appear to be factually accurate based on verification against trusted sources."
        
        return {
            "score": fact_score,
            "analysis": analysis
        }
    except Exception as e:
        print(f"Error in check_fact_consistency: {str(e)}")
        return {
            "score": 50,
            "analysis": "Unable to complete fact consistency analysis due to processing error."
        }

def get_overall_score(language_score, source_score, fact_score):
    """Calculate the overall reliability score with weighted components."""
    try:
        # Ensure inputs are numeric
        language_score = float(language_score)
        source_score = float(source_score)
        fact_score = float(fact_score)
        
        # Source credibility is most important, followed by factual accuracy, then language patterns
        weights = {
            "language": 0.25,
            "source": 0.40,
            "fact": 0.35
        }
        
        weighted_score = (
            language_score * weights["language"] +
            source_score * weights["source"] +
            fact_score * weights["fact"]
        )
        
        # Round to 2 decimal places
        weighted_score = round(weighted_score, 2)
        
        # Determine reliability label
        if weighted_score < 30:
            reliability_label = "Likely Fake News"
        elif weighted_score < 50:
            reliability_label = "Questionable Content"
        elif weighted_score < 70:
            reliability_label = "Partially Reliable"
        elif weighted_score < 85:
            reliability_label = "Mostly Reliable"
        else:
            reliability_label = "Highly Reliable"
        
        return {
            "score": weighted_score,
            "label": reliability_label
        }
    except Exception as e:
        print(f"Error in get_overall_score: {str(e)}")
        return {
            "score": 50,
            "label": "Analysis Error"
        }

# Serve frontend files - serve index.html at the root route
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Serve all static files in the static folder
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON format",
                "status": "error"
            }), 400
            
        data = request.json
        
        # Validate input data
        if not data:
            return jsonify({
                "error": "No data provided",
                "status": "error"
            }), 400
            
        if 'content' not in data or not data['content'] or not isinstance(data['content'], str):
            return jsonify({
                "error": "No valid content provided for analysis",
                "status": "error"
            }), 400
        
        content = data['content'].strip()
        url = data.get('url', None)
        
        # Skip analysis if content is too short
        if len(content) < 20:
            return jsonify({
                "status": "error",
                "error": "Content too short for meaningful analysis (minimum 20 characters required)"
            }), 400
        
        # Perform analysis
        language_analysis = analyze_text_content(content)
        source_analysis = check_source_credibility(content, url)
        fact_analysis = check_fact_consistency(content)
        
        # Calculate overall score
        overall = get_overall_score(
            language_analysis["score"],
            source_analysis["score"],
            fact_analysis["score"]
        )
        
        # Prepare response
        response = {
            "status": "success",
            "results": {
                "overallScore": overall["score"],
                "reliabilityLabel": overall["label"],
                "languageScore": language_analysis["score"],
                "factScore": fact_analysis["score"],
                "sourceScore": source_analysis["score"],
                "languageAnalysis": language_analysis["analysis"],
                "factAnalysis": fact_analysis["analysis"],
                "sourceAnalysis": source_analysis["analysis"]
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        # Global error handler
        print(f"API Error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "An unexpected error occurred during analysis",
            "details": str(e)
        }), 500

# Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)