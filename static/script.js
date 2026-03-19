// Helper to escape HTML entities in dynamic content
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ==================== Format Summary ====================
function formatSummary(rawText) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = rawText;
    const textContent = tempDiv.textContent || tempDiv.innerText || rawText;

    // Clean markdown artifacts
    let cleanedText = textContent
        .replace(/\*{1,3}/g, '')           // Remove **, ***, *
        .replace(/#{1,6}\s*/g, '')          // Remove # headers inline
        .replace(/`+/g, '')                 // Remove backticks
        .replace(/\n{3,}/g, '\n\n');        // Collapse excessive newlines

    let formatted = '';

    // Check for section headers (with or without ### prefix)
    const hasSummaryHeader = /(?:^|\n)\s*(?:###?\s*)?(?:Summary|सारांश)/im.test(cleanedText);
    const hasTakeawaysHeader = /(?:^|\n)\s*(?:###?\s*)?(?:Key Takeaways|मुख्य बिंदु|मुख्य मुद्दे)/im.test(cleanedText);

    if (hasSummaryHeader || hasTakeawaysHeader) {
        const parts = cleanedText.split(/(?:^|\n)\s*(?:###?\s*)?(?=Summary|Key Takeaways|सारांश|मुख्य बिंदु|मुख्य मुद्दे)/im);

        parts.forEach(section => {
            section = section.trim();
            if (!section) return;

            if (/^(?:Summary|सारांश)/i.test(section)) {
                const content = section.replace(/^(?:Summary|सारांश)\s*/i, '').trim();
                if (content) {
                    formatted += `<div class="summary-block"><h4>Summary</h4><p>${content}</p></div>`;
                }
            }
            else if (/^(?:Key Takeaways|मुख्य बिंदु|मुख्य मुद्दे)/i.test(section)) {
                const content = section.replace(/^(?:Key Takeaways|मुख्य बिंदु|मुख्य मुद्दे)\s*/i, '').trim();
                const lines = content.split('\n');
                let bullets = '';
                lines.forEach(line => {
                    line = line.trim();
                    if (line.match(/^[-\*•\d.]+\s*/)) {
                        line = line.replace(/^[-\*•]+\s*/, '').replace(/^\d+[.)]\s*/, '').trim();
                    }
                    if (line && line.length > 3) {
                        bullets += `<li>${line}</li>`;
                    }
                });
                if (bullets) {
                    formatted += `<div class="takeaways-block"><h4>Key Takeaways</h4><ul>${bullets}</ul></div>`;
                }
            } else if (section.length > 10) {
                formatted += `<div class="generic-block"><p>${section}</p></div>`;
            }
        });
    }

    // Fallback formatting
    if (!formatted) {
        const lines = cleanedText.split('\n');
        let bullets = [];
        let paragraphs = [];

        for (let line of lines) {
            line = line.trim();
            if (line === '---') continue;
            if (line.startsWith('Processed') && line.includes('chunks')) continue;
            if (line.toLowerCase().includes('here is a summary') || line.toLowerCase().includes('bullet points:')) continue;
            if (line.match(/^[-\*•]/)) {
                bullets.push(line.replace(/^[-\*•]+\s*/, '').trim());
            } else if (line.match(/^\d+[.)]\s/)) {
                bullets.push(line.replace(/^\d+[.)]\s*/, '').trim());
            } else if (line && line.length > 5) {
                if (bullets.length === 0) {
                    paragraphs.push(line);
                } else {
                    bullets.push(line);
                }
            }
        }

        // if we only got one long paragraph and no bullets, attempt sentence-splitting
        if (paragraphs.length === 1 && bullets.length === 0) {
            const sentenceParts = paragraphs[0].split(/(?<=[\.\?\!])\s+/);
            if (sentenceParts.length > 1) {
                bullets = sentenceParts.map(s => s.trim()).filter(s => s.length > 20 && s.length < 200);
                // make sure we don't treat the entire paragraph as one bullet
                if (bullets.length > 1 && bullets.join(' ') !== paragraphs[0]) {
                    paragraphs = []; // move to takeaways-only mode
                } else {
                    bullets = [];
                }
            }
        }

        if (paragraphs.length > 0) {
            formatted += `<div class="summary-block"><p>${paragraphs.join(' ')}</p></div>`;
        }
        if (bullets.length > 0) {
            formatted += '<div class="takeaways-block"><ul>';
            bullets.forEach(bullet => {
                if (bullet) formatted += `<li>${bullet}</li>`;
            });
            formatted += '</ul></div>';
        }
    }

    return formatted || `<p>${cleanedText}</p>`;
}


// typing animation helper for summaries
let typingTimeouts = [];
function animatedType(element, text, interval) {
    // clear any previous timeouts
    typingTimeouts.forEach(id => clearTimeout(id));
    typingTimeouts = [];
    let idx = 0;
    element.innerHTML = '';
    element.style.opacity = 1;
    function step() {
        if (idx <= text.length) {
            element.innerHTML = text.slice(0, idx);
            idx += 1;
            const id = setTimeout(step, interval);
            typingTimeouts.push(id);
        }
    }
    step();
}

function cancelTyping() {
    typingTimeouts.forEach(id => clearTimeout(id));
    typingTimeouts = [];
    const summaryEl = document.getElementById('summary-content');
    if (summaryEl && summaryEl.dataset.rawSummary) {
        summaryEl.innerHTML = formatSummary(summaryEl.dataset.rawSummary);
    }
}

// ==================== Copy to Clipboard ====================
function copyToClipboard(section) {
    let textToCopy = '';

    if (section === 'summary') {
        const element = document.getElementById('summary-content');
        if (element) {
            textToCopy = element.innerText || element.textContent;
        }
    } else if (section === 'takeaways') {
        const element = document.getElementById('summary-content');
        if (element) {
            const takeawaysBlock = element.querySelector('.takeaways-block');
            if (takeawaysBlock) {
                textToCopy = takeawaysBlock.innerText || takeawaysBlock.textContent;
            } else {
                const listItems = element.querySelectorAll('li');
                if (listItems.length > 0) {
                    textToCopy = Array.from(listItems).map(li => '• ' + li.textContent).join('\n');
                }
            }
        }
    }

    if (!textToCopy) {
        showToast('No content to copy');
        return;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('Copied Successfully');
    }).catch(err => {
        console.error('Copy failed:', err);
        showToast('Copy failed, please try again');
    });
}

// ==================== Show Toast Notification ====================
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}

// ==================== Print Summary ====================
function printSummary() {
    window.print();
}

// ==================== Text-to-Speech ====================
let ttsUtterance = null;
let ttsIsPaused = false;
let ttsIsPlaying = false;

function getVoiceForLanguage(langCode) {
    const voices = window.speechSynthesis.getVoices();
    const langMap = { 'en': 'en', 'hi': 'hi', 'mr': 'mr' };
    const targetLang = langMap[langCode] || 'en';
    let voice = voices.find(v => v.lang.startsWith(targetLang));
    if (!voice && langCode === 'mr') {
        voice = voices.find(v => v.lang.startsWith('hi'));
    }
    return voice || voices.find(v => v.default) || voices[0];
}

function toggleSpeech() {
    if (ttsIsPlaying) { stopSpeech(); return; }
    // stop typing animation so we capture full content
    cancelTyping();
    const summaryEl = document.getElementById('summary-content');
    if (!summaryEl) return;
    const text = summaryEl.innerText || summaryEl.textContent;
    if (!text || text.trim().length === 0) { showToast('No content to speak'); return; }
    const langCode = summaryEl.dataset.language || 'en';
    window.speechSynthesis.cancel();
    ttsUtterance = new SpeechSynthesisUtterance(text.trim());
    const voice = getVoiceForLanguage(langCode);
    if (voice) ttsUtterance.voice = voice;
    ttsUtterance.rate = 0.95;
    ttsUtterance.pitch = 1;
    ttsUtterance.onstart = () => {
        ttsIsPlaying = true;
        ttsIsPaused = false;
        document.getElementById('tts-controls').style.display = 'flex';
        document.getElementById('tts-btn-text').textContent = '🔊 Playing...';
        document.getElementById('tts-pause-btn').style.display = '';
        document.getElementById('tts-resume-btn').style.display = 'none';
    };
    ttsUtterance.onend = () => { resetTtsUI(); };
    ttsUtterance.onerror = () => { resetTtsUI(); };
    window.speechSynthesis.speak(ttsUtterance);
}

function pauseSpeech() {
    if (ttsIsPlaying && !ttsIsPaused) {
        window.speechSynthesis.pause();
        ttsIsPaused = true;
        document.getElementById('tts-pause-btn').style.display = 'none';
        document.getElementById('tts-resume-btn').style.display = '';
        document.getElementById('tts-btn-text').textContent = '⏸ Paused';
    }
}

function resumeSpeech() {
    if (ttsIsPaused) {
        window.speechSynthesis.resume();
        ttsIsPaused = false;
        document.getElementById('tts-pause-btn').style.display = '';
        document.getElementById('tts-resume-btn').style.display = 'none';
        document.getElementById('tts-btn-text').textContent = '🔊 Playing...';
    }
}

function stopSpeech() { window.speechSynthesis.cancel(); resetTtsUI(); }

function resetTtsUI() {
    ttsIsPlaying = false;
    ttsIsPaused = false;
    const controls = document.getElementById('tts-controls');
    const btnText = document.getElementById('tts-btn-text');
    if (controls) controls.style.display = 'none';
    if (btnText) btnText.textContent = 'Speak';
}

// ==================== Theme Toggle ====================
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeUI(newTheme);
}

function updateThemeUI(theme) {
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    const toggleText = document.getElementById('theme-toggle-text');
    if (theme === 'dark') {
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = '';
        if (toggleText) toggleText.textContent = 'Light Mode';
    } else {
        if (sunIcon) sunIcon.style.display = '';
        if (moonIcon) moonIcon.style.display = 'none';
        if (toggleText) toggleText.textContent = 'Dark Mode';
    }
    // landing page icons
    const landingSun = document.getElementById('landing-theme-icon-sun');
    const landingMoon = document.getElementById('landing-theme-icon-moon');
    if (landingSun && landingMoon) {
        if (theme === 'dark') {
            landingSun.style.display = 'none';
            landingMoon.style.display = '';
        } else {
            landingSun.style.display = '';
            landingMoon.style.display = 'none';
        }
    }
}

// ==================== Comments ====================
function loadComments(videoId) {
    const commentsList = document.getElementById('comments-list');
    const loadingEl = document.getElementById('comments-loading');
    if (!commentsList) return;

    fetch(`/comments/${videoId}`)
        .then(res => res.json())
        .then(data => {
            if (loadingEl) loadingEl.remove();
            if (!data.comments || data.comments.length === 0) {
                commentsList.innerHTML = '<div class="no-comments">No comments yet. Be the first to share your thoughts!</div>';
                return;
            }
            commentsList.innerHTML = '';
            data.comments.forEach(c => {
                commentsList.appendChild(createCommentElement(c));
            });
        })
        .catch(err => {
            console.error('Error loading comments:', err);
            if (loadingEl) loadingEl.textContent = 'Failed to load comments.';
        });
}

function createCommentElement(comment) {
    const div = document.createElement('div');
    div.className = 'comment-item';
    div.innerHTML = `
        <div class="comment-header">
            <div class="comment-avatar">${(comment.username || 'U')[0].toUpperCase()}</div>
            <div class="comment-meta">
                <span class="comment-username">${comment.username}</span>
                <span class="comment-time">${comment.created_at}</span>
            </div>
        </div>
        <div class="comment-body">${escapeHtml(comment.comment_text)}</div>
    `;
    return div;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function submitComment(videoId) {
    const input = document.getElementById('comment-input');
    const text = input.value.trim();
    if (!text) return;

    const btn = document.getElementById('submit-comment-btn');
    btn.disabled = true;
    input.disabled = true;

    fetch('/comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: videoId, comment_text: text })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                input.value = '';
                const commentsList = document.getElementById('comments-list');
                const noComments = commentsList.querySelector('.no-comments');
                if (noComments) noComments.remove();
                const newEl = createCommentElement(data.comment);
                commentsList.prepend(newEl);
                showToast('Comment added!');
            } else {
                showToast(data.error || 'Failed to add comment');
            }
        })
        .catch(err => {
            console.error('Comment error:', err);
            showToast('Error submitting comment');
        })
        .finally(() => {
            btn.disabled = false;
            input.disabled = false;
            input.focus();
        });
}

// ==================== Sidebar Toggle ====================
function initSidebar() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (!toggle || !sidebar) return;

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    });

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

// ==================== Scroll Animations ====================
function initScrollAnimations() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    if (!elements.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elements.forEach(el => observer.observe(el));
}

// ==================== Chat History Loading ====================
function loadChatHistory(videoId, chatWindow) {
    fetch(`/chat-history/${videoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.history && data.history.length > 0) {
                // Add a separator for history
                const separator = document.createElement('div');
                separator.className = 'chat-history-separator';
                separator.innerHTML = '<span>Previous Conversation</span>';
                chatWindow.appendChild(separator);

                data.history.forEach(entry => {
                    // User question
                    addChatMessage(chatWindow, entry.question, 'user');
                    // Bot answer with confidence (and language if available)
                    addChatMessage(chatWindow, entry.answer, 'bot', entry.confidence_score, entry.language);
                });

                // Add separator for new conversation
                const newSep = document.createElement('div');
                newSep.className = 'chat-history-separator';
                newSep.innerHTML = '<span>New Conversation</span>';
                chatWindow.appendChild(newSep);

                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        })
        .catch(err => {
            console.error('Error loading chat history:', err);
        });
}

// ==================== Add Chat Message Helper ====================
function addChatMessage(chatWindow, text, sender, confidenceScore, lang) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;

    if (sender === 'bot') {
        const avatar = document.createElement('div');
        avatar.className = 'chat-msg-avatar bot-avatar';
        avatar.textContent = 'AI';
        msgDiv.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    if (lang) {
        bubble.dataset.language = lang;
    }
    msgDiv.appendChild(bubble);

    // Add confidence badge for bot messages
    if (sender === 'bot' && confidenceScore !== undefined && confidenceScore !== null) {
        const badge = document.createElement('div');
        badge.className = 'confidence-badge';
        let colorClass = 'confidence-low';
        if (confidenceScore >= 75) colorClass = 'confidence-high';
        else if (confidenceScore >= 50) colorClass = 'confidence-medium';
        badge.classList.add(colorClass);
        badge.textContent = `Confidence: ${confidenceScore}%`;
        msgDiv.appendChild(badge);
    }

    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ==================== Suggested Questions ====================
function askSuggested(btn) {
    const question = btn.dataset.question;
    const chatInput = document.getElementById('chat-input');
    if (chatInput && question) {
        chatInput.value = question;
        // Trigger send
        const sendBtn = document.getElementById('send-chat-btn');
        if (sendBtn) sendBtn.click();
    }
}

// ==================== Initialize on Page Load ====================
document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle
    initSidebar();

    // Scroll animations
    initScrollAnimations();

    // Theme UI sync
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeUI(currentTheme);

    // also update landing header icons if present
    const landingSun = document.getElementById('landing-theme-icon-sun');
    const landingMoon = document.getElementById('landing-theme-icon-moon');
    if (landingSun && landingMoon) {
        if (currentTheme === 'dark') {
            landingSun.style.display = 'none';
            landingMoon.style.display = '';
        } else {
            landingSun.style.display = '';
            landingMoon.style.display = 'none';
        }
    }

    // Handle existing summary - animate like a live typing AI response
    const summaryElement = document.getElementById('summary-content');
    if (summaryElement && summaryElement.dataset.rawSummary) {
        const rawSummary = summaryElement.dataset.rawSummary;
        const formattedSummary = formatSummary(rawSummary);
        // fade-in container then type
        summaryElement.style.opacity = 0;
        setTimeout(() => {
            animatedType(summaryElement, formattedSummary, 15);
        }, 200);
    }

    // Load voices for TTS
    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }

    // Form submission handler - show loading state
    const form = document.getElementById('analysis-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            const submitButton = document.getElementById('analyze-btn');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                    </svg>
                    Processing... (This may take a few minutes)
                `;
            }
        });
    }

    // Comments initialization
    const commentsSection = document.getElementById('comments-section');
    if (commentsSection) {
        const videoId = commentsSection.dataset.videoId;
        loadComments(videoId);

        const submitBtn = document.getElementById('submit-comment-btn');
        const commentInput = document.getElementById('comment-input');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => submitComment(videoId));
        }
        if (commentInput) {
            commentInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') submitComment(videoId);
            });
        }
    }

    // Chat Functionality (works on both results page inline and dedicated chat page)
    const chatInput = document.getElementById('chat-input');
    const micBtn = document.getElementById('mic-btn');
    let recognition = null;
    const sendBtn = document.getElementById('send-chat-btn');
    const chatWindow = document.getElementById('chat-window');
    // hide mic button by default; show later if support
    if (micBtn) micBtn.style.display = 'none';

    // stop any speech when user navigates away
    window.addEventListener('beforeunload', () => {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    });
    // also stop on visibility change (e.g., SPA nav link)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    });

    // setup speech recognition if available
    if (window.SpeechRecognition || window.webkitSpeechRecognition) {
        if (micBtn) micBtn.style.display = '';
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.lang = 'en-US'; // default, will override if summary language set
        recognition.interimResults = false;
        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            if (chatInput) chatInput.value = transcript;
            if (sendBtn) sendBtn.click();
        };
        recognition.onend = function () {
            if (micBtn) micBtn.classList.remove('listening');
        };
    }

    if (micBtn && recognition) {
        micBtn.addEventListener('click', () => {
            if (recognition) {
                if (micBtn.classList.contains('listening')) {
                    recognition.stop();
                    micBtn.classList.remove('listening');
                } else {
                    // choose language from summary element if available
                    const summaryEl = document.getElementById('summary-content');
                    if (summaryEl && summaryEl.dataset.language) {
                        recognition.lang = summaryEl.dataset.language || 'en-US';
                    }
                    recognition.start();
                    micBtn.classList.add('listening');
                }
            }
        });
    }

    // Get video ID from chat container or chat section
    const chatContainer = document.querySelector('.chat-container') || document.querySelector('.chat-section');

    if (chatInput && sendBtn && chatContainer) {
        const videoId = chatContainer.dataset.videoId;

        // Load chat history for this video
        if (videoId) {
            loadChatHistory(videoId, chatWindow);
        }

        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            addChatMessage(chatWindow, message, 'user');
            chatInput.value = '';
            chatInput.disabled = true;
            sendBtn.disabled = true;

            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('chat-message', 'bot', 'loading-msg');

            const loadAvatar = document.createElement('div');
            loadAvatar.className = 'chat-msg-avatar bot-avatar';
            loadAvatar.textContent = 'AI';
            loadingDiv.appendChild(loadAvatar);

            const loadBubble = document.createElement('div');
            loadBubble.className = 'bubble';
            loadBubble.textContent = 'Thinking...';
            loadingDiv.appendChild(loadBubble);

            chatWindow.appendChild(loadingDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message, video_id: videoId })
                });
                const data = await response.json();
                chatWindow.removeChild(loadingDiv);
                if (data.response) {
                    addChatMessage(chatWindow, data.response, 'bot', data.confidence_score, data.language);
                } else {
                    addChatMessage(chatWindow, "Sorry, something went wrong.", 'bot');
                }
            } catch (error) {
                chatWindow.removeChild(loadingDiv);
                addChatMessage(chatWindow, "Error connecting to server.", 'bot');
                console.error(error);
            } finally {
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // ==================== Progressive Analysis Polling ====================
    const resultsPage = document.querySelector('.results-page');
    if (resultsPage) {
        const videoId = resultsPage.dataset.videoId;
        const progress = resultsPage.dataset.progress;

        // If analysis already finished, remove any leftover loaders immediately
        if (progress === 'complete') {
            ['topics-loading', 'sentiment-loading', 'accuracy-loading'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.remove();
            });
        }

        // Poll if analysis is not yet complete
        if (progress && progress !== 'complete') {
            pollAnalysisStatus(videoId);
        } else if (progress === 'complete') {
            // Edge case: analysis marked complete but sentiment might be missing from
            // the initial render (race condition between background thread & page load).
            // Check if sentiment content is absent and do a one-shot fetch to fix it.
            const sentimentContent = document.getElementById('sentiment-content');
            const hasSentimentData = sentimentContent &&
                sentimentContent.querySelector('.sentiment-block');
            if (!hasSentimentData && videoId) {
                fetch(`/analysis-status/${videoId}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.sentiment &&
                            ((data.sentiment.transcript && Object.keys(data.sentiment.transcript).length > 0) ||
                                (data.sentiment.summary && Object.keys(data.sentiment.summary).length > 0))) {
                            renderSentimentSection(data.sentiment);
                        }
                        if (data.accuracy) renderAccuracySection(data.accuracy);
                        if (data.topics !== undefined) renderTopicsSection(data.topics, data.topic_reason);
                    })
                    .catch(err => console.error('One-shot status fetch error:', err));
            }
        }
    }
});

// ==================== Analysis Status Polling ====================
function pollAnalysisStatus(videoId) {
    async function doPoll() {
        try {
            const res = await fetch(`/analysis-status/${videoId}`);
            const data = await res.json();

            // Update sentiment section
            if (data.sentiment && ((data.sentiment.transcript && Object.keys(data.sentiment.transcript).length > 0) || (data.sentiment.summary && Object.keys(data.sentiment.summary).length > 0))) {
                renderSentimentSection(data.sentiment);
            }

            // Update accuracy section
            if (data.accuracy) {
                // render even if scores are 0 to clear loading spinner
                renderAccuracySection(data.accuracy);
            }

            // Update topics section
            // always call renderTopicsSection so loading spinner is removed
            if (data.topics !== undefined) {
                renderTopicsSection(data.topics, data.topic_reason);
            }

            // Stop polling when complete
            if (data.progress === 'complete') {
                clearInterval(pollInterval);
                console.log('[PodcastAI] All analysis steps complete.');
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }

    // Fire immediately, then every 3 seconds
    doPoll();
    let pollInterval = setInterval(doPoll, 3000);
}

function renderSentimentSection(sentiment) {
    const section = document.getElementById('sentiment-section');
    if (!section) return;

    // Remove loading spinner if present
    const loading = document.getElementById('sentiment-loading');

    // If sentiment content is already rendered (no loading spinner and content present), skip
    if (!loading && document.getElementById('sentiment-content')) return;

    const emotionIcons = {
        'Informative': 'ℹ️', 'Sad': '😢', 'Excited': '😄',
        'Serious': '😐', 'Motivational': '💪', 'Angry': '😠', 'Neutral': '😶'
    };
    const sentimentIcons = { 'positive': '😊', 'negative': '😞', 'neutral': '😐' };

    let html = '<div id="sentiment-content" class="animate-fade-up"><div class="sentiment-grid">';

    for (const [label, data] of [['Transcript', sentiment.transcript], ['Summary', sentiment.summary]]) {
        if (data && Object.keys(data).length > 0) {
            const sent = (data.sentiment || 'Neutral').toLowerCase();
            const sentIcon = sentimentIcons[sent] || '😐';
            const sentLabel = data.sentiment || 'Neutral';
            const score = data.sentiment_score !== undefined ? data.sentiment_score : '';
            const emoRaw = data.emotion || 'Neutral';
            const emoPrimary = emoRaw.split('|')[0].trim();
            const emoIcon = emotionIcons[emoPrimary] || '';
            const emoDisplay = emoRaw.replace(/\|/g, ', ');
            const emoConf = data.emotion_confidence !== undefined ? data.emotion_confidence : null;

            html += `<div class="sentiment-block">
                <h4>${label}</h4>
                <div class="sentiment-metric"><span class="label">Sentiment:</span> <span class="value badge-sentiment-${sent}">${sentIcon} ${sentLabel}</span></div>
                ${score !== '' ? `<div class="sentiment-metric"><span class="label">Score:</span> <span class="value">${score}%</span></div>` : ''}
                <div class="sentiment-metric"><span class="label">Emotion:</span> <span class="value badge-emotion">${emoIcon} ${emoDisplay}</span></div>
                ${emoConf !== null ? `<div class="sentiment-metric"><span class="label">Emotion Confidence:</span> <span class="value">${emoConf}%</span></div>` : ''}
            </div>`;
        }
    }
    html += '</div></div>';

    if (loading) loading.remove();

    // Remove any existing no-data placeholder
    const existingContent = document.getElementById('sentiment-content');
    if (existingContent) existingContent.remove();

    section.querySelector('.results-card-header').insertAdjacentHTML('afterend', html);
}

function renderAccuracySection(accuracy) {
    const loading = document.getElementById('accuracy-loading');
    if (!loading) return;

    const section = document.getElementById('accuracy-section');
    const tc = accuracy.transcription_confidence || 0;
    const sc = accuracy.summary_confidence || 0;
    const tcColor = tc >= 75 ? 'bar-green' : (tc >= 50 ? 'bar-yellow' : 'bar-red');
    const scColor = sc >= 75 ? 'bar-green' : (sc >= 50 ? 'bar-yellow' : 'bar-red');

    const html = `
        <div id="accuracy-content" class="animate-fade-up">
            <div class="metric-cards">
                <div class="metric-card">
                    <h4>Transcription Confidence</h4>
                    <div class="metric-bar-wrap">
                        <span class="metric-bar-label">${tc}%</span>
                        <div class="metric-bar">
                            <div class="metric-bar-fill ${tcColor}" style="width: ${tc}%"></div>
                        </div>
                    </div>
                </div>
                <div class="metric-card">
                    <h4>Summary Confidence</h4>
                    <div class="metric-bar-wrap">
                        <span class="metric-bar-label">${sc}%</span>
                        <div class="metric-bar">
                            <div class="metric-bar-fill ${scColor}" style="width: ${sc}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

    loading.remove();
    section.querySelector('.results-card-header').insertAdjacentHTML('afterend', html);
}

function renderTopicsSection(topics, reason) {
    const loading = document.getElementById('topics-loading');
    if (!loading) return; // already removed/rendered or not present

    const section = document.getElementById('topics-section');
    let html = '<div id="topics-content" class="topics-grid animate-fade-up">';

    try {
        if (!Array.isArray(topics) || topics.length === 0) {
            const message = reason ? reason : 'No key topics could be detected.';
            html += `<div class="no-topics">${escapeHtml(message)}</div>`;
        } else {
            topics.forEach(topic => {
                const name = topic && topic.topic ? topic.topic : '';
                html += `<div class="topic-item">
            <button class="topic-header" onclick="this.parentElement.classList.toggle('open')">
                <span class="topic-name">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    ${escapeHtml(name)}
                </span>
                <svg class="topic-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
            <div class="topic-content">`;

                if (topic && Array.isArray(topic.questions)) {
                    topic.questions.forEach(qa => {
                        const q = qa.q || '';
                        const a = qa.a || '';
                        html += `<div class="topic-qa">
                    <p class="topic-question"><strong>Q:</strong> ${escapeHtml(q)}</p>
                    <p class="topic-answer"><strong>A:</strong> ${escapeHtml(a)}</p>
                </div>`;
                    });
                }

                html += '</div></div>';
            });
        }
    } catch (err) {
        console.error('Error rendering topics section:', err);
        // fallback message
        html = '<div id="topics-content" class="topics-grid animate-fade-up"><div class="no-topics">No key topics could be detected.</div></div>';
    } finally {
        loading.remove();
        section.querySelector('.results-card-header').insertAdjacentHTML('afterend', html);
    }
}

// Spinner animation (used in loading button)
const styleSheet = document.createElement('style');
styleSheet.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(styleSheet);
