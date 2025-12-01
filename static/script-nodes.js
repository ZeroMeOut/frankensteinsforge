// Node Graph System for Frankenstein's Forge
class NodeGraph {
    constructor() {
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.draggedNode = null;
        this.dragOffset = { x: 0, y: 0 };
        this.connectionMode = false;
        this.sourceNode = null;
        this.maxNodes = 10;
        
        // Canvas for drawing connections
        this.canvas = document.getElementById('graphCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Containers
        this.container = document.getElementById('graphContainer');
        this.nodesContainer = document.getElementById('nodesContainer');
        
        // Initialize canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Node counter
        this.updateNodeCount();
    }
    
    resizeCanvas() {
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.drawConnections();
    }
    
    createNode(type, x = null, y = null) {
        if (this.nodes.length >= this.maxNodes) {
            alert(`Maximum ${this.maxNodes} nodes allowed`);
            return null;
        }
        
        const id = Date.now() + Math.random();
        
        // Default position (random in center area)
        if (x === null || y === null) {
            x = Math.random() * (this.canvas.width - 200) + 100;
            y = Math.random() * (this.canvas.height - 200) + 100;
        }
        
        const node = {
            id,
            type,
            x,
            y,
            data: null,
            element: this.createNodeElement(id, type, x, y)
        };
        
        this.nodes.push(node);
        this.updateNodeCount();
        this.updateGenerateButton();
        
        return node;
    }
    
    createNodeElement(id, type, x, y) {
        const nodeEl = document.createElement('div');
        nodeEl.className = `node ${type}-node`;
        nodeEl.style.left = x + 'px';
        nodeEl.style.top = y + 'px';
        nodeEl.dataset.nodeId = id;
        
        const icons = {
            text: '📝',
            image: '🖼️',
            audio: '🎤'
        };
        
        const typeLabels = {
            text: 'Text',
            image: 'Image',
            audio: 'Audio'
        };
        
        nodeEl.innerHTML = `
            <div class="node-header">
                <span class="node-type">${typeLabels[type]}</span>
                <div class="node-actions">
                    <button class="node-btn edit" title="Edit">✏️</button>
                    <button class="node-btn delete" title="Delete">🗑️</button>
                </div>
            </div>
            <div class="node-icon">${icons[type]}</div>
            <div class="node-content">Click to edit</div>
        `;
        
        // Event listeners
        nodeEl.addEventListener('mousedown', (e) => this.onNodeMouseDown(e, id));
        nodeEl.addEventListener('click', (e) => this.onNodeClick(e, id));
        
        // Edit button
        nodeEl.querySelector('.edit').addEventListener('click', (e) => {
            e.stopPropagation();
            this.editNode(id);
        });
        
        // Delete button
        nodeEl.querySelector('.delete').addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteNode(id);
        });
        
        this.nodesContainer.appendChild(nodeEl);
        return nodeEl;
    }
    
    onNodeMouseDown(e, nodeId) {
        if (e.target.closest('.node-btn')) return;
        
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        this.draggedNode = node;
        const rect = node.element.getBoundingClientRect();
        const containerRect = this.container.getBoundingClientRect();
        
        this.dragOffset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        
        node.element.classList.add('dragging');
        
        const onMouseMove = (e) => {
            if (!this.draggedNode) return;
            
            const x = e.clientX - containerRect.left - this.dragOffset.x;
            const y = e.clientY - containerRect.top - this.dragOffset.y;
            
            this.draggedNode.x = Math.max(0, Math.min(x, this.canvas.width - 150));
            this.draggedNode.y = Math.max(0, Math.min(y, this.canvas.height - 100));
            
            this.draggedNode.element.style.left = this.draggedNode.x + 'px';
            this.draggedNode.element.style.top = this.draggedNode.y + 'px';
            
            this.drawConnections();
        };
        
        const onMouseUp = () => {
            if (this.draggedNode) {
                this.draggedNode.element.classList.remove('dragging');
                this.draggedNode = null;
            }
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        
        e.preventDefault();
    }
    
    onNodeClick(e, nodeId) {
        if (e.target.closest('.node-btn')) return;
        if (this.draggedNode) return;
        
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        // Connection mode
        if (!this.sourceNode) {
            this.sourceNode = node;
            this.selectNode(node);
            document.getElementById('modeText').textContent = 'Click another node to connect';
        } else {
            if (this.sourceNode.id !== node.id) {
                this.createConnection(this.sourceNode.id, node.id);
            }
            this.deselectAll();
            this.sourceNode = null;
            document.getElementById('modeText').textContent = 'Click nodes to connect them';
        }
    }
    
    selectNode(node) {
        this.deselectAll();
        node.element.classList.add('selected');
        this.selectedNode = node;
    }
    
    deselectAll() {
        this.nodes.forEach(n => n.element.classList.remove('selected'));
        this.selectedNode = null;
    }
    
    editNode(nodeId) {
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        openNodeEditor(node);
    }
    
    deleteNode(nodeId) {
        const index = this.nodes.findIndex(n => n.id === nodeId);
        if (index === -1) return;
        
        const node = this.nodes[index];
        
        // Remove connections
        this.connections = this.connections.filter(
            c => c.source !== nodeId && c.target !== nodeId
        );
        
        // Remove element
        node.element.remove();
        
        // Remove from array
        this.nodes.splice(index, 1);
        
        this.drawConnections();
        this.updateNodeCount();
        this.updateGenerateButton();
    }
    
    updateNode(nodeId, data) {
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        node.data = data;
        
        // Update visual content
        const contentEl = node.element.querySelector('.node-content');
        
        if (node.type === 'text') {
            contentEl.textContent = data.text.substring(0, 100) + (data.text.length > 100 ? '...' : '');
        } else if (node.type === 'image') {
            if (data.preview) {
                contentEl.innerHTML = `<img src="${data.preview}" class="node-image-preview" alt="Image">`;
            } else {
                contentEl.textContent = data.filename || 'Image uploaded';
            }
        } else if (node.type === 'audio') {
            const duration = data.duration || 0;
            contentEl.textContent = `Audio ${duration}s`;
        }
        
        this.updateGenerateButton();
    }
    
    createConnection(sourceId, targetId) {
        // Check if connection already exists
        const exists = this.connections.some(
            c => (c.source === sourceId && c.target === targetId) ||
                 (c.source === targetId && c.target === sourceId)
        );
        
        if (exists) {
            alert('Connection already exists between these nodes');
            return;
        }
        
        const connection = {
            id: Date.now() + Math.random(),
            source: sourceId,
            target: targetId,
            weight: 0.5
        };
        
        this.connections.push(connection);
        this.drawConnections();
        this.updateGenerateButton();
    }
    
    drawConnections() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.connections.forEach(conn => {
            const sourceNode = this.nodes.find(n => n.id === conn.source);
            const targetNode = this.nodes.find(n => n.id === conn.target);
            
            if (!sourceNode || !targetNode) return;
            
            // Calculate center points of nodes
            const sourceX = sourceNode.x + 75; // Half of node width
            const sourceY = sourceNode.y + 50; // Half of node height
            const targetX = targetNode.x + 75;
            const targetY = targetNode.y + 50;
            
            // Draw line
            this.ctx.strokeStyle = `rgba(74, 222, 128, ${conn.weight})`;
            this.ctx.lineWidth = 2 + (conn.weight * 2);
            this.ctx.beginPath();
            this.ctx.moveTo(sourceX, sourceY);
            this.ctx.lineTo(targetX, targetY);
            this.ctx.stroke();
            
            // Draw weight indicator at midpoint
            const midX = (sourceX + targetX) / 2;
            const midY = (sourceY + targetY) / 2;
            
            // Clickable area for weight editing
            this.ctx.fillStyle = 'rgba(74, 222, 128, 0.3)';
            this.ctx.beginPath();
            this.ctx.arc(midX, midY, 15, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Weight value
            this.ctx.fillStyle = '#4ade80';
            this.ctx.font = '12px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(conn.weight.toFixed(1), midX, midY + 4);
        });
    }
    
    getConnectionAtPoint(x, y) {
        for (let conn of this.connections) {
            const sourceNode = this.nodes.find(n => n.id === conn.source);
            const targetNode = this.nodes.find(n => n.id === conn.target);
            
            if (!sourceNode || !targetNode) continue;
            
            const sourceX = sourceNode.x + 75;
            const sourceY = sourceNode.y + 50;
            const targetX = targetNode.x + 75;
            const targetY = targetNode.y + 50;
            
            const midX = (sourceX + targetX) / 2;
            const midY = (sourceY + targetY) / 2;
            
            const distance = Math.sqrt((x - midX) ** 2 + (y - midY) ** 2);
            
            if (distance < 20) {
                return conn;
            }
        }
        
        return null;
    }
    
    updateNodeCount() {
        document.getElementById('nodeCount').textContent = this.nodes.length;
        
        // Disable add buttons if at max
        const atMax = this.nodes.length >= this.maxNodes;
        document.getElementById('addTextNode').disabled = atMax;
        document.getElementById('addImageNode').disabled = atMax;
        document.getElementById('addAudioNode').disabled = atMax;
    }
    
    updateGenerateButton() {
        const hasNodes = this.nodes.length > 0;
        const hasData = this.nodes.some(n => n.data !== null);
        const hasConnections = this.connections.length > 0;
        
        const canGenerate = hasNodes && hasData && hasConnections;
        document.getElementById('generateBtn').disabled = !canGenerate;
    }
    
    clearGraph() {
        if (this.nodes.length === 0) return;
        
        if (confirm('Are you sure you want to clear all nodes and connections?')) {
            this.nodes.forEach(node => node.element.remove());
            this.nodes = [];
            this.connections = [];
            this.sourceNode = null;
            this.selectedNode = null;
            
            this.drawConnections();
            this.updateNodeCount();
            this.updateGenerateButton();
        }
    }
    
    async serializeForAPI() {
        const serializedNodes = [];
        
        for (let node of this.nodes) {
            if (!node.data) continue;
            
            const serialized = {
                id: node.id,
                type: node.type
            };
            
            if (node.type === 'text') {
                serialized.content = node.data.text;
            } else if (node.type === 'image') {
                serialized.file = node.data.file;
                serialized.filename = node.data.filename;
            } else if (node.type === 'audio') {
                serialized.file = node.data.blob;
                serialized.filename = 'audio.webm';
            }
            
            serializedNodes.push(serialized);
        }
        
        const serializedConnections = this.connections.map(conn => ({
            source: conn.source,
            target: conn.target,
            weight: conn.weight
        }));
        
        return {
            nodes: serializedNodes,
            connections: serializedConnections
        };
    }
}

// Global graph instance
const graph = new NodeGraph();

// Initialize UI
document.addEventListener('DOMContentLoaded', function() {
    // Add node buttons
    document.getElementById('addTextNode').addEventListener('click', () => {
        const node = graph.createNode('text');
        if (node) graph.editNode(node.id);
    });
    
    document.getElementById('addImageNode').addEventListener('click', () => {
        const node = graph.createNode('image');
        if (node) graph.editNode(node.id);
    });
    
    document.getElementById('addAudioNode').addEventListener('click', () => {
        const node = graph.createNode('audio');
        if (node) graph.editNode(node.id);
    });
    
    document.getElementById('clearGraph').addEventListener('click', () => {
        graph.clearGraph();
    });
    
    // Canvas click for connection weight editing
    document.getElementById('graphCanvas').addEventListener('click', (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const connection = graph.getConnectionAtPoint(x, y);
        if (connection) {
            openWeightModal(connection);
        }
    });
    
    // Generate button
    document.getElementById('generateBtn').addEventListener('click', async () => {
        await generateFromGraph();
    });
    
    // Clear results
    document.getElementById('clearResults').addEventListener('click', () => {
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💡</div>
                <p>Create nodes and connections, then generate ideas!</p>
                <div class="help-text">
                    <h4>How to use:</h4>
                    <ol>
                        <li>Add nodes (Text, Image, or Audio)</li>
                        <li>Click a node, then click another to connect them</li>
                        <li>Set connection weights by clicking on connections</li>
                        <li>Click "Generate Idea" to create!</li>
                    </ol>
                </div>
            </div>
        `;
    });
});

// Node Editor Modal
let currentEditingNode = null;
let mediaRecorder = null;
let audioChunks = [];
let recordingInterval = null;
let recordingSeconds = 0;
let recordedBlob = null;

function openNodeEditor(node) {
    currentEditingNode = node;
    const modal = document.getElementById('nodeEditorModal');
    const title = document.getElementById('editorTitle');
    
    title.textContent = `Edit ${node.type.charAt(0).toUpperCase() + node.type.slice(1)} Node`;
    
    // Hide all editors
    document.getElementById('textEditor').classList.add('hidden');
    document.getElementById('imageEditor').classList.add('hidden');
    document.getElementById('audioEditor').classList.add('hidden');
    
    // Show appropriate editor
    if (node.type === 'text') {
        document.getElementById('textEditor').classList.remove('hidden');
        document.getElementById('textInput').value = node.data?.text || '';
        document.getElementById('textInput').focus();
    } else if (node.type === 'image') {
        document.getElementById('imageEditor').classList.remove('hidden');
        document.getElementById('imageInput').value = '';
        document.getElementById('imageFileName').textContent = 'No file chosen';
        document.getElementById('imagePreviewContainer').classList.add('hidden');
        
        if (node.data?.preview) {
            document.getElementById('imagePreview').src = node.data.preview;
            document.getElementById('imagePreviewContainer').classList.remove('hidden');
        }
    } else if (node.type === 'audio') {
        document.getElementById('audioEditor').classList.remove('hidden');
        document.getElementById('audioPlayback').classList.add('hidden');
        document.getElementById('waveform').classList.add('hidden');
        recordedBlob = node.data?.blob || null;
        
        if (recordedBlob) {
            const url = URL.createObjectURL(recordedBlob);
            document.getElementById('audioPlayer').src = url;
            document.getElementById('audioPlayback').classList.remove('hidden');
        }
    }
    
    modal.classList.remove('hidden');
}

function closeNodeEditor() {
    document.getElementById('nodeEditorModal').classList.add('hidden');
    currentEditingNode = null;
    
    // Stop recording if active
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// Image handling
document.getElementById('imageInput').addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        document.getElementById('imageFileName').textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('imagePreview').src = e.target.result;
            document.getElementById('imagePreviewContainer').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

// Audio recording
document.getElementById('recordButton').addEventListener('click', async function() {
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
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            recordedBlob = audioBlob;
            
            const audioUrl = URL.createObjectURL(audioBlob);
            document.getElementById('audioPlayer').src = audioUrl;
            document.getElementById('audioPlayback').classList.remove('hidden');
            document.getElementById('waveform').classList.add('hidden');
            
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        document.getElementById('recordButton').classList.add('recording');
        document.getElementById('recordText').textContent = 'Stop';
        document.getElementById('recordTimer').classList.add('active');
        document.getElementById('waveform').classList.remove('hidden');
        
        recordingInterval = setInterval(() => {
            recordingSeconds++;
            document.getElementById('recordTimer').textContent = `${recordingSeconds}s`;
            
            if (recordingSeconds >= 30) {
                stopRecording();
            }
        }, 1000);
        
    } catch (error) {
        alert('Microphone access denied: ' + error.message);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        document.getElementById('recordButton').classList.remove('recording');
        document.getElementById('recordText').textContent = 'Record';
        document.getElementById('recordTimer').classList.remove('active');
        clearInterval(recordingInterval);
    }
}

// Save node
document.getElementById('saveNode').addEventListener('click', () => {
    if (!currentEditingNode) return;
    
    let data = null;
    
    if (currentEditingNode.type === 'text') {
        const text = document.getElementById('textInput').value.trim();
        if (!text) {
            alert('Please enter some text');
            return;
        }
        data = { text };
    } else if (currentEditingNode.type === 'image') {
        const file = document.getElementById('imageInput').files[0];
        if (!file && !currentEditingNode.data) {
            alert('Please select an image');
            return;
        }
        
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                data = {
                    file: file,
                    filename: file.name,
                    preview: e.target.result
                };
                graph.updateNode(currentEditingNode.id, data);
                closeNodeEditor();
            };
            reader.readAsDataURL(file);
            return; // Async, will close after reader finishes
        } else {
            closeNodeEditor();
            return;
        }
    } else if (currentEditingNode.type === 'audio') {
        if (!recordedBlob) {
            alert('Please record audio');
            return;
        }
        data = {
            blob: recordedBlob,
            duration: recordingSeconds
        };
    }
    
    graph.updateNode(currentEditingNode.id, data);
    closeNodeEditor();
});

// Cancel node editor
document.getElementById('cancelNode').addEventListener('click', closeNodeEditor);
document.getElementById('closeNodeEditor').addEventListener('click', closeNodeEditor);

// Weight Modal
let currentEditingConnection = null;

function openWeightModal(connection) {
    currentEditingConnection = connection;
    const modal = document.getElementById('weightModal');
    const slider = document.getElementById('weightSlider');
    const value = document.getElementById('weightValue');
    
    slider.value = connection.weight * 100;
    value.textContent = connection.weight.toFixed(1);
    
    modal.classList.remove('hidden');
}

function closeWeightModal() {
    document.getElementById('weightModal').classList.add('hidden');
    currentEditingConnection = null;
}

document.getElementById('weightSlider').addEventListener('input', function(e) {
    const value = e.target.value / 100;
    document.getElementById('weightValue').textContent = value.toFixed(1);
});

document.getElementById('saveWeight').addEventListener('click', () => {
    if (!currentEditingConnection) return;
    
    const value = document.getElementById('weightSlider').value / 100;
    currentEditingConnection.weight = value;
    
    graph.drawConnections();
    closeWeightModal();
});

document.getElementById('deleteConnection').addEventListener('click', () => {
    if (!currentEditingConnection) return;
    
    graph.connections = graph.connections.filter(c => c.id !== currentEditingConnection.id);
    graph.drawConnections();
    graph.updateGenerateButton();
    closeWeightModal();
});

document.getElementById('closeWeight').addEventListener('click', closeWeightModal);

// Generate from graph
async function generateFromGraph() {
    const graphData = await graph.serializeForAPI();
    
    // Validate
    if (graphData.nodes.length === 0) {
        alert('Please add at least one node with data');
        return;
    }
    
    if (graphData.connections.length === 0) {
        alert('Please create at least one connection between nodes');
        return;
    }
    
    // Show loading
    document.getElementById('loadingOverlay').classList.remove('hidden');
    
    try {
        const formData = new FormData();
        
        // Build a combined prompt from the graph
        let textParts = [];
        let images = [];
        let audios = [];
        
        // Collect all data
        for (let node of graphData.nodes) {
            if (node.type === 'text') {
                textParts.push(node.content);
            } else if (node.type === 'image') {
                images.push({ file: node.file, filename: node.filename });
            } else if (node.type === 'audio') {
                audios.push({ file: node.file, filename: node.filename });
            }
        }
        
        // Build weighted context description
        let contextDescription = 'Based on the following connected inputs:\n\n';
        
        graphData.connections.forEach(conn => {
            const sourceNode = graphData.nodes.find(n => n.id === conn.source);
            const targetNode = graphData.nodes.find(n => n.id === conn.target);
            
            if (sourceNode && targetNode) {
                contextDescription += `• ${sourceNode.type} connected to ${targetNode.type} (weight: ${conn.weight.toFixed(1)})\n`;
            }
        });
        
        // Combine text with context
        const combinedText = contextDescription + '\n' + textParts.join('\n\n');
        
        formData.append('text', combinedText);
        
        // Add first image and audio (API currently expects one of each)
        if (images.length > 0) {
            formData.append('image', images[0].file, images[0].filename);
        } else {
            // Create a placeholder image if none provided
            const placeholderBlob = await createPlaceholderImage();
            formData.append('image', placeholderBlob, 'placeholder.png');
        }
        
        if (audios.length > 0) {
            formData.append('audio', audios[0].file, audios[0].filename);
        } else {
            // Create a placeholder audio if none provided
            const placeholderBlob = await createPlaceholderAudio();
            formData.append('audio', placeholderBlob, 'placeholder.wav');
        }
        
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayResult(data.idea);
        } else {
            throw new Error(data.error || 'Failed to generate idea');
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

async function createPlaceholderImage() {
    // Create a simple 100x100 white image
    const canvas = document.createElement('canvas');
    canvas.width = 100;
    canvas.height = 100;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 100, 100);
    
    return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png');
    });
}

async function createPlaceholderAudio() {
    // Create a silent audio file
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const sampleRate = audioContext.sampleRate;
    const duration = 0.1; // 0.1 seconds
    const buffer = audioContext.createBuffer(1, sampleRate * duration, sampleRate);
    
    // Create WAV file manually
    const wavData = audioBufferToWav(buffer);
    return new Blob([wavData], { type: 'audio/wav' });
}

function audioBufferToWav(buffer) {
    const length = buffer.length * buffer.numberOfChannels * 2;
    const arrayBuffer = new ArrayBuffer(44 + length);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, buffer.numberOfChannels, true);
    view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * buffer.numberOfChannels * 2, true);
    view.setUint16(32, buffer.numberOfChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, length, true);
    
    return arrayBuffer;
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

// Display result
function displayResult(idea) {
    const container = document.getElementById('resultsContainer');
    
    // Remove empty state if present
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const resultCard = document.createElement('div');
    resultCard.className = 'result-card';
    
    const timestamp = new Date().toLocaleString();
    const formattedIdea = idea
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    resultCard.innerHTML = `
        <div class="result-header">
            <span class="result-timestamp">${timestamp}</span>
            <button class="icon-btn" onclick="this.closest('.result-card').remove()">🗑️</button>
        </div>
        <div class="result-content">${formattedIdea}</div>
        <div class="result-actions">
            <button class="result-btn" onclick="copyResult(this)">📋 Copy</button>
        </div>
        <div class="result-steps hidden"></div>
    `;
    
    container.insertBefore(resultCard, container.firstChild);
}

function copyResult(button) {
    const content = button.closest('.result-card').querySelector('.result-content').textContent;
    navigator.clipboard.writeText(content);
    
    const originalText = button.textContent;
    button.textContent = '✓ Copied!';
    setTimeout(() => {
        button.textContent = originalText;
    }, 2000);
}

async function generateSteps(button, idea) {
    const stepsContainer = button.closest('.result-card').querySelector('.result-steps');
    stepsContainer.innerHTML = '<div class="steps-loading"><div class="spinner-small"></div><p>Generating steps...</p></div>';
    stepsContainer.classList.remove('hidden');
    button.disabled = true;
    
    try {
        const response = await fetch('/generate-steps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea: idea })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const formattedSteps = data.steps
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
            
            stepsContainer.innerHTML = `
                <h4>Implementation Steps</h4>
                <div class="steps-content">${formattedSteps}</div>
            `;
        } else {
            throw new Error(data.error || 'Failed to generate steps');
        }
    } catch (error) {
        stepsContainer.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
    } finally {
        button.disabled = false;
    }
}

// Background noise animation (same as before)
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
    
    function noise(x, y, t) {
        const n = Math.sin(x * 0.01 + t) * Math.cos(y * 0.01 + t) * 0.5 + 0.5;
        return n;
    }
    
    function drawNoise() {
        const imageData = ctx.createImageData(canvas.width, canvas.height);
        const data = imageData.data;
        
        const scale = 3;
        
        for (let y = 0; y < canvas.height; y += scale) {
            for (let x = 0; x < canvas.width; x += scale) {
                const value = noise(x, y, time);
                
                const green = Math.floor(value * 60 + 10);
                const red = Math.floor(value * 20);
                const blue = Math.floor(value * 20);
                
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
        
        time += 0.005;
        requestAnimationFrame(drawNoise);
    }
    
    drawNoise();
})();