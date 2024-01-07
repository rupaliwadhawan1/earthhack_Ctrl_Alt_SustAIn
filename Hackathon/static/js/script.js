document.addEventListener('DOMContentLoaded', function() {
    initializeKpiData();
    initializeEventListeners();
    document.getElementById('simulationForm').addEventListener('submit', function(e) {
        e.preventDefault();
    
        console.log("Form submission intercepted"); // Debugging log
    
        var initialInvestment = document.getElementById('initialInvestment').value;
        var resourceType = document.getElementById('resourceTypes').value;
        var years = document.getElementById('years').value;
    
        console.log("Sending request to /simulate"); // Debugging log
    
        fetch('/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                initial_investment: initialInvestment,
                resource_type: resourceType,
                years: years
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('simulationResult').innerHTML = `<p class="error-message">${data.error}</p>`;
            } else {
                document.getElementById('simulationResult').innerHTML = `
                    <div class="result-item">
                        <label>Resource Efficiency:</label>
                        <span>${data.resource_efficiency.toFixed(2)}</span>
                    </div>
                    <div class="result-item">
                        <label>Environmental Impact:</label>
                        <span>${data.environmental_impact.toFixed(2)}</span>
                    </div>
                `;
            }
        })
    })    
        
});



function initializeEventListeners() {
    const evaluateButton = document.getElementById('evaluateButton');
    if (evaluateButton) {
        evaluateButton.addEventListener('click', evaluateIdea);
    }

    document.querySelectorAll('.slider-container input').forEach(slider => {
        slider.addEventListener('input', sliderInputHandler);
    });
}

function evaluateIdea() {
    const ideaText = document.getElementById("ideaInput").value;
    if (!ideaText.trim()) {
        console.error("Idea text is empty");
        return;
    }

    // Show the overlay
    document.getElementById('overlay').style.display = 'block';

    fetch('/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea_text: ideaText })
    })
    .then(response => response.json())
    .then(data => {
        // Hide the overlay when data is received
        document.getElementById('overlay').style.display = 'none';

        // Update KPI sliders and chart with predicted scores
        if (data && data.kpis) {
            updateSlidersAndChart(data.kpis);
        }
        displayResults(data);
    })
    .catch(error => {
        // Hide the overlay if there is an error
        document.getElementById('overlay').style.display = 'none';
        console.error('Error:', error);
    });
}

function sliderInputHandler() {
    const kpiData = updateKpiDataFromSliders();
    fetch('/calculate-kpis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(kpiData)
    })
    .then(response => response.json())
    .then(updatedKpis => {
        updateSlidersAndChart(updatedKpis);
    })
    .catch(error => console.error('Error:', error));
}

let isProgrammaticChange = false; // Flag to indicate programmatic change

function updateSlidersAndChart(kpiData) {
    isProgrammaticChange = true; // Set flag before programmatic changes

    for (const kpi in kpiData) {
        const slider = document.getElementById(`${kpi}-slider`);
        if (slider) {
            slider.value = kpiData[kpi];
            updateSliderScore(slider.id, kpiData[kpi]);
        }
    }
    updateChart(kpiData);

    isProgrammaticChange = false; // Reset flag after changes
}



function initializeKpiData() {
    return {
        "Innovation and Feasibility": getValue('Innovation and Feasibility'),
        "Resource Efficiency": getValue('Resource Efficiency'),
        "Environmental Impact": getValue('Environmental Impact'),
        "Scalability and Adaptability": getValue('Scalability and Adaptability')
    };
}

function getValue(kpiName) {
    return document.getElementById(`${kpiName}-slider`).value;
}

function updateKpiDataFromSliders() {
    return {
        "Innovation and Feasibility": getValue('Innovation and Feasibility'),
        "Resource Efficiency": getValue('Resource Efficiency'),
        "Environmental Impact": getValue('Environmental Impact'),
        "Scalability and Adaptability": getValue('Scalability and Adaptability')
    };
}


function removeSliderEventListeners() {
    document.querySelectorAll('.slider-container input').forEach(slider => {
        slider.removeEventListener('input', sliderInputHandler);
    });
}

function addSliderEventListeners() {
    document.querySelectorAll('.slider-container input').forEach(slider => {
        slider.addEventListener('input', sliderInputHandler);
    });
}

function sliderInputHandler() {
    const kpiData = updateKpiDataFromSliders();
    fetch('/calculate-kpis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(kpiData)
    })
    .then(response => response.json())
    .then(updatedKpis => {
        console.log("Updated KPIs from server:", updatedKpis); // Debug log
        updateSlidersAndChart(updatedKpis); // Make sure this updates the chart correctly
    })
    .catch(error => console.error('Error:', error));
}




document.querySelectorAll('.slider-container input').forEach(slider => {
    slider.addEventListener('input', function() {
        const kpiData = updateKpiDataFromSliders();
        fetch('/calculate-kpis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(kpiData)
        })
        .then(response => response.json())
        .then(updatedKpis => {
            console.log("Updated KPIs from server:", updatedKpis); // Debug log
            updateSlidersAndChart(updatedKpis);
        })
        .catch(error => console.error('Error:', error));
    });
});



function displayResults(data) {
    const chatbotContent = document.getElementById("chatbotContent");
    if (data && data.advice) {
        let formattedAdvice = data.advice.replace(/\n/g, '<br>');
        chatbotContent.innerHTML = `<p>${formattedAdvice}</p>`;
    } else {
        chatbotContent.innerHTML = "<p>No advice available.</p>";
    }
}



let myRadarChart;

function updateChart(kpiData) {
   
    console.log("Updating chart with KPI data:", kpiData); 
    const ctx = document.getElementById('kpiChart').getContext('2d');
    const data = {
        labels: Object.keys(kpiData),
        datasets: [{
            label: 'KPI Scores',
            data: Object.values(kpiData),
            fill: true,
            backgroundColor: 'rgba(0, 128, 0, 0.2)',
            borderColor: 'rgb(0, 128, 0)',
            pointBackgroundColor: 'rgb(0, 128, 0)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(0, 128, 0)'
        }]
    };

    if (myRadarChart) {
        myRadarChart.destroy();
    }
    myRadarChart = new Chart(ctx, {
        type: 'radar',
        data: data,
        options: {
            elements: { line: { borderWidth: 3 } }
        }
    });
}

document.querySelectorAll('.slider-container input').forEach(slider => {
    slider.addEventListener('input', function() {
        updateSliderScore(this.id, this.value);
    });
});

function updateSliderScore(sliderId, value) {
    const scoreElement = document.getElementById(sliderId.replace('-slider', '-score'));
    if (scoreElement) {
        scoreElement.textContent = value;
    }
}

document.getElementById('simulationForm').addEventListener('submit', function(e) {
    e.preventDefault();

    console.log("Form submission intercepted"); // Debugging log

    var initialInvestment = document.getElementById('initialInvestment').value;
    var resourceType = document.getElementById('resourceTypes').value;
    var years = document.getElementById('years').value;

    console.log("Sending request to /simulate"); // Debugging log

    fetch('/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            initial_investment: initialInvestment,
            resource_type: resourceType,
            years: years
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response received:", data); // Debugging log
        document.getElementById('simulationResult').innerText = JSON.stringify(data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});
