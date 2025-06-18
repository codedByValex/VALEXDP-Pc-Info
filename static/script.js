const ctx = document.getElementById('usageChart').getContext('2d');

const usageChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'CPU (%)',
            data: [],
            borderColor: 'rgba(255, 99, 132, 1)',
            fill: false
        }, {
            label: 'RAM (%)',
            data: [],
            borderColor: 'rgba(54, 162, 235, 1)',
            fill: false
        }]
    },
    options: {
        responsive: true,
        animation: false,
        scales: {
            y: { beginAtZero: true, max: 100 }
        }
    }
});

function fetchData() {
    fetch('/usage')
        .then(response => response.json())
        .then(data => {
            const time = new Date().toLocaleTimeString();

            usageChart.data.labels.push(time);
            usageChart.data.datasets[0].data.push(data.cpu);
            usageChart.data.datasets[1].data.push(data.ram);

            if (usageChart.data.labels.length > 20) {
                usageChart.data.labels.shift();
                usageChart.data.datasets[0].data.shift();
                usageChart.data.datasets[1].data.shift();
            }

            usageChart.update();
        });
}

setInterval(fetchData, 2000); // 2 saniyede bir veri güncelle
