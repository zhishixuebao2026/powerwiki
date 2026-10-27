/* ==========================================================================
   衡天⊙ PowerWiki — Client Interactive Engine v6.0
   - Silent Browsing Cache (Scroll Position + Filter/Sort/View State Memory)
   - Smart Back Navigation Stack (Instant State Restoration on Return)
   - Standalone Character Pages (Zero Popup Modals)
   - 120fps rAF TOC ScrollSpy + Clean Scroll Lock Containment
   ========================================================================== */
(function () {
  "use strict";

  const STORAGE_KEYS = {
    theme: "pw_theme_v2",
    navStack: "pw_nav_stack_v6",
    pageCache: "pw_page_cache_v6",
    tierPrefs: "pw_tier_prefs_v6",
    charPrefs: "pw_char_prefs_v6",
    readerPrefs: "pw_reader_prefs_v6"
  };

  const ICONS = {
    sun: '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    moon: '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    arrowUpRight: '<svg class="svg-icon sm card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>'
  };

  const ROOT_PREFIX = document.documentElement.getAttribute("data-root") || "./";
  const PAGE_ID = document.documentElement.getAttribute("data-page-id") || location.pathname;
  const PAGE_TITLE = document.title.replace(/\s*[·|-]\s*衡天.*$/, "").trim() || document.title;

  function safeGetJSON(storage, key, fallback) {
    try {
      const raw = storage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function safeSetJSON(storage, key, val) {
    try {
      storage.setItem(key, JSON.stringify(val));
    } catch (_) {}
  }

  function escapeHTML(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function resolveUrl(relPath) {
    if (!relPath) return ROOT_PREFIX + "index.html";
    if (/^(https?:)?\/\//.test(relPath) || relPath.startsWith("#")) return relPath;
    const cleanRoot = ROOT_PREFIX.endsWith("/") ? ROOT_PREFIX : ROOT_PREFIX + "/";
    return cleanRoot + relPath.replace(/^\.\//, "");
  }

  function formatEvidenceBadges(text) {
    return escapeHTML(text)
      .replace(/〔实〕/g, '<span class="ev-badge ev-confirmed">〔实〕</span>')
      .replace(/〔下〕/g, '<span class="ev-badge ev-lower">〔下〕</span>')
      .replace(/〔推〕/g, '<span class="ev-badge ev-inferred">〔推〕</span>')
      .replace(/〔隐〕/g, '<span class="ev-badge ev-hidden">〔隐〕</span>')
      .replace(/〔缺〕/g, '<span class="ev-badge ev-missing">〔缺〕</span>');
  }

  /* --------------------------------------------------------------------------
     1. Scroll Lock & Drawer/Modal Backdrop Sync
     -------------------------------------------------------------------------- */
  function syncScrollLock() {
    const anyModalOpen = Boolean(document.querySelector(".modal-backdrop.open"));
    const drawer = document.getElementById("site-drawer");
    const sidebar = document.getElementById("doc-sidebar");
    const drawerBackdrop = document.getElementById("drawer-backdrop");
    const menuBtn = document.getElementById("mobile-menu-btn");

    const navOpen = Boolean(drawer && drawer.classList.contains("open"));
    const tocOpen = Boolean(sidebar && sidebar.classList.contains("drawer-open"));

    if (drawer) drawer.setAttribute("aria-hidden", navOpen ? "false" : "true");
    if (menuBtn) menuBtn.setAttribute("aria-expanded", navOpen ? "true" : "false");
    if (drawerBackdrop) {
      drawerBackdrop.classList.toggle("open", navOpen || tocOpen);
    }
    document.body.classList.toggle("is-scroll-locked", anyModalOpen || navOpen || tocOpen);
  }

  function closeAllDrawersAndModals() {
    document.querySelectorAll(".modal-backdrop.open").forEach((m) => m.classList.remove("open"));
    const drawer = document.getElementById("site-drawer");
    if (drawer) drawer.classList.remove("open");
    const sidebar = document.getElementById("doc-sidebar");
    if (sidebar) sidebar.classList.remove("drawer-open");
    syncScrollLock();
  }

  function scrollToElementWithOffset(el, smooth) {
    if (!el) return;
    const header = document.querySelector(".site-header");
    const alphaBar = document.querySelector(".alpha-bar.visible");
    const headerH = header ? header.getBoundingClientRect().height : 60;
    const alphaH = alphaBar ? alphaBar.getBoundingClientRect().height + 10 : 0;
    const targetY = Math.max(0, el.getBoundingClientRect().top + window.scrollY - headerH - alphaH - 16);
    window.scrollTo({ top: targetY, behavior: smooth ? "smooth" : "auto" });
  }

  /* --------------------------------------------------------------------------
     2. Theme Toggle & Mobile Menu
     -------------------------------------------------------------------------- */
  function initTheme() {
    const btn = document.getElementById("theme-toggle-btn");
    const updateIcon = () => {
      if (!btn) return;
      const cur = document.documentElement.getAttribute("data-theme") || "dark";
      btn.innerHTML = cur === "dark" ? ICONS.sun : ICONS.moon;
      btn.setAttribute("title", cur === "dark" ? "切换至浅色主题" : "切换至深色主题");
    };
    updateIcon();
    if (btn) {
      btn.addEventListener("click", () => {
        const root = document.documentElement;
        const cur = root.getAttribute("data-theme") || "dark";
        const next = cur === "dark" ? "light" : "dark";
        const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const applyTheme = () => {
          root.setAttribute("data-theme", next);
          try {
            localStorage.setItem(STORAGE_KEYS.theme, next);
          } catch (_) {}
          updateIcon();
        };

        if (!reduceMotion && typeof document.startViewTransition === "function") {
          try {
            document.startViewTransition(applyTheme);
            return;
          } catch (_) {}
        }

        if (!reduceMotion) {
          root.classList.add("theme-transitioning");
          void root.offsetWidth;
        }
        applyTheme();
        if (!reduceMotion) {
          window.setTimeout(() => root.classList.remove("theme-transitioning"), 420);
        }
      });
    }
  }

  function initMobileNav() {
    const btn = document.getElementById("mobile-menu-btn");
    const drawer = document.getElementById("site-drawer");
    const closeBtn = document.getElementById("site-drawer-close");
    const drawerBackdrop = document.getElementById("drawer-backdrop");

    window.__PW_CLOSE_ALL__ = closeAllDrawersAndModals;
    window.__PW_SYNC_LOCK__ = syncScrollLock;

    if (drawerBackdrop && drawerBackdrop.dataset.bound !== "1") {
      drawerBackdrop.dataset.bound = "1";
      drawerBackdrop.addEventListener("click", closeAllDrawersAndModals);
    }

    if (closeBtn && closeBtn.dataset.bound !== "1") {
      closeBtn.dataset.bound = "1";
      closeBtn.addEventListener("click", closeAllDrawersAndModals);
    }

    if (btn && drawer && btn.dataset.navBound !== "1") {
      btn.dataset.navBound = "1";
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        document.querySelectorAll(".modal-backdrop.open").forEach((m) => m.classList.remove("open"));
        const sidebar = document.getElementById("doc-sidebar");
        if (sidebar) sidebar.classList.remove("drawer-open");
        drawer.classList.toggle("open");
        syncScrollLock();
      });
    }

    if (drawer && drawer.dataset.linksBound !== "1") {
      drawer.dataset.linksBound = "1";
      drawer.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
          drawer.classList.remove("open");
          syncScrollLock();
        });
      });
    }

    window.addEventListener("pageshow", () => {
      closeAllDrawersAndModals();
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 1080) {
        if (drawer && drawer.classList.contains("open")) drawer.classList.remove("open");
        const sidebar = document.getElementById("doc-sidebar");
        if (sidebar && sidebar.classList.contains("drawer-open")) {
          sidebar.classList.remove("drawer-open");
        }
        syncScrollLock();
      }
    });
  }

  /* --------------------------------------------------------------------------
     3. Silent Browsing State Cache & Smart Back Navigation
     -------------------------------------------------------------------------- */
  function initBrowsingCacheAndBack() {
    const currentUrl = location.href.split("#")[0];
    let stack = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
    const pageCache = safeGetJSON(sessionStorage, STORAGE_KEYS.pageCache, {});

    if (!location.hash && pageCache[PAGE_ID] && typeof pageCache[PAGE_ID].scrollY === "number") {
      const targetY = pageCache[PAGE_ID].scrollY;
      if (targetY > 0) {
        requestAnimationFrame(() => {
          window.scrollTo({ top: targetY, behavior: "auto" });
        });
      }
    }

    if (stack.length === 0 || stack[stack.length - 1].url !== currentUrl) {
      stack.push({ url: currentUrl, pageId: PAGE_ID, title: PAGE_TITLE });
      if (stack.length > 35) stack = stack.slice(-35);
      safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, stack);
    }

    const backTopBtn = document.getElementById("dock-top-btn");
    const syncTopBtn = () => {
      if (backTopBtn) {
        backTopBtn.classList.toggle("is-hidden", (window.scrollY || 0) < 260);
      }
    };
    syncTopBtn();

    let cacheTimer = null;
    const persistScroll = () => {
      cacheTimer = null;
      const map = safeGetJSON(sessionStorage, STORAGE_KEYS.pageCache, {});
      map[PAGE_ID] = Object.assign(map[PAGE_ID] || {}, {
        scrollY: Math.round(window.scrollY || 0),
        ts: Date.now()
      });
      safeSetJSON(sessionStorage, STORAGE_KEYS.pageCache, map);
    };

    window.addEventListener(
      "scroll",
      () => {
        syncTopBtn();
        if (!cacheTimer) {
          cacheTimer = setTimeout(persistScroll, 150);
        }
      },
      { passive: true }
    );

    window.addEventListener("pagehide", persistScroll);

    if (backTopBtn) {
      backTopBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    const backBtns = document.querySelectorAll(".js-smart-back");
    const prevEntry = stack.length >= 2 ? stack[stack.length - 2] : null;

    backBtns.forEach((btn) => {
      const labelSpan = btn.querySelector(".js-back-label");
      const fallbackRel = btn.getAttribute("data-fallback") || "index.html";
      const fallbackName = btn.getAttribute("data-fallback-name") || "首页";

      if (prevEntry && labelSpan) {
        const shortPrev =
          prevEntry.title.length > 10 ? prevEntry.title.slice(0, 10) + "…" : prevEntry.title;
        labelSpan.textContent = "返回 · " + shortPrev;
        btn.setAttribute("title", "返回上一页：" + prevEntry.title);
      } else if (labelSpan) {
        labelSpan.textContent = "返回" + fallbackName;
      }

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        persistScroll();
        const curStack = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
        if (curStack.length >= 2) {
          curStack.pop();
          const target = curStack[curStack.length - 1];
          safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, curStack);
          location.href = target.url;
        } else {
          location.href = resolveUrl(fallbackRel);
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     4. Full-Text Document Reader (TOC ScrollSpy + Font/Wide Prefs)
     -------------------------------------------------------------------------- */
  function initDocumentReader() {
    const sidebar = document.getElementById("doc-sidebar");
    const tocNav = document.getElementById("toc-nav");
    const tocFilter = document.getElementById("toc-filter-input");
    const dockTocBtn = document.getElementById("dock-toc-btn");
    const mdBody = document.querySelector(".markdown-body");

    const prefs = safeGetJSON(localStorage, STORAGE_KEYS.readerPrefs, { fontSize: 15, wide: false });
    if (mdBody && prefs.fontSize) {
      mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
    }
    if (prefs.wide) {
      document.body.classList.add("wide-doc-mode");
    }

    const fontDecBtn = document.getElementById("doc-font-dec");
    const fontIncBtn = document.getElementById("doc-font-inc");
    const wideBtn = document.getElementById("doc-wide-toggle");
    if (wideBtn) {
      wideBtn.classList.toggle("active", Boolean(prefs.wide));
      wideBtn.setAttribute("aria-pressed", String(Boolean(prefs.wide)));
    }

    let rebuildTocOffsets = () => {};

    if (fontDecBtn && mdBody) {
      fontDecBtn.addEventListener("click", () => {
        prefs.fontSize = Math.max(13, Number((prefs.fontSize - 1).toFixed(1)));
        mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildTocOffsets();
      });
    }
    if (fontIncBtn && mdBody) {
      fontIncBtn.addEventListener("click", () => {
        prefs.fontSize = Math.min(20, Number((prefs.fontSize + 1).toFixed(1)));
        mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildTocOffsets();
      });
    }
    if (wideBtn) {
      wideBtn.addEventListener("click", () => {
        prefs.wide = !prefs.wide;
        document.body.classList.toggle("wide-doc-mode", prefs.wide);
        wideBtn.classList.toggle("active", prefs.wide);
        wideBtn.setAttribute("aria-pressed", String(prefs.wide));
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildTocOffsets();
      });
    }

    document.querySelectorAll(".heading-anchor").forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        e.preventDefault();
        const id = anchor.getAttribute("data-target-id");
        const url = location.href.split("#")[0] + "#" + id;
        history.replaceState(null, "", "#" + id);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).catch(() => {});
        }
        const orig = anchor.textContent;
        anchor.textContent = "已复制";
        anchor.style.opacity = "1";
        setTimeout(() => {
          anchor.textContent = orig;
          anchor.style.opacity = "";
        }, 1200);
      });
    });

    if (!sidebar || !tocNav) return;

    const tocLinks = Array.from(tocNav.querySelectorAll(".toc-item"));
    let spyItems = [];
    let activeLink = null;
    let pointerInsideToc = false;

    tocNav.addEventListener("pointerenter", () => (pointerInsideToc = true));
    tocNav.addEventListener("pointerleave", () => (pointerInsideToc = false));

    rebuildTocOffsets = () => {
      const sy = window.scrollY || 0;
      spyItems = tocLinks
        .map((link) => {
          const id = link.getAttribute("href").replace(/^#/, "");
          const el = document.getElementById(id);
          return el ? { link, el, id, top: el.getBoundingClientRect().top + sy } : null;
        })
        .filter(Boolean);
    };
    rebuildTocOffsets();
    window.addEventListener("load", rebuildTocOffsets);
    window.addEventListener("resize", rebuildTocOffsets);

    if (typeof ResizeObserver !== "undefined" && mdBody) {
      let roTimer = null;
      const ro = new ResizeObserver(() => {
        if (roTimer) clearTimeout(roTimer);
        roTimer = setTimeout(rebuildTocOffsets, 120);
      });
      ro.observe(mdBody);
    }

    tocLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        const id = link.getAttribute("href").replace(/^#/, "");
        const targetEl = document.getElementById(id);
        if (targetEl) {
          e.preventDefault();
          sidebar.classList.remove("drawer-open");
          syncScrollLock();
          history.replaceState(null, "", "#" + id);
          scrollToElementWithOffset(targetEl, true);
        }
      });
    });

    let spyTicking = false;
    function runScrollSpy() {
      spyTicking = false;
      if (!spyItems.length) return;
      const scrollPos = (window.scrollY || 0) + 120;
      let current = spyItems[0];
      for (let i = 0; i < spyItems.length; i++) {
        if (spyItems[i].top <= scrollPos) {
          current = spyItems[i];
        } else {
          break;
        }
      }
      if (current && current.link !== activeLink) {
        if (activeLink) activeLink.classList.remove("active");
        activeLink = current.link;
        activeLink.classList.add("active");

        if (!pointerInsideToc && activeLink.offsetParent !== null) {
          const navRect = tocNav.getBoundingClientRect();
          const linkRect = activeLink.getBoundingClientRect();
          if (linkRect.top < navRect.top + 32 || linkRect.bottom > navRect.bottom - 32) {
            tocNav.scrollTop += linkRect.top - navRect.top - navRect.height * 0.38;
          }
        }
      }
    }

    window.addEventListener(
      "scroll",
      () => {
        if (!spyTicking) {
          spyTicking = true;
          requestAnimationFrame(runScrollSpy);
        }
      },
      { passive: true }
    );
    runScrollSpy();

    if (tocFilter) {
      tocFilter.addEventListener("input", () => {
        const q = tocFilter.value.trim().toLowerCase();
        tocLinks.forEach((link) => {
          const match = !q || link.textContent.toLowerCase().includes(q);
          link.style.display = match ? "" : "none";
        });
      });
    }

    if (dockTocBtn) {
      dockTocBtn.addEventListener("click", () => {
        const drawer = document.getElementById("site-drawer");
        if (drawer) drawer.classList.remove("open");
        sidebar.classList.toggle("drawer-open");
        syncScrollLock();
      });
    }
  }

  /* --------------------------------------------------------------------------
     5. Tiers Explorer (tiers.html) — Strictly 从小到大 (#01 -> #97)
     -------------------------------------------------------------------------- */
  function initTiersExplorer() {
    const mount = document.getElementById("tiers-explorer-mount");
    if (!mount || !window.__POWERWIKI_DATA__ || !window.__POWERWIKI_DATA__.tiers) return;

    const { groups, tiers, allCharacters } = window.__POWERWIKI_DATA__;
    const groupMap = {};
    groups.forEach((g) => (groupMap[g.id] = g));
    const charCountByTier = {};
    (allCharacters || []).forEach((c) => {
      if (c && c.tier_slug) {
        charCountByTier[c.tier_slug] = (charCountByTier[c.tier_slug] || 0) + 1;
      }
    });

    const savedPrefs =
      safeGetJSON(sessionStorage, STORAGE_KEYS.tierPrefs, null) ||
      safeGetJSON(localStorage, STORAGE_KEYS.tierPrefs, {});
    const params = new URLSearchParams(location.search);

    const validSegs = ["all", "terrestrial", "stellar", "transition", "cosmic", "fgh", "beyond", "unranked"];
    const initSeg = params.get("seg") || savedPrefs.segment || "all";

    const state = {
      segment: validSegs.includes(initSeg) ? initSeg : "all",
      view: ["card", "flat", "table"].includes(savedPrefs.view) ? savedPrefs.view : "card",
      query: params.get("q") !== null ? params.get("q") : (savedPrefs.query || "")
    };

    const segBtns = document.querySelectorAll("[data-tier-seg]");
    const viewBtns = document.querySelectorAll("[data-tier-view]");
    const filterInput = document.getElementById("tier-filter-input");
    const clearBtn = document.getElementById("tier-filter-clear");
    const countBadge = document.getElementById("tier-result-count");

    if (filterInput && state.query) filterInput.value = state.query;

    function persistPrefs() {
      safeSetJSON(sessionStorage, STORAGE_KEYS.tierPrefs, {
        segment: state.segment,
        view: state.view,
        query: state.query
      });
      safeSetJSON(localStorage, STORAGE_KEYS.tierPrefs, {
        segment: state.segment,
        view: state.view
      });
    }

    function matchesTier(t) {
      if (state.segment !== "all" && t.domain !== state.segment) {
        return false;
      }
      if (!state.query) return true;
      const q = state.query.toLowerCase();
      const hay = [
        t.code,
        t.name,
        t.family,
        t.energy,
        t.scale,
        t.model,
        t.notes,
        t.code_pinyin,
        t.full_pinyin
      ]
        .join(" ")
        .toLowerCase();
      return q.split(/\s+/).every((tok) => hay.includes(tok));
    }

function renderCard(t) {
      const orderText = t.unranked ? "待定" : `#${String(t.order).padStart(2, "0")}`;
      const cCount = charCountByTier[t.slug] || 0;
      const charPill = cCount > 0 ? `<span class="tier-char-count">${cCount} 角色</span>` : "";
      return `
        <a class="tier-card" data-domain="${escapeHTML(t.domain)}" href="${resolveUrl("tier/" + t.slug + ".html")}">
          <span class="tier-card-art" aria-hidden="true"></span>
          <div class="tier-card-top">
            <span class="tier-badge mono">⊙ ${escapeHTML(t.code)}</span>
            <span class="tier-top-right">${charPill}<span class="tier-seq mono">${orderText}</span></span>
          </div>
          <div class="tier-name-row"><h3 class="tier-name">${escapeHTML(t.name)}</h3></div>
          <div class="tier-energy mono">${escapeHTML(t.energy)}</div>
          <p class="tier-scale">${escapeHTML(t.scale)}</p>
        </a>`;
    }

    function renderLadderStream(list) {
      const rows = list
        .map((t) => {
          const orderText = t.unranked ? "—" : `#${String(t.order).padStart(2, "0")}`;
          return `
          <a class="ladder-row" data-domain="${escapeHTML(t.domain)}" href="${resolveUrl("tier/" + t.slug + ".html")}">
            <span class="tier-seq mono">${orderText}</span>
            <span><span class="tier-badge mono">⊙ ${escapeHTML(t.code)}</span></span>
            <span class="ladder-title">${escapeHTML(t.name)}</span>
            <span class="tier-energy mono">${escapeHTML(t.energy)}</span>
            <span class="ladder-scale">${escapeHTML(t.scale)}</span>
            <span class="ladder-arrow">${ICONS.arrowUpRight}</span>
          </a>`;
        })
        .join("");

      return `
        <section class="group-section" id="group-flat">
          <div class="group-header">
            <h2 class="group-title">连续天梯</h2>
            <span class="group-sub">${list.length} 档 · 从小到大</span>
          </div>
          <div class="ladder-list">${rows}</div>
        </section>`;
    }

    function renderTable(list) {
      const rows = list
        .map((t) => {
          const orderText = t.unranked ? "—" : `#${String(t.order).padStart(2, "0")}`;
          return `
          <tr>
            <td class="mono">${orderText}</td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" class="tier-badge mono">⊙ ${escapeHTML(t.code)}</a></td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" class="table-primary-link">${escapeHTML(t.name)}</a></td>
            <td class="tier-energy mono">${escapeHTML(t.energy)}</td>
            <td>${escapeHTML(t.scale)}</td>
            <td>${escapeHTML(t.model)}</td>
          </tr>`;
        })
        .join("");
      return `
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>序位</th>
                <th>衡天代字</th>
                <th>量级名称</th>
                <th>能量 / 数学刻度</th>
                <th>覆盖尺度与典型参照</th>
                <th>计算模型</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
    }

    function render() {
      segBtns.forEach((b) => b.classList.toggle("active", b.dataset.tierSeg === state.segment));
      viewBtns.forEach((b) => b.classList.toggle("active", b.dataset.tierView === state.view));
      if (clearBtn) clearBtn.style.display = state.query ? "block" : "none";

      const filtered = tiers.filter(matchesTier);
      if (countBadge) countBadge.textContent = `${filtered.length} / ${tiers.length} 档`;

      if (filtered.length === 0) {
        mount.innerHTML = `
          <div class="empty-state-box">
            <h3 class="empty-state-title">未找到匹配的量级档位</h3>
            <p class="empty-state-sub">请尝试更换检索词或切换上方区间筛选条件。</p>
            <button type="button" class="btn btn-secondary btn-sm" id="reset-tier-filters">重置筛选条件</button>
          </div>`;
        const resetBtn = document.getElementById("reset-tier-filters");
        if (resetBtn) {
          resetBtn.addEventListener("click", () => {
            state.segment = "all";
            state.query = "";
            if (filterInput) filterInput.value = "";
            persistPrefs();
            render();
          });
        }
        return;
      }

      const ranked = filtered.filter((t) => !t.unranked).sort((a, b) => a.order - b.order);
      const unranked = filtered.filter((t) => t.unranked);
      const allOrdered = ranked.concat(unranked);

      if (state.view === "table") {
        mount.innerHTML = renderTable(allOrdered);
        return;
      }

      if (state.view === "flat") {
        mount.innerHTML = renderLadderStream(allOrdered);
        return;
      }

      const orderedGroupIds = [];
      allOrdered.forEach((t) => {
        if (!orderedGroupIds.includes(t.group_id)) orderedGroupIds.push(t.group_id);
      });

      mount.innerHTML = orderedGroupIds
        .map((gid) => {
          const g = groupMap[gid];
          const gItems = allOrdered.filter((t) => t.group_id === gid);
          return `
            <section class="group-section" id="group-${escapeHTML(gid)}">
              <div class="group-header">
                <h2 class="group-title">${escapeHTML(g ? g.title : gid)}</h2>
                <span class="group-sub">${gItems.length} 档</span>
              </div>
              <div class="tier-grid">${gItems.map(renderCard).join("")}</div>
            </section>`;
        })
        .join("");
    }

    segBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetSeg = btn.dataset.tierSeg;
        if (btn.classList.contains("atlas-cell") && state.segment === targetSeg) {
          state.segment = "all";
        } else {
          state.segment = targetSeg;
        }
        persistPrefs();
        render();
      });
    });

    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.view = btn.dataset.tierView;
        persistPrefs();
        render();
      });
    });

    if (filterInput) {
      filterInput.addEventListener("input", () => {
        state.query = filterInput.value.trim();
        persistPrefs();
        render();
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        state.query = "";
        if (filterInput) filterInput.value = "";
        persistPrefs();
        render();
      });
    }

    render();
  }

  /* --------------------------------------------------------------------------
     6. Characters Explorer (characters.html)
     - Dual Sort: ↑ 按量级从小到大 & A–Z 按首字母排序
     - Clean Cards Navigating to Standalone character/<slug>.html
     -------------------------------------------------------------------------- */
  function initCharactersExplorer() {
    const mount = document.getElementById("chars-explorer-mount");
    if (!mount || !window.__POWERWIKI_DATA__) return;

    const { tiers, allCharacters } = window.__POWERWIKI_DATA__;
    const tierBySlug = {};
    tiers.forEach((t) => (tierBySlug[t.slug] = t));

    const cached =
      safeGetJSON(sessionStorage, STORAGE_KEYS.charPrefs, null) ||
      safeGetJSON(localStorage, STORAGE_KEYS.charPrefs, {});
    const params = new URLSearchParams(location.search);

    const initSort = params.get("sort") || cached.sort || "asc";
    const validDomains = ["all", "terrestrial", "stellar", "transition", "cosmic", "fgh", "beyond"];
    const initDomain = cached.domain || "all";

    const state = {
      sort: initSort === "alpha" ? "alpha" : "asc",
      series: cached.series || "all",
      domain: validDomains.includes(initDomain) ? initDomain : "all",
      query: params.get("q") !== null ? params.get("q") : (cached.query || "")
    };

    const sortBtns = document.querySelectorAll("[data-char-sort]");
    const domainBtns = document.querySelectorAll("[data-char-domain]");
    const seriesSelect = document.getElementById("char-series-select");
    const filterInput = document.getElementById("char-filter-input");
    const alphaBar = document.getElementById("char-alpha-bar");
    const alphaLettersEl = document.getElementById("char-alpha-letters");
    const countBadge = document.getElementById("char-result-count");

    if (filterInput && state.query) filterInput.value = state.query;

    function persistPrefs() {
      safeSetJSON(sessionStorage, STORAGE_KEYS.charPrefs, {
        sort: state.sort,
        series: state.series,
        domain: state.domain,
        query: state.query
      });
      safeSetJSON(localStorage, STORAGE_KEYS.charPrefs, { sort: state.sort });
    }

    const pool = (allCharacters || []).map((c) => {
      const tier = tierBySlug[c.tier_slug] || tierBySlug["pending"];
      return Object.assign({}, c, {
        _tier: tier,
        _order: tier ? tier.order : 999,
        _domain: tier ? tier.domain : "unranked"
      });
    });

    const compactRoster = pool.length <= 8;
    if (compactRoster) {
      state.domain = "all";
      state.series = "all";
    }

    if (seriesSelect) {
      const allSeries = Array.from(new Set(pool.map((c) => c.series).filter(Boolean))).sort();
      seriesSelect.innerHTML =
        `<option value="all">全部作品（${allSeries.length}）</option>` +
        allSeries.map((s) => `<option value="${escapeHTML(s)}">${escapeHTML(s)}</option>`).join("");
      if (allSeries.includes(state.series)) {
        seriesSelect.value = state.series;
      } else {
        state.series = "all";
      }
    }

    function renderCharCard(c) {
      const t = c._tier;
      const orderLabel = t && !t.unranked ? `#${String(t.order).padStart(2, "0")}` : "待定";
      const originLine = escapeHTML(c.series || "未知出处");
      const tierLine = `<div class="char-tier-line"><span>${escapeHTML(t ? t.name : "待定")}</span><span class="mono">${orderLabel}</span></div>`;
      const summary = `<p class="char-summary">${escapeHTML(c.card_summary || c.summary || "")}</p>`;
      const foot = `<div class="char-foot"><span>${escapeHTML(c.doc_date || "已归档")} 更新</span><span class="card-link-hint">阅读档案 ${ICONS.arrowUpRight}</span></div>`;

      if (c.image_url) {
        const rawShape = c.image_shape || "portrait";
        const shape = ["landscape", "square", "portrait"].includes(rawShape) ? rawShape : "portrait";
        const imageUrl = resolveUrl(c.image_url);
        const sizeAttrs = c.image_w && c.image_h ? ` width="${Number(c.image_w)}" height="${Number(c.image_h)}"` : "";
        return `
        <a class="char-card has-media media-top" href="${resolveUrl("character/" + c.slug + ".html")}">
          <div class="char-card-media is-${shape}" data-art-label="${escapeHTML((c.pinyin || c.slug).toUpperCase())}" style="--char-image:url('${escapeHTML(imageUrl)}')"><img class="char-card-img" src="${escapeHTML(imageUrl)}" alt="${escapeHTML(c.name)}"${sizeAttrs} loading="lazy"></div>
          <div class="char-card-body">
            <div class="char-head">
              <div class="char-meta"><h3 class="char-name">${escapeHTML(c.name)}</h3><div class="char-origin">${originLine}</div></div>
              <span class="tier-badge gold mono">⊙ ${escapeHTML(t ? t.code : "待定")}</span>
            </div>
            ${tierLine}${summary}${foot}
          </div>
        </a>`;
      }

      return `
        <a class="char-card" href="${resolveUrl("character/" + c.slug + ".html")}">
          <div class="char-head">
            <div class="char-identity"><div class="char-monogram">${escapeHTML(c.name.slice(0, 1))}</div><div class="char-meta"><h3 class="char-name">${escapeHTML(c.name)}</h3><div class="char-origin">${originLine}</div></div></div>
            <span class="tier-badge gold mono">⊙ ${escapeHTML(t ? t.code : "待定")}</span>
          </div>
          ${tierLine}${summary}${foot}
        </a>`;
    }

    function render() {
      sortBtns.forEach((b) => b.classList.toggle("active", b.dataset.charSort === state.sort));
      domainBtns.forEach((b) => b.classList.toggle("active", b.dataset.charDomain === state.domain));

      const filtered = pool.filter((c) => {
        if (state.series !== "all" && c.series !== state.series) return false;
        if (state.domain !== "all" && c._domain !== state.domain) return false;
        if (!state.query) return true;
        const q = state.query.toLowerCase();
        const hay = [
          c.name,
          c.pinyin,
          c.initial,
          c.alias,
          c.series,
          c.realm,
          c.summary,
          c.full_writing || "",
          c._tier ? c._tier.code : "",
          c._tier ? c._tier.name : "",
          JSON.stringify(c.dims || {})
        ]
          .join(" ")
          .toLowerCase();
        return q.split(/\s+/).every((tok) => hay.includes(tok));
      });

      if (countBadge) {
        countBadge.textContent = `${filtered.length} / ${pool.length} 位`;
      }

      if (pool.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        mount.innerHTML = `
          <div class="empty-state-box">
            <h3 class="empty-state-title">当前暂未收录角色档案</h3>
            <p class="empty-state-sub">角色库已清空待录。后续在 data/characters.json 中录入角色后，将自动生成专属独立页面并支持按量级从小到大与按首字母 A–Z 排序。</p>
          </div>`;
        return;
      }

      if (filtered.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        mount.innerHTML = `
          <div class="empty-state-box">
            <h3 class="empty-state-title">没有符合筛选条件的角色</h3>
            <p class="empty-state-sub">当前区间或检索词下暂无匹配角色，可重置筛选查看全部角色。</p>
            <button type="button" class="btn btn-secondary btn-sm" id="reset-char-filters">重置筛选条件</button>
          </div>`;
        const resetBtn = document.getElementById("reset-char-filters");
        if (resetBtn) {
          resetBtn.addEventListener("click", () => {
            state.domain = "all";
            state.series = "all";
            state.query = "";
            if (filterInput) filterInput.value = "";
            if (seriesSelect) seriesSelect.value = "all";
            persistPrefs();
            render();
          });
        }
        return;
      }

      if (compactRoster) {
        if (alphaBar) alphaBar.classList.remove("visible");
        const sorted = filtered.slice().sort((a, b) => {
          if (state.sort === "alpha") return String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name));
          const diff = a._order - b._order;
          return diff !== 0 ? diff : String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name));
        });
        mount.innerHTML = `<div class="char-grid compact-roster-grid">${sorted.map(renderCharCard).join("")}</div>`;
        return;
      }

      if (state.sort === "alpha") {
        if (alphaBar) alphaBar.classList.add("visible");
        const buckets = {};
        filtered.forEach((c) => {
          const L = (c.initial || "#").toUpperCase();
          if (!buckets[L]) buckets[L] = [];
          buckets[L].push(c);
        });
        const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
        if (alphaLettersEl) {
          alphaLettersEl.innerHTML = alphabet
            .map((L) => {
              const has = buckets[L] && buckets[L].length > 0;
              return `<button type="button" class="alpha-key mono ${has ? "" : "disabled"}" ${
                has ? `data-char-letter="${L}" title="定位至首字母 ${L}"` : "disabled"
              }>${L}</button>`;
            })
            .join("");
          alphaLettersEl.querySelectorAll("[data-char-letter]").forEach((btn) => {
            btn.addEventListener("click", () => {
              const el = document.getElementById("char-letter-" + btn.dataset.charLetter);
              if (el) scrollToElementWithOffset(el, true);
            });
          });
        }

        mount.innerHTML = Object.keys(buckets)
          .sort()
          .map((L) => {
            const list = buckets[L]
              .slice()
              .sort((a, b) => String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name)));
            return `
              <section class="group-section" id="char-letter-${escapeHTML(L)}">
                <div class="group-header">
                  <h2 class="group-title"><span class="letter-pill">${escapeHTML(L)}</span> 首字母 ${escapeHTML(L)}</h2>
                  <span class="group-sub">${list.length} 位角色</span>
                </div>
                <div class="char-grid">${list.map(renderCharCard).join("")}</div>
              </section>`;
          })
          .join("");
      } else {
        if (alphaBar) alphaBar.classList.remove("visible");
        const sorted = filtered.slice().sort((a, b) => {
          const diff = a._order - b._order;
          return diff !== 0 ? diff : String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name));
        });
        mount.innerHTML = `
          <section class="group-section" id="char-scale-list">
            <div class="group-header">
              <h2 class="group-title">按主档量级从小到大排列（低量级 → 高量级）</h2>
              <span class="group-sub">${sorted.length} 位角色</span>
            </div>
            <div class="char-grid">${sorted.map(renderCharCard).join("")}</div>
          </section>`;
      }
    }

    sortBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.sort = btn.dataset.charSort;
        persistPrefs();
        render();
      });
    });

    domainBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.domain = btn.dataset.charDomain;
        persistPrefs();
        render();
      });
    });

    if (seriesSelect) {
      seriesSelect.addEventListener("change", () => {
        state.series = seriesSelect.value;
        persistPrefs();
        render();
      });
    }

    if (filterInput) {
      filterInput.addEventListener("input", () => {
        state.query = filterInput.value.trim();
        persistPrefs();
        render();
      });
    }

    render();
  }

  /* --------------------------------------------------------------------------
     7. Global Search Modal (Ctrl+K) & Dedicated Search Page
     -------------------------------------------------------------------------- */
  function runSearchQuery(rawQuery, typeFilter) {
    const index = window.__POWERWIKI_INDEX__ || [];
    const q = (rawQuery || "").trim().toLowerCase();
    const tokens = q ? q.split(/\s+/).filter(Boolean) : [];

    const results = [];
    for (const item of index) {
      if (typeFilter && typeFilter !== "all" && item.type !== typeFilter) continue;
      if (tokens.length === 0) {
        results.push({ item, score: item.type === "char" ? 55 : item.type === "tier" ? 50 : 30 });
        continue;
      }
      const titleLow = (item.title || "").toLowerCase();
      const codeLow = (item.code || "").toLowerCase();
      const bodyLow = (item.text || "").toLowerCase();
      const pyLow = (item.pinyin || "").toLowerCase();

      let allMatched = true;
      let score = 0;
      for (const tok of tokens) {
        const inCode = codeLow === tok || codeLow.includes(tok);
        const inTitle = titleLow.includes(tok);
        const inPy = pyLow.includes(tok);
        const inBody = bodyLow.includes(tok);
        if (!inCode && !inTitle && !inPy && !inBody) {
          allMatched = false;
          break;
        }
        if (codeLow === tok) score += 120;
        else if (inCode) score += 70;
        if (titleLow === tok) score += 100;
        else if (inTitle) score += 50;
        if (inPy) score += 35;
        if (inBody) score += 15;
      }
      if (allMatched) results.push({ item, score });
    }

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, 60).map((r) => r.item);
  }

  function highlightSnippet(text, rawQuery) {
    const clean = String(text || "");
    const tokens = (rawQuery || "")
      .trim()
      .split(/\s+/)
      .filter((t) => t.length >= 1);
    if (tokens.length === 0) {
      return escapeHTML(clean.slice(0, 145)) + (clean.length > 145 ? "…" : "");
    }
    const lower = clean.toLowerCase();
    let firstIdx = -1;
    for (const tok of tokens) {
      const idx = lower.indexOf(tok.toLowerCase());
      if (idx !== -1 && (firstIdx === -1 || idx < firstIdx)) firstIdx = idx;
    }
    const start = Math.max(0, firstIdx - 32);
    const slice =
      (start > 0 ? "…" : "") +
      clean.slice(start, start + 150) +
      (start + 150 < clean.length ? "…" : "");
    let html = escapeHTML(slice);
    tokens.forEach((tok) => {
      const safeTok = escapeHTML(tok).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      if (safeTok) {
        html = html.replace(new RegExp("(" + safeTok + ")", "gi"), "<mark>$1</mark>");
      }
    });
    return html;
  }

  const TYPE_LABELS = {
    tier: "量级分类",
    char: "角色档案",
    rules: "衡天第五版",
    materials: "材质能量库"
  };

  function initGlobalSearchModal() {
    const triggers = document.querySelectorAll("#global-search-trigger, .js-open-search");
    const backdrop = document.getElementById("search-modal");
    const input = document.getElementById("search-modal-input");
    const closeBtn = document.getElementById("search-modal-close");
    const body = document.getElementById("search-modal-results");
    const tabBtns = document.querySelectorAll("[data-search-tab]");

    if (!backdrop || !input || !body) return;
    let activeTab = "all";
    let focusedIdx = 0;

    function closeModal() {
      backdrop.classList.remove("open");
      syncScrollLock();
    }

    function renderHits() {
      const q = input.value;
      const hits = runSearchQuery(q, activeTab).slice(0, 30);
      focusedIdx = 0;
      if (hits.length === 0) {
        body.innerHTML = `<div class="search-modal-empty">未找到与「${escapeHTML(q)}」相关的条目，可尝试检索「宇◆」「归因」「完整书写」「中子星」「花岗岩」。</div>`;
        return;
      }
      body.innerHTML = hits
        .map(
          (h, idx) => `
          <a class="search-hit ${idx === 0 ? "focused" : ""}" href="${resolveUrl(h.url)}">
            <div class="search-hit-top">
              <span class="search-hit-title">${highlightSnippet(h.title, q)}</span>
              <span class="search-hit-type">${escapeHTML(h.badge || TYPE_LABELS[h.type] || h.type)}</span>
            </div>
            <div class="search-hit-snippet">${highlightSnippet(h.text, q)}</div>
          </a>`
        )
        .join("");

      body.querySelectorAll(".search-hit").forEach((el) => {
        el.addEventListener("click", closeModal);
      });
    }

    function openModal() {
      const drawer = document.getElementById("site-drawer");
      if (drawer) drawer.classList.remove("open");
      const sidebar = document.getElementById("doc-sidebar");
      if (sidebar) sidebar.classList.remove("drawer-open");
      backdrop.classList.add("open");
      syncScrollLock();
      renderHits();
      setTimeout(() => input.focus(), 25);
    }

    triggers.forEach((t) => t.addEventListener("click", openModal));
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal();
    });

    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        activeTab = btn.dataset.searchTab;
        tabBtns.forEach((b) => b.classList.toggle("active", b === btn));
        renderHits();
      });
    });

    input.addEventListener("input", renderHits);
    input.addEventListener("keydown", (e) => {
      const items = Array.from(body.querySelectorAll(".search-hit"));
      if (!items.length) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        focusedIdx = (focusedIdx + 1) % items.length;
        items.forEach((el, i) => el.classList.toggle("focused", i === focusedIdx));
        items[focusedIdx].scrollIntoView({ block: "nearest" });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        focusedIdx = (focusedIdx - 1 + items.length) % items.length;
        items.forEach((el, i) => el.classList.toggle("focused", i === focusedIdx));
        items[focusedIdx].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && items[focusedIdx]) {
        e.preventDefault();
        items[focusedIdx].click();
      }
    });

    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openModal();
      } else if (
        e.key === "/" &&
        !["INPUT", "TEXTAREA", "SELECT"].includes((document.activeElement || {}).tagName)
      ) {
        e.preventDefault();
        openModal();
      } else if (e.key === "Escape") {
        closeAllDrawersAndModals();
      }
    });
  }

  function initDedicatedSearchPage() {
    const mount = document.getElementById("dedicated-search-results");
    const input = document.getElementById("dedicated-search-input");
    const typeBtns = document.querySelectorAll("[data-page-search-type]");
    if (!mount || !input) return;

    const params = new URLSearchParams(location.search);
    let curType = params.get("type") || "all";
    if (params.get("q")) input.value = params.get("q");

    function render() {
      typeBtns.forEach((b) => b.classList.toggle("active", b.dataset.pageSearchType === curType));
      const q = input.value;
      const hits = runSearchQuery(q, curType);
      const countEl = document.getElementById("dedicated-search-count");
      if (countEl) countEl.textContent = `${hits.length} 条结果`;

      if (hits.length === 0) {
        mount.innerHTML = `
          <div class="empty-state-box">
            <h3 class="empty-state-title">没有找到匹配内容</h3>
            <p class="empty-state-sub">试试检索代字（如 恒○、宇◆、外·门）、第五版规则（如 明确设定陈述、标注图与动图、归因审查）或材质名称（如 中子星、花岗岩）。</p>
          </div>`;
        return;
      }

      mount.innerHTML = hits
        .map(
          (h) => `
          <a class="search-hit card-mode" href="${resolveUrl(h.url)}">
            <div class="search-hit-top">
              <span class="search-hit-title">${highlightSnippet(h.title, q)}</span>
              <span class="search-hit-type">${escapeHTML(h.badge || TYPE_LABELS[h.type] || h.type)}</span>
            </div>
            <div class="search-hit-snippet">${highlightSnippet(h.text, q)}</div>
          </a>`
        )
        .join("");
    }

    input.addEventListener("input", render);
    typeBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        curType = btn.dataset.pageSearchType;
        render();
      });
    });

    document.querySelectorAll("[data-hot-query]").forEach((chip) => {
      chip.addEventListener("click", () => {
        input.value = chip.getAttribute("data-hot-query");
        render();
      });
    });

    render();
  }

  function initReadingProgress() {
    const bar = document.getElementById("reading-progress-bar");
    const article = document.querySelector(".markdown-body");
    if (!bar || !article) return;

    let queued = false;
    function update() {
      queued = false;
      const headerHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-h")) || 64;
      const articleTop = article.getBoundingClientRect().top + window.scrollY;
      const start = articleTop - headerHeight - 24;
      const end = articleTop + article.offsetHeight - window.innerHeight * 0.55;
      const progress = Math.min(1, Math.max(0, (window.scrollY - start) / Math.max(1, end - start)));
      bar.style.transform = `scaleX(${progress})`;
      bar.parentElement.classList.toggle("is-reading", progress > 0 && progress < 1);
      bar.parentElement.classList.toggle("is-complete", progress >= 1);
    }
    function requestUpdate() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(update);
    }

    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(requestUpdate);
    update();
  }

  function initHorizontalRails() {
    document.querySelectorAll(".chip-rail, .alpha-letters").forEach((rail) => {
      rail.addEventListener(
        "wheel",
        (e) => {
          if (rail.scrollWidth > rail.clientWidth && Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
            e.preventDefault();
            rail.scrollLeft += e.deltaY;
          }
        },
        { passive: false }
      );
    });
  }

  function initMotionReveal() {
    const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    const targets = document.querySelectorAll(
      ".portal-card, .tier-card, .char-card, .spec-card, .neighbor-row, .pager-card"
    );
    if (!targets.length) return;

    const observer = new IntersectionObserver((entries, activeObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in-view");
        activeObserver.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -36px 0px", threshold: 0.06 });

    targets.forEach((target, index) => {
      target.classList.add("motion-reveal");
      target.style.setProperty("--reveal-delay", `${(index % 4) * 55}ms`);
      observer.observe(target);
    });
    requestAnimationFrame(() => document.documentElement.classList.add("has-motion-reveal"));
  }

  /* --------------------------------------------------------------------------
     Boot — Render synchronous DOM lists FIRST, then restore cached scrollY
     -------------------------------------------------------------------------- */
  function bootAll() {
    initTheme();
    initMobileNav();
    initTiersExplorer();
    initCharactersExplorer();
    initDedicatedSearchPage();
    initDocumentReader();
    initReadingProgress();
    initBrowsingCacheAndBack();
    initGlobalSearchModal();
    initHorizontalRails();
    initMotionReveal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootAll);
  } else {
    bootAll();
  }
})();
