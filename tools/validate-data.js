const fs = require('fs');

const data = JSON.parse(fs.readFileSync('./data/database.json', 'utf8'));

console.log('--- Starting Data Integrity Check ---');

let errors = 0;

// Check Brands
data.brands.forEach(brand => {
    brand.types.forEach(typeId => {
        if (!data.device_types.find(t => t.id === typeId)) {
            console.error(`Error: Brand ${brand.id} references unknown device type ${typeId}`);
            errors++;
        }
    });
});

// Check Models
data.models.forEach(model => {
    if (!data.brands.find(b => b.id === model.brand_id)) {
        console.error(`Error: Model ${model.id} references unknown brand ${model.brand_id}`);
        errors++;
    }
    if (!data.device_types.find(t => t.id === model.type_id)) {
        console.error(`Error: Model ${model.id} references unknown device type ${model.type_id}`);
        errors++;
    }
    model.visual_hotspots.forEach(spot => {
        if (!data.parts.find(p => p.id === spot.part_id)) {
            console.error(`Error: Model ${model.id} hotspot references unknown part ${spot.part_id}`);
            errors++;
        }
    });
});

// Check Parts
data.parts.forEach(part => {
    if (!data.models.find(m => m.id === part.model_id)) {
        console.error(`Error: Part ${part.id} references unknown model ${part.model_id}`);
        errors++;
    }
});

if (errors === 0) {
    console.log('✅ All data integrity checks passed!');
} else {
    console.log(`❌ Found ${errors} errors in data.`);
    process.exit(1);
}
