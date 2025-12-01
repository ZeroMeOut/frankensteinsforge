document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('forgeForm');
    const imageInput = document.getElementById('image');
    const imageName = document.getElementById('imageName');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const forgeButton = document.getElementById('forgeButton');
    const recordButton = document.getElementById('recordButton');
    const recordText = document.getElementById('recordText');
    const recordTimer = document.getElementById('recordTimer');
    const recordStatus = document.getElementById('recordStatus');
    
    // New elements
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const removeImage = document.getElementById('removeImage');
    const dropZone = document.getElementById('dropZone');
    const audioPlayback = document.getElementById('audioPlayback');
    const audioPlayer = document.getElementById('audioPlayer');
    const removeAudio = document.getElementById('removeAudio');
    const waveform = document.getElementById('waveform');
    const historyButton = document.getElementById('historyButton');
    const historyModal = document.getElementById('historyModal');
    const closeHistory = document.getElementById('closeHistory');
    const historyList = document.getElementById('historyList');
    const clearHistory = document.getElementById('clearHistory');
    
    // Modal elements
    const resultModal = document.getElementById('resultModal');
    const closeModal = document.getElementById('closeModal');
    const ideaOutput = document.getElementById('ideaOutput');
    const copyButton = document.getElementById('copyButton');
    const exportButton = document.getElementById('exportButton');
    const regenerateButton = document.getElementById('regenerateButton');
    const generateStepsButton = document.getElementById('generateStepsButton');
    const stepsOutput = document.getElementById('stepsOutput');
    const stepsContent = document.getElementById('stepsContent');
    const stepsLoading = document.getElementById('stepsLoading');

    let mediaRecorder;
    let audioChunks = [];
    let recordingInterval;
    let recordingSeconds = 0;
    let recordedBlob = null;
    let currentIdea = '';
    let currentInputs = {};
    let audioContext;
    let analyser;
    let animationId;
    const MAX_RECORDING_TIME = 30;
    const HISTORY_KEY = 'forgeHistory';

    // Image preview and drag & drop
    imageInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleImageFile(e.target.files[0]);
        }
    });

    function handleImageFile(file) {
        imageName.textContent = file.name;
        imageName.style.color = '#e0e0e0';
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            imagePreview.classList.remove('hidden');
            dropZone.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }

    removeImage.addEventListener('click', function() {
        imageInput.value = '';
        imageName.textContent = 'No file chosen';
        imageName.style.color = '#666';
        imagePreview.classList.add('hidden');
        dropZone.classList.remove('hidden');
    });

    // Drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            imageInput.files = dataTransfer.files;
            handleImageFile(files[0]);
        }
    });



    // Recording functionality
    recordButton.addEventListener('click', async function() {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            await startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            recordingSeconds = 0;

            // Setup audio visualization
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            
            waveform.classList.remove('hidden');
            drawWaveform();

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                recordedBlob = audioBlob;
                
                // Show audio player
                const audioUrl = URL.createObjectURL(audioBlob);
                audioPlayer.src = audioUrl;
                audioPlayback.classList.remove('hidden');
                waveform.classList.add('hidden');
                
                // Update status display
                recordStatus.textContent = `Recorded (${recordingSeconds}s)`;
                recordStatus.classList.add('recorded');

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
                if (audioContext) {
                    audioContext.close();
                }
                if (animationId) {
                    cancelAnimationFrame(animationId);
                }
            };

            mediaRecorder.start();
            recordButton.classList.add('recording');
            recordText.textContent = 'Stop';
            recordTimer.classList.add('active');

            // Update timer
            recordingInterval = setInterval(() => {
                recordingSeconds++;
                recordTimer.textContent = `${recordingSeconds}s`;

                if (recordingSeconds >= MAX_RECORDING_TIME) {
                    stopRecording();
                }
            }, 1000);

        } catch (error) {
            errorDiv.textContent = `⚠️ Microphone access denied: ${error.message}`;
            errorDiv.classList.remove('hidden');
        }
    }

    function drawWaveform() {
        const canvas = waveform;
        const ctx = canvas.getContext('2d');
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        canvas.width = canvas.offsetWidth;
        canvas.height = 60;

        function draw() {
            animationId = requestAnimationFrame(draw);
            analyser.getByteTimeDomainData(dataArray);

            ctx.fillStyle = '#0a0a0a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.lineWidth = 2;
            ctx.strokeStyle = '#4ade80';
            ctx.beginPath();

            const sliceWidth = canvas.width / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvas.height / 2;

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }

                x += sliceWidth;
            }

            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
        }

        draw();
    }

    removeAudio.addEventListener('click', function() {
        recordedBlob = null;
        audioPlayer.src = '';
        audioPlayback.classList.add('hidden');
        recordStatus.textContent = 'No recording';
        recordStatus.classList.remove('recorded');
        recordingSeconds = 0;
        recordTimer.textContent = '';
    });

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordButton.classList.remove('recording');
            recordText.textContent = 'Record';
            recordTimer.classList.remove('active');
            clearInterval(recordingInterval);
        }
    }

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate recording
        if (!recordedBlob) {
            errorDiv.textContent = '⚠️ Please record audio before submitting';
            errorDiv.classList.remove('hidden');
            return;
        }

        // Hide previous errors
        errorDiv.classList.add('hidden');
        
        // Show loading
        loadingDiv.classList.remove('hidden');
        forgeButton.disabled = true;

        try {
            const formData = new FormData();
            formData.append('image', imageInput.files[0]);
            formData.append('audio', recordedBlob, 'recording.webm');
            formData.append('text', document.getElementById('text').value);

            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store idea and inputs
                currentIdea = data.idea;
                currentInputs = {
                    text: data.inputs.text,
                    imageFilename: data.inputs.image_filename,
                    audioFilename: data.inputs.audio_filename,
                    timestamp: new Date().toISOString()
                };
                
                // Save to history
                saveToHistory(currentIdea, currentInputs);
                
                // Show modal with formatting
                let formattedIdea = currentIdea
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Convert **text** to bold
                    .replace(/\n/g, '<br>'); // Convert line breaks
                ideaOutput.innerHTML = formattedIdea;
                resultModal.classList.remove('hidden');
                stepsOutput.classList.add('hidden');
            } else {
                throw new Error(data.detail || 'Failed to generate idea');
            }
        } catch (error) {
            // Show error
            errorDiv.textContent = `⚠️ Error: ${error.message}`;
            errorDiv.classList.remove('hidden');
        } finally {
            // Hide loading
            loadingDiv.classList.add('hidden');
            forgeButton.disabled = false;
        }
    });

    // Modal close handlers
    closeModal.addEventListener('click', function() {
        resultModal.classList.add('hidden');
    });

    resultModal.addEventListener('click', function(e) {
        if (e.target === resultModal) {
            resultModal.classList.add('hidden');
        }
    });

    // Copy to clipboard
    copyButton.addEventListener('click', async function() {
        try {
            await navigator.clipboard.writeText(currentIdea);
            const originalText = copyButton.textContent;
            copyButton.textContent = '✓ Copied!';
            setTimeout(() => {
                copyButton.textContent = originalText;
            }, 2000);
        } catch (error) {
            alert('Failed to copy to clipboard');
        }
    });

    // Generate steps
    generateStepsButton.addEventListener('click', async function() {
        stepsOutput.classList.add('hidden');
        stepsLoading.classList.remove('hidden');
        generateStepsButton.disabled = true;

        try {
            const response = await fetch('/generate-steps', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idea: currentIdea })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Format the steps with proper line breaks and bold text
                let formattedSteps = data.steps
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Convert **text** to bold
                    .replace(/\n/g, '<br>'); // Convert line breaks
                stepsContent.innerHTML = formattedSteps;
                stepsOutput.classList.remove('hidden');
            } else {
                throw new Error(data.detail || 'Failed to generate steps');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            stepsLoading.classList.add('hidden');
            generateStepsButton.disabled = false;
        }
    });

    // Export functionality
    exportButton.addEventListener('click', function() {
        const exportData = {
            idea: currentIdea,
            inputs: currentInputs,
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `forge-idea-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        const originalText = exportButton.textContent;
        exportButton.textContent = '✓ Exported!';
        setTimeout(() => {
            exportButton.textContent = originalText;
        }, 2000);
    });

    // Regenerate functionality
    regenerateButton.addEventListener('click', async function() {
        if (!currentInputs.text) {
            alert('No previous inputs to regenerate from');
            return;
        }
        
        resultModal.classList.add('hidden');
        
        // Trigger regeneration with same inputs
        alert('Regeneration requires re-uploading files. Please submit the form again with your files.');
    });

    // History functionality
    function saveToHistory(idea, inputs) {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history.unshift({ idea, inputs, timestamp: new Date().toISOString() });
        
        // Keep only last 20 items
        if (history.length > 20) {
            history = history.slice(0, 20);
        }
        
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    }

    function loadHistory() {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        
        if (history.length === 0) {
            historyList.innerHTML = '<p class="empty-history">No history yet. Generate your first idea!</p>';
            return;
        }
        
        historyList.innerHTML = history.map((item, index) => {
            const date = new Date(item.timestamp);
            return `
                <div class="history-item" data-index="${index}">
                    <div class="history-header">
                        <span class="history-date">${date.toLocaleDateString()} ${date.toLocaleTimeString()}</span>
                        <button class="history-delete" data-index="${index}">🗑️</button>
                    </div>
                    <div class="history-idea">${item.idea}</div>
                    <div class="history-meta">
                        <span>📝 ${item.inputs.text.substring(0, 50)}${item.inputs.text.length > 50 ? '...' : ''}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add click handlers
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', function(e) {
                if (e.target.classList.contains('history-delete')) {
                    return;
                }
                const index = parseInt(this.dataset.index);
                const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
                currentIdea = history[index].idea;
                currentInputs = history[index].inputs;
                let formattedIdea = currentIdea
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Convert **text** to bold
                    .replace(/\n/g, '<br>'); // Convert line breaks
                ideaOutput.innerHTML = formattedIdea;
                historyModal.classList.add('hidden');
                resultModal.classList.remove('hidden');
                stepsOutput.classList.add('hidden');
            });
        });
        
        document.querySelectorAll('.history-delete').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const index = parseInt(this.dataset.index);
                let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
                history.splice(index, 1);
                localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
                loadHistory();
            });
        });
    }

    historyButton.addEventListener('click', function() {
        loadHistory();
        historyModal.classList.remove('hidden');
    });

    closeHistory.addEventListener('click', function() {
        historyModal.classList.add('hidden');
    });

    clearHistory.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all history?')) {
            localStorage.removeItem(HISTORY_KEY);
            loadHistory();
        }
    });

    historyModal.addEventListener('click', function(e) {
        if (e.target === historyModal) {
            historyModal.classList.add('hidden');
        }
    });

    // Template functionality
    const templates = {
        tech: "I want to build a web application that helps people solve everyday problems using modern technology.",
        art: "I want to create an artistic project that combines traditional and digital media to express creativity.",
        business: "I want to start a business that provides value to customers while being sustainable and scalable."
    };

    document.querySelectorAll('.template-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const template = this.dataset.template;
            document.getElementById('text').value = templates[template];
            
            // Visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
        });
    });

});


// Perlin Noise Background Animation
(function() {
    const canvas = document.getElementById('noiseCanvas');
    const ctx = canvas.getContext('2d');
    
    let time = 0;
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Simple noise function (pseudo-Perlin)
    function noise(x, y, t) {
        const n = Math.sin(x * 0.01 + t) * Math.cos(y * 0.01 + t) * 0.5 + 0.5;
        return n;
    }
    
    function drawNoise() {
        const imageData = ctx.createImageData(canvas.width, canvas.height);
        const data = imageData.data;
        
        const scale = 3; // Lower = more detail, higher = smoother
        
        for (let y = 0; y < canvas.height; y += scale) {
            for (let x = 0; x < canvas.width; x += scale) {
                const value = noise(x, y, time);
                
                // Dark green color based on noise value
                const green = Math.floor(value * 60 + 10); // 10-70 range
                const red = Math.floor(value * 20); // 0-20 range
                const blue = Math.floor(value * 20); // 0-20 range
                
                // Fill a block instead of single pixel for performance
                for (let dy = 0; dy < scale && y + dy < canvas.height; dy++) {
                    for (let dx = 0; dx < scale && x + dx < canvas.width; dx++) {
                        const index = ((y + dy) * canvas.width + (x + dx)) * 4;
                        data[index] = red;
                        data[index + 1] = green;
                        data[index + 2] = blue;
                        data[index + 3] = 255;
                    }
                }
            }
        }
        
        ctx.putImageData(imageData, 0, 0);
        
        time += 0.005; // Animation speed
        requestAnimationFrame(drawNoise);
    }
    
    drawNoise();
})();
