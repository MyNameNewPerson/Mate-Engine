const fs = require('fs');

const data = JSON.parse(fs.readFileSync('./data/database.json', 'utf8'));
const baseUrl = 'https://fixit3d.com/#';

let sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n';
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

// Home
sitemap += `  <url><loc>${baseUrl}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n`;

// Brands
data.brands.forEach(brand => {
    sitemap += `  <url><loc>${baseUrl}/brand/${brand.id}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n`;
});

// Models
data.models.forEach(model => {
    sitemap += `  <url><loc>${baseUrl}/device/${model.id}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>\n`;
});

// Parts
data.parts.forEach(part => {
    sitemap += `  <url><loc>${baseUrl}/product/${part.id}</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>\n`;
});

sitemap += '</urlset>';

fs.writeFileSync('sitemap.xml', sitemap);
console.log('Sitemap generated successfully in sitemap.xml');
