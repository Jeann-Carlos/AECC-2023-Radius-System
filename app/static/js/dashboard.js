// AECC Admin Dashboard Controller
document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('devices-table-body')) {
        return; // Not on the dashboard page
    }

    console.log("Admin Dashboard Panel Loaded.");

    // State Variables
    let allDevices = [];
    let filteredDevices = [];
    let activeChart = null;

    // Elements
    const tableBody = document.getElementById('devices-table-body');
    const searchInput = document.getElementById('device-search');
    const statusFilter = document.getElementById('status-filter');
    const syncButton = document.getElementById('legacy-sync-btn');
    const addDeviceForm = document.getElementById('add-device-form');

    // Tab Navigation
    const tabs = document.querySelectorAll('.dashboard-tab');
    const sections = document.querySelectorAll('.dashboard-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = tab.getAttribute('data-target');
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            sections.forEach(sec => {
                if (sec.id === targetSection) {
                    sec.style.display = 'block';
                } else {
                    sec.style.display = 'none';
                }
            });
        });
    });

    // Fetch and Load Dashboard Data
    function loadDashboardData() {
        // Fetch stats
        fetch('/admin/api/stats')
            .then(res => res.json())
            .then(stats => {
                document.getElementById('stat-total-devices').innerText = stats.total_devices;
                document.getElementById('stat-active-devices').innerText = stats.active_devices;
                document.getElementById('stat-active-sessions').innerText = stats.active_sessions;
                document.getElementById('stat-auth-failures').innerText = stats.auth_failures;
                
                renderChart(stats);
            })
            .catch(err => console.error("Error loading stats:", err));

        // Fetch device list
        fetch('/admin/api/devices')
            .then(res => res.json())
            .then(devices => {
                allDevices = devices;
                applyFilters();
            })
            .catch(err => console.error("Error loading devices:", err));

        // Fetch logs
        fetch('/admin/api/logs')
            .then(res => res.json())
            .then(data => {
                renderLogs(data.auth_logs, data.sessions);
            })
            .catch(err => console.error("Error loading logs:", err));
    }

    // Apply Filter & Search Conditions
    function applyFilters() {
        const query = searchInput.value.toLowerCase().strip ? searchInput.value.toLowerCase().trim() : searchInput.value.toLowerCase();
        const statusVal = statusFilter.value;

        filteredDevices = allDevices.filter(d => {
            const matchesSearch = 
                (d.student_id && d.student_id.toLowerCase().includes(query)) ||
                (d.mac_address && d.mac_address.toLowerCase().includes(query)) ||
                (d.telephone && d.telephone.toLowerCase().includes(query)) ||
                (d.ip_address && d.ip_address.toLowerCase().includes(query));
                
            const matchesStatus = statusVal === 'all' || d.status === statusVal;

            return matchesSearch && matchesStatus;
        });

        renderDevicesTable();
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);

    // Render Table Entries
    function renderDevicesTable() {
        tableBody.innerHTML = '';
        if (filteredDevices.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No devices match the criteria.</td></tr>`;
            return;
        }

        filteredDevices.forEach(device => {
            const tr = document.createElement('tr');
            
            const badgeClass = device.status === 'Active' ? 'badge-active' : (device.status === 'Blocked' ? 'badge-blocked' : 'badge-pending');
            
            // Format time
            const date = new Date(device.created_at);
            const dateString = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            tr.innerHTML = `
                <td><strong>${device.student_id}</strong></td>
                <td><code style="color: var(--primary); font-weight: 600;">${device.mac_address || 'N/A'}</code></td>
                <td>${device.ip_address || '<span class="text-muted">Not Connected</span>'}</td>
                <td>${device.telephone}</td>
                <td><span class="badge ${badgeClass}">${device.status}</span></td>
                <td>
                    <div class="action-btn-group">
                        <button class="icon-btn toggle-status-btn" title="Toggle Access" data-id="${device.student_id}" data-mac="${device.mac_address}" data-status="${device.status}">
                            <i class="fa ${device.status === 'Active' ? 'fa-ban' : 'fa-check'}"></i>
                        </button>
                        <button class="icon-btn icon-btn-danger delete-device-btn" title="Delete Device" data-id="${device.student_id}" data-mac="${device.mac_address}">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;

            tableBody.appendChild(tr);
        });

        // Attach action handlers
        document.querySelectorAll('.toggle-status-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const sId = btn.getAttribute('data-id');
                const mac = btn.getAttribute('data-mac');
                const currentStatus = btn.getAttribute('data-status');
                const newStatus = currentStatus === 'Active' ? 'Blocked' : 'Active';
                toggleDeviceStatus(sId, mac, newStatus);
            });
        });

        document.querySelectorAll('.delete-device-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const sId = btn.getAttribute('data-id');
                const mac = btn.getAttribute('data-mac');
                if (confirm(`Are you sure you want to remove student device ${sId}?`)) {
                    deleteDevice(sId, mac);
                }
            });
        });
    }

    // Render system logs terminal
    function renderLogs(authLogs, sessions) {
        const term1 = document.getElementById('log-terminal-auth');
        const term2 = document.getElementById('log-terminal-acct');
        
        // Render auth attempts
        term1.innerHTML = '';
        if (authLogs.length === 0) {
            term1.innerHTML = '<div class="log-line">No authentication logs found.</div>';
        } else {
            authLogs.forEach(log => {
                const badge = log.reply === 'Access-Accept' ? '[ACCEPT]' : '[REJECT]';
                const color = log.reply === 'Access-Accept' ? '#5ff' : '#f55';
                term1.innerHTML += `
                    <div class="log-line" style="color: ${color}">
                        ${log.authdate} - ${badge} Device ${log.username} validated with secret.
                    </div>
                `;
            });
        }
        
        // Render accounting sessions
        term2.innerHTML = '';
        if (sessions.length === 0) {
            term2.innerHTML = '<div class="log-line">No active connection logs found.</div>';
        } else {
            sessions.forEach(sess => {
                const status = sess.acctstoptime ? `Disconnected (Duration: ${sess.acctsessiontime}s)` : 'Connected (Active)';
                const color = sess.acctstoptime ? 'var(--text-secondary)' : '#5ff';
                const inputMB = (sess.acctinputoctets / (1024 * 1024)).toFixed(2);
                const outputMB = (sess.acctoutputoctets / (1024 * 1024)).toFixed(2);
                
                term2.innerHTML += `
                    <div class="log-line" style="color: ${color}">
                        ${sess.acctstarttime} - User MAC ${sess.username} (${sess.framedipaddress}) - ${status} | Tx: ${outputMB} MB, Rx: ${inputMB} MB
                    </div>
                `;
            });
        }
    }

    // Toggle status AJAX API
    function toggleDeviceStatus(studentId, macAddress, status) {
        fetch('/admin/api/device/toggle_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId, mac_address: macAddress, status: status })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadDashboardData();
            } else {
                alert("Error updating status: " + data.error);
            }
        })
        .catch(err => console.error("Error:", err));
    }

    // Delete device AJAX API
    function deleteDevice(studentId, macAddress) {
        fetch('/admin/api/device/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId, mac_address: macAddress })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadDashboardData();
            } else {
                alert("Error deleting device: " + data.error);
            }
        })
        .catch(err => console.error("Error:", err));
    }

    // Add device manually AJAX API
    addDeviceForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const student_id = document.getElementById('add-student-id').value.trim();
        const telephone = document.getElementById('add-telephone').value.trim();
        const mac_address = document.getElementById('add-mac').value.trim();

        fetch('/admin/api/device/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id, telephone, mac_address })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                addDeviceForm.reset();
                alert("Device registered successfully!");
                loadDashboardData();
            } else {
                alert("Error registering device: " + data.error);
            }
        })
        .catch(err => console.error("Error adding device:", err));
    });

    // Legacy sync button trigger
    syncButton.addEventListener('click', () => {
        syncButton.disabled = true;
        syncButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Synchronizing...';
        
        fetch('/admin/api/sync_legacy', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                syncButton.disabled = false;
                syncButton.innerHTML = '<i class="fa fa-refresh"></i> Sync Legacy List';
                if (data.success) {
                    alert(data.message);
                    loadDashboardData();
                } else {
                    alert("Error: " + data.error);
                }
            })
            .catch(err => {
                syncButton.disabled = false;
                syncButton.innerHTML = '<i class="fa fa-refresh"></i> Sync Legacy List';
                console.error(err);
            });
    });

    // Render Stats Chart via Chart.js
    function renderChart(stats) {
        const ctx = document.getElementById('devicesChart');
        if (!ctx) return;

        if (activeChart) {
            activeChart.destroy();
        }

        activeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Active Devices', 'Blocked/Sandboxed', 'Simulated Active Sessions', 'Auth Failures'],
                datasets: [{
                    label: 'RADIUS Client Activity Status',
                    data: [
                        stats.active_devices, 
                        stats.blocked_devices, 
                        stats.active_sessions, 
                        stats.auth_failures
                    ],
                    backgroundColor: [
                        'rgba(0, 255, 178, 0.25)',
                        'rgba(255, 40, 80, 0.25)',
                        'rgba(0, 150, 255, 0.25)',
                        'rgba(240, 170, 0, 0.25)'
                    ],
                    borderColor: [
                        '#0ff',
                        '#f36',
                        '#39f',
                        '#f90'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#8a99ad',
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#8a99ad'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Initial load and run interval polling
    loadDashboardData();
    setInterval(loadDashboardData, 10000); // Poll logs/stats every 10 seconds
});
