"""
Output Cleaner Service
Strips markdown artifacts and normalizes LLM output into clean structured data.
"""
import re
import json


def clean_text(text):
    """Remove markdown symbols and normalize whitespace."""
    if not text:
        return text

    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}', '', text)
    # Remove heading markers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # Remove inline code backticks
    text = re.sub(r'`+', '', text)
    # Normalize bullet characters to •
    text = re.sub(r'^[\s]*[-*]\s+', '• ', text, flags=re.MULTILINE)
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def parse_summary_sections(raw_text):
    """
    Parse LLM summary output into structured sections.
    Returns: {
        'summary': str,
        'keypoints': list[str],
        'raw_cleaned': str
    }
    """
    if not raw_text:
        return {'summary': '', 'keypoints': [], 'raw_cleaned': ''}

    cleaned = clean_text(raw_text)

    summary_part = ''
    keypoints = []

    # Try to split by known section headers
    # Match headers like "Summary", "सारांश", "Key Takeaways", "मुख्य बिंदु", etc.
    summary_pattern = re.compile(
        r'(?:Summary|सारांश|सारांश)\s*\n(.*?)(?=(?:Key Takeaways|मुख्य बिंदु|मुख्य मुद्दे|$))',
        re.DOTALL | re.IGNORECASE
    )
    takeaways_pattern = re.compile(
        r'(?:Key Takeaways|मुख्य बिंदु|मुख्य मुद्दे)\s*\n(.*)',
        re.DOTALL | re.IGNORECASE
    )

    summary_match = summary_pattern.search(cleaned)
    takeaways_match = takeaways_pattern.search(cleaned)

    if summary_match:
        summary_part = summary_match.group(1).strip()
    elif not takeaways_match:
        # No headers found — treat everything as summary
        summary_part = cleaned

    if takeaways_match:
        takeaway_text = takeaways_match.group(1).strip()
        for line in takeaway_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove bullet prefix
            line = re.sub(r'^[•\-*\d.]+\s*', '', line).strip()
            if line and len(line) > 3:
                keypoints.append(line)

    return {
        'summary': summary_part,
        'keypoints': keypoints,
        'raw_cleaned': cleaned
    }


def build_clean_response(summary_text, sentiment_data=None, language='en'):
    """
    Build a structured response dict for the frontend.
    """
    parsed = parse_summary_sections(summary_text)

    response = {
        'summary': parsed['summary'],
        'keypoints': parsed['keypoints'],
        'sentiment': {
            'score': sentiment_data.get('sentiment_score', 0) if sentiment_data else 0,
            'emotion': sentiment_data.get('emotion', 'Neutral') if sentiment_data else 'Neutral',
            'label': sentiment_data.get('sentiment', 'Neutral') if sentiment_data else 'Neutral'
        },
        'language': language
    }
    return response
