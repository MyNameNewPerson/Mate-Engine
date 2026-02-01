import { DataLoader } from './data-loader.js';
import { Router } from './router.js';
import { Personalization } from './personalization.js';

class App {
    constructor() {
        this.db = new DataLoader();
        this.router = new Router();
        this.personal = new Personalization(this.db);
        this.currentMode = 'repair';
        this.userRegion = 'Global'; // Default

        this.init();
    }

    async init() {
        await this.db.load();
        this.detectRegion();
        this.setupRoutes();
        this.setupEventListeners();
        this.renderSidebar();
        this.personal.init();
        this.router.init();
    }

    detectRegion() {
        // Mocking GEO detection
        // In a real app, we could use a free IP API or browser locale
        const isCIS = navigator.language.includes('ru') || navigator.language.includes('be') || navigator.language.includes('kk');
        this.userRegion = isCIS ? 'CIS' : 'Global';
        console.log(`Detected region: ${this.userRegion}`);
    }

    setupRoutes() {
        this.router.addRoute('#/', () => this.renderHome());
        this.router.addRoute('#/brand/:id', (params) => this.renderBrandView(params.id));
        this.router.addRoute('#/device/:id', (params) => this.renderDeviceView(params.id));
        this.router.addRoute('#/product/:id', (params) => this.renderProductPage(params.id));
    }

    setupEventListeners() {
        document.getElementById('repair-mode-btn').addEventListener('click', () => this.setMode('repair'));
        document.getElementById('hobby-mode-btn').addEventListener('click', () => this.setMode('hobby'));

        const searchInput = document.getElementById('omni-search');
        searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));

        // Close search results on click outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#omni-search') && !e.target.closest('#search-results')) {
                document.getElementById('search-results').classList.add('hidden');
            }
        });
    }

    setMode(mode) {
        this.currentMode = mode;
        const repairBtn = document.getElementById('repair-mode-btn');
        const hobbyBtn = document.getElementById('hobby-mode-btn');
        const body = document.body;

        if (mode === 'repair') {
            body.classList.remove('hobby-mode');
            body.classList.add('repair-mode');
            repairBtn.classList.add('bg-skyBlue', 'text-white');
            repairBtn.classList.remove('text-slate-400');
            hobbyBtn.classList.remove('bg-orangeAccent', 'text-white');
            hobbyBtn.classList.add('text-slate-400');
            document.getElementById('sidebar-context-title').textContent = 'Комнаты';
        } else {
            body.classList.remove('repair-mode');
            body.classList.add('hobby-mode');
            hobbyBtn.classList.add('bg-orangeAccent', 'text-white');
            hobbyBtn.classList.remove('text-slate-400');
            repairBtn.classList.remove('bg-skyBlue', 'text-white');
            repairBtn.classList.add('text-slate-400');
            document.getElementById('sidebar-context-title').textContent = 'Категории Хобби';
        }

        this.renderSidebar();
        if (window.location.hash === '#/' || !window.location.hash) {
            this.renderHome();
        }
    }

    renderSidebar() {
        const sidebarList = document.getElementById('dynamic-sidebar-list');
        const brandList = document.getElementById('sidebar-brands');

        // Render Rooms/Categories
        if (this.currentMode === 'repair') {
            sidebarList.innerHTML = this.db.getRooms().map(room => `
                <li>
                    <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white transition-all">
                        <i class="fas ${room.icon} w-5 text-center"></i> ${room.name}
                    </a>
                </li>
            `).join('');
        } else {
            sidebarList.innerHTML = `
                <li><a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white transition-all"><i class="fas fa-dragon w-5 text-center"></i> Миниатюры</a></li>
                <li><a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white transition-all"><i class="fas fa-home w-5 text-center"></i> Декор</a></li>
                <li><a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white transition-all"><i class="fas fa-car w-5 text-center"></i> Моделизм</a></li>
            `;
        }

        // Render Brands
        brandList.innerHTML = this.db.getBrands().map(brand => `
            <a href="#/brand/${brand.id}" class="glass p-3 rounded-xl flex items-center justify-center hover:border-white/20 transition-all group">
                <img src="${brand.logo}" alt="${brand.name}" class="h-6 object-contain grayscale group-hover:grayscale-0 transition-all">
            </a>
        `).join('');
    }

    renderHome() {
        const viewContainer = document.getElementById('view-container');
        const bentoItems = this.db.getBento(this.currentMode);

        viewContainer.innerHTML = `
            <h1 class="text-4xl font-black mb-8">${this.currentMode === 'repair' ? 'Ремонтируй с умом' : 'Твори без границ'}</h1>
            <div class="bento-grid">
                ${bentoItems.map((item, index) => {
                    let link = '#/';
                    if (item.type === 'device_type') link = `#/brand/bosch`; // Simplified for demo
                    else if (item.type === 'tag') link = `#/device/bosch_benvenuto_tca`;
                    else if (item.type === 'category') link = `#/device/bosch_benvenuto_tca`;

                    return `
                        <div class="bento-item ${item.size}" onclick="location.hash='${link}'">
                            <img src="https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=60&w=800&sig=${index}" class="absolute inset-0 w-full h-full object-cover">
                            <div class="overlay"></div>
                        <div class="content">
                            <h3 class="text-xl font-bold">${item.title}</h3>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        this.updateBreadcrumbs([{ name: 'Главная', link: '#/' }]);
    }

    handleSearch(query) {
        const resultsContainer = document.getElementById('search-results');
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }

        const brands = this.db.getBrands().filter(b => b.name.toLowerCase().includes(query.toLowerCase()));
        const models = this.db.data.models.filter(m => m.name.toLowerCase().includes(query.toLowerCase()));
        const parts = this.db.data.parts.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));

        if (brands.length === 0 && models.length === 0 && parts.length === 0) {
            resultsContainer.innerHTML = '<div class="p-4 text-slate-500 text-sm italic">Ничего не найдено...</div>';
        } else {
            resultsContainer.innerHTML = `
                <div class="max-h-96 overflow-y-auto custom-scrollbar">
                    ${brands.map(b => `
                        <a href="#/brand/${b.id}" class="flex items-center gap-4 p-4 hover:bg-white/5 transition-all border-b border-white/5">
                            <div class="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center p-2"><img src="${b.logo}" class="object-contain grayscale"></div>
                            <div>
                                <div class="font-bold text-skyBlue">${b.name}</div>
                                <div class="text-xs text-slate-500 uppercase tracking-widest font-bold">Бренд</div>
                            </div>
                        </a>
                    `).join('')}
                    ${models.map(m => `
                        <a href="#/device/${m.id}" class="flex items-center gap-4 p-4 hover:bg-white/5 transition-all border-b border-white/5">
                            <div class="w-10 h-10 rounded-lg overflow-hidden bg-white/10"><img src="${m.image}" class="w-full h-full object-cover"></div>
                            <div>
                                <div class="font-bold text-white">${m.name}</div>
                                <div class="text-xs text-slate-500 uppercase tracking-widest font-bold">Устройство</div>
                            </div>
                        </a>
                    `).join('')}
                    ${parts.map(p => `
                        <a href="#/product/${p.id}" class="flex items-center gap-4 p-4 hover:bg-white/5 transition-all border-b border-white/5">
                            <div class="w-10 h-10 rounded-lg bg-skyBlue/20 flex items-center justify-center text-skyBlue"><i class="fas fa-cog"></i></div>
                            <div>
                                <div class="font-bold text-white">${p.name}</div>
                                <div class="text-xs text-slate-500 uppercase tracking-widest font-bold">Деталь</div>
                            </div>
                        </a>
                    `).join('')}
                </div>
            `;
        }

        resultsContainer.classList.remove('hidden');
    }

    updateBreadcrumbs(crumbs) {
        const container = document.getElementById('breadcrumbs');
        container.innerHTML = crumbs.map((crumb, index) => `
            ${index > 0 ? '<i class="fas fa-chevron-right text-[10px] mx-1"></i>' : ''}
            <a href="${crumb.link || '#'}" class="${index === crumbs.length - 1 ? 'text-white font-bold' : 'hover:text-slate-300 transition-all'}">${crumb.name}</a>
        `).join('');
    }

    renderBrandView(id) {
        const brand = this.db.getBrandById(id);
        if (!brand) return;

        const viewContainer = document.getElementById('view-container');
        const deviceTypes = brand.types.map(tid => this.db.getDeviceTypeById(tid)).filter(Boolean);

        viewContainer.innerHTML = `
            <div class="mb-8">
                <img src="${brand.logo}" class="h-12 object-contain mb-4 grayscale brightness-200">
                <h1 class="text-4xl font-black">Какая у вас техника ${brand.name}?</h1>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${deviceTypes.map(type => `
                    <div class="glass p-8 rounded-3xl hover:border-skyBlue/50 transition-all cursor-pointer group" onclick="location.hash='#/device/${this.db.getModelsByBrand(id).find(m => m.type_id === type.id)?.id || ''}'">
                        <i class="fas ${type.icon_class} text-5xl text-skyBlue mb-6 group-hover:scale-110 transition-all block"></i>
                        <h3 class="text-2xl font-black">${type.name}</h3>
                        <p class="text-slate-500 mt-2">Найти запчасти для ${type.name.toLowerCase()}</p>
                    </div>
                `).join('')}
            </div>
        `;

        this.updateBreadcrumbs([
            { name: 'Главная', link: '#/' },
            { name: brand.name, link: `#/brand/${id}` }
        ]);
    }

    renderDeviceView(id) {
        const model = this.db.getModelById(id);
        if (!model) return;

        const viewContainer = document.getElementById('view-container');
        const brand = this.db.getBrandById(model.brand_id);

        viewContainer.innerHTML = `
            <div class="mb-8 flex justify-between items-end">
                <div>
                    <h1 class="text-4xl font-black mb-2">${model.name}</h1>
                    <p class="text-slate-400">Выберите узел на схеме или деталь из списка ниже</p>
                </div>
                <button id="add-to-garage-btn" class="px-6 py-3 glass rounded-xl text-sm font-bold hover:border-skyBlue/50 transition-all">
                    <i class="fas fa-plus mr-2 text-skyBlue"></i> В ГАРАЖ
                </button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Visual Navigator -->
                <div class="lg:col-span-2 relative glass rounded-3xl overflow-hidden aspect-video group">
                    <img src="${model.image}" class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-all">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>

                    <!-- Hotspots -->
                    ${model.visual_hotspots.map(spot => {
                        const part = this.db.getPartById(spot.part_id);
                        return `
                            <div class="hotspot group/spot" style="left: ${spot.x}%; top: ${spot.y}%"
                                onclick="location.hash='#/product/${spot.part_id}'">
                                <div class="hidden group-hover/spot:block absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-48 glass p-3 rounded-xl text-center pointer-events-none">
                                    <div class="text-xs font-black uppercase text-skyBlue mb-1">Узел</div>
                                    <div class="text-sm font-bold text-white">${part?.name || 'Деталь'}</div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Parts List -->
                <div class="space-y-4">
                    <h3 class="text-xl font-black mb-4">Все запчасти</h3>
                    <div class="space-y-2 max-h-[500px] overflow-y-auto custom-scrollbar pr-2">
                        ${this.db.getPartsByModel(id).map(part => `
                            <a href="#/product/${part.id}" class="flex items-center gap-4 p-4 glass rounded-2xl hover:border-white/20 transition-all">
                                <div class="w-12 h-12 rounded-xl bg-skyBlue/10 flex items-center justify-center text-skyBlue text-xl">
                                    <i class="fas fa-cog"></i>
                                </div>
                                <div>
                                    <div class="font-bold text-sm">${part.name}</div>
                                    <div class="text-[10px] text-slate-500 uppercase font-black mt-1">${part.specs.material}</div>
                                </div>
                                <i class="fas fa-chevron-right ml-auto text-slate-600 text-xs"></i>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        this.updateBreadcrumbs([
            { name: 'Главная', link: '#/' },
            { name: brand.name, link: `#/brand/${brand.id}` },
            { name: model.name, link: `#/device/${id}` }
        ]);

        document.getElementById('add-to-garage-btn').addEventListener('click', () => {
            this.personal.addToGarage(id);
            alert('Добавлено в ваш виртуальный гараж!');
        });
    }

    renderProductPage(id) {
        const part = this.db.getPartById(id);
        if (!part) return;

        this.personal.addToHistory(id);

        const model = this.db.getModelById(part.model_id);
        const brand = this.db.getBrandById(model.brand_id);
        const viewContainer = document.getElementById('view-container');

        // Calculate Savings
        const weightGram = parseInt(part.specs.weight);
        const costToPrint = (weightGram * 0.02).toFixed(2);
        const retailPrice = 25.00; // Mock retail price
        const savings = (retailPrice - costToPrint).toFixed(2);

        const affiliateLinks = this.generateAffiliateLinks(part.affiliate_query);

        viewContainer.innerHTML = `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                <!-- Left: Visuals -->
                <div class="space-y-6">
                    <div class="glass rounded-3xl overflow-hidden aspect-square relative group">
                        <img src="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=800" class="w-full h-full object-cover">
                        <div class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-all backdrop-blur-sm">
                            <button class="px-8 py-4 bg-white text-black font-black rounded-xl hover:scale-105 transition-all">
                                <i class="fas fa-cube mr-2"></i> 3D VIEW
                            </button>
                        </div>
                    </div>

                    <!-- Print Recipe -->
                    <div class="glass p-6 rounded-3xl">
                        <h3 class="text-xl font-black mb-4">Print Recipe</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-white/5 p-4 rounded-2xl border border-white/5">
                                <div class="text-[10px] text-slate-500 font-black uppercase mb-1">Material</div>
                                <div class="font-bold"><i class="fas fa-scroll text-skyBlue mr-2"></i>${part.specs.material}</div>
                            </div>
                            <div class="bg-white/5 p-4 rounded-2xl border border-white/5">
                                <div class="text-[10px] text-slate-500 font-black uppercase mb-1">Infill</div>
                                <div class="font-bold"><i class="fas fa-border-none text-skyBlue mr-2"></i>${part.specs.infill}</div>
                            </div>
                            <div class="bg-white/5 p-4 rounded-2xl border border-white/5">
                                <div class="text-[10px] text-slate-500 font-black uppercase mb-1">Supports</div>
                                <div class="font-bold"><i class="fas fa-tree text-skyBlue mr-2"></i>${part.specs.supports}</div>
                            </div>
                            <div class="bg-white/5 p-4 rounded-2xl border border-white/5">
                                <div class="text-[10px] text-slate-500 font-black uppercase mb-1">Print Time</div>
                                <div class="font-bold"><i class="fas fa-clock text-skyBlue mr-2"></i>${part.specs.print_time}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right: Info & Actions -->
                <div class="space-y-8">
                    <div>
                        <div class="flex items-center gap-3 mb-4">
                            <span class="badge badge-verified">Verified</span>
                            ${parseInt(part.specs.print_time) < 1 ? '<span class="badge badge-easy">Easy Print</span>' : ''}
                            ${part.tags.includes('mechanical') ? '<span class="badge badge-stress">High Stress</span>' : ''}
                        </div>
                        <h1 class="text-5xl font-black leading-tight mb-2">${part.name}</h1>
                        <p class="text-slate-400 text-lg">Совместимо с <strong>${part.compatibility.join(', ')}</strong></p>
                    </div>

                    <!-- Cost Calculator -->
                    <div class="bg-skyBlue/10 border border-skyBlue/20 p-6 rounded-3xl flex items-center justify-between">
                        <div>
                            <div class="text-skyBlue font-black uppercase text-xs tracking-widest">Savings Calculator</div>
                            <div class="text-2xl font-black">Вы экономите $${savings}!</div>
                            <div class="text-slate-400 text-sm">Себестоимость печати: $${costToPrint} vs $${retailPrice} (Retail)</div>
                        </div>
                        <i class="fas fa-piggy-bank text-4xl text-skyBlue"></i>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <button class="py-4 bg-skyBlue text-white font-black rounded-2xl shadow-xl shadow-skyBlue/20 hover:scale-105 active:scale-95 transition-all">
                            <i class="fas fa-download mr-2"></i> STL FREE
                        </button>
                        <button id="i-made-this-btn" class="py-4 glass border-white/10 text-white font-black rounded-2xl hover:bg-white/5 transition-all">
                            <i class="fas fa-check-circle mr-2 text-green-400"></i> I MADE THIS!
                        </button>
                    </div>

                    <div class="flex items-center gap-4 text-sm font-bold">
                        <div class="flex -space-x-2">
                            <img src="https://i.pravatar.cc/150?u=1" class="w-8 h-8 rounded-full border-2 border-slate-900">
                            <img src="https://i.pravatar.cc/150?u=2" class="w-8 h-8 rounded-full border-2 border-slate-900">
                            <img src="https://i.pravatar.cc/150?u=3" class="w-8 h-8 rounded-full border-2 border-slate-900">
                        </div>
                        <div class="text-slate-400"><span id="makes-counter" class="text-white transition-all duration-500 inline-block">${part.fake_makes_count}</span> человек уже напечатали это</div>
                    </div>

                    <!-- Affiliate Section -->
                    <div class="space-y-4">
                        <h3 class="text-sm font-black uppercase tracking-widest text-slate-500">Купить готовое</h3>
                        <div class="grid grid-cols-1 gap-2">
                            ${affiliateLinks.map(link => `
                                <a href="${link.url}" target="_blank" class="flex items-center justify-between p-4 glass rounded-2xl hover:border-white/20 transition-all group">
                                    <div class="flex items-center gap-3">
                                        <i class="fab ${link.icon} text-xl text-slate-400 group-hover:text-white transition-all"></i>
                                        <span class="font-bold text-slate-300 group-hover:text-white">${link.name}</span>
                                    </div>
                                    <i class="fas fa-external-link-alt text-xs text-slate-600"></i>
                                </a>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Installation Video -->
                    ${part.installation_guide ? `
                        <div class="space-y-4">
                            <h3 class="text-sm font-black uppercase tracking-widest text-slate-500">Инструкция по установке</h3>
                            <div class="glass rounded-3xl overflow-hidden aspect-video relative">
                                <iframe class="w-full h-full" src="https://www.youtube.com/embed/${part.installation_guide.youtube_id}" frameborder="0" allowfullscreen></iframe>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        this.updateBreadcrumbs([
            { name: 'Главная', link: '#/' },
            { name: brand.name, link: `#/brand/${brand.id}` },
            { name: model.name, link: `#/device/${model.id}` },
            { name: part.name, link: `#/product/${id}` }
        ]);

        document.getElementById('i-made-this-btn').addEventListener('click', () => {
            this.personal.handleIMadeThis(id);
        });

        this.updateSEO(part, brand, model);
    }

    updateSEO(part, brand, model) {
        document.title = `Скачать ${part.name} для ${brand.name} ${model.name} | Бесплатно STL | FixIt3D`;

        // Dynamic JSON-LD
        let script = document.getElementById('json-ld');
        if (script) script.remove();

        script = document.createElement('script');
        script.id = 'json-ld';
        script.type = 'application/ld+json';
        const jsonLd = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": part.name,
            "image": `https://source.unsplash.com/random/800x800?${part.tags[0]}`,
            "description": `3D-печатная запчасть ${part.name} для устройства ${brand.name} ${model.name}.`,
            "brand": {
                "@type": "Brand",
                "name": brand.name
            },
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        };
        script.text = JSON.stringify(jsonLd);
        document.head.appendChild(script);
    }

    generateAffiliateLinks(query) {
        if (this.userRegion === 'CIS') {
            return [
                { name: 'AliExpress', url: `https://search.aliexpress.com/search.htm?keywords=${encodeURIComponent(query)}`, icon: 'fa-alipay' },
                { name: 'Ozon', url: `https://www.ozon.ru/search/?text=${encodeURIComponent(query)}`, icon: 'fa-shopping-basket' }
            ];
        } else {
            return [
                { name: 'Amazon', url: `https://www.amazon.com/s?k=${encodeURIComponent(query)}`, icon: 'fa-amazon' },
                { name: 'eBay', url: `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(query)}`, icon: 'fa-ebay' }
            ];
        }
    }
}

// Instantiate the App
new App();
