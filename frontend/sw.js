/**
 * 书法识文 — Service Worker
 * 提供基础离线缓存 + PWA 安装能力
 */
const CACHE_NAME = "calligraphy-app-v6";

// 需要缓存的静态资源
const PRECACHE_URLS = [
    "./",
    "./index.html",
    "./style.css",
    "./config.js",
    "./app.js",
    "./manifest.json"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        })
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((names) => {
            return Promise.all(
                names
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    // 只缓存静态资源，API 请求不做缓存
    if (event.request.url.includes("/api/")) {
        return;
    }
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request);
        })
    );
});
