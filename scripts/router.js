export class Router {
    constructor() {
        this.routes = {};
        window.addEventListener('hashchange', () => this.handleRoute());
    }

    addRoute(path, callback) {
        this.routes[path] = callback;
    }

    handleRoute() {
        const hash = window.location.hash || '#/';
        const [path, paramsStr] = hash.split('?');

        // Find matching route with parameters
        for (const routePath in this.routes) {
            const routeParts = routePath.split('/');
            const hashParts = path.split('/');

            if (routeParts.length === hashParts.length) {
                const params = {};
                let match = true;

                for (let i = 0; i < routeParts.length; i++) {
                    if (routeParts[i].startsWith(':')) {
                        params[routeParts[i].slice(1)] = hashParts[i];
                    } else if (routeParts[i] !== hashParts[i]) {
                        match = false;
                        break;
                    }
                }

                if (match) {
                    this.routes[routePath](params);
                    return;
                }
            }
        }

        // Default to home if no match
        if (this.routes['#/']) {
            this.routes['#/']();
        }
    }

    navigateTo(hash) {
        window.location.hash = hash;
    }

    init() {
        this.handleRoute();
    }
}
