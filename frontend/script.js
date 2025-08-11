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
  const runButton = document.getElementById('run-button');
  const resultsSection = document.getElementById('results');
  
  // Results elements
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const finalOutput = document.getElementById('final-output');
  const iterationsList = document.getElementById('iterations-list');
  const evaluationScores = document.getElementById('evaluation-scores');
  
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
    
    // Show loading state
    const refineButton = document.getElementById('refine-button');
    refineButton.innerHTML = '<span class="spinner"></span> Processing...';
    refineButton.disabled = true;
    
    try {
      // Call the backend API
      const response = await fetch('/api/refine', {
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
      
      // Display results
      resultsSection.classList.remove('hidden');
      
      // Set final output
      finalOutput.textContent = result.refined_output;
      
      // Set iteration count
      iterationsCount.textContent = result.iterations;
      
      // Set overall score
      overallScore.textContent = result.scores.overall.toFixed(2);
      
      // Clear previous iterations
      iterationsList.innerHTML = '';
      
      // Add iterations
      result.iterations_data.forEach((iteration, index) => {
        const iterItem = document.createElement('div');
        iterItem.className = 'iteration-item';
        iterItem.innerHTML = `
          <div class="iteration-header">
            <h4>Iteration ${index + 1}</h4>
            <span class="iteration-score">Score: ${iteration.score.toFixed(2)}</span>
          </div>
          <p>${iteration.output}</p>
        `;
        iterationsList.appendChild(iterItem);
      });
      
      // Set evaluation scores
      evaluationScores.innerHTML = '';
      Object.entries(result.scores.details).forEach(([key, value]) => {
        const scoreCard = document.createElement('div');
        scoreCard.className = 'score-card';
        scoreCard.innerHTML = `
          <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
          <div class="score-value">${value.toFixed(2)}</div>
        `;
        evaluationScores.appendChild(scoreCard);
      });
      
      // Scroll to results
      resultsSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred during refinement. Please try again.');
    } finally {
      // Reset button state
      refineButton.innerHTML = 'Refine Output';
      refineButton.disabled = false;
    }
  });
  
  // Display results in the UI
  function displayResults(result) {
    // Display final output
    finalOutput.textContent = result.refined_output;
    
    // Display iterations
    iterationsList.innerHTML = '';
    result.iterations.forEach(iteration => {
      const iterationEl = document.createElement('div');
      iterationEl.className = 'iteration-item';
      
      const header = document.createElement('div');
      header.className = 'iteration-header';
      
      const title = document.createElement('h4');
      title.textContent = `Iteration ${iteration.iteration}`;
      
      const score = document.createElement('div');
      score.textContent = `Score: ${(iteration.score * 100).toFixed(0)}%`;
      score.style.color = 'var(--primary)';
      score.style.fontWeight = 'bold';
      
      header.appendChild(title);
      header.appendChild(score);
      
      const content = document.createElement('div');
      content.className = 'iteration-content';
      content.textContent = iteration.solution;
      
      const critique = document.createElement('div');
      critique.className = 'iteration-critique';
      critique.innerHTML = `<h5>Critique:</h5><p>${iteration.critique}</p>`;
      
      iterationEl.appendChild(header);
      iterationEl.appendChild(content);
      iterationEl.appendChild(critique);
      
      iterationsList.appendChild(iterationEl);
    });
    
    // Display evaluation scores
    evaluationScores.innerHTML = '';
    
    // Overall score
    const overallScore = document.createElement('div');
    overallScore.className = 'score-card';
    overallScore.innerHTML = `
      <h4>Overall</h4>
      <div class="score-value">${(result.scores.overall * 100).toFixed(0)}%</div>
    `;
    evaluationScores.appendChild(overallScore);
    
    // Detail scores
    for (const [key, value] of Object.entries(result.scores.details)) {
      const scoreCard = document.createElement('div');
      scoreCard.className = 'score-card';
      scoreCard.innerHTML = `
        <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
        <div class="score-value">${(value * 100).toFixed(0)}%</div>
      `;
      evaluationScores.appendChild(scoreCard);
    }
  }
});
