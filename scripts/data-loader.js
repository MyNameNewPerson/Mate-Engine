export class DataLoader {
    constructor() {
        this.data = null;
    }

    async load() {
        try {
            const response = await fetch('data/database.json');
            this.data = await response.json();
            return this.data;
        } catch (error) {
            console.error('Failed to load database:', error);
            return null;
        }
    }

    getBrands() {
        return this.data.brands;
    }

    getDeviceTypes() {
        return this.data.device_types;
    }

    getModelsByBrand(brandId) {
        return this.data.models.filter(m => m.brand_id === brandId);
    }

    getModelsByType(typeId) {
        return this.data.models.filter(m => m.type_id === typeId);
    }

    getModelById(modelId) {
        return this.data.models.find(m => m.id === modelId);
    }

    getPartsByModel(modelId) {
        return this.data.parts.filter(p => p.model_id === modelId);
    }

    getPartById(partId) {
        return this.data.parts.find(p => p.id === partId);
    }

    getDeviceTypeById(typeId) {
        return this.data.device_types.find(t => t.id === typeId);
    }

    getBrandById(brandId) {
        return this.data.brands.find(b => b.id === brandId);
    }

    getRooms() {
        return this.data.rooms;
    }

    getBento(mode) {
        return this.data.bento[mode];
    }
}
