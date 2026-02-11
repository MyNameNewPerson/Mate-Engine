export class Personalization {
    constructor(db) {
        this.db = db;
        this.historyKey = 'fixit3d_history';
        this.garageKey = 'fixit3d_garage';
        this.favoritesKey = 'fixit3d_favorites';
    }

    // --- HISTORY ---
    getHistory() {
        return JSON.parse(localStorage.getItem(this.historyKey)) || [];
    }

    addToHistory(partId) {
        let history = this.getHistory();
        history = history.filter(id => id !== partId);
        history.unshift(partId);
        localStorage.setItem(this.historyKey, JSON.stringify(history.slice(0, 5)));
        this.renderHistory();
    }

    renderHistory() {
        const container = document.getElementById('history-list');
        if (!container) return;

        const history = this.getHistory();
        if (history.length === 0) {
            container.innerHTML = '<li class="text-xs text-slate-600 italic">История пуста</li>';
            return;
        }

        container.innerHTML = history.map(id => {
            const part = this.db.getPartById(id);
            if (!part) return '';
            return `
                <li>
                    <a href="#/product/${part.id}" class="flex items-center gap-3 group">
                        <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-500 group-hover:text-skyBlue transition-all">
                            <i class="fas fa-history text-xs"></i>
                        </div>
                        <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-all truncate">${part.name}</span>
                    </a>
                </li>
            `;
        }).join('');
    }

    // --- GARAGE ---
    getGarage() {
        return JSON.parse(localStorage.getItem(this.garageKey)) || [];
    }

    addToGarage(deviceId) {
        let garage = this.getGarage();
        if (!garage.includes(deviceId)) {
            garage.push(deviceId);
            localStorage.setItem(this.garageKey, JSON.stringify(garage));
            this.renderGarage();
        }
    }

    renderGarage() {
        const container = document.getElementById('garage-list');
        if (!container) return;

        const garage = this.getGarage();
        const models = garage.map(id => this.db.getModelById(id)).filter(Boolean);

        container.innerHTML = `
            ${models.map(model => `
                <a href="#/device/${model.id}" class="flex items-center gap-3 p-3 glass rounded-xl hover:border-skyBlue/30 transition-all group">
                    <img src="${model.image}" class="w-10 h-10 rounded-lg object-cover">
                    <div class="truncate">
                        <div class="text-xs font-bold text-white truncate">${model.name}</div>
                        <div class="text-[10px] text-slate-500 uppercase font-black">В гараже</div>
                    </div>
                </a>
            `).join('')}
            <div onclick="location.hash='#/'" class="p-4 rounded-2xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center gap-2 text-slate-500 hover:border-skyBlue/30 hover:text-slate-300 transition-all cursor-pointer">
                <i class="fas fa-plus-circle text-2xl"></i>
                <span class="text-xs font-bold">Добавить устройство</span>
            </div>
        `;
    }

    // --- MAKES & CONFETTI ---
    handleIMadeThis(partId) {
        // Trigger Confetti
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#38BDF8', '#F97316', '#FFFFFF']
        });

        // Update User Badge
        document.getElementById('user-badge').classList.remove('hidden');

        // Visual Increment
        const counterEl = document.getElementById('makes-counter');
        if (counterEl) {
            const current = parseInt(counterEl.textContent);
            counterEl.textContent = current + 1;
            counterEl.classList.add('text-green-400', 'scale-110');
            setTimeout(() => counterEl.classList.remove('text-green-400', 'scale-110'), 1000);
        }
    }

    init() {
        this.renderHistory();
        this.renderGarage();
    }
}
