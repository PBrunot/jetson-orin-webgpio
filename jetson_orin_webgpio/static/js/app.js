class GPIOController {
    constructor() {
        this.pins = {};
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshRate = 5000; // 5 seconds
        this.userSelections = {}; // Track user's combo box selections
        this.init();
    }

    init() {
        this.loadPins();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshPins();
        });

        document.getElementById('clear-log').addEventListener('click', () => {
            this.clearLog();
        });

        document.getElementById('auto-refresh-toggle').addEventListener('click', () => {
            const enabled = this.toggleAutoRefresh();
            const button = document.getElementById('auto-refresh-toggle');
            button.textContent = `Auto-Refresh: ${enabled ? 'ON' : 'OFF'}`;
            button.className = `btn ${enabled ? 'btn-info' : 'btn-secondary'}`;
        });
    }

    startAutoRefresh() {
        if (this.autoRefreshEnabled && !this.refreshInterval) {
            this.refreshInterval = setInterval(() => {
                this.refreshPins();
            }, this.refreshRate);
            this.log('Auto-refresh started (5 second interval)', 'info');
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            this.log('Auto-refresh stopped', 'info');
        }
    }

    toggleAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.stopAutoRefresh();
            this.autoRefreshEnabled = false;
        } else {
            this.autoRefreshEnabled = true;
            this.startAutoRefresh();
        }
        return this.autoRefreshEnabled;
    }

    async loadPins() {
        try {
            const response = await fetch('/api/pins');
            if (!response.ok) throw new Error('Failed to load pins');
            
            this.pins = await response.json();
            this.renderPins();
            this.log('Pins loaded successfully', 'success');
        } catch (error) {
            this.log(`Error loading pins: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    renderPins() {
        this.renderPinoutDiagram();
        this.renderControllablePins();
    }

    renderPinoutDiagram() {
        const leftContainer = document.getElementById('pins-left');
        const rightContainer = document.getElementById('pins-right');
        
        leftContainer.innerHTML = '';
        rightContainer.innerHTML = '';

        // Render left side pins (odd numbers: 1, 3, 5, ..., 39)
        for (let pin = 1; pin <= 39; pin += 2) {
            const pinElement = this.createPinElement(pin, this.pins[pin]);
            leftContainer.appendChild(pinElement);
        }

        // Render right side pins (even numbers: 2, 4, 6, ..., 40)  
        for (let pin = 2; pin <= 40; pin += 2) {
            const pinElement = this.createPinElement(pin, this.pins[pin]);
            rightContainer.appendChild(pinElement);
        }
    }

    renderControllablePins() {
        const container = document.getElementById('controllable-pins');
        
        // Save current user selections before clearing
        this.saveCurrentSelections();
        
        container.innerHTML = '';

        for (const [pinNum, pinInfo] of Object.entries(this.pins)) {
            // Show all GPIO pins, both controllable and non-controllable
            if (pinInfo.type === 'gpio' && pinInfo.has_gpio_num) {
                const pinCard = this.createPinCard(pinNum, pinInfo);
                container.appendChild(pinCard);
            }
        }
    }

    saveCurrentSelections() {
        // Save user's combo box selections before refresh
        const selects = document.querySelectorAll('.direction-select');
        selects.forEach(select => {
            const pinNum = select.closest('[data-pin]').dataset.pin;
            this.userSelections[pinNum] = select.value;
        });
    }

    createPinElement(pinNum, pinInfo) {
        const pin = document.createElement('div');
        pin.className = `pin ${pinInfo.type}`;
        pin.dataset.pin = pinNum;

        if (pinInfo.type === 'gpio') {
            pin.classList.add(pinInfo.controllable ? 'controllable' : 'not-controllable');
        }

        const gpioNumText = pinInfo.gpio_num ? ` (${pinInfo.gpio_num})` : '';
        
        pin.innerHTML = `
            <div class="pin-number">${pinNum}</div>
            <div class="pin-label">${pinInfo.description}</div>
            ${pinInfo.gpio_num ? `<div class="pin-gpio-num">${pinInfo.gpio_num}</div>` : ''}
        `;

        // Add tooltip for more info
        pin.title = `Pin ${pinNum}: ${pinInfo.description}${gpioNumText}`;
        
        return pin;
    }

    createPinCard(pinNum, pinInfo) {
        const card = document.createElement('div');
        const isDisabled = !pinInfo.controllable;
        card.className = `pin-card gpio ${isDisabled ? 'disabled' : ''}`;
        card.dataset.pin = pinNum;

        const stateClass = pinInfo.state ? 'high' : 'low';
        const directionClass = pinInfo.direction ? pinInfo.direction.toLowerCase() : 'input';
        
        // Determine what to show in the combo box:
        // 1. User's pending selection (if they changed it but haven't clicked Setup)
        // 2. Server's actual pin direction
        // 3. Default to INPUT
        const userSelection = this.userSelections[pinNum];
        const serverDirection = pinInfo.direction || 'INPUT';
        const displayDirection = userSelection || serverDirection;

        // Determine status message for disabled pins
        let statusMessage = '';
        if (isDisabled) {
            if (pinInfo.has_gpio_num && !pinInfo.dts_configured) {
                statusMessage = `<div class="pin-status disabled-status">⚠️ Not configured in device tree</div>`;
            }
        } else {
            statusMessage = `<div class="pin-state ${stateClass} ${directionClass}">
                ${serverDirection} - ${pinInfo.state ? 'HIGH' : 'LOW'}
                ${userSelection && userSelection !== serverDirection ? 
                    `<span class="pending-change">(→${userSelection})</span>` : ''}
            </div>`;
        }

        card.innerHTML = `
            <div class="pin-header">
                <div class="pin-info">
                    <div class="pin-number">Pin ${pinNum}</div>
                    <div class="pin-label">${pinInfo.description}</div>
                    <div class="pin-bcm">GPIO ${pinInfo.gpio_num || 'N/A'}</div>
                </div>
                ${statusMessage}
            </div>
            <div class="pin-controls">
                <select class="direction-select" data-pin="${pinNum}" ${isDisabled ? 'disabled' : ''}>
                    <option value="INPUT" ${displayDirection === 'INPUT' ? 'selected' : ''}>INPUT</option>
                    <option value="OUTPUT" ${displayDirection === 'OUTPUT' ? 'selected' : ''}>OUTPUT</option>
                </select>
                <button class="setup-btn btn ${isDisabled ? 'btn-secondary' : 'btn-primary'} ${userSelection && userSelection !== serverDirection ? 'btn-warning' : ''}" ${isDisabled ? 'disabled' : ''}>
                    ${userSelection && userSelection !== serverDirection ? 'Apply Change' : 'Setup'}
                </button>
                <button class="read-btn btn ${isDisabled ? 'btn-secondary' : 'btn-info'}" ${isDisabled ? 'disabled' : ''}>Read</button>
                <button class="write-high-btn btn ${isDisabled ? 'btn-secondary' : 'btn-success'}" ${isDisabled ? 'disabled' : ''}>HIGH</button>
                <button class="write-low-btn btn ${isDisabled ? 'btn-secondary' : 'btn-danger'}" ${isDisabled ? 'disabled' : ''}>LOW</button>
            </div>
        `;

        if (!isDisabled) {
            this.setupPinEventListeners(card, pinNum);
        }
        return card;
    }

    setupPinEventListeners(card, pinNum) {
        const setupBtn = card.querySelector('.setup-btn');
        const readBtn = card.querySelector('.read-btn');
        const writeHighBtn = card.querySelector('.write-high-btn');
        const writeLowBtn = card.querySelector('.write-low-btn');
        const directionSelect = card.querySelector('.direction-select');

        // Track combo box changes
        directionSelect.addEventListener('change', () => {
            this.userSelections[pinNum] = directionSelect.value;
            this.updateSetupButton(pinNum);
        });

        setupBtn.addEventListener('click', () => {
            const direction = directionSelect.value;
            this.setupPin(pinNum, direction);
        });

        readBtn.addEventListener('click', () => {
            this.readPin(pinNum);
        });

        writeHighBtn.addEventListener('click', () => {
            this.writePin(pinNum, true);
        });

        writeLowBtn.addEventListener('click', () => {
            this.writePin(pinNum, false);
        });
    }

    updateSetupButton(pinNum) {
        const card = document.querySelector(`[data-pin="${pinNum}"]`);
        if (!card) return;

        const setupBtn = card.querySelector('.setup-btn');
        const directionSelect = card.querySelector('.direction-select');
        const stateElement = card.querySelector('.pin-state');

        const userSelection = this.userSelections[pinNum];
        const serverDirection = this.pins[pinNum]?.direction || 'INPUT';
        const hasChanges = userSelection && userSelection !== serverDirection;

        if (hasChanges) {
            setupBtn.textContent = 'Apply Change';
            setupBtn.className = 'setup-btn btn btn-warning';
            // Show pending change in state display
            if (stateElement && !stateElement.querySelector('.pending-change')) {
                stateElement.innerHTML += `<span class="pending-change">(→${userSelection})</span>`;
            }
        } else {
            setupBtn.textContent = 'Setup';
            setupBtn.className = 'setup-btn btn btn-primary';
            // Remove pending change indicator
            const pendingSpan = stateElement?.querySelector('.pending-change');
            if (pendingSpan) {
                pendingSpan.remove();
            }
        }
    }

    async setupPin(pinNum, direction) {
        try {
            this.showStatus(`Setting up pin ${pinNum} as ${direction}...`);
            
            const response = await fetch(`/api/pin/${pinNum}/setup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ direction: direction })
            });

            const result = await response.json();
            
            if (result.success) {
                this.log(`Pin ${pinNum}: ${result.message}`, 'success');
                this.showStatus(result.message, 'success');
                // Clear user selection since it's now applied
                delete this.userSelections[pinNum];
                this.updatePinDisplay(pinNum, result.pin_info);
            } else {
                this.log(`Pin ${pinNum} setup failed: ${result.message}`, 'error');
                this.showStatus(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`Error setting up pin ${pinNum}: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    async writePin(pinNum, state) {
        try {
            this.showStatus(`Writing ${state ? 'HIGH' : 'LOW'} to pin ${pinNum}...`);
            
            const response = await fetch(`/api/pin/${pinNum}/write`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ state: state })
            });

            const result = await response.json();
            
            if (result.success) {
                this.log(`Pin ${pinNum}: ${result.message}`, 'success');
                this.showStatus(result.message, 'success');
                this.updatePinDisplay(pinNum, result.pin_info);
            } else {
                this.log(`Pin ${pinNum} write failed: ${result.message}`, 'error');
                this.showStatus(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`Error writing to pin ${pinNum}: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    async readPin(pinNum) {
        try {
            this.showStatus(`Reading pin ${pinNum}...`);
            
            const response = await fetch(`/api/pin/${pinNum}/read`);
            const result = await response.json();
            
            if (result.success) {
                const stateText = result.state ? 'HIGH' : 'LOW';
                this.log(`Pin ${pinNum}: ${result.message} - ${stateText}`, 'info');
                this.showStatus(`Pin ${pinNum} is ${stateText}`, 'success');
                this.updatePinDisplay(pinNum, result.pin_info);
            } else {
                this.log(`Pin ${pinNum} read failed: ${result.message}`, 'error');
                this.showStatus(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`Error reading pin ${pinNum}: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    updatePinDisplay(pinNum, pinInfo) {
        const card = document.querySelector(`[data-pin="${pinNum}"]`);
        if (!card) return;

        const stateElement = card.querySelector('.pin-state');
        const directionSelect = card.querySelector('.direction-select');
        
        if (stateElement) {
            const stateClass = pinInfo.state ? 'high' : 'low';
            const directionClass = pinInfo.direction.toLowerCase();
            
            stateElement.className = `pin-state ${stateClass} ${directionClass}`;
            stateElement.textContent = `${pinInfo.direction} - ${pinInfo.state ? 'HIGH' : 'LOW'}`;
        }
        
        if (directionSelect) {
            directionSelect.value = pinInfo.direction;
        }

        // Update stored pin info
        this.pins[pinNum] = pinInfo;
    }

    async refreshPins() {
        this.showStatus('Refreshing pin states...');
        await this.loadPins();
        this.showStatus('Pin states refreshed', 'success');
    }

    showStatus(message, type = '') {
        const statusElement = document.getElementById('status-message');
        statusElement.textContent = message;
        statusElement.className = `status-message ${type}`;
        
        // Clear status after 5 seconds
        setTimeout(() => {
            statusElement.textContent = 'Ready';
            statusElement.className = 'status-message';
        }, 5000);
    }

    log(message, type = '') {
        const logContainer = document.getElementById('log-container');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Keep only last 100 log entries
        const entries = logContainer.querySelectorAll('.log-entry');
        if (entries.length > 100) {
            entries[0].remove();
        }
    }

    clearLog() {
        const logContainer = document.getElementById('log-container');
        logContainer.innerHTML = '<div class="log-entry">Log cleared</div>';
    }
}

// Initialize the GPIO controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new GPIOController();
});