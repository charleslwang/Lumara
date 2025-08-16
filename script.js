// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  // Navigation
  const navLinks = document.querySelectorAll('.nav-links a');
  const sections = document.querySelectorAll('.section');
  
  // Form elements
  const promptInput = document.getElementById('prompt');
  const modelSelect = document.getElementById('model');
  const apiKeyInput = document.getElementById('api-key');
  const iterationsInput = document.getElementById('iterations');
  const refineButton = document.getElementById('refine-button');
  const stopButton = document.getElementById('stop-button');
  const resultsSection = document.getElementById('results');
  
  // Progress elements
  const progressContainer = document.getElementById('progress-container');
  const progressFill = document.getElementById('progress-fill');
  const progressText = document.getElementById('progress-text');
  const currentIterationText = document.getElementById('current-iteration-text');
  
  // Results elements
  const tabButtons = document.querySelectorAll('.tab');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const finalOutput = document.getElementById('final-output');
  const iterationsContainer = document.getElementById('iterations-container');
  const restartButton = document.getElementById('restart-from-iteration');
  const viewToggleBtns = document.querySelectorAll('.toggle-btn');
  
  // State variables
  let currentRefinementProcess = null;
  let isProcessing = false;
  let iterationsData = [];
  let selectedIteration = null;
  let currentView = 'timeline';
  
  // Navigation smooth scrolling
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
      
      // Update active link
      document.querySelectorAll('.nav-links a').forEach(link => {
        link.classList.remove('active');
      });
      this.classList.add('active');
    });
  });
  
  // Highlight active section on scroll
  window.addEventListener('scroll', function() {
    const sections = document.querySelectorAll('section');
    let current = '';
    
    sections.forEach(section => {
      const sectionTop = section.offsetTop - 100;
      if (window.scrollY >= sectionTop) {
        current = section.getAttribute('id');
      }
    });
    
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
  
  // Tab switching
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const tabId = button.getAttribute('data-tab');
      
      // Update active tab button
      tabButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      // Show corresponding tab pane
      tabPanes.forEach(pane => pane.classList.remove('active'));
      document.getElementById(`${tabId}-tab`).classList.add('active');
    });
  });
  
  // Refine button click handler
  document.getElementById('refine-button').addEventListener('click', async () => {
    const prompt = promptInput.value.trim();
    const modelOutput = document.getElementById('model-output').value.trim();
    const model = modelSelect.value;
    const apiKey = apiKeyInput.value.trim();
    const maxIterations = parseInt(iterationsInput?.value) || 3;
    
    if (!prompt || !modelOutput || !apiKey) {
      // Show elegant error message
      const formHeader = document.querySelector('.form-header');
      let errorMsg = document.querySelector('.error-message');
      
      if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.className = 'error-message';
        formHeader.appendChild(errorMsg);
      }
      
      errorMsg.textContent = 'Please fill in all required fields';
      errorMsg.style.opacity = '1';
      
      setTimeout(() => {
        errorMsg.style.opacity = '0';
      }, 3000);
      
      return;
    }
    
    // Start processing
    isProcessing = true;
    startProgressIndicator(maxIterations);
    
    // Update button states
    refineButton.innerHTML = '<span class="spinner"></span> Processing...';
    refineButton.disabled = true;
    stopButton.classList.remove('hidden');
    
    // Clear previous results
    iterationsData = [];
    selectedIteration = null;
    
    try {
      // Call the backend API using config
      const BACKEND_URL = LUMARA_CONFIG.BACKEND_URL + LUMARA_CONFIG.ENDPOINTS.REFINE;
      console.log('Calling backend:', BACKEND_URL);
      
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          model_output: modelOutput,
          model,
          api_key: apiKey,
          max_iterations: maxIterations
        })
      });
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const result = await response.json();
      
      // Check if there was an error
      if (result.error) {
        throw new Error(result.error);
      }
      
      // Display results using new system
      displayResults(result);
      
      // Scroll to results
      resultsSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      console.error('Error:', error);
      
      // More detailed error handling
      let errorMessage = 'An error occurred during refinement. ';
      
      if (error.message.includes('API request failed')) {
        errorMessage += 'The server returned an error. Please check if the backend is running and your API key is valid.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage += 'Could not connect to the server. Please ensure the backend is running on localhost:5000.';
      } else if (error.message.includes('API key')) {
        errorMessage += 'Invalid API key. Please check your Google Gemini API key.';
      } else {
        errorMessage += `Details: ${error.message}`;
      }
      
      // Show detailed error in console for debugging
      console.error('Detailed error information:', {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });
      
      alert(errorMessage);
    } finally {
      // Reset UI state
      stopProcessing();
    }
  });
  
  // Display results in the UI
  function displayResults(result) {
    // Display final output
    finalOutput.textContent = result.refined_output;
    
    // Display iterations using new system
    if (result.iterations_data && result.iterations_data.length > 0) {
      displayIterations(result.iterations_data);
    }
    
    // Show results section
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Display evaluation scores if available
    const scoresContainer = document.getElementById('scores-container');
    if (scoresContainer && result.scores) {
      scoresContainer.innerHTML = '';
      
      // Overall score
      const overallScore = document.createElement('div');
      overallScore.className = 'score-card';
      overallScore.innerHTML = `
        <h4>Overall</h4>
        <div class="score-value">${result.scores.overall.toFixed(1)}/10</div>
      `;
      scoresContainer.appendChild(overallScore);
      
      // Detail scores
      if (result.scores.details) {
        for (const [key, value] of Object.entries(result.scores.details)) {
          const scoreCard = document.createElement('div');
          scoreCard.className = 'score-card';
          scoreCard.innerHTML = `
            <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
            <div class="score-value">${value.toFixed(1)}/10</div>
          `;
          scoresContainer.appendChild(scoreCard);
        }
      }
    }
  }
  
  // Progress indicator functions
  function startProgressIndicator(maxIterations) {
    progressContainer.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = 'Initializing refinement process...';
    currentIterationText.textContent = 'Preparing first iteration...';
  }
  
  function updateProgress(currentIteration, maxIterations, status = '') {
    const progress = (currentIteration / maxIterations) * 100;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = status || `Processing iteration ${currentIteration} of ${maxIterations}`;
    currentIterationText.textContent = `Iteration ${currentIteration}: ${status || 'In progress...'}`;
  }
  
  function stopProcessing() {
    isProcessing = false;
    progressContainer.classList.add('hidden');
    refineButton.innerHTML = '<span class="button-text"><i class="fas fa-sparkles"></i> Refine Output</span>';
    refineButton.disabled = false;
    stopButton.classList.add('hidden');
  }
  
  // Stop button handler
  stopButton?.addEventListener('click', () => {
    if (currentRefinementProcess) {
      currentRefinementProcess.abort();
    }
    stopProcessing();
    alert('Refinement process stopped.');
  });
  
  // Enhanced iteration display
  function displayIterations(iterations) {
    iterationsContainer.innerHTML = '';
    iterationsData = iterations;
    
    if (currentView === 'timeline') {
      displayTimelineView(iterations);
    } else {
      displayComparisonView(iterations);
    }
  }
  
  function displayTimelineView(iterations) {
    iterations.forEach((iteration, index) => {
      const iterationEl = document.createElement('div');
      iterationEl.className = 'iteration-item selectable';
      iterationEl.dataset.iteration = index;
      
      iterationEl.innerHTML = `
        <div class="iteration-header">
          <span class="iteration-number">Iteration ${index + 1}</span>
          <span class="iteration-score">Score: ${(iteration.score * 100).toFixed(0)}%</span>
        </div>
        <div class="iteration-content">${iteration.solution}</div>
      `;
      
      iterationEl.addEventListener('click', () => selectIteration(index));
      iterationsContainer.appendChild(iterationEl);
    });
  }
  
  function displayComparisonView(iterations) {
    if (iterations.length < 2) {
      iterationsContainer.innerHTML = '<p>Need at least 2 iterations for comparison view.</p>';
      return;
    }
    
    const comparisonEl = document.createElement('div');
    comparisonEl.className = 'comparison-view';
    
    const firstIteration = iterations[0];
    const lastIteration = iterations[iterations.length - 1];
    
    comparisonEl.innerHTML = `
      <div class="comparison-side">
        <h4>Initial Output (Iteration 1)</h4>
        <div class="iteration-content">${firstIteration.solution}</div>
      </div>
      <div class="comparison-side">
        <h4>Final Output (Iteration ${iterations.length})</h4>
        <div class="iteration-content">${lastIteration.solution}</div>
      </div>
    `;
    
    iterationsContainer.appendChild(comparisonEl);
  }
  
  function selectIteration(index) {
    // Remove previous selection
    document.querySelectorAll('.iteration-item.selected').forEach(el => {
      el.classList.remove('selected');
    });
    
    // Select new iteration
    const iterationEl = document.querySelector(`[data-iteration="${index}"]`);
    if (iterationEl) {
      iterationEl.classList.add('selected');
      selectedIteration = index;
      restartButton.classList.remove('hidden');
    }
  }
  
  // View toggle handlers
  viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewToggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentView = btn.dataset.view;
      
      if (iterationsData.length > 0) {
        displayIterations(iterationsData);
      }
    });
  });
  
  // Restart from iteration handler
  restartButton?.addEventListener('click', () => {
    if (selectedIteration !== null) {
      const confirmRestart = confirm(`Restart refinement from iteration ${selectedIteration + 1}?`);
      if (confirmRestart) {
        // TODO: Implement restart functionality
        alert('Restart functionality will be implemented in the backend.');
      }
    }
  });
});
