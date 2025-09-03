/**
 * Session Analytics Modal JavaScript
 * For detailed session analysis in Django Admin
 */

let currentSessionData = null;
let charts = {};

// Open modal and load session data
async function openSessionModal(sessionId) {
  const modal = document.getElementById('sessionAnalyticsModal');
  const modalSessionId = document.getElementById('modalSessionId');
  const modalLoading = document.getElementById('modalLoading');
  const modalCharts = document.getElementById('modalCharts');
  
  // Show modal
  modal.classList.remove('hidden');
  modalSessionId.textContent = sessionId;
  modalLoading.classList.remove('hidden');
  modalCharts.classList.add('hidden');
  
  try {
    // Fetch session analytics data
    const response = await fetch(`/admin/session-analytics/${sessionId}/`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const sessionData = await response.json();
    currentSessionData = sessionData;
    
    // Populate modal with data
    populateSessionData(sessionData);
    createCharts(sessionData);
    
    // Show charts, hide loading
    modalLoading.classList.add('hidden');
    modalCharts.classList.remove('hidden');
    
  } catch (error) {
    console.error('Error loading session analytics:', error);
    modalLoading.innerHTML = `
      <div class="text-center py-12">
        <div class="text-red-600 text-xl mb-4">⚠️</div>
        <p class="text-gray-600">Error loading session data</p>
        <p class="text-sm text-gray-500">${error.message}</p>
      </div>
    `;
  }
}

// Populate session summary data
function populateSessionData(data) {
  // Summary cards
  document.getElementById('sessionDuration').textContent = data.session_duration || '--';
  document.getElementById('promptsGenerated').textContent = data.prompts_generated || '0';
  document.getElementById('successRate').textContent = (data.success_rate || 0) + '%';
  document.getElementById('copyRate').textContent = (data.copy_rate || 0) + '%';
  
  // Demographics
  if (data.demographics) {
    const aiExp = data.demographics.ai_experience;
    const teachingExp = data.demographics.teaching_years;
    
    // AI Experience bar
    const aiLevels = {'none': 25, 'basic': 50, 'intermediate': 75, 'advanced': 100};
    const aiWidth = aiLevels[aiExp] || 0;
    document.getElementById('aiExperienceBar').style.width = aiWidth + '%';
    document.getElementById('aiExperienceText').textContent = 
      aiExp ? aiExp.charAt(0).toUpperCase() + aiExp.slice(1) : 'Not specified';
    
    // Teaching Experience bar  
    const teachingLevels = {'0-5': 25, '6-15': 50, '16-25': 75, '25+': 100};
    const teachingWidth = teachingLevels[teachingExp] || 0;
    document.getElementById('teachingExperienceBar').style.width = teachingWidth + '%';
    document.getElementById('teachingExperienceText').textContent = 
      teachingExp ? teachingExp + ' years' : 'Not specified';
  }
  
  // Training priorities
  if (data.training_priorities) {
    const priorities = data.training_priorities;
    const priorityNames = {
      'technical_training': 'Technical Training',
      'pedagogical_integration': 'Classroom Integration',
      'content_assessment': 'Content & Assessment',
      'academic_integrity': 'Academic Integrity',
      'ai_literacy': 'AI Literacy',
      'ethics': 'Ethics',
      'school_implementation': 'Implementation',
      'workshops': 'Workshops',
      'community': 'Community'
    };
    
    // Find priorities by rank
    const priority1 = Object.keys(priorities).find(key => priorities[key] === 1);
    const priority2 = Object.keys(priorities).find(key => priorities[key] === 2);
    const priority3 = Object.keys(priorities).find(key => priorities[key] === 3);
    
    document.getElementById('priority1').textContent = priority1 ? priorityNames[priority1] || priority1 : '--';
    document.getElementById('priority2').textContent = priority2 ? priorityNames[priority2] || priority2 : '--';
    document.getElementById('priority3').textContent = priority3 ? priorityNames[priority3] || priority3 : '--';
  }
  
  // Research participation
  if (data.research_participation) {
    const hasEmail = data.research_participation.has_email;
    const interviewInterest = data.research_participation.interview_interest;
    
    // Email status
    const emailStatus = document.getElementById('emailStatus');
    const emailText = document.getElementById('emailText');
    if (hasEmail) {
      emailStatus.className = 'w-4 h-4 rounded-full mr-2 bg-green-500';
      emailText.textContent = 'Email provided';
    } else {
      emailStatus.className = 'w-4 h-4 rounded-full mr-2 bg-gray-300';
      emailText.textContent = 'No email';
    }
    
    // Interview status
    const interviewStatus = document.getElementById('interviewStatus');
    const interviewText = document.getElementById('interviewText');
    if (interviewInterest) {
      interviewStatus.className = 'w-4 h-4 rounded-full mr-2 bg-blue-500';
      interviewText.textContent = 'Interested in interview';
    } else {
      interviewStatus.className = 'w-4 h-4 rounded-full mr-2 bg-gray-300';
      interviewText.textContent = 'No interview interest';
    }
  }
  
  // Show/hide training section based on data
  const trainingSection = document.getElementById('trainingPrioritiesSection');
  if (data.training_interests && data.training_interests.length > 0) {
    trainingSection.classList.remove('hidden');
  } else {
    trainingSection.classList.add('hidden');
  }
}

// Create charts
function createCharts(data) {
  // Destroy existing charts
  Object.values(charts).forEach(chart => {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  });
  charts = {};
  
  // Training Interests Doughnut Chart
  if (data.training_interests && data.training_interests.length > 0) {
    const ctx1 = document.getElementById('trainingInterestsChart').getContext('2d');
    charts.trainingInterests = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: data.training_interests.map(formatInterestLabel),
        datasets: [{
          data: data.training_interests.map(() => 1), // Equal weight for selected interests
          backgroundColor: [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
            '#8B5CF6', '#06B6D4', '#84CC16', '#F97316', '#EC4899'
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              fontSize: 12
            }
          }
        }
      }
    });
  }
  
  // Usage Patterns Bar Chart
  if (data.usage_patterns) {
    const ctx2 = document.getElementById('usagePatternsChart').getContext('2d');
    charts.usagePatterns = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Templates Used', 'Custom Prompts', 'Copy Actions', 'Improvements'],
        datasets: [{
          label: 'Count',
          data: [
            data.usage_patterns.templates_used || 0,
            data.usage_patterns.custom_prompts || 0,
            data.usage_patterns.copy_actions || 0,
            data.usage_patterns.improvements || 0
          ],
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }
  
  // Theory Selection Pie Chart
  if (data.theory_usage && Object.keys(data.theory_usage).length > 0) {
    const ctx3 = document.getElementById('theorySelectionChart').getContext('2d');
    const theories = Object.keys(data.theory_usage);
    const counts = Object.values(data.theory_usage);
    
    charts.theorySelection = new Chart(ctx3, {
      type: 'pie',
      data: {
        labels: theories.map(formatTheoryLabel),
        datasets: [{
          data: counts,
          backgroundColor: [
            '#7C3AED', '#059669', '#DC2626', '#D97706', 
            '#2563EB', '#16A34A', '#C2410C'
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  } else {
    // Show "No theory data" message
    const ctx3 = document.getElementById('theorySelectionChart').getContext('2d');
    ctx3.font = '14px Arial';
    ctx3.fillStyle = '#6B7280';
    ctx3.textAlign = 'center';
    ctx3.fillText('No theory selection data', ctx3.canvas.width/2, ctx3.canvas.height/2);
  }
}

// Format interest labels for display
function formatInterestLabel(interest) {
  const labels = {
    'technical_training': 'Technical Training',
    'pedagogical_integration': 'Classroom Integration',
    'content_assessment': 'Content & Assessment',
    'academic_integrity': 'Academic Integrity',
    'ai_literacy': 'AI Literacy',
    'ethics': 'Ethics',
    'school_implementation': 'Implementation',
    'workshops': 'Workshops',
    'community': 'Community',
    'other': 'Other'
  };
  return labels[interest] || interest;
}

// Format theory labels for display
function formatTheoryLabel(theory) {
  const labels = {
    'blooms': "Bloom's Taxonomy",
    'udl': 'UDL Principles',
    'tpack': 'TPACK Framework',
    'constructivist': 'Constructivist',
    'social_learning': 'Social Learning',
    'scaffolding': 'Scaffolding',
    'differentiation': 'Differentiation'
  };
  return labels[theory] || theory;
}

// Close modal
function closeSessionModal() {
  const modal = document.getElementById('sessionAnalyticsModal');
  modal.classList.add('hidden');
  
  // Cleanup charts
  Object.values(charts).forEach(chart => {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  });
  charts = {};
  currentSessionData = null;
}

// Export session data
function exportSessionData(format) {
  if (!currentSessionData) {
    alert('No session data available');
    return;
  }
  
  const sessionId = document.getElementById('modalSessionId').textContent;
  
  if (format === 'json') {
    const dataStr = JSON.stringify(currentSessionData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    downloadFile(dataBlob, `session_${sessionId}_analytics.json`);
  } else if (format === 'csv') {
    const csvData = convertToCSV(currentSessionData);
    const dataBlob = new Blob([csvData], {type: 'text/csv'});
    downloadFile(dataBlob, `session_${sessionId}_analytics.csv`);
  }
}

// Convert data to CSV format
function convertToCSV(data) {
  const rows = [
    ['Metric', 'Value'],
    ['Session ID', data.session_id || ''],
    ['Duration', data.session_duration || ''],
    ['Prompts Generated', data.prompts_generated || '0'],
    ['Success Rate', (data.success_rate || 0) + '%'],
    ['Copy Rate', (data.copy_rate || 0) + '%'],
    ['AI Experience', data.demographics?.ai_experience || ''],
    ['Teaching Years', data.demographics?.teaching_years || ''],
    ['Training Interests', (data.training_interests || []).join('; ')],
    ['Email Provided', data.research_participation?.has_email ? 'Yes' : 'No'],
    ['Interview Interest', data.research_participation?.interview_interest ? 'Yes' : 'No']
  ];
  
  return rows.map(row => row.map(field => `"${field}"`).join(',')).join('\n');
}

// Download file helper
function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
  const modal = document.getElementById('sessionAnalyticsModal');
  if (modal && e.target === modal) {
    closeSessionModal();
  }
});