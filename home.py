from flask import Blueprint, render_template, request, flash, session, redirect, url_for, send_file, make_response, jsonify
from flask_login import login_required, current_user
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from db import summaries_collection, history_collection, comments_collection, chat_history_collection
from datetime import datetime, timedelta, timezone

# IST timezone offset
IST = timezone(timedelta(hours=5, minutes=30))
import re
import os
import asyncio
import json
import threading
from reportlab.lib.pagesizes import letter

# email helper for OTP and notifications
import smtplib
from email.mime.text import MIMEText

def send_reset_email(to_addr, otp=None, success=False):
    """Sends a simple email. If otp provided, send code; if success True send notification."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    from_addr = os.getenv('FROM_EMAIL', smtp_user or 'noreply@example.com')
    if not smtp_server or not smtp_port:
        print("Email configuration missing, not sending message")
        return False
    if success:
        subject = "Your PodcastAI password has been reset"
        body = "Your password was successfully updated. If this wasn't you, contact support."
    else:
        subject = "Your PodcastAI password reset code"
        body = f"Use the following code to reset your password: {otp}\n\nIf you didn't request this, ignore this email."
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from io import BytesIO
from services.chat_service import ChatService
from services.output_cleaner import clean_text, parse_summary_sections, build_clean_response

# language detection (requires langdetect package)
from langdetect import detect, LangDetectException

def detect_language(text, default='en'):
    """Try to guess the language code for the given text.
    Returns a 2‑letter ISO code (e.g. 'en', 'hi', 'mr').
    Falls back to `default` on failure.
    """
    if not text or not text.strip():
        return default
    try:
        return detect(text)
    except LangDetectException:
        return default


# Initialize Services
chat_service = ChatService()

home_bp = Blueprint('home_bp', __name__)

# -------------------- Helpers --------------------

def get_video_id(url):
    if not url:
        return None

    # Normalize common copy/paste artifacts
    cleaned = url.strip()
    cleaned = cleaned.strip("[]()<>")
    cleaned = cleaned.split()[0]

    patterns = [
        r"v=([0-9A-Za-z_-]{11})",                 # watch?v=VIDEO_ID
        r"youtu\.be/([0-9A-Za-z_-]{11})",         # youtu.be/VIDEO_ID
        r"/shorts/([0-9A-Za-z_-]{11})",           # /shorts/VIDEO_ID
        r"/embed/([0-9A-Za-z_-]{11})",            # /embed/VIDEO_ID
        r"/live/([0-9A-Za-z_-]{11})",             # /live/VIDEO_ID
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return match.group(1)

    # Fallback: raw 11-char ID
    match = re.search(r"\b([0-9A-Za-z_-]{11})\b", cleaned)
    return match.group(1) if match else None


def fetch_available_captions(video_url):
    video_id = get_video_id(video_url)
    if not video_id:
        return None

    try:
        proxy_config = None
        if os.getenv("PROXY_USERNAME") and os.getenv("PROXY_PASSWORD"):
            proxy_config = WebshareProxyConfig(
                proxy_username=os.getenv("PROXY_USERNAME"),
                proxy_password=os.getenv("PROXY_PASSWORD")
            )
        elif os.getenv("PROXY_URL"):
            proxy_config = GenericProxyConfig(
                http_url=os.getenv("PROXY_URL"),
                https_url=os.getenv("PROXY_URL")
            )

        api = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcripts = list(transcript_list)

        preferred_langs = os.getenv("TRANSCRIPT_LANGS", "en")
        preferred_langs = [l.strip() for l in preferred_langs.split(",") if l.strip()]

        transcript = None

        for lang in preferred_langs:
            transcript = next(
                (t for t in transcripts if (not t.is_generated) and t.language_code == lang),
                None
            )
            if transcript:
                break

        if not transcript:
            for lang in preferred_langs:
                transcript = next(
                    (t for t in transcripts if t.is_generated and t.language_code == lang),
                    None
                )
                if transcript:
                    break

        if not transcript:
            transcript = next((t for t in transcripts if not t.is_generated), None)

        if not transcript and transcripts:
            transcript = transcripts[0]

        if not transcript:
            return None

        target_lang = os.getenv("TRANSCRIPT_TRANSLATE_TO", "").strip()
        if (
            target_lang
            and getattr(transcript, "is_translatable", False)
            and transcript.language_code != target_lang
        ):
            try:
                transcript = transcript.translate(target_lang)
            except Exception:
                pass

        formatter = TextFormatter()
        formatted_text = formatter.format_transcript(transcript.fetch())
        
        # return dict to be consistent
        return {'text': formatted_text, 'chapters': []}  # No semantic chapters for standard captions

    except Exception as e:
        print("Caption error:", e)
        return None


# -------------------- Async summarization --------------------

async def summarize_chunk(chunk_text, index):
    try:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7
        )

        prompt = PromptTemplate.from_template("""
        Summarize this transcript chunk into 2-3 concise bullet points.

        Chunk {num}:
        {text}
        """)

        response = await llm.ainvoke(
            prompt.format(
                text=chunk_text,
                num=index + 1
            )
        )

        return index, response.content

    except Exception as e:
        error_msg = str(e)
        if "Connection" in error_msg or "refused" in error_msg:
            print(f"⚠️ Ollama connection failed for chunk {index+1}. Is Ollama running?")
        else:
            print(f"Chunk {index+1} failed:", e)
        return index, None


async def generate_distributed_summary_async(text):
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
        docs = splitter.split_documents([Document(page_content=text)])

        tasks = []
        for i, doc in enumerate(docs):
            tasks.append(
                summarize_chunk(doc.page_content, i)
            )

        results = await asyncio.gather(*tasks)

        summaries = [r for r in results if r[1]]
        summaries.sort(key=lambda x: x[0])

        if not summaries:
            return None

        combined = "\n".join(s[1] for s in summaries)

        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7
        )

        final_prompt = PromptTemplate.from_template("""
You are an expert content summarizer.
Please provide a response in English in the following format:

### Summary
(A concise paragraph summarizing the entire video content.)

### Key Takeaways
(Exactly 10-15 bullet points containing the most important insights.)

Input text:
{text}
        """)

        final_response = await llm.ainvoke(final_prompt.format(text=combined))
        return final_response.content
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "refused" in error_msg:
            print("⚠️ ERROR: Cannot connect to Ollama. Please ensure Ollama is running on http://localhost:11434")
            print("   Run 'ollama serve' to start Ollama")
        else:
            print(f"⚠️ Summary generation error: {e}")
        return None


def generate_distributed_summary(text):
    return asyncio.run(generate_distributed_summary_async(text))


# -------------------- Sentiment & Emotion Analysis --------------------

async def analyze_sentiment_emotion_async(text, text_type="transcript"):
    """
    Analyzes sentiment and emotion of the given text using LLM.
    Returns: {
        'sentiment': 'Positive|Negative|Neutral',
        'sentiment_score': 0-100,
        'emotion': 'Excited|Serious|...',
        'emotion_confidence': 0-100
    }
    """
    try:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7
        )

        # Truncate text if too long to save processing
        if len(text) > 5000:
            text = text[:5000]

        prompt = PromptTemplate.from_template("""
Analyze the sentiment and emotion of this {text_type} text. Respond ONLY with valid JSON, no other text.

Expected JSON format:
{{"sentiment": "Positive|Negative|Neutral", "sentiment_score": 0-100, "emotion": "Excited|Serious|Motivational|Sad|Informative|Angry|Neutral", "emotion_confidence": 0-100}}

Text:
{text}
        """)

        response = await llm.ainvoke(
            prompt.format(text=text, text_type=text_type)
        )

        # Parse JSON response
        response_text = response.content.strip()
        # Extract JSON from response (in case it has extra text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Ensure sentiment_score is present and valid
            if 'sentiment_score' not in result or not isinstance(result.get('sentiment_score'), (int, float)):
                result['sentiment_score'] = 50
            else:
                result['sentiment_score'] = max(0, min(100, int(result['sentiment_score'])))
            return result
        else:
            # Fallback if JSON parsing fails
            return {
                'sentiment': 'Neutral',
                'sentiment_score': 50,
                'emotion': 'Informative',
                'emotion_confidence': 50
            }

    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        # Return default values if analysis fails
        return {
            'sentiment': 'Neutral',
            'sentiment_score': 50,
            'emotion': 'Informative',
            'emotion_confidence': 50
        }


def analyze_sentiment_emotion(text, text_type="transcript"):
    return asyncio.run(analyze_sentiment_emotion_async(text, text_type))


# -------------------- Accuracy Calculation --------------------

async def calculate_accuracy_scores_async(full_text, summary):
    """
    Calculates transcription and summary confidence scores using LLM.
    Returns: {
        'transcription_confidence': 0-100,
        'summary_confidence': 0-100
    }
    """
    try:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.5
        )

        # Truncate text if too long
        analysis_text = full_text if len(full_text) <= 3000 else full_text[:3000]

        transcription_prompt = PromptTemplate.from_template("""
Rate the quality and completeness of this transcript (0-100). Consider grammar, punctuation, sentence structure, and comprehensiveness.
Respond with ONLY a number 0-100, nothing else.

Transcript:
{text}
        """)

        trans_response = await llm.ainvoke(
            transcription_prompt.format(text=analysis_text)
        )

        # Parse transcription confidence
        trans_score = 50  # default
        try:
            extracted = ''.join(filter(str.isdigit, trans_response.content.strip()[:3]))
            if extracted:
                trans_score = int(extracted)
                trans_score = max(0, min(100, trans_score))
        except Exception:
            pass
        # if we evaluated an actual transcript but got 0, use neutral fallback instead
        if analysis_text.strip() and trans_score == 0:
            trans_score = 50

        # Summary confidence
        summary_prompt = PromptTemplate.from_template("""
Rate how well this summary captures the original transcript content (0-100). Consider completeness, accuracy, and relevance.
Respond with ONLY a number 0-100, nothing else.

Summary:
{summary}
        """)

        summary_response = await llm.ainvoke(
            summary_prompt.format(summary=summary if len(summary) <= 2000 else summary[:2000])
        )

        # Parse summary confidence
        summary_score = 50  # default
        try:
            extracted = ''.join(filter(str.isdigit, summary_response.content.strip()[:3]))
            if extracted:
                summary_score = int(extracted)
                summary_score = max(0, min(100, summary_score))
        except Exception:
            pass
        # avoid a false zero when summary exists
        if summary.strip() and summary_score == 0:
            summary_score = 50

        return {
            'transcription_confidence': trans_score,
            'summary_confidence': summary_score
        }

    except Exception as e:
        print(f"Accuracy calculation error: {e}")
        # Return default values
        return {
            'transcription_confidence': 70,
            'summary_confidence': 70
        }


def calculate_accuracy_scores(full_text, summary):
    return asyncio.run(calculate_accuracy_scores_async(full_text, summary))


# -------------------- Topic Detection & Q&A Generation --------------------

def generate_topics_qa(full_text, language='en'):
    """
    Extracts key topics from the transcript and generates related Q&A pairs.
    The returned Q&A will be in the specified language (default English).
    Returns: list of { 'topic': str, 'questions': [{'q': str, 'a': str}] }
    """
    try:
        if not full_text or len(full_text) < 100:
            return []

        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.5
        )

        # Truncate for manageable processing
        analysis_text = full_text if len(full_text) <= 5000 else full_text[:5000]

        prompt = PromptTemplate.from_template("""
Analyze this podcast transcript and extract exactly 5 key topics discussed.
For each topic, generate 2 relevant questions and their answers based ONLY on the transcript.

Transcript:
{text}

Please respond in {language}.

Respond ONLY with valid JSON in this EXACT format, no other text:
[{{
    "topic": "Topic Name",
    "questions": [
        {{"q": "Question 1?", "a": "Answer 1"}},
        {{"q": "Question 2?", "a": "Answer 2"}}
    ]
}}]
        """ )

        response = llm.invoke(prompt.format(text=analysis_text, language=language))
        response_text = response.content.strip()

        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            topics = json.loads(json_match.group())
            # Validate structure
            valid_topics = []
            for t in topics[:5]:
                if isinstance(t, dict) and 'topic' in t and 'questions' in t:
                    valid_qs = []
                    for q in t['questions'][:2]:
                        if isinstance(q, dict) and 'q' in q and 'a' in q:
                            valid_qs.append({'q': str(q['q']), 'a': str(q['a'])})
                    if valid_qs:
                        valid_topics.append({'topic': str(t['topic']), 'questions': valid_qs})
            return valid_topics

        return []

    except Exception as e:
        print(f"Topic detection error: {e}")
        return []

# -------------------- PDF Generation --------------------

def generate_pdf(video_id, record):
    """
    Generates a polished, professional PDF report.
    Returns: BytesIO object containing the PDF
    """
    try:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, pagesize=letter,
            rightMargin=60, leftMargin=60,
            topMargin=55, bottomMargin=55
        )

        elements = []
        styles   = getSampleStyleSheet()
        avail_width = letter[0] - 120   # 8.5in page - 60pt left - 60pt right

        # ── Colour palette ───────────────────────────────────────────────────
        BRAND_BLUE    = colors.HexColor('#3B6FE8')
        DARK_TEXT     = colors.HexColor('#1A1A2E')
        MID_GREY      = colors.HexColor('#6B7280')
        LIGHT_BG      = colors.HexColor('#F8FAFF')
        DIVIDER_COLOR = colors.HexColor('#D1D9F0')
        GREEN_BG      = colors.HexColor('#D1FAE5')
        GREEN_TEXT    = colors.HexColor('#065F46')
        RED_BG        = colors.HexColor('#FEE2E2')
        RED_TEXT      = colors.HexColor('#991B1B')
        NEUTRAL_BG    = colors.HexColor('#F3F4F6')
        NEUTRAL_TEXT  = colors.HexColor('#374151')
        ALT_ROW_BG    = colors.HexColor('#EEF2FF')

        # ── Helper: quickly create a ParagraphStyle ──────────────────────────
        def ps(name, **kwargs):
            base = kwargs.pop('parent', styles['Normal'])
            return ParagraphStyle(name, parent=base, **kwargs)

        # ── Typography ───────────────────────────────────────────────────────
        title_st = ps('RTitle',
            fontSize=24, textColor=BRAND_BLUE,
            fontName='Helvetica-Bold', alignment=1, spaceAfter=12)

        subtitle_st = ps('RSub',
            fontSize=10, textColor=MID_GREY,
            fontName='Helvetica', alignment=1, spaceAfter=2)

        meta_st = ps('RMeta',
            fontSize=9, textColor=MID_GREY,
            fontName='Helvetica', spaceAfter=2)

        heading_st = ps('RHead',
            fontSize=13, textColor=DARK_TEXT,
            fontName='Helvetica-Bold',
            spaceBefore=8, spaceAfter=12, keepWithNext=True)

        body_st = ps('RBody',
            parent=styles['BodyText'],
            fontSize=10, textColor=DARK_TEXT,
            leading=15, spaceAfter=4)

        bullet_st = ps('RBullet',
            parent=styles['BodyText'],
            fontSize=10, textColor=DARK_TEXT,
            leading=15,
            leftIndent=20,       # indent the whole paragraph
            firstLineIndent=-10, # hang the bullet back to the left
            spaceBefore=1, spaceAfter=5)  # breathing room between points

        cell_st = ps('RCell',
            fontSize=9, textColor=DARK_TEXT, alignment=1, leading=12)

        hdr_cell_st = ps('RHdr',
            fontSize=10, fontName='Helvetica-Bold',
            textColor=colors.white, alignment=1, leading=13)

        # ── Helper: thin horizontal rule ─────────────────────────────────────
        def divider():
            t = Table([['']], colWidths=[avail_width])
            t.setStyle(TableStyle([
                ('LINEABOVE',      (0, 0), (-1, 0), 0.8, DIVIDER_COLOR),
                ('TOPPADDING',     (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING',  (0, 0), (-1, -1), 0),
            ]))
            return t

        # ── Helper: solid colour accent strip ────────────────────────────────
        def accent_bar(clr=BRAND_BLUE, h=4):
            t = Table([['']], colWidths=[avail_width], rowHeights=[h])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), clr),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            return t

        # ════════════════════════════════════════════════════════════════════
        # HEADER
        # ════════════════════════════════════════════════════════════════════
        elements.append(accent_bar())
        elements.append(Spacer(1, 0.16 * inch))
        elements.append(Paragraph("Podcast Summary Report", title_st))

        video_title = (record.get('video_title') or '').strip()
        if video_title:
            safe_vt = video_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(safe_vt, subtitle_st))

        elements.append(Spacer(1, 0.18 * inch))

        video_url = record.get('video_url', '')
        date_str  = datetime.now(IST).strftime("%d %B %Y  \u2022  %I:%M %p IST")
        if video_url:
            elements.append(Paragraph(f"<b>URL:</b>  {video_url}", meta_st))
        elements.append(Paragraph(f"<b>Generated:</b>  {date_str}", meta_st))
        elements.append(Spacer(1, 0.16 * inch))
        elements.append(accent_bar(clr=DIVIDER_COLOR, h=1))
        elements.append(Spacer(1, 0.2 * inch))

        # ════════════════════════════════════════════════════════════════════
        # Parse summary
        # ════════════════════════════════════════════════════════════════════
        raw_summary   = clean_text(record.get('summary', 'N/A'))
        summary_part  = raw_summary
        key_takeaways = []

        if any(kw in raw_summary for kw in
               ['### Summary', '### Key Takeaways', '### \u0938\u093e\u0930\u093e\u0902\u0936',
                '### \u092e\u0941\u0916\u094d\u092f', 'Summary', 'Key Takeaways']):
            parsed        = parse_summary_sections(raw_summary)
            summary_part  = parsed.get('summary', raw_summary)
            key_takeaways = parsed.get('keypoints', [])

        if not summary_part:
            summary_part = raw_summary

        # ════════════════════════════════════════════════════════════════════
        # SUMMARY
        # ════════════════════════════════════════════════════════════════════
        elements.append(Paragraph("Summary", heading_st))
        safe_sum = (summary_part
                    .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        for block in safe_sum.split('\n\n'):
            block = block.strip()
            if block:
                elements.append(Paragraph(block, body_st))
        elements.append(Spacer(1, 0.1 * inch))

        # ════════════════════════════════════════════════════════════════════
        # KEY TAKEAWAYS
        # ════════════════════════════════════════════════════════════════════
        if key_takeaways:
            elements.append(divider())
            elements.append(Spacer(1, 0.06 * inch))
            elements.append(Paragraph("Key Takeaways", heading_st))
            for t in key_takeaways:
                safe_t = (t.replace('&', '&amp;')
                           .replace('<', '&lt;').replace('>', '&gt;'))
                # U+2022 (•) — standard typographic bullet, smaller and refined
                elements.append(Paragraph(f"\u2022  {safe_t}", bullet_st))
            elements.append(Spacer(1, 0.1 * inch))

        # ════════════════════════════════════════════════════════════════════
        # SENTIMENT & EMOTION
        # ════════════════════════════════════════════════════════════════════
        trans_sent   = record.get('transcript_sentiment') or {}
        summary_sent = record.get('summary_sentiment')    or {}

        if trans_sent or summary_sent:
            elements.append(divider())
            elements.append(Spacer(1, 0.08 * inch))

            SENT_COLORS = {
                'positive': (GREEN_BG,   GREEN_TEXT),
                'negative': (RED_BG,     RED_TEXT),
                'neutral':  (NEUTRAL_BG, NEUTRAL_TEXT),
            }

            def sent_color(s):
                return SENT_COLORS.get((s or '').lower(), (NEUTRAL_BG, NEUTRAL_TEXT))

            def fmt_emo(s):
                parts = [e.strip() for e in (s or '').split('|') if e.strip()]
                return ('\n'.join(f'\u2022 {e}' for e in parts)) if parts else 'N/A'

            col_w = [avail_width * r for r in (.18, .20, .14, .48)]
            hdr_row = [Paragraph(h, hdr_cell_st)
                       for h in ['Type', 'Sentiment', 'Score', 'Emotions']]
            tdata = [hdr_row]
            rc    = []   # row colour overrides

            for ri, (lbl, sd) in enumerate(
                    [('Transcript', trans_sent), ('Summary', summary_sent)], 1):
                if not sd:
                    continue
                sv       = sd.get('sentiment', 'Neutral')
                bg, fg   = sent_color(sv)
                score    = sd.get('sentiment_score', 0)
                emo_safe = (fmt_emo(sd.get('emotion', 'N/A'))
                            .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

                sv_st  = ps(f'Sv{ri}', fontSize=9, textColor=fg,
                             fontName='Helvetica-Bold', alignment=1)
                emo_st = ps(f'Ev{ri}', fontSize=8, textColor=DARK_TEXT,
                             leading=11, alignment=0)

                tdata.append([
                    Paragraph(lbl,           cell_st),
                    Paragraph(sv,            sv_st),
                    Paragraph(f'{score}%',   cell_st),
                    Paragraph(emo_safe,      emo_st),
                ])
                rc.append(('BACKGROUND', (1, ri), (1, ri), bg))

            st_tbl = Table(tdata, colWidths=col_w, repeatRows=1)
            ts = TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),  BRAND_BLUE),
                ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('ROWBACKGROUNDS',(0, 1), (-1, -1), [LIGHT_BG, ALT_ROW_BG]),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING',   (0, 0), (-1, -1), 7),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
                ('GRID',          (0, 0), (-1, -1), 0.5, DIVIDER_COLOR),
                ('BOX',           (0, 0), (-1, -1), 1,   BRAND_BLUE),
            ])
            for cmd in rc:
                ts.add(*cmd)
            ts.add('ALIGN', (3, 0), (3, -1), 'LEFT')
            st_tbl.setStyle(ts)

            elements.append(KeepTogether([
                Paragraph("Sentiment &amp; Emotion Analysis", heading_st),
                st_tbl,
            ]))
            elements.append(Spacer(1, 0.15 * inch))

        # ════════════════════════════════════════════════════════════════════
        # ANALYSIS ACCURACY
        # ════════════════════════════════════════════════════════════════════
        trans_acc   = record.get('transcription_confidence') or 0
        summary_acc = record.get('summary_confidence')       or 0

        if trans_acc or summary_acc:
            elements.append(divider())
            elements.append(Spacer(1, 0.08 * inch))

            def conf_bar(sc):
                filled = round(sc / 5)
                return f"{'█' * filled}{'░' * (20 - filled)}  {sc}%"

            def conf_color(sc):
                if sc >= 75:
                    return GREEN_BG, GREEN_TEXT
                if sc >= 50:
                    return colors.HexColor('#FEF3C7'), colors.HexColor('#92400E')
                return RED_BG, RED_TEXT

            acc_cw  = [avail_width * 0.28, avail_width * 0.72]
            acc_hdr = [Paragraph(h, hdr_cell_st) for h in ['Type', 'Confidence Level']]
            acc_dat = [acc_hdr]
            acc_rc  = []

            for ri2, (lbl, sc) in enumerate(
                    [('Transcription', trans_acc), ('Summary', summary_acc)], 1):
                bg2, fg2 = conf_color(sc)
                vst = ps(f'Av{ri2}', fontSize=9, textColor=fg2,
                          fontName='Helvetica-Bold', leading=11, alignment=0)
                acc_dat.append([Paragraph(lbl, cell_st), Paragraph(conf_bar(sc), vst)])
                acc_rc.append(('BACKGROUND', (0, ri2), (-1, ri2), bg2))

            acc_tbl = Table(acc_dat, colWidths=acc_cw)
            ats = TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),  BRAND_BLUE),
                ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
                ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
                ('GRID',          (0, 0), (-1, -1), 0.5, DIVIDER_COLOR),
                ('BOX',           (0, 0), (-1, -1), 1,   BRAND_BLUE),
            ])
            for cmd in acc_rc:
                ats.add(*cmd)
            ats.add('ALIGN', (1, 1), (1, -1), 'LEFT')
            acc_tbl.setStyle(ats)

            # Flow naturally — keepWithNext on heading_st keeps heading+table together
            elements.append(Paragraph("Analysis Accuracy", heading_st))
            elements.append(acc_tbl)

        # ════════════════════════════════════════════════════════════════════
        # FOOTER
        # ════════════════════════════════════════════════════════════════════
        elements.append(Spacer(1, 0.22 * inch))
        elements.append(divider())
        elements.append(Spacer(1, 0.07 * inch))
        elements.append(Paragraph(
            "Generated by <b>PodcastAI</b> \u2014 AI-powered podcast analysis",
            ps('Ftr', fontSize=8, textColor=MID_GREY, alignment=1)
        ))

        doc.build(elements)
        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback; traceback.print_exc()
        return None


# -------------------- Background Analysis --------------------

def _run_background_analysis(video_id, full_text, summary):
    """
    Runs sentiment, accuracy, and topic analysis in a background thread.
    Updates the DB record progressively as each step completes.
    """
    try:
        # ensure language field exists (for older records)
        detected_lang = detect_language(summary or full_text)
        summaries_collection.update_one(
            {'video_id': video_id},
            {'$set': {'language': detected_lang}},
            upsert=False
        )
        # Step 1: Sentiment analysis
        print(f"[PodcastAI] [{video_id}] Background: Starting sentiment analysis...")
        transcript_sentiment = analyze_sentiment_emotion(full_text, "transcript")
        summary_sentiment = analyze_sentiment_emotion(summary, "summary")
        summaries_collection.update_one(
            {'video_id': video_id},
            {'$set': {
                'transcript_sentiment': transcript_sentiment,
                'summary_sentiment': summary_sentiment,
                'analysis_progress': 'sentiment_done'
            }}
        )
        print(f"[PodcastAI] [{video_id}] Background: Sentiment analysis complete.")

        # Step 2: Accuracy scores
        print(f"[PodcastAI] [{video_id}] Background: Calculating accuracy scores...")
        accuracy_scores = calculate_accuracy_scores(full_text, summary)
        summaries_collection.update_one(
            {'video_id': video_id},
            {'$set': {
                'transcription_confidence': accuracy_scores['transcription_confidence'],
                'summary_confidence': accuracy_scores['summary_confidence'],
                'analysis_progress': 'accuracy_done'
            }}
        )
        print(f"[PodcastAI] [{video_id}] Background: Accuracy scores complete.")

        # Step 3: Topic detection + Q&A (use detected language)
        print(f"[PodcastAI] [{video_id}] Background: Generating topics...")
        # generate topics/questions in detected language (fallback english)
        topics = generate_topics_qa(full_text, language=detected_lang or 'en')
        summaries_collection.update_one(
            {'video_id': video_id},
            {'$set': {
                'topics': topics,
                'analysis_progress': 'complete'
            }}
        )
        print(f"[PodcastAI] [{video_id}] Background: \u2705 All analysis complete.")

    except Exception as e:
        print(f"[PodcastAI] [{video_id}] Background analysis error: {e}")
        summaries_collection.update_one(
            {'video_id': video_id},
            {'$set': {'analysis_progress': 'complete'}}
        )


# -------------------- Routes --------------------

@home_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        video_id = get_video_id(youtube_url)

        if not video_id:
            flash("Invalid YouTube URL", "error")
            return redirect(url_for('home_bp.dashboard'))

        # Check cache first
        cached = summaries_collection.find_one({'video_id': video_id})

        if cached:
            # If cached but missing background analysis, kick it off
            if cached.get('analysis_progress') != 'complete':
                full_text = cached.get('full_text', '')
                summary = cached.get('summary', '')
                if full_text and summary:
                    thread = threading.Thread(
                        target=_run_background_analysis,
                        args=(video_id, full_text, summary),
                        daemon=True
                    )
                    thread.start()
        else:
            content_data = fetch_available_captions(youtube_url)
            if not content_data:
                flash("Could not fetch captions/audio. Check URL or try again.", "error")
                return redirect(url_for('home_bp.dashboard'))

            full_text = content_data['text']

            # Generate summary ONLY (the user sees this immediately)
            print(f"[PodcastAI] [{video_id}] Generating summary...")
            raw_summary = generate_distributed_summary(full_text)

            if not raw_summary:
                flash("\u274c Summary generation failed. Make sure Ollama is running (ollama serve).", "error")
                return redirect(url_for('home_bp.dashboard'))

            summary = clean_text(raw_summary)
            # detect language from the cleaned summary (fallback to english)
            lang_code = detect_language(summary)
            print(f"[PodcastAI] [{video_id}] Summary ready (lang={lang_code}). Redirecting to results...")

            # Save summary immediately with progress marker
            summaries_collection.insert_one({
                'video_id': video_id,
                'video_url': youtube_url,
                'summary': summary,
                'full_text': full_text,
                'language': lang_code,
                'analysis_progress': 'summary_done',
                'created_at': datetime.utcnow()
            })

            # Kick off background analysis in a separate thread
            thread = threading.Thread(
                target=_run_background_analysis,
                args=(video_id, full_text, summary),
                daemon=True
            )
            thread.start()

        history_collection.update_one(
            {'user_id': current_user.id, 'video_id': video_id},
            {'$set': {'video_url': youtube_url, 'viewed_at': datetime.utcnow()}},
            upsert=True
        )

        # Redirect to the results page IMMEDIATELY (summary is ready)
        return redirect(url_for('home_bp.results', video_id=video_id))

    # --- GET request ---
    recent_history = list(
        history_collection.find({'user_id': current_user.id}).sort('viewed_at', -1).limit(4)
    )

    response = make_response(render_template(
        'dashboard.html',
        username=current_user.username,
        recent_history=recent_history
    ))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@home_bp.route('/results/<video_id>')
@login_required
def results(video_id):
    """Display analysis results for a specific video."""
    record = summaries_collection.find_one({'video_id': video_id})

    if not record or 'summary' not in record:
        flash("No summary found for this video. Please analyze it first.", "error")
        return redirect(url_for('home_bp.dashboard'))

    summary = record['summary']
    progress = record.get('analysis_progress', 'complete')
    sentiment_data = {
        'transcript': record.get('transcript_sentiment', {}),
        'summary': record.get('summary_sentiment', {})
    }
    accuracy_data = {
        'transcription_confidence': record.get('transcription_confidence', 0),
        'summary_confidence': record.get('summary_confidence', 0)
    }
    topics = record.get('topics', [])
    lang_code = record.get('language', 'en')

    # determine why topics might be empty
    full_text = record.get('full_text', '') or ''
    topic_reason = ''
    if not topics:
        if len(full_text.strip()) < 100:
            topic_reason = 'Transcript too short to extract topics.'
        else:
            topic_reason = 'No topics could be detected from the transcript.'

    # attempt to surface some video metadata if present in the record
    return render_template(
        'results.html',
        username=current_user.username,
        summary=summary,
        video_id=video_id,
        video_title=record.get('video_title', ''),
        video_channel=record.get('video_channel', ''),
        video_duration=record.get('video_duration', ''),
        sentiment_data=sentiment_data,
        accuracy_data=accuracy_data,
        topics=topics,
        analysis_progress=progress,
        language=lang_code,
        topic_reason=topic_reason
    )


@home_bp.route('/analysis-status/<video_id>')
@login_required
def analysis_status(video_id):
    """API endpoint for frontend to poll background analysis progress."""
    record = summaries_collection.find_one({'video_id': video_id})
    if not record:
        return jsonify({'progress': 'not_found'}), 404

    progress = record.get('analysis_progress', 'complete')
    data = {'progress': progress}

    # Include completed data sections so the frontend can render them
    if progress in ('sentiment_done', 'accuracy_done', 'complete'):
        data['sentiment'] = {
            'transcript': record.get('transcript_sentiment', {}),
            'summary': record.get('summary_sentiment', {})
        }
        data['language'] = record.get('language', 'en')

    if progress in ('accuracy_done', 'complete'):
        data['accuracy'] = {
            'transcription_confidence': record.get('transcription_confidence', 0),
            'summary_confidence': record.get('summary_confidence', 0)
        }

    if progress == 'complete':
        data['topics'] = record.get('topics', [])
        # also include reason if topics empty
        if not data['topics']:
            full_text = record.get('full_text', '') or ''
            if len(full_text.strip()) < 100:
                data['topic_reason'] = 'Transcript too short to extract topics.'
            else:
                data['topic_reason'] = 'No topics could be detected from the transcript.'

    return jsonify(data)


@home_bp.route('/chat-page/<video_id>')
@login_required
def chat_page(video_id):
    """Dedicated interactive Q&A page for a video."""
    record = summaries_collection.find_one({'video_id': video_id})

    if not record or 'summary' not in record:
        flash("No summary found for this video. Please analyze it first.", "error")
        return redirect(url_for('home_bp.dashboard'))

    topics = record.get('topics', [])

    return render_template(
        'chat.html',
        username=current_user.username,
        video_id=video_id,
        topics=topics
    )


@home_bp.route('/clear_summary')
@login_required
def clear_summary():
    session.clear()
    return redirect(url_for('home_bp.dashboard'))


@home_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message')
    video_id = data.get('video_id')

    if not video_id:
        return {'response': 'Error: Video context missing.'}, 400

    # Retrieve full transcript and summary from DB
    record = summaries_collection.find_one({'video_id': video_id})

    if not record or 'summary' not in record:
        return {'response': 'Error: No summary found for this video. Please generate it first.'}, 404

    full_text = record.get('full_text', '')
    summary = record.get('summary', '')

    # determine language from existing record (fallback english)
    lang_code = record.get('language', 'en')

    # Get response with confidence score using full transcript
    result = chat_service.get_chat_response(full_text, summary, message, language=lang_code)

    # Store chat history in DB
    try:
        chat_history_collection.insert_one({
            'user_id': current_user.id,
            'video_id': video_id,
            'question': message,
            'answer': result['answer'],
            'confidence_score': result['confidence_score'],
            'language': result.get('language', lang_code),
            'timestamp': datetime.now(IST)
        })
    except Exception as e:
        print(f"Chat history save error: {e}")

    return {
        'response': result['answer'],
        'confidence_score': result['confidence_score'],
        'language': result.get('language', lang_code)
    }


@home_bp.route('/chat-history/<video_id>', methods=['GET'])
@login_required
def get_chat_history(video_id):
    """Fetch previous Q&A history for the current user and video."""
    records = list(
        chat_history_collection.find(
            {'user_id': current_user.id, 'video_id': video_id}
        ).sort('timestamp', 1).limit(50)
    )

    history = []
    for r in records:
        history.append({
            'question': r.get('question', ''),
            'answer': r.get('answer', ''),
            'confidence_score': r.get('confidence_score', 0),
            'language': r.get('language', ''),
            'timestamp': r.get('timestamp', datetime.utcnow()).strftime('%b %d, %Y at %H:%M')
        })

    return jsonify({'history': history})


# -------------------- Comments API --------------------

@home_bp.route('/comments/<video_id>', methods=['GET'])
@login_required
def get_comments(video_id):
    """Fetch all comments for a video, sorted newest first."""
    comments = list(
        comments_collection.find({'video_id': video_id})
            .sort('created_at', -1)
            .limit(100)
    )
    
    result = []
    for c in comments:
        result.append({
            'username': c.get('username', 'Anonymous'),
            'comment_text': c.get('comment_text', ''),
            'created_at': (c.get('created_at', datetime.utcnow()).replace(tzinfo=timezone.utc).astimezone(IST)).strftime('%b %d, %Y at %H:%M')
        })
    
    return jsonify({'comments': result})


@home_bp.route('/comments', methods=['POST'])
@login_required
def add_comment():
    """Add a new comment for a video."""
    data = request.get_json()
    video_id = data.get('video_id')
    comment_text = data.get('comment_text', '').strip()
    
    if not video_id or not comment_text:
        return jsonify({'error': 'Video ID and comment text are required.'}), 400
    
    if len(comment_text) > 2000:
        return jsonify({'error': 'Comment too long (max 2000 characters).'}), 400
    
    comment = {
        'video_id': video_id,
        'username': current_user.username,
        'comment_text': comment_text,
        'created_at': datetime.now(IST)
    }
    
    comments_collection.insert_one(comment)
    
    return jsonify({
        'success': True,
        'comment': {
            'username': comment['username'],
            'comment_text': comment['comment_text'],
            'created_at': comment['created_at'].strftime('%b %d, %Y at %H:%M')
        }
    })


@home_bp.route('/history')
@login_required
def history():
    history = list(
        history_collection.find({'user_id': current_user.id}).sort('viewed_at', -1)
    )

    return render_template(
        'history.html',
        username=current_user.username,
        history=history
    )


@home_bp.route('/download-pdf/<video_id>')
@login_required
def download_pdf(video_id):
    """Download podcast summary as PDF"""
    try:
        record = summaries_collection.find_one({'video_id': video_id})

        if not record or 'summary' not in record:
            flash("Summary not found.", "error")
            return redirect(url_for('home_bp.dashboard'))

        pdf_buffer = generate_pdf(video_id, record)

        if not pdf_buffer:
            flash("Error generating PDF.", "error")
            return redirect(url_for('home_bp.dashboard'))

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'podcast_summary_{video_id}.pdf'
        )


    except Exception as e:
        print(f"Download PDF error: {e}")
        flash("Error downloading PDF.", "error")
        return redirect(url_for('home_bp.dashboard'))
