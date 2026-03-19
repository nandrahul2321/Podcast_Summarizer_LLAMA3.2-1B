# PodcastAI — AI-Powered Podcast Summarization and Analysis System

### A Project Report

**Submitted in partial fulfillment of the requirements for the award of the degree of**
**Bachelor of Engineering / Bachelor of Technology in Computer Science and Engineering**

---

| | |
|---|---|
| **Project Title** | PodcastAI — AI-Powered Podcast Summarization and Analysis System |
| **Technology Used** | Python, Flask (+ Flask-Login), MongoDB (PyMongo), LangChain, Ollama (llama3.2:1b), ReportLab, youtube-transcript-api, langdetect, python-dotenv, Web Speech API (browser TTS) |
| **Academic Year** | 2025–2026 |

---

## List of Screenshots

| S.No | Description |
|------|-------------|
| 1 | Landing Page (index.html) — Hero section with feature highlights |
| 2 | User Registration and Login Pages |
| 3 | Dashboard — YouTube URL input and recent history |
| 4 | Results Page — Summary, Key Takeaways, Sentiment & Emotion Analysis |
| 5 | Sentiment and Emotion Analysis Table (Transcript + Summary) |
| 6 | Analysis Accuracy Confidence Bar |
| 7 | Topic Detection and Q&A Section |
| 8 | Interactive AI Chat Page |
| 9 | Generated PDF Report (Podcast Summary Report) |
| 10 | History Page — Previous analysis records |
| 11 | Forgot Password Page |
| 12 | OTP Verification Page |
| 13 | Reset Password Page |
| 14 | Password Reset Email (HTML) |

> **Note:** Each screenshot corresponds to an actual template/view in the project (e.g., `templates/index.html`, `templates/dashboard.html`, `templates/results.html`, etc.), and the PDF report is generated dynamically by `home.py`.

---

## List of Tables

| S.No | Table Title | Chapter |
|------|-------------|---------|
| 1 | Comparison of Existing Podcast Analysis Tools | Chapter 1 |
| 2 | Functional Requirements Specification | Chapter 3 |
| 3 | Software Requirements | Chapter 3 |
| 4 | Hardware Requirements | Chapter 3 |
| 5 | MongoDB Collections and Their Purpose | Chapter 4 |
| 6 | API Endpoints and Their Functions | Chapter 5 |
| 7 | Sentiment and Accuracy Score Format | Chapter 5 |

---

## List of Figures

| S.No | Figure Title | Chapter |
|------|-------------|---------|
| 1 | System Architecture Diagram | Chapter 4 |
| 2 | Data Flow Diagram (Level 0 — Context) | Chapter 4 |
| 3 | Data Flow Diagram (Level 1 — System) | Chapter 4 |
| 4 | Use Case Diagram | Chapter 4 |
| 5 | Class Diagram | Chapter 4 |
| 6 | Sequence Diagram — Podcast Summarization Flow | Chapter 4 |
| 7 | Activity Diagram — User Workflow | Chapter 4 |
| 8 | Background Thread Analysis Pipeline | Chapter 5 |

---

## Abstract

The exponential growth of podcast content on platforms such as YouTube has created a significant challenge for users who wish to extract meaningful information without investing the full duration required to listen to or watch an episode. PodcastAI is a web-based, AI-powered podcast summarization and analysis system designed to address this challenge by automatically transcribing, summarizing, and performing deep analytical processing of YouTube podcast content.

The system accepts a YouTube URL as input, fetches the available video transcript using the YouTube Transcript API, and passes it through a locally hosted Large Language Model (LLM) — specifically Meta's Llama 3.2 (1B parameter variant), served via Ollama — to generate structured summaries and extract key insights. Beyond summarization, PodcastAI performs sentiment and emotion analysis on both the raw transcript and the generated summary, calculates confidence scores for transcription quality and summary accuracy, detects key discussion topics, and auto-generates relevant question-and-answer pairs. Users may also engage in an interactive AI chat session grounded exclusively in the podcast's transcript content.

The system is built on a Flask (Python) web framework, uses MongoDB as the persistent data store, integrates LangChain for prompt engineering and LLM orchestration, and leverages ReportLab for generating polished, downloadable PDF reports. A complete user authentication subsystem — including registration, login, and a secure OTP-based password reset workflow — is implemented using Flask-Login and SMTP email delivery.

PodcastAI demonstrates that even a relatively compact, locally-running language model can deliver practically useful NLP tasks when combined with smart chunking strategies, background threading, and prompt engineering. The project has strong implications for students, researchers, content creators, and professionals who need rapid, intelligent digestion of audio/video content.

---

# Chapter 1: INTRODUCTION

## 1.1 Motivation

In the contemporary digital landscape, podcasts have emerged as one of the most consumed forms of media. Millions of hours of podcast content are published weekly across platforms such as YouTube, Spotify, and Apple Podcasts. While podcasts are rich sources of information covering fields such as technology, science, business, education, and culture, their inherently time-consuming nature presents a barrier to efficient knowledge consumption. A typical podcast episode may run anywhere from thirty minutes to three hours, making it impractical for users to extract key insights in a time-constrained environment.

The advent of Large Language Models (LLMs) has created unprecedented opportunities for automating natural language tasks such as summarization, question answering, sentiment classification, and topic detection. However, most implementations of LLM-based summarization tools rely on cloud-hosted APIs (such as OpenAI's GPT-4 or Anthropic's Claude), which introduce concerns about data privacy, latency, and API costs. The motivation behind PodcastAI is two-fold: (1) to provide a practical, locally-deployable AI summarization system that can process real-world podcast content without relying on proprietary cloud APIs, and (2) to go beyond simple summarization by delivering a comprehensive analytical dashboard that includes sentiment analysis, accuracy estimation, topic detection, and interactive Q&A.

The choice of Meta's Llama 3.2 (1B parameters) as the inference backend, served via Ollama, was deliberate. It makes the system lightweight enough to run on consumer hardware while remaining capable of producing coherent, structured language outputs when guided by carefully engineered prompts.

## 1.2 Need

The need for a system like PodcastAI arises from several practical limitations in the current podcast consumption ecosystem:

- **Time Constraint**: Users do not always have the time to consume full-length podcast episodes. A concise AI-generated summary allows them to decide whether to engage with the full content.
- **Information Density**: Podcasts often contain a mix of valuable insights and conversational filler. Automated summarization filters for only the most relevant content.
- **Lack of Cross-Platform Analysis**: No widely available, privacy-respecting, self-hostable tool currently provides summarization, sentiment analysis, topic detection, and interactive Q&A for podcast content in a unified interface.
- **Accessibility**: Transcripts and summaries make podcast content accessible to hearing-impaired users and to those who prefer reading over listening.
- **Research Utility**: Academics and professionals often need to process large volumes of spoken content for analysis. PodcastAI automates this pipeline end-to-end.
- **PDF Archiving**: The ability to download a professionally formatted PDF report allows users to archive and share podcast insights without requiring re-analysis.

## 1.3 Literature Survey

Several existing tools and research efforts are relevant to the domain addressed by PodcastAI:

**1. OpenAI Whisper + GPT-4 Pipelines**: Many open-source projects have combined OpenAI's Whisper model for audio transcription with GPT-4 for summarization. While effective, these pipelines require API keys, incur per-token costs, and raise data privacy concerns for sensitive content.

**2. YouTube Transcript API**: The `youtube-transcript-api` Python library has been widely used in academic and hobbyist projects to retrieve auto-generated or manually submitted captions from YouTube videos. PodcastAI uses this as the transcript acquisition layer.

**3. LangChain for LLM Orchestration**: LangChain is a well-established framework for building LLM-powered applications. Research papers and industrial implementations have demonstrated its effectiveness in chaining prompts, splitting documents, and managing LLM invocation patterns. PodcastAI employs LangChain's `RecursiveCharacterTextSplitter`, `PromptTemplate`, and `ChatOllama` components.

**4. Ollama for Local LLM Serving**: Ollama is an increasingly popular tool for self-hosting open-source LLMs such as Meta's Llama series, Mistral, and Gemma. Academic projects exploring privacy-preserving AI systems have begun to adopt Ollama as a cost-free, local alternative to cloud APIs.

**5. Sentiment Analysis in NLP**: Classical approaches to sentiment analysis employ tools such as VADER, TextBlob, and BERT-based classifiers. LLM-based sentiment analysis, as implemented in PodcastAI, represents a newer paradigm where the model is prompted to output structured JSON containing both sentiment polarity and emotion classification.

**6. ReportLab for PDF Generation**: ReportLab is a mature Python library for programmatic PDF document generation. Its use in PodcastAI enables the creation of richly formatted, multi-section podcast analysis reports.

**Comparison of Existing Podcast Analysis Tools:**

| Tool / System | Summarization | Sentiment | Chat Q&A | PDF Export | Local / Free |
|---|---|---|---|---|---|
| Podcastle AI | Yes | No | No | No | Partial |
| Snipd | Yes | No | No | No | No |
| ChatGPT (GPT-4) | Yes | Partial | Yes | No | No |
| AssemblyAI | Yes | Yes | No | No | No |
| **PodcastAI (This Project)** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

## 1.4 Organization of Report

This report is organized into six primary chapters as follows:

- **Chapter 1 (Introduction)**: Presents the motivation, need, a survey of existing literature, and the overall organization of this report.
- **Chapter 2 (Proposed System Analysis and Design)**: Defines the problem statement, enumerates the features of the proposed system, scopes its applicability, describes the development methodology, and lists project objectives.
- **Chapter 3 (Specifications)**: Details all functional, non-functional, software, and hardware requirements of the system.
- **Chapter 4 (System Architecture)**: Presents the architectural design, module breakdown, Data Flow Diagrams (DFDs), and UML diagrams (use case, class, sequence, and activity).
- **Chapter 5 (Implementation)**: Describes the implementation of each module with supporting logic and presents the final results of the project.
- **Chapter 6 (Conclusion and Future Scope)**: Summarizes the project's achievements, proposes future enhancements, identifies implementation challenges, and provides closing remarks.
- **References**: Citations for all technologies, frameworks, and research used.

---

# Chapter 2: PROPOSED SYSTEM ANALYSIS AND DESIGN

## 2.1 Problem Statement

Given a public YouTube video URL of a podcast episode, automatically retrieve its transcript, generate a structured and coherent textual summary, perform sentiment and emotion analysis at both transcript and summary levels, estimate the quality of the transcription and summary, detect key discussion topics with associated Q&A pairs, and provide an interactive conversational interface grounded entirely in the podcast's content — all within a secure, multi-user, authenticated web application that also supports downloadable PDF report generation.

The system must achieve this while:
- Operating entirely on locally hosted open-source LLMs (no cloud API dependency).
- Handling transcripts of arbitrary length through intelligent chunking and distributed summarization.
- Persisting all analysis results in a non-relational database for fast retrieval and caching.
- Processing secondary analysis tasks (sentiment, accuracy, topics) asynchronously in background threads so that users receive their primary summary result without delay.

## 2.2 Features

The major features of PodcastAI are:

1. **YouTube Transcript Extraction**: Automatically retrieves captions from YouTube videos in multiple languages using the YouTube Transcript API, with proxy support for geo-restricted content. Supports standard watch URLs, short URLs (youtu.be), YouTube Shorts, embedded, and live stream formats.

2. **Distributed AI Summarization**: Splits long transcripts into manageable chunks using `RecursiveCharacterTextSplitter`, summarizes each chunk independently using Llama 3.2:1b via Ollama, then consolidates the results into a structured final summary comprising a paragraph summary and 10–15 key takeaway bullet points.

3. **Sentiment and Emotion Analysis**: Analyzes both the raw transcript and the generated summary for overall sentiment (Positive / Negative / Neutral) with a numerical confidence score (0–100), and emotion classification (Excited, Serious, Motivational, Sad, Informative, Angry, Neutral).

4. **Analysis Accuracy / Confidence Scoring**: Estimates the quality of transcription (0–100) and the quality of the generated summary (0–100) using LLM-based self-evaluation prompts.

5. **Topic Detection and Q&A Generation**: Extracts up to five key topics discussed in the podcast and generates two relevant questions with answers for each topic, based strictly on the transcript content. Results are generated in the detected transcript language.

6. **Interactive AI Chat (Q&A)**: Users can ask free-form questions about a podcast's content through a dedicated chat interface. The system retrieves the most relevant transcript chunks using keyword-based ranking and generates answers via the LLM, accompanied by a confidence score.

7. **Text-to-Speech Playback**: The results page includes a “Speak” control that uses the browser's Web Speech API to read the generated summary aloud, with playback controls for pause, resume, and stop.

8. **PDF Report Generation**: Generates a polished, professionally formatted PDF report containing the summary, key takeaways, sentiment and emotion table, analysis accuracy bars, and metadata — available as a downloadable file.

8. **User Authentication System**: Full user registration, login, and session management using Flask-Login with Werkzeug password hashing. Supports login via both username and email.

9. **Secure Password Reset (OTP + Token)**: A two-factor password reset flow: the user receives a 6-digit OTP and a unique 64-character hex token via a rich HTML email, validates the OTP on a dedicated page, and sets a new password using the tokenized link. Reset records have a 5-minute TTL enforced at both application and database (MongoDB TTL index) levels.

10. **Analysis History**: Records and displays a user's previously analyzed videos, ordered by most recent first.

11. **Comments System**: Users can post and view comments on any analyzed video.

12. **Caching**: Previously analyzed videos are retrieved from MongoDB rather than re-processed, with a fallback to restart background analysis if it was not completed.

13. **Language Detection**: Automatically detects the language of the transcript and summary using the `langdetect` library, ensuring that Q&A and chat responses are returned in the appropriate language.

## 2.3 Scope

PodcastAI is applicable in the following domains and use cases:

- **Educational Institutions**: Students and educators can use it to quickly extract key information from educational YouTube videos and podcasts.
- **Research and Journalism**: Researchers can process large volumes of interview or discussion content for qualitative analysis.
- **Corporate Learning**: Organizations can use it to analyze training content, recorded webinars, or panel discussions.
- **Personal Productivity**: Individual users can maintain a personal library of analyzed podcasts for quick reference.
- **Accessibility**: Provides text-based access to audio-visual content for users with hearing impairments.
- **Content Creation**: Podcasters and YouTubers can use it to generate show notes or social media summaries automatically.

The current scope is limited to YouTube videos with available transcripts (auto-generated or manually submitted captions). Videos without any captions cannot be processed in the current version.

## 2.4 Methodology

The development of PodcastAI followed an iterative, feature-driven development approach:

1. **Requirements Gathering**: Identified the core NLP tasks (summarization, sentiment, Q&A) and supporting infrastructure requirements (authentication, database, PDF, email).
2. **Technology Selection**: Selected Flask for its lightweight web framework characteristics, MongoDB for schema-flexible document storage, LangChain + Ollama for LLM orchestration, and ReportLab for PDF generation.
3. **Modular Design**: Separated concerns into discrete modules — `app.py` for authentication routes, `home.py` for the main feature Blueprint, `db.py` for database configuration, and `services/` for reusable service classes.
4. **Iterative Feature Implementation**: Implemented and tested features in priority order: transcript extraction → summarization → results display → sentiment analysis → accuracy scoring → topic Q&A → chat → PDF → authentication → password reset.
5. **Background Threading**: Introduced Python `threading.Thread` (daemon threads) to decouple the time-critical summary generation from secondary analyses (sentiment, accuracy, topics), improving perceived performance.
6. **Testing and Refinement**: Tested with a diverse set of YouTube podcast URLs across different lengths, languages, and content types. Prompt templates were refined iteratively to improve output structure consistency.

## 2.5 Limitations & Assumptions

While PodcastAI is designed to be a fully functional self-hosted system, it operates within a set of practical constraints:

- **Transcript availability**: The system requires an available YouTube transcript (auto-generated or manually uploaded). Videos without captions cannot be processed.
- **No metadata retrieval**: The current implementation does not use the YouTube Data API to fetch video metadata (title, channel, duration). The UI will only display those fields if they are present in the stored record.
- **LLM output variability**: The system relies on structured output from a locally running LLM. Because model responses can vary, parsing and scoring routines include fallback defaults to ensure stability.
- **Keyword-based chat retrieval**: Chat context is selected using keyword matching rather than semantic embeddings, which may miss relevant transcript passages when phrasing differs.

## 2.6 Objectives

The primary objectives of the PodcastAI project are:

1. To design and implement an end-to-end web application that can automatically transcribe and summarize YouTube podcast content using a locally hosted LLM.
2. To perform multi-dimensional NLP analysis — including sentiment analysis, emotion detection, and confidence scoring — on podcast transcripts.
3. To implement an intelligent topic detection and Q&A generation pipeline based on transcript content.
4. To build an interactive, transcript-grounded chatbot interface for podcast-specific question answering.
5. To generate downloadable, professionally formatted PDF reports summarizing all analysis results.
6. To implement a secure, multi-user authentication system with OTP-based password recovery.
7. To ensure system scalability and responsiveness through asynchronous background processing and database-level caching.
8. To demonstrate the viability of a compact, locally-run open-source LLM (Llama 3.2:1b) for practical NLP tasks in a production-like web application.

---

# Chapter 3: SPECIFICATIONS

## 3.1 Requirements Specification

### 3.1.1 Performance Requirements

- **Summarization Latency**: For a typical 1-hour podcast transcript (approximately 8,000–15,000 words), the system should generate a structured summary within 60–180 seconds on a machine equipped with at least 8 GB RAM, using the Llama 3.2:1b model via Ollama. The user is redirected to results immediately upon summary completion, while secondary analyses proceed in a background thread.
- **Concurrent Users**: The Flask development server supports single-threaded request handling. For production deployment, a WSGI server such as Gunicorn (with multiple worker processes) should be used to handle concurrent users. Database reads and writes to MongoDB are synchronous but fast due to indexed collections.
- **Background Analysis**: Sentiment analysis, accuracy scoring, and topic detection are executed sequentially within a single daemon thread. The combined processing time for these three tasks is typically 30–90 seconds for standard transcripts, during which the user may interact with the page.
- **Response Time for Chat**: Chat responses should be returned within 10–30 seconds depending on model load and context size.
- **PDF Generation**: PDF reports should be generated and streamed to the client within 2–5 seconds, since all data retrieval is from MongoDB and processing is via ReportLab (no LLM inference required).
- **Caching**: Previously analyzed videos are retrieved from MongoDB without re-invoking the LLM, resulting in near-instantaneous results page display.

### 3.1.2 Functional and Operational Requirements

| Requirement ID | Description |
|---|---|
| FR-01 | The system shall accept a YouTube video URL as input from an authenticated user. |
| FR-02 | The system shall extract the video transcript using the YouTube Transcript API. |
| FR-03 | The system shall support multiple YouTube URL formats (watch, short, embed, Shorts, live). |
| FR-04 | The system shall split long transcripts into chunks and summarize each chunk using an LLM. |
| FR-05 | The system shall consolidate chunk summaries into a structured final summary (paragraph + bullet points). |
| FR-06 | The system shall analyze sentiment of the transcript and summary independently. |
| FR-07 | The system shall classify the dominant emotion of the transcript/summary. |
| FR-08 | The system shall calculate transcription quality and summary quality confidence scores (0–100). |
| FR-09 | The system shall detect up to five key topics and generate two Q&A pairs per topic. |
| FR-10 | The system shall display an analysis progress status on the results page via AJAX polling. |
| FR-11 | The system shall allow authenticated users to ask questions about a podcast via a chat interface. |
| FR-12 | The system shall generate downloadable PDF reports of analysis results. |
| FR-13 | The system shall authenticate users through registration, login, and session management. |
| FR-14 | The system shall support password reset via a 6-digit OTP and tokenized email link. |
| FR-15 | The system shall record a user's analysis history and display it on a history page. |
| FR-16 | The system shall allow users to post and view comments on any analyzed video. |
| FR-17 | The system shall detect the language of the transcript and generate Q&A and chat responses accordingly. |
| FR-18 | The system shall support optional proxy configuration for geo-restricted transcripts. |

## 3.2 Software and Hardware Requirements

### 3.2.1 Software Requirements

| Component | Specification |
|---|---|
| **Operating System** | Windows 10/11, macOS 12+, or Ubuntu 20.04+ |
| **Python Version** | Python 3.10 or higher |
| **Web Framework** | Flask 3.x |
| **Database** | MongoDB 6.x (Community Edition), running locally or via MongoDB Atlas |
| **MongoDB Driver** | PyMongo 4.x |
| **LLM Runtime** | Ollama (latest) with `llama3.2:1b` model pulled. Requires `ollama serve` to be running during operation. |
| **LLM Orchestration** | LangChain (`langchain-core`, `langchain-ollama`, `langchain-text-splitters`) |
| **Transcript API** | youtube-transcript-api 0.6.x |
| **PDF Generation** | ReportLab 4.x |
| **Authentication** | Flask-Login 0.6.x, Werkzeug 3.x |
| **Language Detection** | langdetect 1.0.9 |
| **Environment Management** | python-dotenv 1.x |
| **Email** | Python standard library (`smtplib`, `email.mime`) |
| **Concurrency / Async** | Python `threading` (background worker) + `asyncio` (LLM calls) |
| **IDE** | Visual Studio Code (recommended) |
| **Browser** | Chrome, Firefox, or Edge (latest) with Web Speech API support |

### 3.2.2 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **Processor** | Intel Core i5 / AMD Ryzen 5 (4 cores) | Intel Core i7 / AMD Ryzen 7 (8 cores) |
| **RAM** | 8 GB | 16 GB or more |
| **Storage** | 5 GB free (for Ollama + model weights) | 20 GB SSD (for model cache and MongoDB data) |
| **GPU** | Not required (CPU inference) | NVIDIA GPU with CUDA (for faster inference) |
| **Network** | Internet connection required for YouTube transcript fetching | Stable broadband |
| **OS Architecture** | x86-64 | x86-64 or ARM64 (Apple Silicon) |

> **Note**: The Llama 3.2:1b model (quantized GGUF format via Ollama) requires approximately 1.2–1.5 GB of RAM for model weights. CPU-based inference is feasible but slower than GPU-accelerated inference.

## 3.3 Functional Requirements

The following describes each major function/module of the system:

**1. User Authentication Module**
- Allows new users to register with a unique username, email, and password (minimum 6 characters). Passwords are hashed using Werkzeug's `generate_password_hash` (PBKDF2/SHA-256). Duplicate username and email checks are enforced before account creation.
- Login supports authentication via either username or email, with `check_password_hash` for password verification. Sessions are managed by Flask-Login with `session_protection = "strong"`.

**2. Transcript Extraction Module**
- Accepts a YouTube URL, extracts the 11-character video ID using regex patterns, and fetches available transcripts via `YouTubeTranscriptApi`. Preferred languages can be configured via environment variables. Manual and auto-generated captions are distinguished and prioritized. Optional translation to a target language is supported if the transcript is translatable.

**3. Summarization Module**
- Splits the full transcript into chunks of 3,000 characters with 200-character overlap using `RecursiveCharacterTextSplitter`. Each chunk is summarized asynchronously using `asyncio.gather`. The chunk summaries are then combined and passed to the LLM with a final prompt instructing it to produce a structured output containing a paragraph summary and 10–15 key takeaways.

**4. Background Analysis Module**
- Executed in a daemon thread after the summary is saved. Sequentially performs: (1) sentiment and emotion analysis on transcript and summary, (2) transcription and summary confidence scoring, and (3) topic detection and Q&A generation. Updates the MongoDB record progressively after each step. The frontend polls a `/analysis-status/<video_id>` endpoint every few seconds to fetch and render the results as they become available.

**5. Chat Module**
- The `ChatService` class splits the transcript into 2,000-character chunks and scores each chunk against the user's query by keyword overlap, selecting the top-4 most relevant chunks. The selected context is passed to the LLM with a strictly constrained prompt ensuring answers are derived only from the provided transcript. A `CONFIDENCE: [score]` line is parsed from the model's response to provide a trust indicator for each answer.

**6. PDF Generation Module**
- Uses ReportLab's `SimpleDocTemplate` and `Platypus` layout engine to create a multi-section PDF report. Sections include: a header with branding, video metadata, summary narrative, key takeaway bullet points, sentiment & emotion analysis table (color-coded by sentiment), analysis accuracy table with progress bars, and a footer. The PDF is generated into an in-memory `BytesIO` buffer and streamed to the user.

**7. Password Reset Module**
- Generates a 6-digit OTP using `secrets.randbelow` and a 64-character token using `secrets.token_hex`. Both are stored in the `password_resets` MongoDB collection with a 5-minute expiry timestamp. A MongoDB TTL index automatically deletes expired records. The user verifies the OTP on a dedicated page; upon success, they are redirected to a tokenized reset URL. The password update erases the reset record and sends a confirmation email.

## 3.4 Non-Functional Requirements

**Security**
- Passwords are never stored in plaintext; Werkzeug hashing (PBKDF2/SHA-256) is applied.
- OTP and reset tokens are generated using Python's `secrets` module (cryptographically secure random number generation).
- Flask-Login's `session_protection = "strong"` mode invalidates sessions if the client signature changes.
- Email enumeration is prevented by returning a generic message for unregistered emails in the password reset flow.
- MongoDB reset records are cleaned up immediately after use and via TTL index.

**Scalability**
- Background threading ensures that LLM inference for secondary tasks does not block the web server.
- MongoDB's indexed collections ensure fast document retrieval even as the dataset grows.
- The architecture can be scaled horizontally by deploying multiple Flask worker processes (Gunicorn) and replacing local Ollama with a shared inference server.

**Reliability**
- Each LLM call is wrapped in `try/except` blocks with sensible fallback values (e.g., default sentiment of `Neutral` with score `50`).
- The analysis pipeline is designed to mark progress at each step; if the background thread crashes, the `analysis_progress` field is set to `complete` to prevent infinite frontend polling.

**Usability**
- The web interface provides real-time feedback through progress status messages while background analysis is running.
- Flash messages provide contextual feedback for all user actions (login errors, submission success, analysis failure, etc.).
- The results page renders progressively — the summary is immediately visible while sentiment, accuracy, and topics load asynchronously.

**Maintainability**
- The codebase is modularly organized: `app.py` (auth), `home.py` (feature Blueprint), `db.py` (database), `services/chat_service.py` (chat), `services/output_cleaner.py` (text normalization).
- Environment-specific configuration (SMTP credentials, Ollama URL, model name, proxy settings) is externalized to a `.env` file via `python-dotenv`.

---

# Chapter 4: SYSTEM ARCHITECTURE

## 4.1 Proposed System Architecture

PodcastAI follows a **three-tier web application architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   PRESENTATION TIER (Browser)                    │
│   HTML Templates (Jinja2)  |  CSS (style.css)  |  JS (script.js) │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP Requests / AJAX Polling
┌────────────────────────────▼────────────────────────────────────┐
│                   APPLICATION TIER (Flask)                       │
│  app.py (Auth Routes)  |  home.py (Blueprint)  |  services/      │
│  Background Threads    |  LangChain + Ollama    |  Email (SMTP)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ PyMongo Queries
┌────────────────────────────▼────────────────────────────────────┐
│                   DATA TIER (MongoDB)                            │
│  users | summaries | history | chat_history | comments          │
│  password_resets  (TTL-indexed)                                  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │ HTTP (localhost:11434)
┌────────────────────────────┴────────────────────────────────────┐
│                   OLLAMA LLM SERVER (local)                      │
│              Model: llama3.2:1b (GGUF quantized)                 │
└─────────────────────────────────────────────────────────────────┘
```

The application layer is further divided into two Flask route groups:
- **`app.py`**: Handles authentication-related routes (`/`, `/signup`, `/login`, `/logout`, `/forgot-password`, `/verify-otp`, `/reset-password`).
- **`home.py` (Blueprint `home_bp`)**: Handles all feature-related routes (`/dashboard`, `/results/<video_id>`, `/chat`, `/chat-page/<video_id>`, `/download-pdf/<video_id>`, `/history`, `/comments`, `/analysis-status/<video_id>`).

## 4.2 Modules in the System

### Module 1: Authentication Module (`app.py`)
Manages user identity and security. Provides routes for signup, login, logout, and the three-step password reset flow. Integrates Flask-Login for session persistence.

### Module 2: Database Configuration Module (`db.py`)
Centralizes all MongoDB collection references and index definitions. Creates performance-optimized indexes (ascending, compound, and TTL) for all collections at application startup.

### Module 3: Core Feature Module (`home.py`)
The largest module, implementing all primary functionality via a Flask Blueprint. Contains helper functions, async coroutines, background thread functions, and all feature routes.

### Module 4: Chat Service (`services/chat_service.py`)
Encapsulates the logic for relevance-ranked transcript chunk retrieval and LLM-based Q&A with confidence scoring in the `ChatService` class.

### Module 5: Output Cleaner (`services/output_cleaner.py`)
Provides utilities (`clean_text`, `parse_summary_sections`, `build_clean_response`) to normalize LLM output — removing markdown artifacts, parsing structured sections, and building clean response dictionaries for the frontend and PDF generator.

**MongoDB Collections:**

| Collection | Purpose |
|---|---|
| `users` | Stores user accounts (username, email, hashed password) |
| `summaries` | Caches video transcripts, summaries, sentiment, accuracy, and topics per `video_id` |
| `history` | Records each user's view history (user_id, video_id, last viewed timestamp) |
| `chat_history` | Stores all Q&A chat exchanges per user and video |
| `comments` | Stores user comments on analyzed videos |
| `password_resets` | Stores OTP, token, expiry, and verification state for password resets (TTL auto-deleted) |

### 4.2.1 Data Flow Diagram (DFD)

**Level 0 — Context Diagram:**

```
                    ┌─────────────────────────────┐
                    │                             │
YouTube URL ───────►│       PodcastAI System      │──────► Summary, Sentiment,
User Queries ──────►│                             │         Topics, PDF, Chat
                    │                             │
                    └─────────────────────────────┘
                                  │
                                  ▼
                              YouTube / Ollama / MongoDB / SMTP
```

**Level 1 — System Diagram:**

```
User
 │
 ├──[Login/Register]──► (1) Authentication Module ──► MongoDB (users, password_resets)
 │                                                         │
 │                                                  SMTP Email Server
 │
 ├──[Submit URL]──► (2) URL Parsing & Transcript Extraction ──► YouTube Transcript API
 │                          │
 │                          ▼
 │                  (3) Distributed Summarization ──► Ollama (llama3.2:1b)
 │                          │
 │                          ▼
 │                  MongoDB (summaries – summary saved, progress = "summary_done")
 │                          │
 │             ┌────────────┘  [Background Thread]
 │             │
 │             ├──► (4) Sentiment & Emotion Analysis ──► Ollama
 │             ├──► (5) Accuracy / Confidence Scoring ──► Ollama
 │             └──► (6) Topic Detection & Q&A ──► Ollama
 │                          │
 │                  MongoDB (summaries – all fields updated, progress = "complete")
 │
 ├──[Poll /analysis-status]──► (7) Status API ──► MongoDB ──► JSON response
 │
 ├──[Ask Question]──► (8) Chat Module ──► ChatService ──► Ollama ──► MongoDB (chat_history)
 │
 └──[Download PDF]──► (9) PDF Generator ──► ReportLab ──► BytesIO stream ──► User
```

## 4.3 UML Diagrams

### 4.3.1 Use Case Diagram

**Actors**: Guest User, Authenticated User, System (Background Thread), Ollama LLM

```
Guest User:
  - View Landing Page
  - Register Account
  - Login
  - Request Password Reset (OTP flow)

Authenticated User (extends Guest):
  - Submit YouTube URL for Analysis
  - View Summary & Key Takeaways
  - View Sentiment & Emotion Analysis
  - View Analysis Accuracy Scores
  - View Topic Detection & Q&A
  - Download PDF Report
  - Interact via AI Chat
  - View Analysis History
  - Post / View Comments
  - Logout

System (Background Thread):
  - Perform Sentiment Analysis <<include>>
  - Perform Accuracy Scoring <<include>>
  - Perform Topic & Q&A Detection <<include>>

Ollama LLM (External System):
  - Receive Prompt & Return Completion <<extend>>
```

### 4.3.2 Class Diagram

**Key classes and their relationships:**

```
Flask Application (app)
  ├── LoginManager (flask_login)
  ├── User : UserMixin
  │     + id: str
  │     + username: str
  │     + password_hash: str
  │     + get_id(): str
  │
  └── Blueprint: home_bp (home.py)
        ├── ChatService (services/chat_service.py)
        │     - splitter: RecursiveCharacterTextSplitter
        │     + _get_relevant_chunks(full_text, query, max_chunks): str
        │     + get_chat_response(full_text, summary, user_query, language): dict
        │
        └── Functions (top-level, home.py):
              + get_video_id(url): str
              + fetch_available_captions(video_url): dict
              + summarize_chunk(chunk_text, index): coroutine
              + generate_distributed_summary_async(text): coroutine
              + analyze_sentiment_emotion_async(text, text_type): coroutine
              + calculate_accuracy_scores_async(full_text, summary): coroutine
              + generate_topics_qa(full_text, language): list
              + generate_pdf(video_id, record): BytesIO
              + _run_background_analysis(video_id, full_text, summary): None

MongoDB Collections (db.py):
  + users_collection
  + summaries_collection
  + history_collection
  + chat_history_collection
  + comments_collection
  + password_resets_collection

OutputCleaner (services/output_cleaner.py):
  + clean_text(text): str
  + parse_summary_sections(raw_text): dict
  + build_clean_response(summary_text, sentiment_data, language): dict
```

### 4.3.3 Sequence Diagram — Podcast Summarization Flow

```
User        Browser        Flask(home_bp)     YouTube API     Ollama LLM     MongoDB
 │              │                │                 │               │              │
 │─Submit URL──►│                │                 │               │              │
 │              │─POST /dash────►│                 │               │              │
 │              │                │──get_video_id───│               │              │
 │              │                │──fetch_captions►│               │              │
 │              │                │◄────transcript──│               │              │
 │              │                │──split chunks   │               │              │
 │              │                │──invoke LLM────────────────────►│              │
 │              │                │◄───chunk summaries──────────────│              │
 │              │                │──final LLM call────────────────►│              │
 │              │                │◄───structured summary───────────│              │
 │              │                │──insert {summary}───────────────────────────►│ │
 │              │                │──start thread (background)      │              │
 │              │◄──redirect to /results/video_id─│               │              │
 │              │                │   [background]                  │              │
 │              │                │──analyze_sentiment─────────────►│              │
 │              │                │◄──sentiment JSON────────────────│              │
 │              │                │──update DB──────────────────────────────────► │
 │              │                │──calc_accuracy─────────────────►│              │
 │              │                │◄──scores────────────────────────│              │
 │              │                │──update DB──────────────────────────────────► │
 │              │                │──generate_topics_qa────────────►│              │
 │              │                │◄──topics JSON───────────────────│              │
 │              │                │──update DB (progress=complete)────────────────►│
 │              │─Poll /status──►│──query MongoDB──────────────────────────────► │
 │              │◄──JSON data────│◄──record──────────────────────────────────────│
 │◄─render UI───│                │                 │               │              │
```

### 4.3.4 Activity Diagram — User Workflow

```
[Start] ──► Visit Landing Page
               │
          [Registered?] ──No──► Register ──► Login
               │ Yes
               ▼
          Dashboard (Enter YouTube URL)
               │
          [URL Valid?] ──No──► Flash Error ──► Dashboard
               │ Yes
          [Cached in DB?] ──Yes──► Redirect to Results Page
               │ No
               ▼
          Fetch Transcript
               │
          [Transcript Available?] ──No──► Flash Error ──► Dashboard
               │ Yes
               ▼
          Generate Summary (via LLM)
               │
          [Summary Generated?] ──No──► Flash Error ──► Dashboard
               │ Yes
               ▼
          Save Summary to DB
          Start Background Thread ──────────────────────────────────────────►
               │                                                              │
          Redirect to Results Page                              Sentiment Analysis
               │                                                              │
          Display Summary                                       Save to DB
               │                                                              │
          AJAX Poll /analysis-status ◄──── Analysis Progress ─── Accuracy Scoring
               │                                                              │
          Render Sentiment, Accuracy, Topics as data arrives    Save to DB
               │                                                              │
          [User Action?]                                        Topic Q&A Gen
          ├──► Ask Question in Chat ──► ChatService ──► LLM ──► Display Answer │
          ├──► Download PDF ──► ReportLab ──► PDF File          Save to DB ◄──┘
          ├──► View History
          ├──► Post Comment
          └──► Logout

[End]
```


---

# Chapter 5: IMPLEMENTATION

## 5.1 Modules

### 5.1.1 Authentication Module Implementation

The authentication module is implemented in `app.py` using Flask routes and Flask-Login. Upon user registration, the system validates input fields (email format, username length >= 4, password length >= 6) and checks MongoDB for existing accounts before inserting a new document with a hashed password. The `User` class extends `UserMixin` and wraps a MongoDB user document; the `load_user` callback reconstructs the `User` object from the session on each request.

Login supports dual-mode authentication: if the submitted identifier contains `@`, it queries by email field; otherwise by username. This allows users to use either credential to log in.

```python
# Dual-mode login query (from app.py)
query = {'username': identifier}
if '@' in identifier:
    query = {'email': identifier.lower()}
user_data = users_collection.find_one(query)
```

### 5.1.2 Transcript Extraction Implementation

The `get_video_id` function uses a set of regex patterns to extract the 11-character YouTube video identifier from any supported URL format (watch?v=, youtu.be/, /shorts/, /embed/, /live/). The `fetch_available_captions` function instantiates `YouTubeTranscriptApi`, optionally configured with a Webshare or generic proxy, and attempts to retrieve a transcript in the user-configured preferred language order. Manual captions are preferred over auto-generated ones. The selected transcript is optionally translated to a target language, then formatted as plain text via `TextFormatter`.

### 5.1.3 Distributed Summarization Implementation

The summarization pipeline implements a two-stage Map-Reduce pattern:

**Stage 1 (Map)**: Each transcript chunk (3,000 characters with 200-character overlap) is independently summarized into 2-3 bullet points by the LLM, invoked concurrently using `asyncio.gather`. Failed chunk summarizations are skipped gracefully.

**Stage 2 (Reduce)**: Successful chunk summaries are joined and passed to the LLM with a structured final prompt requesting a `### Summary` paragraph and a `### Key Takeaways` section of 10-15 bullet points. The LangChain `PromptTemplate` is used to inject the combined text.

### 5.1.4 Sentiment and Emotion Analysis Implementation

The `analyze_sentiment_emotion_async` function constructs a prompt instructing the LLM to return ONLY a valid JSON object with four fields: `sentiment`, `sentiment_score`, `emotion`, and `emotion_confidence`. The response text is parsed using `re.search(r'{.*}', response_text, re.DOTALL)`. Score bounds are enforced within [0, 100]. Default fallback values (Neutral, score 50) are returned if parsing fails.

Both the raw transcript (first 5,000 characters) and the generated summary are analyzed independently, producing separate sentiment records in `transcript_sentiment` and `summary_sentiment` fields in MongoDB.

### 5.1.5 Accuracy Scoring Implementation

`calculate_accuracy_scores_async` sends two separate LLM prompts — one to rate transcription quality (grammar, punctuation, completeness) and one to rate summary fidelity (completeness, accuracy, relevance). Each prompt requests a single integer (0-100). The first valid numeric sequence (up to 3 digits) is extracted from the response with a fallback of 50 if parsing yields zero on non-empty content.

### 5.1.6 Topic Detection and Q&A Implementation

`generate_topics_qa` sends the first 5,000 characters of the transcript with a prompt requesting a JSON array of exactly 5 topic objects, each with a `"topic"` name and a `"questions"` array of 2 objects `{"q": "...", "a": "..."}`. The JSON array is extracted using regex and validated structurally before saving. Results are generated in the auto-detected transcript language.

### 5.1.7 Background Analysis Pipeline

`_run_background_analysis` is executed in a Python daemon thread and updates the `analysis_progress` field in MongoDB at each step:

| Phase | `analysis_progress` | Data Saved |
|---|---|---|
| Summary saved (before thread) | `summary_done` | `summary`, `full_text`, `language` |
| After sentiment analysis | `sentiment_done` | `transcript_sentiment`, `summary_sentiment` |
| After accuracy scoring | `accuracy_done` | `transcription_confidence`, `summary_confidence` |
| After topic Q&A generation | `complete` | `topics` |

The `/analysis-status/<video_id>` endpoint is polled by the frontend via AJAX; it returns the current progress and all completed data sections, enabling progressive rendering of results without page reload.

### 5.1.8 Chat Module Implementation

`ChatService.get_chat_response` implements keyword-based Retrieval-Augmented Generation (RAG):

1. Query keywords (words with length > 2) are extracted.
2. Each transcript chunk receives a relevance score (count of matching keywords).
3. Top-4 highest-scoring chunks are re-sorted by original position for coherent context.
4. The LLM is invoked with a strictly constrained prompt — answers must come ONLY from the provided transcript excerpts.
5. The LLM appends `CONFIDENCE: [0-100]` to its response, which is parsed via regex and stripped from the displayed answer.

Chat exchanges are persisted to `chat_history_collection` with `user_id`, `video_id`, `question`, `answer`, `confidence_score`, `language`, and IST timestamp.

### 5.1.9 PDF Generation Implementation

`generate_pdf` uses ReportLab's Platypus layout engine to build a structured in-memory PDF. A custom color palette (brand blue, green/red/grey for sentiment, confidence-coded colors) is defined. Key layout elements:

- **Accent Bars**: Thin colored horizontal rules using `Table` with `LINEABOVE` style.
- **Key Takeaways**: Bullet paragraphs with hanging indent (`leftIndent=20`, `firstLineIndent=-10`).
- **Sentiment Table**: Color-coded cells (green for Positive, red for Negative, grey for Neutral).
- **Accuracy Table**: ASCII-art progress bars (`█░`) inside confidence-colored rows.

The completed document is built into a `BytesIO` buffer via `doc.build(elements)` and streamed to the client with Flask's `send_file`.

### 5.1.10 Password Reset Implementation

**`/forgot-password`**: Validates email, generates a 6-digit OTP (`secrets.randbelow(900000) + 100000`) and 64-character token (`secrets.token_hex(32)`). Stores the reset record in MongoDB with a UTC expiry 5 minutes ahead. Dispatches a rich HTML+plain-text email via SMTP with STARTTLS. Stores only the email in the Flask session.

**`/verify-otp`**: Reads the email from session, finds the unverified reset record, checks UTC expiry, compares the submitted OTP, and marks `verified=True` on success. Redirects to `/reset-password?token=<token>`.

**`/reset-password`**: Finds the record by token, validates expiry, hashes and saves the new password, deletes the reset record, and sends a success notification.

A MongoDB TTL index (`expireAfterSeconds=0` on `expires_at`) ensures automatic server-side garbage collection of expired records.

### 5.1.11 Output Cleaner Implementation

`clean_text` normalizes LLM output by removing markdown artifacts via sequential regex substitutions and normalizing bullet prefixes to `•`. `parse_summary_sections` uses multilingual regex patterns to split text at recognized section headings (English and Hindi variants), returning a structured dict with `summary` and `keypoints` fields used by both the frontend and the PDF generator.

## 5.2 Result of Project

**API Endpoints Summary:**

| Route | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | No | Landing page |
| `/signup` | GET, POST | No | User registration |
| `/login` | GET, POST | No | User login |
| `/logout` | GET | Yes | User logout |
| `/forgot-password` | GET, POST | No | Request OTP reset |
| `/verify-otp` | GET, POST | No | Verify 6-digit OTP |
| `/reset-password` | GET, POST | No | Set new password via token |
| `/dashboard` | GET, POST | Yes | Main dashboard; submit URL |
| `/results/<video_id>` | GET | Yes | View analysis results |
| `/analysis-status/<video_id>` | GET | Yes | AJAX polling endpoint |
| `/chat-page/<video_id>` | GET | Yes | Interactive chat page |
| `/chat` | POST | Yes | AI chat response |
| `/chat-history/<video_id>` | GET | Yes | Fetch chat history |
| `/download-pdf/<video_id>` | GET | Yes | Download PDF report |
| `/history` | GET | Yes | View analysis history |
| `/comments/<video_id>` | GET | Yes | Fetch video comments |
| `/comments` | POST | Yes | Post a comment |

**Sentiment and Accuracy Output Format:**

| Field | Type | Range | Description |
|---|---|---|---|
| `sentiment` | String | Positive, Negative, Neutral | Overall polarity |
| `sentiment_score` | Integer | 0-100 | Sentiment confidence |
| `emotion` | String | Excited, Serious, Motivational, Sad, Informative, Angry, Neutral | Dominant emotion |
| `emotion_confidence` | Integer | 0-100 | Emotion confidence |
| `transcription_confidence` | Integer | 0-100 | Transcript quality estimate |
| `summary_confidence` | Integer | 0-100 | Summary fidelity estimate |

**End-to-End Workflow:**

1. Authenticated user pastes a YouTube URL on the Dashboard and submits.
2. Server extracts video ID, fetches transcript, splits into chunks, generates distributed summary.
3. Summary saved to MongoDB (`analysis_progress = "summary_done"`); user immediately redirected to Results page.
4. Background thread begins secondary analysis pipeline (sentiment → accuracy → topics).
5. Results page JavaScript polls `/analysis-status/<video_id>` and dynamically renders sections as they complete.
6. User may download PDF, open Chat, view/post comments, or browse history.
7. Chat queries are processed through keyword-ranked chunk retrieval and LLM-based answer generation with confidence scoring.
8. All interactions are persisted to MongoDB.

---

# Chapter 6: CONCLUSION AND FUTURE SCOPE

## 6.1 Conclusion

PodcastAI successfully demonstrates the design and implementation of a fully functional, self-hosted, AI-powered podcast analysis platform. The system achieves its primary objective of enabling users to extract structured, multi-dimensional insights from YouTube podcast content without relying on commercial cloud AI APIs.

By integrating a locally running Large Language Model (Meta Llama 3.2:1b via Ollama) with a production-grade web stack (Flask, MongoDB, LangChain), the system delivers summarization, sentiment and emotion analysis, quality confidence scoring, topic-based Q&A, interactive transcript-grounded chat, and polished PDF report generation — all within a secure, authenticated multi-user web environment.

The use of background threading for secondary NLP tasks delivers superior perceived performance: users receive their summary within seconds while more intensive analyses proceed asynchronously. The MongoDB caching layer ensures previously analyzed videos are served instantaneously on re-access.

The security design reflects production awareness: OTP and token generation use Python's cryptographic `secrets` module, MongoDB TTL indexes auto-clean expired reset records, and Flask-Login's strong session protection guards user accounts.

Overall, PodcastAI validates that a compact, quantized open-source LLM is sufficient for practically useful NLP tasks when combined with prompt engineering, intelligent chunking, and structured output parsing — demonstrating a compelling model for privacy-preserving, cost-free intelligent web applications.

## 6.2 Future Scope

1. **Whisper-Based Audio Transcription**: Integrate self-hosted OpenAI Whisper for videos without existing captions.
2. **Multi-Platform Support**: Extend to Spotify, Apple Podcasts, Vimeo, and direct audio file uploads.
3. **Larger LLM Backends**: Allow model selection (Llama 3.1:8b, Mistral-7B) or optional cloud API integration.
4. **Vector Database RAG**: Replace keyword-based chunk retrieval with vector similarity search using ChromaDB/Qdrant and Ollama embeddings.
5. **Speaker Diarization**: Identify and label different speakers for speaker-specific analysis.
6. **Episode Comparison**: Cross-compare summaries, sentiments, and topics across multiple episodes.
7. **Streaming LLM Responses**: Token-level streaming for chat to reduce perceived latency.
8. **Batch Processing**: Submit multiple URLs or schedule new-episode analysis for followed podcasts.
9. **Social Sharing**: Generate unique public URLs for sharing analysis results.
10. **Mobile App**: React Native or Flutter companion app consuming the PodcastAI REST API.
11. **Multilingual UI**: Localize the web interface for non-English users.
12. **Feedback Loop**: User ratings on summary quality feed into iterative prompt template improvement.

## 6.3 Challenges and Solutions in Future Implementations

| Challenge | Description | Proposed Solution |
|---|---|---|
| **LLM Output Inconsistency** | Compact LLMs may deviate from JSON schema. | Use LangChain's `PydanticOutputParser` and retry logic with fallback defaults. |
| **Long Transcript Handling** | 3+ hour podcasts may exceed context even after chunking. | Implement hierarchical multi-level Map-Reduce summarization. |
| **YouTube API Restrictions** | YouTube may restrict automated transcript access. | Proxy rotation support; fall back to Whisper audio transcription. |
| **Concurrency Under Load** | Multiple users overloading a single Ollama instance. | Load-balance across multiple Ollama instances or use a GPU inference server. |
| **Chat Hallucination** | LLM may generate responses not grounded in the transcript. | Adopt vector-embedding RAG; add hallucination detection heuristics. |
| **Multilingual Prompt Engineering** | Non-English content requires localized prompts and output parsers. | Language-conditional prompt templates; extend `output_cleaner` for target-language section headers. |

## 6.4 Final Thoughts

PodcastAI represents a purposeful synthesis of modern AI tooling and full-stack web development. It demonstrates that the availability of high-quality open-source LLMs combined with orchestration frameworks like LangChain and lightweight serving tools like Ollama has lowered the barrier to building sophisticated NLP applications to the point of academic projects running entirely on commodity hardware.

The system addresses a genuine user need — efficient consumption of long-form audio content — while serving as a blueprint for privacy-preserving, cost-free AI applications requiring content analysis, question answering, and intelligent report generation.

As larger and more capable open-source LLMs continue to emerge, systems like PodcastAI will grow proportionally more powerful without any increase in infrastructure cost, validating the local AI paradigm for production-grade intelligent applications.

---

# REFERENCES

1. **Meta AI** — Llama 3.2 Model Family. *Meta AI Research*, 2024. https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/

2. **Ollama** — Get up and running with large language models locally. *Ollama*, 2024. https://ollama.com/

3. **LangChain Documentation** — Building applications with LLMs through composability. *LangChain*, 2024. https://docs.langchain.com/

4. **Flask Documentation** — Web Development, one drop at a time. *Pallets Projects*, 2024. https://flask.palletsprojects.com/

5. **Flask-Login Documentation** — User session management for Flask. *Max Countryman*, 2024. https://flask-login.readthedocs.io/

6. **PyMongo Documentation** — Python Driver for MongoDB. *MongoDB Inc.*, 2024. https://pymongo.readthedocs.io/

7. **MongoDB Documentation** — The Developer Data Platform. *MongoDB Inc.*, 2024. https://www.mongodb.com/docs/

8. **YouTube Transcript API** — Python API to retrieve transcript/subtitles for YouTube videos. *Jonas Depoix*, 2024. https://github.com/jdepoix/youtube-transcript-api

9. **ReportLab Documentation** — PDF generation library for Python. *ReportLab Inc.*, 2024. https://www.reportlab.com/docs/

10. **LangChain Text Splitters** — RecursiveCharacterTextSplitter. *LangChain*, 2024. https://python.langchain.com/docs/how_to/recursive_text_splitter/

11. **Werkzeug Security** — Password hashing utilities. *Pallets Projects*, 2024. https://werkzeug.palletsprojects.com/

12. **langdetect** — Language detection library ported from Google's language-detection. *Michal Mimino Danilak*, 2024. https://pypi.org/project/langdetect/

13. **Python Secrets Module** — Generate cryptographically strong random numbers. *Python Software Foundation*, 2024. https://docs.python.org/3/library/secrets.html

14. **Python asyncio Module** — Asynchronous I/O framework. *Python Software Foundation*, 2024. https://docs.python.org/3/library/asyncio.html

15. **Radford, A., et al.** — "Robust Speech Recognition via Large-Scale Weak Supervision" (Whisper). *OpenAI*, 2022. https://arxiv.org/abs/2212.09058

16. **Brown, T., et al.** — "Language Models are Few-Shot Learners" (GPT-3). *NeurIPS*, 2020. https://arxiv.org/abs/2005.14165

17. **python-dotenv** — Read key-value pairs from a .env file. *Thiago Gloria-de-Sa*, 2024. https://pypi.org/project/python-dotenv/

18. **Jinja2 Template Engine Documentation**. *Pallets Projects*, 2024. https://jinja.palletsprojects.com/

---

# Appendix A: Setup & Run Instructions

To run PodcastAI locally, follow these steps:

1. **Clone the repository** and open a terminal in the project root.
2. **Create and activate a Python virtual environment** (recommended):
   - Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a `.env` file** in the project root with the required configuration values (at minimum):
   ```env
   SECRET_KEY=your-secret-key
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:1b
   # Optional email settings (for password reset emails):
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=you@example.com
   SMTP_PASS=yourpassword
   FROM_EMAIL=noreply@example.com
   ```
5. **Start the MongoDB server** (if not already running). The app connects to `mongodb://localhost:27017/` by default.
6. **Start Ollama** (required for LLM inference):
   ```bash
   ollama serve
   ```
   Ensure the `llama3.2:1b` model is available in Ollama. If it is not already downloaded, run:
   ```bash
   ollama pull llama3.2:1b
   ```
7. **Run the Flask app**:
   ```bash
   python app.py
   ```
8. **Open the app in your browser**:
   - Visit `http://localhost:5000/`

> **Tip:** The app requires YouTube videos with available transcripts (auto-generated or user-uploaded). If a video has no captions, it cannot be processed.

---

# PAPER PUBLISHED

> **[Placeholder for Published Paper]**
>
> A research paper based on this project titled:
>
> *"PodcastAI: A Locally-Deployed LLM-Powered Framework for Automated Podcast Summarization, Sentiment Analysis, and Interactive Question Answering"*
>
> is currently under preparation for submission to a relevant conference or journal in the domain of Natural Language Processing and Intelligent Systems (e.g., IEEE International Conference on NLP, Springer Journal of Intelligent Systems, or ACM Transactions on Intelligent Systems and Technology).
>
> **Authors**: [Author Name(s)]
> **Institution**: [Institution Name]
> **Year**: 2026
> **Status**: In Preparation / Under Review / Published *(update as applicable)*

---

*End of Report*

*Generated by PodcastAI — AI-Powered Podcast Analysis System*
*Academic Year 2025-2026*
