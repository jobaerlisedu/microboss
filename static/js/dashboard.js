var CHART_COLORS = ['#3b82f6','#f59e0b','#22c55e','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'];
var chartInstances = {};
var currentTrendInterval = 'day';

function refreshDashboardData() {
  var period = window.dashboardPeriod || 'month';
  fetch('/api/v1/analytics/dashboard/?period=' + period)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.kpi) updateKPIs(data.kpi);
      if (data.content_trend) renderContentTrend(data.content_trend);
      if (data.daily_trend) renderDailyTrend(data.daily_trend);
      if (data.platform_breakdown) renderPlatformBreakdown(data.platform_breakdown);
      if (data.sponsored_vs_organic) renderContentRatio(data.sponsored_vs_organic);
      if (data.member_performance) renderTopContributors(data.member_performance);
      if (data.assignment_metrics) renderAssignmentPipeline(data.assignment_metrics);
      if (data.script_metrics) renderScriptPipeline(data.script_metrics);
      if (data.content_list_sources) renderSourceMetrics(data.content_list_sources);
      if (data.day_of_week) renderDayOfWeek(data.day_of_week);
      if (data.hourly) renderHourlyChart(data.hourly);
      if (data.monthly_comparison) renderPeriodComparison(data.monthly_comparison);
      if (data.assignment_trend) renderAssignmentTrend(data.assignment_trend);
    })
    .catch(function(err) { console.warn('Dashboard fetch failed:', err); });
}

function updateKPIs(kpi) {
  setText('kpiTotalEntries', kpi.total_entries);
  setText('kpiTodayEntries', kpi.today_entries);
  setText('kpiMonthEntries', kpi.month_entries);
  setText('kpiActiveSponsors', kpi.active_sponsors);
  setText('kpiTotalSponsors', kpi.total_sponsors);
  setText('kpiPendingScripts', kpi.pending_scripts);
  setText('kpiActiveAssignments', kpi.active_assignments);
  setText('kpiPeriodEntries', kpi.period_entries);
  setText('kpiTotalAssignments', kpi.total_assignments);
  setText('kpiTotalScripts', kpi.total_scripts);
  setText('kpiDoneAssignments', kpi.completed_assignments || 0);
  setText('kpiApprovedScripts', kpi.approved_scripts || 0);
  var gb = document.getElementById('kpiGrowthBadge');
  if (gb) {
    var pct = kpi.growth_pct || 0;
    gb.innerHTML = pct >= 0
      ? '<span class="trend-up"><i class="bi bi-arrow-up-short"></i>+' + pct + '%</span>'
      : '<span class="trend-down"><i class="bi bi-arrow-down-short"></i>' + pct + '%</span>';
  }
}

function destroyChart(key) {
  if (chartInstances[key]) { chartInstances[key].destroy(); delete chartInstances[key]; }
}

function createCtx(id) {
  var el = document.getElementById(id);
  if (!el) return null;
  return el.getContext('2d');
}

function renderContentTrend(trend) {
  destroyChart('contentTrend');
  var ctx = createCtx('chartContentTrend');
  if (!ctx || !trend.labels) return;
  var labels = currentTrendInterval === 'month'
    ? trend.labels.slice(-24)
    : (trend.labels.length > 60 ? trend.labels.filter(function(_,i){return i%3===0||i===trend.labels.length-1;}) : trend.labels);
  var allLabels = trend.labels;
  var labelIndices = labels.map(function(l){ return allLabels.indexOf(l); });
  var values = labelIndices.map(function(i){ return trend.values[i]; });
  var movingAvg = trend.moving_avg || [];
  var avgValues = labelIndices.map(function(i){ return movingAvg[i] !== undefined ? movingAvg[i] : null; });
  var parent = ctx.canvas.parentElement;
  ctx.canvas.width = parent.clientWidth || 600;
  chartInstances.contentTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Publications',
          data: values,
          borderColor: '#3b82f6',
          backgroundColor: function(context) {
            var g = context.chart.ctx.createLinearGradient(0, 0, 0, 260);
            g.addColorStop(0, 'rgba(59,130,246,0.25)');
            g.addColorStop(1, 'rgba(59,130,246,0.0)');
            return g;
          },
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
          borderWidth: 2,
        },
        {
          label: '7-Day Avg',
          data: avgValues,
          borderColor: '#f59e0b',
          borderDash: [4, 4],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 12, font: { size: 11 } } },
        tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', titleFont: { size: 12 }, bodyFont: { size: 11 } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 15 } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { size: 10 }, stepSize: 1 } }
      },
      interaction: { mode: 'index', intersect: false }
    }
  });
}

function switchTrendInterval(interval) {
  currentTrendInterval = interval;
  document.querySelectorAll('.chart-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.interval === interval); });
  var period = window.dashboardPeriod || 'month';
  fetch('/api/v1/analytics/content-trend/?period=' + period + '&interval=' + interval)
    .then(function(r){ return r.json(); })
    .then(function(data){ if (data) renderContentTrend(data); })
    .catch(function(e){});
}

function renderDailyTrend(trend) {
  destroyChart('dailyTrend');
  var ctx = createCtx('chartDailyTrend');
  if (!ctx || !trend.values) return;
  var parent = ctx.canvas.parentElement;
  ctx.canvas.width = parent.clientWidth || 300;
  setText('dailyAvg', trend.average != null ? trend.average : '-');
  setText('dailyPeak', trend.peak != null ? trend.peak : '-');
  if (trend.values.length > 0) setText('dailyTrendTotal', trend.values[trend.values.length - 1]);
  chartInstances.dailyTrend = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: trend.labels,
      datasets: [{
        label: 'Entries',
        data: trend.values,
        backgroundColor: trend.values.map(function(v,i){
          return i === trend.values.length - 1 ? '#3b82f6' : 'rgba(59,130,246,0.35)';
        }),
        borderRadius: 3,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { display: false }, ticks: { display: false } }
      }
    }
  });
}

function renderTopContributors(members) {
  destroyChart('topContributors');
  var ctx = createCtx('chartTopContributors');
  if (!ctx || !members || members.length === 0) return;
  var names = members.map(function(m){ return m.name.length > 12 ? m.name.substring(0,12)+'...' : m.name; }).reverse();
  var vals = members.map(function(m){ return m.total; }).reverse();
  var colors = vals.map(function(_,i){ return CHART_COLORS[i % CHART_COLORS.length]; }).reverse();
  chartInstances.topContributors = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: names,
      datasets: [{
        label: 'Entries',
        data: vals,
        backgroundColor: colors,
        borderRadius: 3,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(c){ return c.raw + ' entries'; } } } },
      scales: {
        x: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 }, stepSize: 1 } },
        y: { grid: { display: false }, ticks: { font: { size: 10 } } }
      }
    }
  });
}

function renderPlatformBreakdown(data) {
  destroyChart('platformBreakdown');
  var ctx = createCtx('chartPlatformBreakdown');
  if (!ctx || !data.breakdown) return;
  chartInstances.platformBreakdown = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.breakdown.map(function(s){ return s.label; }),
      datasets: [{
        data: data.breakdown.map(function(s){ return s.count; }),
        backgroundColor: data.breakdown.map(function(s){ return s.color; }),
        borderWidth: 2,
        borderColor: 'transparent',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: function(c){ return c.label + ': ' + c.raw + ' (' + data.breakdown[c.dataIndex].pct + '%)'; } } }
      }
    }
  });
  var list = document.getElementById('platformLegendList');
  if (list) {
    list.innerHTML = data.breakdown.map(function(s) {
      return '<div class="legend-item-row"><span><span class="dot" style="background:' + s.color + '"></span> ' + s.label + '</span><strong>' + s.count + '</strong></div>';
    }).join('');
  }
}

function renderContentRatio(data) {
  destroyChart('contentRatio');
  var ctx = createCtx('chartContentRatio');
  if (!ctx) return;
  setText('ratioSponsored', data.sponsored);
  setText('ratioSponsoredPct', data.sponsored_pct);
  setText('ratioOrganic', data.organic);
  setText('ratioOrganicPct', data.organic_pct);
  chartInstances.contentRatio = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Sponsored', 'Organic'],
      datasets: [{
        data: [data.sponsored, data.organic],
        backgroundColor: ['#3b82f6', '#e2e8f0'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: { legend: { display: false } }
    }
  });
}

function renderAssignmentPipeline(data) {
  destroyChart('assignmentPipeline');
  var ctx = createCtx('chartAssignmentPipeline');
  if (!ctx) return;
  chartInstances.assignmentPipeline = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Completed', 'Processing', 'Assigned', 'Cancelled'],
      datasets: [{
        data: [data.done, data.processing, data.assigned, data.cancelled],
        backgroundColor: ['#22c55e', '#f59e0b', '#3b82f6', '#ef4444'],
        borderWidth: 2,
        borderColor: 'transparent',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '55%',
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, padding: 8 } },
        tooltip: { callbacks: { label: function(c){
          var map = {done:'done_pct',processing:'processing_pct',assigned:'assigned_pct',cancelled:'cancelled_pct'};
          var key = map[c.label.toLowerCase()] || c.label.toLowerCase()+'_pct';
          var pct = data[key];
          return c.label + ': ' + c.raw + (pct != null ? ' (' + pct + '%)' : '');
        } } }
      }
    }
  });
}

function renderScriptPipeline(data) {
  destroyChart('scriptPipeline');
  var ctx = createCtx('chartScriptPipeline');
  if (!ctx) return;
  chartInstances.scriptPipeline = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Approved', 'Pending', 'Draft'],
      datasets: [{
        data: [data.approved, data.pending, data.draft],
        backgroundColor: ['#22c55e', '#f59e0b', '#94a3b8'],
        borderWidth: 2,
        borderColor: 'transparent',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '55%',
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, padding: 8 } },
        tooltip: { callbacks: { label: function(c){ return c.label + ': ' + c.raw + ' (' + data[c.label.toLowerCase()+'_pct'] + '%)'; } } }
      }
    }
  });
}

function renderSourceMetrics(data) {
  destroyChart('sourceMetrics');
  var ctx = createCtx('chartSourceMetrics');
  if (!ctx || !data.sources) return;
  var srcColors = {district:'#3b82f6', reuters:'#ef4444', social:'#22c55e', studio:'#f59e0b'};
  var colors = data.sources.map(function(s){ return srcColors[s.source] || '#94a3b8'; });
  chartInstances.sourceMetrics = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: data.sources.map(function(s){ return s.source; }),
      datasets: [{
        data: data.sources.map(function(s){ return s.total; }),
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: 'transparent',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, padding: 8 } },
        tooltip: { callbacks: { label: function(c){ return c.label + ': ' + c.raw + ' (' + data.sources[c.dataIndex].pct + '%)'; } } }
      }
    }
  });
}

function renderDayOfWeek(data) {
  destroyChart('dayOfWeek');
  var ctx = createCtx('chartDayOfWeek');
  if (!ctx || !data.labels) return;
  chartInstances.dayOfWeek = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Entries',
        data: data.values,
        backgroundColor: data.values.map(function(v){
          return v === data.peak_value ? '#f59e0b' : 'rgba(59,130,246,0.4)';
        }),
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 }, stepSize: 1 } }
      }
    }
  });
}

function renderHourlyChart(data) {
  destroyChart('hourly');
  var ctx = createCtx('chartHourly');
  if (!ctx || !data.labels) return;
  chartInstances.hourly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Entries',
        data: data.values,
        backgroundColor: data.values.map(function(v){
          var max = Math.max.apply(null, data.values) || 1;
          var intensity = v / max;
          return 'rgba(139,92,246,' + (0.2 + intensity * 0.6) + ')';
        }),
        borderRadius: 2,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 8 }, maxTicksLimit: 12 } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 9 }, stepSize: 1 } }
      }
    }
  });
}

function renderPeriodComparison(data) {
  setText('periodCurrentCount', data.current_period ? data.current_period.total : '-');
  setText('periodPrevCount', data.previous_period ? data.previous_period.total : '-');
  var el = document.getElementById('periodChange');
  if (el) {
    var pct = data.change_pct || 0;
    el.textContent = (pct >= 0 ? '+' : '') + pct + '%';
    el.className = pct >= 0 ? 'badge-pill badge-pos' : 'badge-pill badge-neg';
  }
}

function renderAssignmentTrend(data) {
  destroyChart('assignmentTrend');
  var ctx = createCtx('chartAssignmentTrend');
  if (!ctx || !data.labels) return;
  chartInstances.assignmentTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'Created', data: data.created, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2 },
        { label: 'Completed', data: data.done, borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.1)', fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 10 } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 9 }, stepSize: 1 } }
      },
      interaction: { mode: 'index', intersect: false }
    }
  });
}

function setText(id, val) {
  var el = document.getElementById(id);
  if (el) el.textContent = val != null ? val : '-';
}
