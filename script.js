document.addEventListener('DOMContentLoaded', () => {
    const apiMeta = document.querySelector('meta[name="axiom-api-url"]');
    window.AXIOM_API_URL = apiMeta ? apiMeta.getAttribute('content') : 'http://localhost:8000';

    // Elements - Screen 1
    const queryInput = document.getElementById('query-input');
    const charCount = document.getElementById('char-count');
    const submitBtn = document.getElementById('submit-btn');
    const slider = document.getElementById('confidence-slider');
    const sliderValue = document.getElementById('slider-value');
    const form = document.getElementById('query-form');
    const querySection = document.getElementById('query-form');

    // Elements - Screen 2
    const stepTrackerContainer = document.getElementById('step-tracker-container');
    const cancelBtn = document.getElementById('cancel-btn');
    const confidenceMeterContainer = document.getElementById('confidence-meter-container');
    const confidenceMeterLabel = document.getElementById('confidence-meter-label');
    const confidenceMeterFill = document.getElementById('confidence-meter-fill');
    const confidenceMeterStatus = document.getElementById('confidence-meter-status');

    // Elements - Screen 3
    const screen1 = document.getElementById('screen-1');
    const screen3 = document.getElementById('screen-3');
    const resultsBanner = document.getElementById('results-banner');
    const auditToggle = document.getElementById('audit-toggle');
    const auditPanelWrapper = document.getElementById('audit-panel-wrapper');
    const newQueryBtn = document.getElementById('new-query-btn');

    let abortController = null;

    // Textarea auto-resize and character count
    queryInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        const length = this.value.length;
        charCount.textContent = length;

        if (this.value.trim().length > 0) {
            submitBtn.removeAttribute('disabled');
        } else {
            submitBtn.setAttribute('disabled', 'true');
        }
    });

    // Slider logic
    function updateSlider() {
        const val = parseFloat(slider.value).toFixed(2);
        sliderValue.textContent = val;
        
        const min = parseFloat(slider.min);
        const max = parseFloat(slider.max);
        const percentage = ((val - min) / (max - min)) * 100;
        
        slider.style.background = `linear-gradient(to right, var(--primary-teal) ${percentage}%, var(--border-color) ${percentage}%)`;
    }

    slider.addEventListener('input', updateSlider);
    updateSlider();

    // Submit via Keyboard
    queryInput.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!submitBtn.hasAttribute('disabled')) {
                startProcessing();
            }
        }
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        startProcessing();
    });

    // Cancel Processing
    cancelBtn.addEventListener('click', resetToIdle);

    // New Query
    newQueryBtn.addEventListener('click', () => {
        queryInput.value = '';
        queryInput.dispatchEvent(new Event('input')); // trigger resize and btn disable
        resetToIdle();
    });

    // Audit trail toggle
    auditToggle.addEventListener('click', () => {
        if (auditPanelWrapper.classList.contains('open')) {
            auditPanelWrapper.classList.remove('open');
            auditToggle.innerHTML = 'View agent trace &darr;';
        } else {
            auditPanelWrapper.classList.add('open');
            auditToggle.innerHTML = 'Hide agent trace &uarr;';
        }
    });

    // Delegated event listener for expand buttons
    document.addEventListener('click', (e) => {
        if (e.target.matches('.expand-btn')) {
            const card = e.target.closest('.evidence-card');
            const excerpt = card.querySelector('.evidence-excerpt');
            
            if (e.target.textContent.includes('Show')) {
                excerpt.textContent = excerpt.getAttribute('data-full');
                e.target.innerHTML = 'Hide abstract &uarr;';
            } else {
                excerpt.textContent = excerpt.getAttribute('data-short');
                e.target.innerHTML = 'Show full abstract &darr;';
            }
        }
    });

    function setStepState(stepNumber, state, newLabel = null) {
        const step = document.getElementById(`step-${stepNumber}`);
        if (!step) return;
        const icon = step.querySelector('.step-icon');
        const label = step.querySelector('.step-label');

        icon.className = `step-icon ${state}`;
        label.className = `step-label ${state}`;

        if (newLabel) {
            label.textContent = newLabel;
        }
    }

    function resetToIdle() {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }

        // Reset Screen 1 UI
        querySection.classList.remove('processing');
        submitBtn.removeAttribute('disabled');
        if (queryInput.value.trim().length === 0) {
            submitBtn.setAttribute('disabled', 'true');
        }
        
        // Hide screens/components
        stepTrackerContainer.classList.add('hidden');
        confidenceMeterContainer.classList.add('hidden');
        resultsBanner.classList.add('hidden');
        
        // Reset banner styles
        resultsBanner.style.backgroundColor = '';
        resultsBanner.style.borderBottomColor = '';
        const bannerContent = resultsBanner.querySelector('.banner-content');
        if (bannerContent) bannerContent.style.color = '';

        screen3.classList.add('hidden');
        screen1.classList.remove('hidden');

        // Reset step states
        [1, 2, 3, 4].forEach(i => setStepState(i, 'pending'));
        document.getElementById('step-2').querySelector('.step-label').textContent = 'Retrieving evidence from PubMed corpus';
        document.getElementById('step-3').querySelector('.step-label').textContent = 'Evaluating confidence';
        
        // Reset audit trace
        auditPanelWrapper.classList.remove('open');
        auditToggle.innerHTML = 'View agent trace &darr;';
        const auditTable = document.getElementById('audit-table');
        if (auditTable) auditTable.innerHTML = '';
        
        // Reset evidence section
        const evidenceSection = document.getElementById('evidence-section');
        if (evidenceSection) {
            const cards = evidenceSection.querySelectorAll('.evidence-card');
            cards.forEach(c => c.remove());
        }

        const answerText = document.getElementById('answer-text');
        if (answerText) answerText.innerHTML = '';
        
        evidenceDelayMs = 0;
    }

    let evidenceDelayMs = 0;

    async function startProcessing() {
        resetToIdle(); // Clear previous state just in case
        
        querySection.classList.add('processing');
        stepTrackerContainer.classList.remove('hidden');
        screen1.classList.remove('hidden');
        screen3.classList.add('hidden');
        resultsBanner.classList.add('hidden');
        confidenceMeterContainer.classList.add('hidden');

        // Initial states
        [1, 2, 3, 4].forEach(i => setStepState(i, 'pending'));
        document.getElementById('step-2').querySelector('.step-label').textContent = 'Retrieving evidence from PubMed corpus';

        const query = queryInput.value.trim();
        const confidence_threshold = parseFloat(slider.value);

        abortController = new AbortController();

        try {
            const response = await fetch(window.AXIOM_API_URL + "/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                body: JSON.stringify({ query, confidence_threshold }),
                signal: abortController.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep the incomplete line in the buffer

                let currentEvent = null;

                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    
                    try {
                        const event = JSON.parse(line);
                        handleSseEvent(event.type, event.data);
                    } catch (e) {
                        console.error("Error parsing SSE JSON line", e, line);
                    }
                }
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error("Stream error:", error);
                showError("Connection lost. Please retry.");
            }
        }
    }

    function showError(msg) {
        screen1.classList.add('hidden');
        stepTrackerContainer.classList.add('hidden');
        screen3.classList.remove('hidden');
        resultsBanner.classList.remove('hidden');
        
        resultsBanner.style.backgroundColor = 'rgba(248, 113, 113, 0.08)';
        resultsBanner.style.borderBottomColor = 'var(--error)';
        const bannerContent = resultsBanner.querySelector('.banner-content');
        if (bannerContent) {
            bannerContent.style.color = 'var(--error)';
            bannerContent.textContent = msg;
        }
    }

    function handleSseEvent(type, data) {
        if (type === "step_update") {
            const stepNum = data.step;
            const status = data.status;

            if (status === "active") {
                setStepState(stepNum, 'active');
                if (stepNum > 1) {
                    setStepState(stepNum - 1, 'complete');
                }
            } else if (status === "complete") {
                setStepState(stepNum, 'complete');
            } else if (status === "retry") {
                setStepState(stepNum, 'retry');
                setStepState(stepNum + 1, 'pending'); // Ensure next step is pending
            }

        } else if (type === "confidence") {
            confidenceMeterContainer.classList.remove('hidden');
            confidenceMeterLabel.textContent = `Current confidence: ${data.value.toFixed(2)}`;
            confidenceMeterFill.style.width = `${data.value * 100}%`;
            
            if (data.met) {
                 confidenceMeterLabel.style.color = 'var(--primary-teal)';
                 confidenceMeterFill.style.backgroundColor = 'var(--primary-teal)';
                 confidenceMeterStatus.textContent = 'Threshold met';
                 confidenceMeterStatus.style.color = 'var(--primary-teal)';
            } else {
                 confidenceMeterLabel.style.color = 'var(--amber)';
                 confidenceMeterFill.style.backgroundColor = 'var(--amber)';
                 confidenceMeterStatus.textContent = 'Below threshold — retrying...';
                 confidenceMeterStatus.style.color = 'var(--amber)';
            }
        } else if (type === "evidence") {
            const evidenceSection = document.getElementById('evidence-section');
            if (!evidenceSection) return;
            
            data.items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'evidence-card';
                card.style.animationDelay = `${evidenceDelayMs}ms`;
                evidenceDelayMs += 150;

                const shortAbstract = item.excerpt.length > 150 ? item.excerpt.substring(0, 150) + '...' : item.excerpt;

                card.innerHTML = `
                    <div class="evidence-card-header">
                        <h3 class="evidence-card-title">${item.title}</h3>
                        <span class="evidence-confidence-chip">${item.score.toFixed(2)}</span>
                    </div>
                    <div class="evidence-meta">PubMed &middot; PMID ${item.pmid} &middot; ${item.year}</div>
                    <div class="evidence-excerpt" data-short="${shortAbstract}" data-full="${item.excerpt}">
                        ${shortAbstract}
                    </div>
                    <button class="expand-btn">Show full abstract &darr;</button>
                `;
                
                evidenceSection.appendChild(card);
            });

        } else if (type === "answer") {
            screen1.classList.add('hidden');
            stepTrackerContainer.classList.add('hidden');
            screen3.classList.remove('hidden');
            resultsBanner.classList.remove('hidden');

            const bannerContent = resultsBanner.querySelector('.banner-content');
            bannerContent.textContent = `✓  Evidence generated`;

            const answerText = document.getElementById('answer-text');
            if (answerText) answerText.innerHTML = data.text;
            
            setStepState(4, 'complete');

        } else if (type === "audit") {
            const auditTable = document.getElementById('audit-table');
            if (!auditTable) return;
            
            auditTable.textContent += data.trace + '\n';
        } else if (type === "error") {
            showError(data.message);
        }
    }
});
