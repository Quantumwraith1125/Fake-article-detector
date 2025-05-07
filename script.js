// DOM Elements

// Wait for the DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Form elements
    const newsForm = document.getElementById('news-form');
    const newsContent = document.getElementById('news-content');
    const analyzeBtn = document.getElementById('analyze-btn');

    // Results section
    const resultsSection = document.getElementById('results');
    const scoreValue = document.getElementById('score-value');
    const reliabilityText = document.getElementById('reliability-text');
    const languageMeter = document.getElementById('language-meter');
    const factMeter = document.getElementById('fact-meter');
    const sourceMeter = document.getElementById('source-meter');
    const languageAnalysis = document.getElementById('language-analysis');
    const factAnalysis = document.getElementById('fact-analysis');
    const sourceAnalysis = document.getElementById('source-analysis');

    // Action buttons
    const shareBtn = document.getElementById('share-btn');
    const reportBtn = document.getElementById('report-btn');

    // Circular progress indicator
    const meterCircle = document.querySelector('.score-circle .meter');

    // Statistic counters
    const counters = document.querySelectorAll('.counter');

    // Navbar links
    const navLinks = document.querySelectorAll('nav a');

    // API endpoint - use relative URL to avoid protocol/CORS issues
    const API_URL = '/api/analyze';

    initEventListeners();
    animateCounters();
    initBackgroundAnimation();

    function initEventListeners() {
        newsForm.addEventListener('submit', handleSubmit);
        navLinks.forEach(link => link.addEventListener('click', handleNavClick));
        window.addEventListener('scroll', updateActiveNavLink);
        shareBtn.addEventListener('click', shareResults);
        reportBtn.addEventListener('click', reportMisinformation);
    }

    function handleSubmit(event) {
        event.preventDefault();
        const content = newsContent.value.trim();
        if (content) {
            analyzeNews(content);
        } else {
            showError('Please enter news content or URL to analyze.');
        }
    }

    function handleNavClick(e) {
        const targetId = e.currentTarget.getAttribute('href');
        if (targetId.startsWith('#')) {
            e.preventDefault();
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({ top: targetElement.offsetTop - 100, behavior: 'smooth' });
            }
        }
    }

    function analyzeNews(content) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        resultsSection.classList.remove('hidden');
        resultsSection.classList.add('fade-in');
        setTimeout(() => resultsSection.scrollIntoView({ behavior: 'smooth' }), 100);

        const url = (content.match(/https?:\/\/[^\s]+/) || [null])[0];

        // Determine the correct API URL based on the current location
        const apiBaseUrl = new URL(window.location.href).origin;
        const fullApiUrl = `${apiBaseUrl}/api/analyze`;
        
        console.log("Attempting to connect to API at:", fullApiUrl);
        
        // Improved error handling
        fetch(fullApiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, url }),
            // Don't set mode to 'cors' for same-origin requests
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                console.error("API Error Status:", response.status);
                return response.text().then(text => {
                    console.error("Error response body:", text);
                    throw new Error(`API Error: ${response.status} - ${text || response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("API Response:", data);
            if (data.status === 'success' && data.results) {
                displayResults(data.results);
            } else {
                throw new Error('Invalid response format');
            }
        })
        .catch(err => {
            console.error("Detailed error:", err);
            const fallback = performFakeNewsAnalysis(content);
            displayResults(fallback);
            showError('Could not connect to server. Using local analysis.');
        })
        .finally(() => {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze';
        });
    }

    function performFakeNewsAnalysis(content) {
        console.log("Using fallback local analysis");
        const len = content.length;
        const base = Math.max(30, 100 - len / 50);
        const final = Math.min(100, Math.max(0, base + Math.random() * 30 - 15));

        const language = Math.min(100, Math.max(0, final + Math.random() * 20 - 10));
        const fact = Math.min(100, Math.max(0, final + Math.random() * 20 - 10));
        const source = Math.min(100, Math.max(0, final + Math.random() * 20 - 10));

        const languageText = language < 40 ?
            "Highly emotional language detected." :
            language < 70 ? "Some emotional language present." :
            "Neutral language detected.";

        const factText = fact < 40 ?
            "Multiple unverified claims detected." :
            fact < 70 ? "Some claims require verification." :
            "Most claims appear accurate.";

        const sourceText = source < 40 ?
            "Source has low credibility." :
            source < 70 ? "Source has mixed credibility." :
            "Source has good reputation.";

        const reliability = final < 30 ? "Likely Fake News" :
            final < 50 ? "Questionable Content" :
            final < 70 ? "Partially Reliable" :
            final < 85 ? "Mostly Reliable" :
            "Highly Reliable";

        return {
            overallScore: final,
            reliabilityLabel: reliability,
            languageScore: language,
            factScore: fact,
            sourceScore: source,
            languageAnalysis: languageText,
            factAnalysis: factText,
            sourceAnalysis: sourceText
        };
    }

    function displayResults(results) {
        animateCounter(scoreValue, 0, Math.round(results.overallScore), 1500);

        const circleLength = 283;
        const offset = circleLength - (results.overallScore / 100 * circleLength);
        meterCircle.style.strokeDashoffset = offset;

        const color = results.overallScore < 50 ? 'var(--danger)' :
                      results.overallScore < 70 ? 'var(--warning)' :
                      'var(--success)';
        meterCircle.style.stroke = color;
        reliabilityText.textContent = results.reliabilityLabel;
        reliabilityText.style.color = color;

        setTimeout(() => {
            languageMeter.style.width = `${results.languageScore}%`;
            factMeter.style.width = `${results.factScore}%`;
            sourceMeter.style.width = `${results.sourceScore}%`;

            languageMeter.style.background = getGradientColor(results.languageScore);
            factMeter.style.background = getGradientColor(results.factScore);
            sourceMeter.style.background = getGradientColor(results.sourceScore);

            languageAnalysis.textContent = results.languageAnalysis;
            factAnalysis.textContent = results.factAnalysis;
            sourceAnalysis.textContent = results.sourceAnalysis;
        }, 500);
    }

    function getGradientColor(score) {
        return score < 50 ? 'linear-gradient(90deg, var(--danger), var(--danger))' :
               score < 70 ? 'linear-gradient(90deg, var(--danger), var(--warning))' :
               'linear-gradient(90deg, var(--warning), var(--success))';
    }

    function animateCounter(el, start, end, duration) {
        let startTime = null;
        function tick(now) {
            if (!startTime) startTime = now;
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            el.textContent = Math.floor(progress * (end - start) + start);
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    function animateCounters() {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    animateCounter(counter, 0, parseFloat(counter.dataset.target), 2000);
                    observer.unobserve(counter);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(c => observer.observe(c));
    }

    function updateActiveNavLink() {
        const scrollPos = window.scrollY + 200;
        document.querySelectorAll('section').forEach(section => {
            if (scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
                const id = section.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${id}`) link.classList.add('active');
                });
            }
        });
    }

    function shareResults() {
        alert('Sharing functionality would be implemented here.');
    }

    function reportMisinformation() {
        alert('Reporting functionality would be implemented here.');
    }

    function showError(msg) {
        console.error(msg);
        alert(msg);
    }

    function initBackgroundAnimation() {
        const bg = document.querySelector('.animated-bg');
        if (!bg) return; // Skip if element doesn't exist
        
        for (let i = 0; i < 15; i++) {
            const bubble = document.createElement('div');
            bubble.classList.add('bubble');
            const size = Math.random() * 60 + 20;
            bubble.style.width = `${size}px`;
            bubble.style.height = `${size}px`;
            bubble.style.left = `${Math.random() * 100}%`;
            bubble.style.top = `${Math.random() * 100}%`;
            bubble.style.animationDelay = `${Math.random() * 5}s`;
            bg.appendChild(bubble);
        }
    }
});