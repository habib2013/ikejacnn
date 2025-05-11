document.addEventListener('DOMContentLoaded', () => {
    const feedersCanvas = document.getElementById('topFeedersChart');
    const areasCanvas = document.getElementById('mostAffectedAreasChart');
    const reasonsCanvas = document.getElementById('reasonsChart');
    const statusCanvas = document.getElementById('statusChart');
    const lastUpdatedElem = document.getElementById('lastUpdated');
    const errorDisplayElem = document.getElementById('errorDisplay');
    const refreshStatusElem = document.getElementById('refreshStatus');
    const locationDropdown = document.getElementById('locationDropdown');
    const locationSearch = document.getElementById('locationSearch');
    const searchStatus = document.getElementById('searchStatus');
    const locationResults = document.getElementById('locationResults');
    const locationName = document.getElementById('locationName');
    const locationCount = document.getElementById('locationCount');
    const locationTableBody = document.getElementById('locationTableBody');
    const locationMostCommonStatus = document.getElementById('locationMostCommonStatus');
    const locationMostRecentOutage = document.getElementById('locationMostRecentOutage');
    const locationMostAffectedFeeder = document.getElementById('locationMostAffectedFeeder');
    const locationMostCommonReason = document.getElementById('locationMostCommonReason');

    let feedersChartInstance;
    let areasChartInstance;
    let reasonsChartInstance;
    let statusChartInstance;
    
    // Store all locations for filtering
    let allLocations = [];
    
    // Debounce function to limit how often a function can be called
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    async function fetchDataAndRenderCharts() {
        if (lastUpdatedElem) lastUpdatedElem.textContent = 'Last updated: Loading...';
        if (errorDisplayElem) errorDisplayElem.textContent = '';
        if (refreshStatusElem) refreshStatusElem.textContent = ''; // Clear refresh status

        try {
            const response = await fetch('/api/outage-summary');
            if (!response.ok) {
                let errorMsg = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorData.message || errorMsg;
                } catch (e) {
                    // Ignore if response is not JSON
                }
                throw new Error(errorMsg);
            }
            const data = await response.json();

            if (lastUpdatedElem && data.last_updated) {
                lastUpdatedElem.textContent = `Data loaded: ${data.last_updated}`;
            } else if (lastUpdatedElem) {
                lastUpdatedElem.textContent = `Data loaded: ${new Date().toLocaleString()}`;
            }

            // Store all locations and populate dropdown
            if (data.all_locations && data.all_locations.length > 0) {
                allLocations = data.all_locations;
                
                if (locationDropdown) {
                    // Clear existing options except the first one
                    while (locationDropdown.options.length > 1) {
                        locationDropdown.remove(1);
                    }
                    
                    // Add new options
                    allLocations.forEach(location => {
                        const option = document.createElement('option');
                        option.value = location;
                        option.textContent = location;
                        locationDropdown.appendChild(option);
                    });
                }
            }

            // Render all charts
            if (feedersCanvas) {
                renderBarChart(feedersCanvas.getContext('2d'), feedersChartInstance, data.top_feeders, 'Top 5 Faulty Feeders', 'Feeder', 'Outage Count', 'feedersChart');
            } else {
                console.error('Canvas for feeders chart (topFeedersChart) not found.');
                if (errorDisplayElem) errorDisplayElem.textContent += ' Feeders chart canvas not found. ';
            }
            
            if (areasCanvas) {
                renderBarChart(areasCanvas.getContext('2d'), areasChartInstance, data.most_affected_areas, 'Top 5 Affected Areas', 'Area', 'Outage Count', 'areasChart');
            } else {
                console.error('Canvas for areas chart (mostAffectedAreasChart) not found.');
                if (errorDisplayElem) errorDisplayElem.textContent += ' Areas chart canvas not found. ';
            }
            
            if (reasonsCanvas) {
                renderPieChart(reasonsCanvas.getContext('2d'), reasonsChartInstance, data.frequent_reasons, 'Frequent Outage Reasons', 'reasonsChart');
            } else {
                console.error('Canvas for reasons chart (reasonsChart) not found.');
            }
            
            if (statusCanvas) {
                renderPieChart(statusCanvas.getContext('2d'), statusChartInstance, data.status_distribution, 'Outage Status Distribution', 'statusChart');
            } else {
                console.error('Canvas for status chart (statusChart) not found.');
            }
            
        } catch (error) {
            console.error('Error fetching or rendering data:', error);
            if (lastUpdatedElem) lastUpdatedElem.textContent = 'Failed to load data.';
            if (errorDisplayElem) errorDisplayElem.textContent = `Error: ${error.message}`;
            if (feedersChartInstance) feedersChartInstance.destroy();
            if (areasChartInstance) areasChartInstance.destroy();
            if (reasonsChartInstance) reasonsChartInstance.destroy();
            if (statusChartInstance) statusChartInstance.destroy();
            feedersChartInstance = null;
            areasChartInstance = null;
            reasonsChartInstance = null;
            statusChartInstance = null;
        }
    }

    function renderBarChart(ctx, chartInstance, chartData, title, xAxisLabel, yAxisLabel, chartIdInternal) {
        // chartIdInternal is used for managing instances, not for getElementById here
        if (!ctx) {
            console.error(`Canvas context not found for a chart.`);
            return;
        }

        let currentChartInstance;
        if (chartIdInternal === 'feedersChart') {
            currentChartInstance = feedersChartInstance;
        } else if (chartIdInternal === 'areasChart') {
            currentChartInstance = areasChartInstance;
        }

        if (currentChartInstance) {
            currentChartInstance.destroy();
        }

        if (!chartData || Object.keys(chartData).length === 0) {
            console.warn(`No data for ${title}.`);
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = 'grey';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
            if (chartIdInternal === 'feedersChart') feedersChartInstance = null;
            if (chartIdInternal === 'areasChart') areasChartInstance = null;
            return;
        }

        const labels = Object.keys(chartData);
        const dataValues = Object.values(chartData);

        const newChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: yAxisLabel, // This label appears in tooltips and legend if enabled
                    data: dataValues,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)',
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: yAxisLabel
                        },
                        ticks: { 
                            stepSize: 1 // Ensure y-axis shows whole numbers for counts
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: xAxisLabel
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false // Requirement is to show two bar charts, legend might be redundant
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 18
                        }
                    }
                }
            }
        });

        if (chartIdInternal === 'feedersChart') feedersChartInstance = newChart;
        if (chartIdInternal === 'areasChart') areasChartInstance = newChart;
    }
    
    function renderPieChart(ctx, chartInstance, chartData, title, chartIdInternal) {
        if (!ctx) {
            console.error(`Canvas context not found for a chart.`);
            return;
        }

        let currentChartInstance;
        if (chartIdInternal === 'reasonsChart') {
            currentChartInstance = reasonsChartInstance;
        } else if (chartIdInternal === 'statusChart') {
            currentChartInstance = statusChartInstance;
        }

        if (currentChartInstance) {
            currentChartInstance.destroy();
        }

        if (!chartData || Object.keys(chartData).length === 0) {
            console.warn(`No data for ${title}.`);
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = 'grey';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
            if (chartIdInternal === 'reasonsChart') reasonsChartInstance = null;
            if (chartIdInternal === 'statusChart') statusChartInstance = null;
            return;
        }

        const labels = Object.keys(chartData);
        const dataValues = Object.values(chartData);
        
        // Generate colors for pie chart segments
        const backgroundColors = [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
            'rgba(83, 102, 255, 0.7)',
            'rgba(40, 159, 64, 0.7)',
            'rgba(210, 199, 199, 0.7)'
        ];

        const newChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: backgroundColors.slice(0, labels.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 15,
                            font: {
                                size: 11
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 18
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        if (chartIdInternal === 'reasonsChart') reasonsChartInstance = newChart;
        if (chartIdInternal === 'statusChart') statusChartInstance = newChart;
    }

    // Initial data load
    fetchDataAndRenderCharts();

    // Make refreshData globally accessible for the button in HTML
    window.refreshData = async () => {
        if (refreshStatusElem) refreshStatusElem.textContent = 'Refreshing data...';
        // The /refresh-data endpoint was removed from app.py as per the requirements.
        // Re-fetching /api/outage-summary will get cached data from the server unless the server cache itself is cleared.
        // This client-side refresh will effectively re-render with potentially the same data.
        await fetchDataAndRenderCharts();
        if (refreshStatusElem) refreshStatusElem.textContent = 'Data re-fetched. Charts updated.';
        setTimeout(() => { if (refreshStatusElem) refreshStatusElem.textContent = ''; }, 3000); // Clear status after a few seconds
    };
    
    // Function to filter locations based on search input
    const filterLocations = debounce((searchText) => {
        if (!locationDropdown || !allLocations.length) {
            if (searchStatus) searchStatus.textContent = 'Location list not yet loaded.';
            return;
        }
        
        // Clear existing options except the first one ("Select your location...")
        while (locationDropdown.options.length > 1) {
            locationDropdown.remove(1);
        }

        if (!searchText.trim()) {
            // If search text is empty, populate with all locations
            allLocations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationDropdown.appendChild(option);
            });
            if (searchStatus) searchStatus.textContent = 'Type to search locations.';
            locationResults.style.display = 'none'; // Hide results when search is cleared
            return;
        }
        
        if (searchStatus) searchStatus.textContent = 'Searching...';
        
        // Filter locations that contain the search text (case insensitive)
        const filteredLocations = allLocations.filter(location => 
            location.toLowerCase().includes(searchText.toLowerCase().trim())
        );
        
        // Add filtered options
        filteredLocations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            locationDropdown.appendChild(option);
        });
        
        // Update search status
        if (filteredLocations.length === 0) {
            if (searchStatus) searchStatus.textContent = 'No locations found matching your search.';
            locationResults.style.display = 'none'; // Hide results if no matches
        } else if (filteredLocations.length === 1) {
            if (searchStatus) searchStatus.textContent = '1 location found.';
            // Auto-select the only match
            locationDropdown.value = filteredLocations[0];
            // Trigger the location check automatically
            checkLocation(); // Ensure this function is defined and accessible
        } else {
            if (searchStatus) searchStatus.textContent = `${filteredLocations.length} locations found. Select one below.`;
            locationResults.style.display = 'none'; // Hide previous results when multiple options are shown
        }
    }, 300); // 300ms debounce delay
    
    // Add event listener to search input
    if (locationSearch) {
        locationSearch.addEventListener('input', (e) => {
            filterLocations(e.target.value);
        });
    }
    
    // Function to analyze location data
    function analyzeLocationData(outages) {
        if (!outages || outages.length === 0) {
            return {
                mostCommonStatus: 'N/A',
                mostRecentOutage: 'N/A',
                mostAffectedFeeder: 'N/A',
                mostCommonReason: 'N/A'
            };
        }
        
        // Find most common status
        const statusCounts = {};
        outages.forEach(outage => {
            const status = outage.Status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });
        const mostCommonStatus = Object.entries(statusCounts)
            .sort((a, b) => b[1] - a[1])[0][0];
        
        // Find most recent outage
        let mostRecentDate = outages[0].Date;
        outages.forEach(outage => {
            if (outage.Date > mostRecentDate) {
                mostRecentDate = outage.Date;
            }
        });
        
        // Find most affected feeder
        const feederCounts = {};
        outages.forEach(outage => {
            const feeder = outage.Feeder || 'Unknown';
            feederCounts[feeder] = (feederCounts[feeder] || 0) + 1;
        });
        const mostAffectedFeeder = Object.entries(feederCounts)
            .sort((a, b) => b[1] - a[1])[0][0];
        
        // Find most common reason
        const reasonCounts = {};
        outages.forEach(outage => {
            const reason = outage.Reason || 'Unknown';
            reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;
        });
        const mostCommonReason = Object.entries(reasonCounts)
            .sort((a, b) => b[1] - a[1])[0][0];
        
        return {
            mostCommonStatus,
            mostRecentOutage: mostRecentDate,
            mostAffectedFeeder,
            mostCommonReason
        };
    }
    
    // Function to check outages for a specific location
    const checkLocation = async () => {
        const selectedLocation = locationDropdown.value;
        if (!selectedLocation) {
            // alert('Please select a location first.'); // Can be annoying if search auto-triggers this
            locationResults.style.display = 'none';
            return;
        }
        
        // Reset and show loading state for analysis
        if (locationName) locationName.textContent = `Location: ${selectedLocation}`;
        if (locationCount) locationCount.textContent = 'Loading data...';
        if (locationMostCommonStatus) locationMostCommonStatus.textContent = '-';
        if (locationMostRecentOutage) locationMostRecentOutage.textContent = '-';
        if (locationMostAffectedFeeder) locationMostAffectedFeeder.textContent = '-';
        if (locationMostCommonReason) locationMostCommonReason.textContent = '-';
        if (locationTableBody) locationTableBody.innerHTML = ''; // Clear previous table
        locationResults.style.display = 'block';

        try {
            const response = await fetch(`/api/location-data?location=${encodeURIComponent(selectedLocation)}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({})); // Try to parse error, default to empty obj
                const errorMsg = errorData.error || `HTTP error! status: ${response.status}`;
                throw new Error(errorMsg);
            }
            
            const data = await response.json();
            
            // Update location results section
            if (locationCount) locationCount.textContent = `Outages: ${data.count || 0}`;
            
            // Analyze location data and update analysis section
            if (data.data && data.data.length > 0) {
                const analysis = analyzeLocationData(data.data); // Ensure analyzeLocationData is robust
                
                if (locationMostCommonStatus) {
                    locationMostCommonStatus.textContent = analysis.mostCommonStatus;
                }
                
                if (locationMostRecentOutage) {
                    locationMostRecentOutage.textContent = analysis.mostRecentOutage;
                }
                
                if (locationMostAffectedFeeder) {
                    locationMostAffectedFeeder.textContent = analysis.mostAffectedFeeder;
                }
                
                if (locationMostCommonReason) {
                    locationMostCommonReason.textContent = analysis.mostCommonReason;
                }

                // Add new rows to the table
                data.data.forEach(outage => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${outage.Date || 'N/A'}</td>
                        <td>${outage.Feeder || 'Unknown'}</td>
                        <td>${outage.Status || 'N/A'}</td>
                        <td>${outage.Reason || 'Not specified'}</td>
                    `;
                    locationTableBody.appendChild(row);
                });
            } else {
                // Reset analysis and table if no data for the location
                if (locationMostCommonStatus) locationMostCommonStatus.textContent = 'N/A';
                if (locationMostRecentOutage) locationMostRecentOutage.textContent = 'N/A';
                if (locationMostAffectedFeeder) locationMostAffectedFeeder.textContent = 'N/A';
                if (locationMostCommonReason) locationMostCommonReason.textContent = 'N/A';
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="4" style="text-align: center;">No outage data found for this location.</td>';
                locationTableBody.appendChild(row);
            }
            
        } catch (error) {
            console.error('Error fetching location data:', error);
            if (locationCount) locationCount.textContent = 'Error loading data.';
            if (locationTableBody) {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="4" style="text-align: center; color: red;">Error: ${error.message}</td>`;
                locationTableBody.appendChild(row);
            }
        }
    };
    
    // Make checkLocation globally accessible for the button in HTML
    window.checkLocation = checkLocation;
});
