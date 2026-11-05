/* ==========================================================================
   衡天⊙ PowerWiki — 离线缓存
   目标：断网也能打开已看过的页面，并且打开就有壳，不用等网络。全站无安装提示。
   策略：
     - 页面导航：先走网络，失败回缓存，再失败回 offline.html（永不白屏）
     - 样式 / 脚本 / manifest：先走网络（保证改完立刻生效），断网回缓存
     - 字体 / 图片：缓存优先 + 后台更新（这些文件基本不变，省流量）
     - 站内资源随看随缓存，离线时可用的页面会越来越多
   注意：service worker 只在 https 或 localhost 下注册，本地 file:// 打开不受影响。
   ========================================================================== */
const VERSION = "pw-v8";
const SHELL_CACHE = `${VERSION}-shell`;
const RUNTIME_CACHE = `${VERSION}-runtime`;

const SHELL = [
  "./",
  "./index.html",
  "./offline.html",
  "./manifest.webmanifest",
  "./rules.html",
  "./tiers.html",
  "./characters.html",
  "./materials.html",
  "./static/css/style.css",
  "./static/css/editorial.css",
  "./static/css/experience.css",
  "./static/css/editions.css",
  "./static/css/polish.css",
  "./static/css/app.css",
  "./static/js/theme.js",
  "./static/js/app.js",
  "./static/js/pwa.js",
  "./static/js/chrome.js",
  "./static/js/editions.js",
  "./static/img/icons/icon-192.png",
  "./static/img/icons/icon-512.png",
  "./static/img/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(SHELL_CACHE);
      // 单个文件失败不该让整次安装失败（比如某个页面刚好被改名）
      await Promise.all(
        SHELL.map((url) =>
          cache.add(new Request(url, { cache: "reload" })).catch(() => {})
        )
      );
      self.skipWaiting();
    })()
  );
});

async function warmShell() {
  const cache = await caches.open(SHELL_CACHE);
  const have = new Set((await cache.keys()).map((r) => new URL(r.url).pathname));
  await Promise.all(
    SHELL.map(async (url) => {
      const abs = new URL(url, self.registration.scope);
      if (have.has(abs.pathname)) return;
      try {
        const res = await fetch(abs.href, { cache: "reload" });
        if (res && res.ok) await cache.put(abs.href, res);
      } catch (err) {
        /* 断网时补不齐很正常，下次再补 */
      }
    })
  );
}

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))
      );
      await self.clients.claim();
      // 缓存被系统回收、或者用户手动清过，这里补齐常用的几个页面
      await warmShell();
    })()
  );
});

function isStatic(url) {
  return /\.(?:css|js|mjs|woff2?|ttf|otf|png|jpe?g|webp|avif|gif|svg|ico|json|webmanifest)$/i.test(
    url.pathname
  );
}

function isCode(url) {
  return /\.(?:css|js|mjs|webmanifest)$/i.test(url.pathname);
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // 跨域一律不管

  // 页面导航：网络优先，断网回落缓存，再回落离线页
  if (req.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const fresh = await fetch(req);
          // 只缓存真正存在的页面：404 之类的错误页不要留在本地
          if (fresh && fresh.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(req, fresh.clone());
          }
          return fresh;
        } catch (err) {
          const cached = (await caches.match(req)) || (await caches.match(req, { ignoreSearch: true }));
          if (cached) return cached;
          const offline =
            (await caches.match(new URL("./offline.html", self.registration.scope).href)) ||
            (await caches.match("./offline.html"));
          if (offline) return offline;
          return new Response("离线，且这个页面还没缓存过。", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
          });
        }
      })()
    );
    return;
  }

  if (!isStatic(url)) return;

  // 代码类资源更新频繁：先走网络，成功就顺手更新缓存；失败（离线）才用缓存。
  // 反过来（缓存优先）会让改完的样式在用户那里「晚一天」才生效。
  if (isCode(url)) {
    event.respondWith(
      (async () => {
        try {
          const fresh = await fetch(req);
          if (fresh && fresh.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(req, fresh.clone());
          }
          return fresh;
        } catch (err) {
          const cached = await caches.match(req);
          return cached || new Response("", { status: 504, statusText: "offline" });
        }
      })()
    );
    return;
  }

  // 字体 / 图片：缓存优先 + 后台更新
  event.respondWith(
    (async () => {
      const cached = await caches.match(req, { ignoreSearch: false });
      const network = fetch(req)
        .then(async (res) => {
          if (res && res.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(req, res.clone());
          }
          return res;
        })
        .catch(() => null);
      if (cached) return cached;
      const fresh = await network;
      return (
        fresh ||
        new Response("", { status: 504, statusText: "offline" })
      );
    })()
  );
});

// 页面里可以让 SW 预热当前栏目，方便「今天看过的明天没网也能看」
self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "pw-warm-shell") {
    event.waitUntil(warmShell());
    return;
  }
  if (data.type === "pw-precache" && Array.isArray(data.urls)) {
    event.waitUntil(
      (async () => {
        const cache = await caches.open(RUNTIME_CACHE);
        await Promise.all(
          data.urls.slice(0, 40).map((u) => cache.add(new Request(u, { cache: "reload" })).catch(() => {}))
        );
      })()
    );
  }
});
