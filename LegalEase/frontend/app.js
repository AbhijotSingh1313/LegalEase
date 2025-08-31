// Utility functions
function toggle(el, show) {
  el.classList[show ? "remove" : "add"]("hidden");
}

function showError(message) {
  alert(`Error: ${message}`);
}

function showSuccess(message) {
  console.log(`Success: ${message}`);
}

// Tab switching
document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((b) =>
      b.classList.remove("active")
    );
    document.querySelectorAll(".tab-content").forEach((c) =>
      c.classList.add("hidden")
    );
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.remove("hidden");
  });
});

// DOM elements
const loading = document.getElementById("loading");
const output = document.getElementById("outputPanel");

// Display comprehensive analysis results
function displayResults(data) {
  try {
    console.log("Displaying results:", data);

    // Detailed Summary
    const ds = data.detailed_summary;
    document.getElementById("detailed").innerHTML = `
      <div class="summary-section">
        <h3>Executive Summary</h3>
        <p class="executive-summary">${ds.executive_summary}</p>
        
        <h4>Key Points</h4>
        <ul class="key-points">
          ${ds.key_points.map((pt) => `<li>${pt}</li>`).join("")}
        </ul>
        
        <h4>Financial Terms</h4>
        <div class="financial-terms">
          ${ds.financial_terms.amounts?.length ? 
            `<p><strong>Amounts:</strong> ${ds.financial_terms.amounts.join(', ')}</p>` : 
            '<p>No specific amounts identified</p>'
          }
          ${ds.financial_terms.payment_schedule?.length ? 
            `<p><strong>Payment Schedule:</strong> ${ds.financial_terms.payment_schedule.join(', ')}</p>` : 
            ''
          }
          ${ds.financial_terms.interest_rates?.length ? 
            `<p><strong>Interest Rates:</strong> ${ds.financial_terms.interest_rates.join(', ')}</p>` : 
            ''
          }
          ${ds.financial_terms.payment_methods?.length ? 
            `<p><strong>Payment Methods:</strong> ${ds.financial_terms.payment_methods.join(', ')}</p>` : 
            ''
          }
        </div>
        
        <h4>Timeline</h4>
        <div class="timeline">
          ${ds.timeline?.length ? 
            `<ul>${ds.timeline.map((e) => `<li><strong>${e.event}:</strong> ${e.date}</li>`).join("")}</ul>` :
            '<p>No specific timeline identified</p>'
          }
        </div>
        
        <h4>Contract Details</h4>
        <div class="contract-details">
          <p><strong>Type:</strong> ${ds.contract_type}</p>
          <p><strong>Subject:</strong> ${ds.main_subject}</p>
        </div>
      </div>
    `;

// Key Terms (show definitions only)
document.getElementById("terms").innerHTML = `
  <div class="terms-section">
    <h3>Legal Terms Found in Contract</h3>
    <div class="terms-grid">
      ${data.key_terms.map((k) => 
        `<div class="term-card">
           <h4>${k.term}</h4>
           <p class="definition">${k.definition}</p>
         </div>`
      ).join("")}
    </div>
  </div>
`;


    // Risk Assessment
    const ra = data.risk_assessment;
    document.getElementById("risk").innerHTML = `
      <div class="risk-section">
        <h3>Risk Assessment</h3>
        <div class="risk-overview">
          <div class="risk-level risk-${ra.risk_level.toLowerCase()}">
            <h4>Overall Risk Level: ${ra.risk_level}</h4>
            <p>Risk Score: ${ra.risk_score}/10</p>
          </div>
        </div>
        
        <h4>Risk Factors</h4>
        <ul class="risk-reasons">
          ${ra.reasons.map((r) => `<li>${r}</li>`).join("")}
        </ul>
        
        ${ra.detailed_analysis?.length ? 
          `<h4>Detailed Risk Analysis</h4>
           <div class="detailed-risks">
             ${ra.detailed_analysis.map((analysis) => 
               `<div class="risk-item">
                  <h5>${analysis.factor}</h5>
                  <p><strong>Impact:</strong> ${analysis.impact}</p>
                  <p><strong>Context:</strong> ${analysis.context}</p>
                </div>`
             ).join("")}
           </div>` : 
          ''
        }
      </div>
    `;

    // Obligations
    const ob = data.obligations;
    document.getElementById("obligations").innerHTML = `
      <div class="obligations-section">
        <h3>Contract Obligations</h3>
        
        <div class="obligation-category">
          <h4>Critical Obligations</h4>
          <div class="obligations-list">
            ${ob.critical_obligations?.length ? 
              `<ul>${ob.critical_obligations.map((o) => `<li>${o}</li>`).join("")}</ul>` :
              '<p>No critical obligations identified</p>'
            }
          </div>
        </div>
        
        <div class="obligation-category">
          <h4>Payment Obligations</h4>
          <div class="obligations-list">
            ${ob.payment_obligations?.length ? 
              `<ul>${ob.payment_obligations.map((o) => `<li>${o}</li>`).join("")}</ul>` :
              '<p>No payment obligations identified</p>'
            }
          </div>
        </div>
        
        <div class="obligation-category">
          <h4>Performance Obligations</h4>
          <div class="obligations-list">
            ${ob.performance_obligations?.length ? 
              `<ul>${ob.performance_obligations.map((o) => `<li>${o}</li>`).join("")}</ul>` :
              '<p>No performance obligations identified</p>'
            }
          </div>
        </div>
        
        <div class="obligation-category">
          <h4>All Obligations</h4>
          <div class="obligations-list">
            ${ob.all_obligations?.length ? 
              `<ul>${ob.all_obligations.map((o) => `<li>${o}</li>`).join("")}</ul>` :
              '<p>No obligations identified</p>'
            }
          </div>
        </div>
      </div>
    `;

    // Show results
    toggle(loading, false);
    toggle(output, true);
    
    showSuccess("Contract analysis completed successfully");
    
  } catch (error) {
    console.error("Error displaying results:", error);
    showError("Failed to display analysis results");
    toggle(loading, false);
  }
}

// POST helper with better error handling
async function postJson(url, body) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to server. Please ensure the backend is running.');
    }
    throw error;
  }
}

// Analyze text
document.getElementById("analyzeTextBtn").onclick = async () => {
  const text = document.getElementById("contractInput").value.trim();
  
  if (!text) {
    showError("Please paste contract text first.");
    return;
  }
  
  if (text.length < 100) {
    showError("Contract text is too short for meaningful analysis. Please provide a more complete contract.");
    return;
  }
  
  toggle(loading, true);
  toggle(output, false);
  
  try {
    console.log("Analyzing contract text...");
    const data = await postJson("http://127.0.0.1:8000/analyze-text", {
      contract_text: text
    });
    
    displayResults(data);
    
  } catch (error) {
    console.error("Analysis error:", error);
    showError(error.message || "Failed to analyze contract text");
    toggle(loading, false);
  }
};

// Analyze file
document.getElementById("analyzeBtn").onclick = async () => {
  const fileInput = document.getElementById("upload");
  
  if (!fileInput.files.length) {
    showError("Please choose a file first.");
    return;
  }
  
  const file = fileInput.files[0];
  
  // Validate file size (10MB max)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    showError("File is too large. Maximum size is 10MB.");
    return;
  }
  
  // Validate file type
  const allowedTypes = ['pdf', 'docx', 'txt'];
  const fileExt = file.name.split('.').pop().toLowerCase();
  if (!allowedTypes.includes(fileExt)) {
    showError(`Unsupported file type '${fileExt}'. Please use PDF, DOCX, or TXT files.`);
    return;
  }
  
  toggle(loading, true);
  toggle(output, false);

  const form = new FormData();
  form.append("file", file);

  try {
    console.log(`Uploading and analyzing ${fileExt.toUpperCase()} file...`);
    
    const response = await fetch("http://127.0.0.1:8000/upload-file", {
      method: "POST",
      body: form,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    const data = await response.json();
    displayResults(data);
    
  } catch (error) {
    console.error("Upload error:", error);
    showError(error.message || "Failed to process uploaded file");
    toggle(loading, false);
  }
};

// Ask question with enhanced functionality
document.getElementById("askBtn").onclick = async () => {
  const question = document.getElementById("questionInput").value.trim();
  const qaResult = document.getElementById("qaResult");
  
  if (!question) {
    showError("Please enter a question.");
    return;
  }
  
  if (question.length > 500) {
    showError("Question is too long. Please keep it under 500 characters.");
    return;
  }
  
  const context = document.getElementById("detailed").innerText;
  if (!context || context.length < 100) {
    showError("Please analyze a contract first before asking questions.");
    return;
  }
  
  qaResult.innerHTML = '<div class="thinking">Analyzing your question... Please wait.</div>';
  
  try {
    console.log("Asking question:", question);
    
    const resp = await postJson("http://127.0.0.1:8000/ask-question", {
      question: question,
      contract_context: context
    });
    
    qaResult.innerHTML = `
      <div class="qa-response">
        <h4>Answer</h4>
        <div class="answer-content">
          <p>${resp.answer}</p>
        </div>
        
        ${resp.relevant_clauses?.length ? 
          `<h4>Relevant Contract Clauses</h4>
           <div class="relevant-clauses">
             <ul>${resp.relevant_clauses.map((c) => `<li>${c}</li>`).join("")}</ul>
           </div>` : 
          ''
        }
        
        <div class="confidence-score">
          <small>Confidence: ${Math.round(resp.confidence * 100)}%</small>
        </div>
        
        ${resp.follow_up_suggestions?.length ? 
          `<h4>Suggested Follow-up Questions</h4>
           <div class="follow-up-questions">
             <ul>
               ${resp.follow_up_suggestions.map((q) => 
                 `<li><button class="follow-up-btn" onclick="document.getElementById('questionInput').value='${q}'">${q}</button></li>`
               ).join("")}
             </ul>
           </div>` : 
          ''
        }
      </div>
    `;
    
    showSuccess("Question answered successfully");
    
  } catch (error) {
    console.error("Question error:", error);
    qaResult.innerHTML = `
      <div class="error-response">
        <p><strong>Error:</strong> ${error.message || "Failed to process question"}</p>
        <p><small>Please try rephrasing your question or check your connection.</small></p>
      </div>
    `;
  }
};

// Clear form function
function clearForm() {
  document.getElementById("contractInput").value = "";
  document.getElementById("upload").value = "";
  document.getElementById("questionInput").value = "";
  document.getElementById("qaResult").innerHTML = "";
  toggle(output, false);
}

// Add clear button functionality if it exists
const clearBtn = document.getElementById("clearBtn");
if (clearBtn) {
  clearBtn.onclick = clearForm;
}

// Initialize
console.log("Legal Contract Simplifier v2.0 - Frontend Loaded");
// About button functionality
document.addEventListener('DOMContentLoaded', () => {
  const aboutBtn = document.getElementById('aboutBtn');
  if (aboutBtn) {
    aboutBtn.addEventListener('click', () => {
      window.location.href = 'about.html';
    });
  }
});
