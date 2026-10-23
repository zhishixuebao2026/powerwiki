/* ==========================================================================
   衡天⊙ PowerWiki — Client Interactive Engine v4.0
   - 120fps rAF Scroll Engine (Cached Offsets + GPU scaleX Progress Bar)
   - Full Scroll-Lock & Overscroll Containment for Modals & Mobile Drawers
   - Tiers: Strictly 从小到大 (#01 -> #97) across Card / Timeline / Sheet views
   - Characters: Dual Sort (量级从小到大 & 首字母 A–Z) + 7D Astrolabe Modal
   ========================================================================== */
(function () {
  "use strict";

  const STORAGE_KEYS = {
    theme: "pw_theme_v2",
    progress: "pw_progress_v3",
    footprints: "pw_footprints_v3",
    navStack: "pw_nav_stack_v3",
    restoreScroll: "pw_restore_scroll_v3",
    tierPrefs: "pw_tier_prefs_v3",
    charPrefs: "pw_char_prefs_v3",
    readerPrefs: "pw_reader_prefs_v3"
  };

  const ICONS = {
    sun: '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    moon: '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    arrowUpRight: '<svg class="svg-icon sm tier-card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>',
    search: '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    check: '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    bookmark: '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>'
  };

  const ROOT_PREFIX = document.documentElement.getAttribute("data-root") || "./";
  const PAGE_ID = document.documentElement.getAttribute("data-page-id") || location.pathname;
  const PAGE_TITLE = document.title.replace(/\s*[·|-]\s*衡天.*$/, "").trim() || document.title;
  const PAGE_TYPE = document.documentElement.getAttribute("data-page-type") || "page";

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
    const escaped = escapeHTML(text);
    return escaped
      .replace(/〔实〕/g, '<span class="ev-badge ev-confirmed">〔实〕</span>')
      .replace(/〔下〕/g, '<span class="ev-badge ev-lower">〔下〕</span>')
      .replace(/〔推〕/g, '<span class="ev-badge ev-inferred">〔推〕</span>')
      .replace(/〔隐〕/g, '<span class="ev-badge ev-hidden">〔隐〕</span>')
      .replace(/〔缺〕/g, '<span class="ev-badge ev-missing">〔缺〕</span>');
  }

  function timeAgo(ts) {
    if (!ts) return "";
    const sec = Math.max(1, Math.floor((Date.now() - ts) / 1000));
    if (sec < 60) return "刚刚";
    if (sec < 3600) return Math.floor(sec / 60) + " 分钟前";
    if (sec < 86400) return Math.floor(sec / 3600) + " 小时前";
    return Math.floor(sec / 86400) + " 天前";
  }

  /* --------------------------------------------------------------------------
     Centralized Scroll Lock & Drawer Backdrop Manager (Eliminates Scroll Bleed)
     -------------------------------------------------------------------------- */
  function syncScrollLock() {
    const anyModalOpen = Boolean(document.querySelector(".modal-backdrop.open"));
    const nav = document.getElementById("main-nav");
    const sidebar = document.getElementById("doc-sidebar");
    const drawerBackdrop = document.getElementById("drawer-backdrop");

    const navOpen = Boolean(nav && nav.classList.contains("open"));
    const tocOpen = Boolean(sidebar && sidebar.classList.contains("drawer-open"));

    if (drawerBackdrop) {
      drawerBackdrop.classList.toggle("open", navOpen || tocOpen);
    }
    document.body.classList.toggle(
      "is-scroll-locked",
      anyModalOpen || navOpen || tocOpen
    );
  }

  function closeAllDrawersAndModals() {
    document.querySelectorAll(".modal-backdrop.open").forEach((m) => m.classList.remove("open"));
    const nav = document.getElementById("main-nav");
    if (nav) nav.classList.remove("open");
    const sidebar = document.getElementById("doc-sidebar");
    if (sidebar) sidebar.classList.remove("drawer-open");
    syncScrollLock();
  }

  function scrollToElementWithOffset(el, smooth) {
    if (!el) return;
    const header = document.querySelector(".site-header");
    const alphaBar = document.querySelector(".alpha-bar.visible");
    const headerH = header ? header.getBoundingClientRect().height : 60;
    const alphaH = alphaBar ? alphaBar.getBoundingClientRect().height + 12 : 0;
    const offset = headerH + alphaH + 18;
    const targetY = Math.max(0, el.getBoundingClientRect().top + window.scrollY - offset);
    window.scrollTo({ top: targetY, behavior: smooth ? "smooth" : "auto" });
  }

  /* Build SVG 7-Dimension Astrolabe Chart */
  function buildHeptadRadarSVG(dims, tierOrder) {
    const axes = ["破", "控", "域", "御", "速", "算", "性"];
    const cx = 100;
    const cy = 100;
    const maxR = 68;
    const baseRatio = Math.min(0.95, Math.max(0.28, (tierOrder || 30) / 97));

    function scoreAxis(key) {
      const val = String((dims && dims[key]) || "").trim();
      if (!val || val === "—" || val.startsWith("〔缺〕")) return 0.16;
      if (key === "性") {
        const count = val.split(/[、，,]/).filter(Boolean).length;
        return Math.min(0.92, 0.42 + count * 0.18);
      }
      if (key === "算") {
        if (val.includes("超限") || val.includes("0⁽ω⁾")) return 0.94;
        if (val.includes("0′") || val.includes("0″")) return 0.78;
        if (val.includes("有限")) return 0.48;
        return 0.4;
      }
      if (key === "速") {
        if (val.includes("无限") || val.includes("时间外")) return 0.96;
        if (val.includes("超光速")) return 0.82;
        if (val.includes("亚光速") || val.includes("马赫")) return 0.58;
        return 0.38;
      }
      if (key === "域") {
        if (val.includes("可数无限") || val.includes("全域")) return 0.88;
        return 0.56;
      }
      return baseRatio;
    }

    const rings = [0.33, 0.66, 1.0]
      .map((r) => {
        const pts = axes
          .map((_, i) => {
            const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 7;
            return `${(cx + maxR * r * Math.cos(ang)).toFixed(1)},${(cy + maxR * r * Math.sin(ang)).toFixed(1)}`;
          })
          .join(" ");
        return `<polygon points="${pts}" fill="none" stroke="var(--border-medium)" stroke-width="1"/>`;
      })
      .join("");

    const spokes = axes
      .map((label, i) => {
        const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 7;
        const x2 = (cx + maxR * Math.cos(ang)).toFixed(1);
        const y2 = (cy + maxR * Math.sin(ang)).toFixed(1);
        const lx = (cx + (maxR + 17) * Math.cos(ang)).toFixed(1);
        const ly = (cy + (maxR + 17) * Math.sin(ang) + 4).toFixed(1);
        return `
          <line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="var(--border-subtle)" stroke-width="1"/>
          <text x="${lx}" y="${ly}" text-anchor="middle" fill="var(--accent-gold)" font-size="11.5" font-weight="600">${label}</text>`;
      })
      .join("");

    const dataPts = axes.map((k, i) => {
      const s = scoreAxis(k);
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 7;
      return {
        x: (cx + maxR * s * Math.cos(ang)).toFixed(1),
        y: (cy + maxR * s * Math.sin(ang)).toFixed(1)
      };
    });

    const polyPts = dataPts.map((p) => `${p.x},${p.y}`).join(" ");
    const dots = dataPts
      .map((p) => `<circle cx="${p.x}" cy="${p.y}" r="3" fill="var(--accent-gold)"/>`)
      .join("");

    return `
      <svg width="200" height="200" viewBox="0 0 200 200" aria-label="七维战力浑仪">
        ${rings}
        ${spokes}
        <polygon points="${polyPts}" fill="var(--accent-gold-soft)" stroke="var(--accent-gold)" stroke-width="1.75"/>
        ${dots}
      </svg>`;
  }

  /* --------------------------------------------------------------------------
     1. Theme Management
     -------------------------------------------------------------------------- */
  function initTheme() {
    const btn = document.getElementById("theme-toggle-btn");
    const updateIcon = () => {
      if (!btn) return;
      const cur = document.documentElement.getAttribute("data-theme") || "dark";
      btn.innerHTML = cur === "dark" ? ICONS.sun : ICONS.moon;
      btn.setAttribute("title", cur === "dark" ? "切换至浅色纸本主题" : "切换至深空黑曜主题");
    };
    updateIcon();
    if (btn) {
      btn.addEventListener("click", () => {
        const cur = document.documentElement.getAttribute("data-theme") || "dark";
        const next = cur === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        try {
          localStorage.setItem(STORAGE_KEYS.theme, next);
        } catch (_) {}
        updateIcon();
      });
    }
  }

  /* --------------------------------------------------------------------------
     2. Mobile Navigation & Drawer Backdrop
     -------------------------------------------------------------------------- */
  function initMobileNav() {
    const btn = document.getElementById("mobile-menu-btn");
    const nav = document.getElementById("main-nav");
    const drawerBackdrop = document.getElementById("drawer-backdrop");

    if (drawerBackdrop) {
      drawerBackdrop.addEventListener("click", () => {
        closeAllDrawersAndModals();
      });
    }

    if (!btn || !nav) return;
    btn.addEventListener("click", () => {
      const sidebar = document.getElementById("doc-sidebar");
      if (sidebar) sidebar.classList.remove("drawer-open");
      nav.classList.toggle("open");
      syncScrollLock();
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("open");
        syncScrollLock();
      });
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 1080) {
        if (nav.classList.contains("open")) nav.classList.remove("open");
        const sidebar = document.getElementById("doc-sidebar");
        if (sidebar && sidebar.classList.contains("drawer-open")) {
          sidebar.classList.remove("drawer-open");
        }
        syncScrollLock();
      }
    });
  }

  /* --------------------------------------------------------------------------
     3. Smart Back Button & Internal Navigation Stack
     -------------------------------------------------------------------------- */
  function initSmartNavigation() {
    let stack = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
    const currentUrl = location.href.split("#")[0];

    const restoreTarget = safeGetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, null);
    if (restoreTarget && restoreTarget.url === currentUrl) {
      sessionStorage.removeItem(STORAGE_KEYS.restoreScroll);
      requestAnimationFrame(() => {
        window.scrollTo({ top: restoreTarget.scrollY || 0, behavior: "auto" });
      });
    }

    if (stack.length === 0 || stack[stack.length - 1].url !== currentUrl) {
      stack.push({
        url: currentUrl,
        pageId: PAGE_ID,
        title: PAGE_TITLE,
        scrollY: window.scrollY || 0,
        ts: Date.now()
      });
      if (stack.length > 30) stack = stack.slice(-30);
      safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, stack);
    }

    let scrollTimer = null;
    window.addEventListener(
      "scroll",
      () => {
        if (scrollTimer) return;
        scrollTimer = setTimeout(() => {
          scrollTimer = null;
          const st = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
          if (st.length > 0 && st[st.length - 1].url === currentUrl) {
            st[st.length - 1].scrollY = Math.round(window.scrollY || 0);
            safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, st);
          }
        }, 220);
      },
      { passive: true }
    );

    const backBtns = document.querySelectorAll(".js-smart-back");
    const prevEntry = stack.length >= 2 ? stack[stack.length - 2] : null;

    backBtns.forEach((btn) => {
      const labelSpan = btn.querySelector(".js-back-label");
      const fallbackRel = btn.getAttribute("data-fallback") || "index.html";
      const fallbackName = btn.getAttribute("data-fallback-name") || "首页";

      if (prevEntry && labelSpan) {
        const shortPrev =
          prevEntry.title.length > 12 ? prevEntry.title.slice(0, 12) + "…" : prevEntry.title;
        labelSpan.textContent = "返回 · " + shortPrev;
        btn.setAttribute("title", "返回上一页：" + prevEntry.title);
      } else if (labelSpan) {
        labelSpan.textContent = "返回" + fallbackName;
      }

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const curStack = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
        if (curStack.length >= 2) {
          curStack.pop();
          const target = curStack[curStack.length - 1];
          safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, curStack);
          safeSetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, {
            url: target.url,
            scrollY: target.scrollY || 0
          });
          location.href = target.url;
        } else {
          location.href = resolveUrl(fallbackRel);
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     4. 120fps rAF Scroll Progress, Cached Heading Offsets & Resume Toast
     -------------------------------------------------------------------------- */
  let cachedHeadingPositions = [];

  function rebuildHeadingCache() {
    const nodes = Array.from(
      document.querySelectorAll(
        ".markdown-body h1[id], .markdown-body h2[id], .markdown-body h3[id], .tier-group-block[id]"
      )
    );
    const sy = window.scrollY || 0;
    cachedHeadingPositions = nodes.map((el) => {
      const titleEl = el.matches(".tier-group-block")
        ? el.querySelector(".tier-group-title")
        : el;
      const txt = titleEl ? titleEl.textContent.replace(/#$/, "").trim() : PAGE_TITLE;
      return {
        id: el.id || "",
        text: txt,
        top: el.getBoundingClientRect().top + sy
      };
    });
  }

  function getActiveHeadingFromCache() {
    if (!cachedHeadingPositions.length) rebuildHeadingCache();
    if (!cachedHeadingPositions.length) return { id: "", text: PAGE_TITLE };
    const threshold = (window.scrollY || 0) + 130;
    let active = cachedHeadingPositions[0];
    for (let i = 0; i < cachedHeadingPositions.length; i++) {
      if (cachedHeadingPositions[i].top <= threshold) {
        active = cachedHeadingPositions[i];
      } else {
        break;
      }
    }
    return active;
  }

  function recordFootprint() {
    if (PAGE_ID === "index.html") return;
    let list = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);
    list = list.filter((item) => item.pageId !== PAGE_ID);
    list.unshift({
      pageId: PAGE_ID,
      title: PAGE_TITLE,
      type: PAGE_TYPE,
      ts: Date.now()
    });
    if (list.length > 18) list = list.slice(0, 18);
    safeSetJSON(localStorage, STORAGE_KEYS.footprints, list);
  }

  function initReadingProgress() {
    const topBar = document.getElementById("reading-progress-bar");
    const ringCircle = document.getElementById("dock-progress-circle");
    const tocPct = document.getElementById("toc-progress-pct");
    const backTopBtn = document.getElementById("dock-top-btn");
    const historyBtn = document.getElementById("history-open-btn");
    const liveStatus = document.getElementById("live-save-status");
    const bookmarkBtn = document.getElementById("save-bookmark-btn");

    const isTrackable =
      PAGE_TYPE === "doc" ||
      PAGE_TYPE === "tiers" ||
      PAGE_TYPE === "chars" ||
      PAGE_TYPE === "tier-detail" ||
      PAGE_TYPE === "char-detail";

    rebuildHeadingCache();
    window.addEventListener("load", rebuildHeadingCache);
    window.addEventListener("resize", rebuildHeadingCache);

    const updateHistoryDot = () => {
      if (!historyBtn) return;
      const prog = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const fp = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);
      historyBtn.classList.toggle(
        "has-progress",
        Object.keys(prog).length > 0 || fp.length > 0
      );
    };
    updateHistoryDot();

    if (backTopBtn) {
      backTopBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    function getScrollMetrics() {
      const docEl = document.documentElement;
      const maxScroll = Math.max(1, docEl.scrollHeight - window.innerHeight);
      if (docEl.scrollHeight <= window.innerHeight + 40) {
        return { ratio: 1, pct: 100 };
      }
      const ratio = Math.min(1, Math.max(0, (window.scrollY || 0) / maxScroll));
      return { ratio, pct: Math.round(ratio * 100) };
    }

    function saveNow(manualBookmark) {
      if (!isTrackable) return;
      const { pct } = getScrollMetrics();
      const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const curH = getActiveHeadingFromCache();
      allProg[PAGE_ID] = {
        pageId: PAGE_ID,
        title: PAGE_TITLE,
        pct: pct,
        scrollY: Math.round(window.scrollY || 0),
        headingId: curH.id,
        headingText: curH.text,
        bookmarked: Boolean(manualBookmark || (allProg[PAGE_ID] && allProg[PAGE_ID].bookmarked)),
        ts: Date.now()
      };
      safeSetJSON(localStorage, STORAGE_KEYS.progress, allProg);
      updateHistoryDot();
      if (liveStatus) {
        liveStatus.textContent = `进度 ${pct}% · 已保存`;
      }
    }

    if (bookmarkBtn) {
      bookmarkBtn.addEventListener("click", () => {
        saveNow(true);
        const orig = bookmarkBtn.innerHTML;
        bookmarkBtn.innerHTML = `${ICONS.check}<span>已保存</span>`;
        bookmarkBtn.classList.add("active");
        setTimeout(() => {
          bookmarkBtn.innerHTML = orig;
          bookmarkBtn.classList.remove("active");
        }, 1600);
      });
    }

    let saveTimer = null;
    let rafPending = false;

    function applyFrame() {
      rafPending = false;
      const { ratio, pct } = getScrollMetrics();
      if (topBar) topBar.style.transform = `scaleX(${ratio.toFixed(4)})`;
      if (tocPct) tocPct.textContent = pct + "%";
      if (liveStatus) liveStatus.textContent = `进度 ${pct}%`;
      if (ringCircle) {
        const circumference = 114;
        ringCircle.style.strokeDashoffset = String(circumference - circumference * ratio);
      }

      if (isTrackable) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => saveNow(false), 260);
      }
    }

    window.addEventListener(
      "scroll",
      () => {
        if (!rafPending) {
          rafPending = true;
          requestAnimationFrame(applyFrame);
        }
      },
      { passive: true }
    );
    applyFrame();

    if (isTrackable && !location.hash) {
      const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const saved = allProg[PAGE_ID];
      const toast = document.getElementById("resume-toast");
      if (saved && saved.scrollY > 320 && saved.pct >= 2 && saved.pct <= 98 && toast) {
        const txtEl = document.getElementById("resume-toast-text");
        const goBtn = document.getElementById("resume-toast-btn");
        const closeBtn = document.getElementById("resume-toast-close");
        const secLabel = saved.headingText ? `「${saved.headingText}」` : "";
        if (txtEl) {
          txtEl.textContent = `上次浏览至 ${secLabel}（${saved.pct}%）`;
        }
        toast.classList.add("show");
        if (goBtn) {
          goBtn.addEventListener("click", () => {
            toast.classList.remove("show");
            window.scrollTo({ top: saved.scrollY, behavior: "smooth" });
            if (saved.headingId) {
              const hEl = document.getElementById(saved.headingId);
              if (hEl) {
                hEl.classList.add("flash-highlight");
                setTimeout(() => hEl.classList.remove("flash-highlight"), 2000);
              }
            }
          });
        }
        if (closeBtn) {
          closeBtn.addEventListener("click", () => {
            toast.classList.remove("show");
          });
        }
      }
    }
  }

  /* --------------------------------------------------------------------------
     5. Home Bento Live Progress Integration & History Modal
     -------------------------------------------------------------------------- */
  function renderHomeResumeHub() {
    const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
    const footprints = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);

    // Hydrate embedded reading progress boxes inside the two Standard Bento cards
    ["rules.html", "materials.html"].forEach((docKey) => {
      const mount = document.querySelector(`[data-bento-progress="${docKey}"]`);
      if (!mount) return;
      const p = allProg[docKey];
      const pct = p ? p.pct : 0;
      const labelEl = mount.querySelector("[data-prog-label]");
      const pctEl = mount.querySelector("[data-prog-pct]");
      const fillEl = mount.querySelector("[data-prog-fill]");
      if (pctEl) pctEl.textContent = pct + "%";
      if (fillEl) fillEl.style.width = pct + "%";
      if (labelEl) {
        labelEl.textContent =
          p && p.scrollY > 120
            ? `断点续读：${p.headingText || "上次位置"} · ${timeAgo(p.ts)}`
            : "点击阅读完整无删减原文";
      }
      const parentCard = mount.closest("a.bento-card");
      if (parentCard && p && p.scrollY > 120) {
        parentCard.addEventListener("click", (e) => {
          e.preventDefault();
          const targetUrl = new URL(resolveUrl(docKey), location.href).href.split("#")[0];
          safeSetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, {
            url: targetUrl,
            scrollY: p.scrollY
          });
          location.href = targetUrl;
        });
      }
    });

    const fpMount = document.getElementById("home-footprints-mount");
    if (!fpMount) return;
    if (footprints.length === 0) {
      fpMount.innerHTML = "";
      return;
    }

    const pills = footprints
      .slice(0, 8)
      .map(
        (f) =>
          `<a class="footprint-pill" href="${resolveUrl(f.pageId)}"><span>${escapeHTML(f.title)}</span><span class="mono" style="opacity:0.55;font-size:10.5px">${timeAgo(f.ts)}</span></a>`
      )
      .join("");

    fpMount.innerHTML = `
      <div class="footprints-strip">
        <span style="font-size:12px;color:var(--text-muted);white-space:nowrap;flex-shrink:0">最近足迹</span>
        ${pills}
        <button type="button" class="chip-btn" id="home-clear-history" style="margin-left:auto">清空记录</button>
      </div>`;

    const clearBtn = document.getElementById("home-clear-history");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        localStorage.removeItem(STORAGE_KEYS.progress);
        localStorage.removeItem(STORAGE_KEYS.footprints);
        renderHomeResumeHub();
      });
    }
  }

  function initHistoryModal() {
    const openBtn = document.getElementById("history-open-btn");
    const backdrop = document.getElementById("history-modal");
    const closeBtn = document.getElementById("history-close-btn");
    const body = document.getElementById("history-modal-body");
    const clearAllBtn = document.getElementById("history-clear-btn");
    if (!openBtn || !backdrop || !body) return;

    function closeModal() {
      backdrop.classList.remove("open");
      syncScrollLock();
    }

    function renderModalContent() {
      const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const footprints = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);
      const progList = Object.values(allProg).sort((a, b) => (b.ts || 0) - (a.ts || 0));

      let html = `<div style="margin-bottom:18px"><div style="font-size:12px;font-weight:600;letter-spacing:0.04em;margin-bottom:8px;color:var(--accent-gold)">已保存的浏览与阅读进度</div>`;
      if (progList.length === 0) {
        html += `<div style="color:var(--text-muted);font-size:13px;padding:10px 4px">暂无已保存进度。阅读标准全文或浏览量级/角色列表时会自动记录滚动位置。</div>`;
      } else {
        html += progList
          .map(
            (p) => `
          <a class="search-hit js-resume-jump" href="${resolveUrl(p.pageId)}" data-jump-page="${p.pageId}" data-jump-y="${p.scrollY || 0}">
            <div class="search-hit-top">
              <span class="search-hit-title">${escapeHTML(p.title)}</span>
              <span class="search-hit-type mono">${p.pct}% · ${timeAgo(p.ts)}</span>
            </div>
            <div class="search-hit-snippet">上次位置：${escapeHTML(p.headingText || "页面顶部")}</div>
          </a>`
          )
          .join("");
      }
      html += `</div><div><div style="font-size:12px;font-weight:600;letter-spacing:0.04em;margin-bottom:8px;color:var(--text-secondary)">最近访问足迹</div>`;
      if (footprints.length === 0) {
        html += `<div style="color:var(--text-muted);font-size:13px;padding:8px 4px">暂无最近访问记录。</div>`;
      } else {
        html += footprints
          .map(
            (f) => `
          <a class="search-hit" href="${resolveUrl(f.pageId)}">
            <div class="search-hit-top">
              <span class="search-hit-title">${escapeHTML(f.title)}</span>
              <span class="search-hit-type">${timeAgo(f.ts)}</span>
            </div>
          </a>`
          )
          .join("");
      }
      html += `</div>`;
      body.innerHTML = html;

      body.querySelectorAll(".js-resume-jump").forEach((el) => {
        el.addEventListener("click", (e) => {
          const page = el.getAttribute("data-jump-page");
          const y = Number(el.getAttribute("data-jump-y") || 0);
          if (page === PAGE_ID) {
            e.preventDefault();
            closeModal();
            window.scrollTo({ top: y, behavior: "smooth" });
          } else if (y > 80) {
            e.preventDefault();
            const targetUrl = new URL(resolveUrl(page), location.href).href.split("#")[0];
            safeSetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, { url: targetUrl, scrollY: y });
            location.href = targetUrl;
          }
        });
      });
    }

    openBtn.addEventListener("click", () => {
      renderModalContent();
      backdrop.classList.add("open");
      syncScrollLock();
    });

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal();
    });
    if (clearAllBtn) {
      clearAllBtn.addEventListener("click", () => {
        localStorage.removeItem(STORAGE_KEYS.progress);
        localStorage.removeItem(STORAGE_KEYS.footprints);
        openBtn.classList.remove("has-progress");
        renderModalContent();
        renderHomeResumeHub();
      });
    }
  }

  /* --------------------------------------------------------------------------
     6. Document Reader (120fps rAF ScrollSpy + Auto-Sync TOC + In-Doc Finder)
     -------------------------------------------------------------------------- */
  function initDocumentReader() {
    const sidebar = document.getElementById("doc-sidebar");
    const tocNav = document.getElementById("toc-nav");
    const tocFilter = document.getElementById("toc-filter-input");
    const dockTocBtn = document.getElementById("dock-toc-btn");
    const mdBody = document.querySelector(".markdown-body");

    const prefs = safeGetJSON(localStorage, STORAGE_KEYS.readerPrefs, { fontSize: 15.5, wide: false });
    if (mdBody && prefs.fontSize) {
      mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
    }
    if (prefs.wide) {
      document.body.classList.add("wide-doc-mode");
    }

    const fontDecBtn = document.getElementById("doc-font-dec");
    const fontIncBtn = document.getElementById("doc-font-inc");
    const wideBtn = document.getElementById("doc-wide-toggle");
    if (wideBtn) wideBtn.classList.toggle("active", Boolean(prefs.wide));

    let rebuildTocOffsets = () => {};

    if (fontDecBtn && mdBody) {
      fontDecBtn.addEventListener("click", () => {
        prefs.fontSize = Math.max(13.5, Number((prefs.fontSize - 1).toFixed(1)));
        mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildHeadingCache();
        rebuildTocOffsets();
      });
    }
    if (fontIncBtn && mdBody) {
      fontIncBtn.addEventListener("click", () => {
        prefs.fontSize = Math.min(20.5, Number((prefs.fontSize + 1).toFixed(1)));
        mdBody.style.setProperty("--doc-font-size", prefs.fontSize + "px");
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildHeadingCache();
        rebuildTocOffsets();
      });
    }
    if (wideBtn) {
      wideBtn.addEventListener("click", () => {
        prefs.wide = !prefs.wide;
        document.body.classList.toggle("wide-doc-mode", prefs.wide);
        wideBtn.classList.toggle("active", prefs.wide);
        safeSetJSON(localStorage, STORAGE_KEYS.readerPrefs, prefs);
        rebuildHeadingCache();
        rebuildTocOffsets();
      });
    }

    const findInput = document.getElementById("doc-find-input");
    const findNextBtn = document.getElementById("doc-find-next");
    const findCountEl = document.getElementById("doc-find-count");
    let findMatches = [];
    let findIdx = -1;

    function runDocFind(jump) {
      if (!findInput || !mdBody) return;
      const q = findInput.value.trim().toLowerCase();
      if (!q) {
        findMatches = [];
        findIdx = -1;
        if (findCountEl) findCountEl.textContent = "";
        return;
      }
      const blocks = Array.from(mdBody.querySelectorAll("h1, h2, h3, p, li, tr"));
      findMatches = blocks.filter((el) => el.textContent.toLowerCase().includes(q));
      if (findMatches.length === 0) {
        if (findCountEl) findCountEl.textContent = "0 处";
        return;
      }
      if (jump) {
        findIdx = (findIdx + 1) % findMatches.length;
        const target = findMatches[findIdx];
        scrollToElementWithOffset(target, true);
        target.classList.remove("flash-highlight");
        void target.offsetWidth;
        target.classList.add("flash-highlight");
        if (findCountEl) findCountEl.textContent = `${findIdx + 1}/${findMatches.length}`;
      } else {
        findIdx = -1;
        if (findCountEl) findCountEl.textContent = `${findMatches.length} 处`;
      }
    }

    if (findInput) {
      findInput.addEventListener("input", () => runDocFind(false));
      findInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          runDocFind(true);
        }
      });
    }
    if (findNextBtn) {
      findNextBtn.addEventListener("click", () => runDocFind(true));
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
        roTimer = setTimeout(() => {
          rebuildHeadingCache();
          rebuildTocOffsets();
        }, 120);
      });
      ro.observe(mdBody);
    }

    // Smoothly scroll to section with exact sticky offset when clicking TOC
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
      const scrollPos = (window.scrollY || 0) + 125;
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

        // Keep active TOC item comfortably inside visible area of sidebar without jerking page
        if (!pointerInsideToc && activeLink.offsetParent !== null) {
          const navRect = tocNav.getBoundingClientRect();
          const linkRect = activeLink.getBoundingClientRect();
          if (linkRect.top < navRect.top + 36 || linkRect.bottom > navRect.bottom - 36) {
            const delta = linkRect.top - navRect.top - navRect.height * 0.38;
            tocNav.scrollTop += delta;
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
        const nav = document.getElementById("main-nav");
        if (nav) nav.classList.remove("open");
        sidebar.classList.toggle("drawer-open");
        syncScrollLock();
      });
    }
  }

  /* --------------------------------------------------------------------------
     7. Interactive Tiers Explorer (tiers.html) — Strictly 从小到大 (#01 -> #97)
     -------------------------------------------------------------------------- */
  function initTiersExplorer() {
    const mount = document.getElementById("tiers-explorer-mount");
    if (!mount || !window.__POWERWIKI_DATA__ || !window.__POWERWIKI_DATA__.tiers) return;

    const { groups, tiers } = window.__POWERWIKI_DATA__;
    const groupMap = {};
    groups.forEach((g) => (groupMap[g.id] = g));

    const savedPrefs = safeGetJSON(localStorage, STORAGE_KEYS.tierPrefs, {});
    const params = new URLSearchParams(location.search);

    const state = {
      segment: params.get("seg") || savedPrefs.segment || "all",
      view: savedPrefs.view || "card", // card | flat | table
      query: params.get("q") || ""
    };

    const segBtns = document.querySelectorAll("[data-tier-seg]");
    const viewBtns = document.querySelectorAll("[data-tier-view]");
    const filterInput = document.getElementById("tier-filter-input");
    const clearBtn = document.getElementById("tier-filter-clear");
    const countBadge = document.getElementById("tier-result-count");

    if (filterInput && state.query) filterInput.value = state.query;

    function persistPrefs() {
      safeSetJSON(localStorage, STORAGE_KEYS.tierPrefs, {
        segment: state.segment,
        view: state.view
      });
    }

    function matchesTier(t) {
      if (state.segment !== "all") {
        const g = groupMap[t.group_id];
        if (!g || g.filter_group !== state.segment) return false;
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
      return `
        <a class="tier-card" data-domain="${t.domain}" href="${resolveUrl("tier/" + t.slug + ".html")}">
          <div class="tier-card-top">
            <span class="tier-code-badge mono">⊙ ${escapeHTML(t.code)}</span>
            <span class="tier-order-num mono">${orderText}</span>
          </div>
          <div class="tier-card-name">
            <span>${escapeHTML(t.name)}</span>
            <span class="tier-family-tag">${escapeHTML(t.family)}</span>
          </div>
          <div class="tier-energy-line mono">${escapeHTML(t.energy)}</div>
          <div class="tier-scale-line">${escapeHTML(t.scale)}</div>
          <div class="tier-card-foot">
            <span>${escapeHTML(t.model)}</span>
            ${ICONS.arrowUpRight}
          </div>
        </a>`;
    }

    function renderLadderStream(list) {
      const rows = list
        .map((t) => {
          const orderText = t.unranked ? "—" : `#${String(t.order).padStart(2, "0")}`;
          return `
          <a class="ladder-row" data-domain="${t.domain}" href="${resolveUrl("tier/" + t.slug + ".html")}">
            <span class="mono" style="font-size:12px;color:var(--text-muted)">${orderText}</span>
            <span class="tier-code-badge mono" style="justify-self:start;--dom-color:var(--dom-${t.domain},var(--accent-gold))">⊙ ${escapeHTML(t.code)}</span>
            <span style="font-weight:650;color:var(--text-primary);font-size:14px">${escapeHTML(t.name)}</span>
            <span class="mono" style="font-size:12.5px;color:var(--accent-gold);overflow-wrap:anywhere">${escapeHTML(t.energy)}</span>
            <span class="ladder-col-scale" style="font-size:12.5px;color:var(--text-secondary)">${escapeHTML(t.scale)}</span>
            <span class="ladder-col-arrow" style="color:var(--text-muted);justify-self:end">${ICONS.arrowUpRight}</span>
          </a>`;
        })
        .join("");

      return `
        <section class="tier-group-block" id="group-flat">
          <div class="tier-group-header">
            <h2 class="tier-group-title">连续标尺序列（#01 昆虫级 → #97 论天最上）</h2>
            <span class="tier-group-sub">严格按量级从小到大排列 · 共 ${list.length} 档</span>
          </div>
          <div class="ladder-stream">${rows}</div>
        </section>`;
    }

    function renderTable(list) {
      const rows = list
        .map((t) => {
          const orderText = t.unranked ? "—" : `#${String(t.order).padStart(2, "0")}`;
          return `
          <tr>
            <td class="mono" style="color:var(--text-muted)">${orderText}</td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" class="tier-code-badge mono" style="--dom-color:var(--dom-${t.domain},var(--accent-gold))">⊙ ${escapeHTML(t.code)}</a></td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" style="font-weight:650;color:var(--text-primary)">${escapeHTML(t.name)}</a></td>
            <td class="mono" style="color:var(--accent-gold)">${escapeHTML(t.energy)}</td>
            <td style="color:var(--text-secondary)">${escapeHTML(t.scale)}</td>
            <td style="color:var(--text-muted)">${escapeHTML(t.model)}</td>
          </tr>`;
        })
        .join("");
      return `
        <div class="compact-table-wrap">
          <table class="compact-table">
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
            <div class="empty-icon">${ICONS.search}</div>
            <h3 style="margin:0 0 8px;font-size:17px">未找到匹配的量级档位</h3>
            <p style="color:var(--text-muted);margin:0 0 18px;font-size:13.5px">请尝试更换搜索词或切换上方区间筛选条件。</p>
            <button type="button" class="btn btn-surface" id="reset-tier-filters">重置筛选条件</button>
          </div>`;
        const resetBtn = document.getElementById("reset-tier-filters");
        if (resetBtn) {
          resetBtn.addEventListener("click", () => {
            state.segment = "all";
            state.query = "";
            if (filterInput) filterInput.value = "";
            render();
          });
        }
        rebuildHeadingCache();
        return;
      }

      const ranked = filtered.filter((t) => !t.unranked).sort((a, b) => a.order - b.order);
      const unranked = filtered.filter((t) => t.unranked);
      const allOrdered = ranked.concat(unranked);

      if (state.view === "table") {
        mount.innerHTML = renderTable(allOrdered);
        rebuildHeadingCache();
        return;
      }

      if (state.view === "flat") {
        mount.innerHTML = renderLadderStream(allOrdered);
        rebuildHeadingCache();
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
            <section class="tier-group-block" id="group-${gid}">
              <div class="tier-group-header">
                <h2 class="tier-group-title">${escapeHTML(g ? g.title : gid)}</h2>
                <span class="tier-group-sub">${escapeHTML(g ? g.subtitle : "")} · ${gItems.length} 档</span>
              </div>
              <div class="tier-grid">${gItems.map(renderCard).join("")}</div>
            </section>`;
        })
        .join("");

      rebuildHeadingCache();
    }

    segBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.segment = btn.dataset.tierSeg;
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
        render();
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        state.query = "";
        if (filterInput) filterInput.value = "";
        render();
      });
    }

    render();
  }

  /* --------------------------------------------------------------------------
     8. Interactive Characters Explorer (characters.html) — 首字母 & 从小到大
     -------------------------------------------------------------------------- */
  function initCharactersExplorer() {
    const mount = document.getElementById("chars-explorer-mount");
    if (!mount || !window.__POWERWIKI_DATA__) return;

    const { tiers, characters, demoArchetypes } = window.__POWERWIKI_DATA__;
    const tierBySlug = {};
    tiers.forEach((t) => (tierBySlug[t.slug] = t));

    const savedPrefs = safeGetJSON(localStorage, STORAGE_KEYS.charPrefs, {});
    const params = new URLSearchParams(location.search);

    const defaultShowDemo =
      characters.length === 0
        ? savedPrefs.showDemo !== undefined
          ? Boolean(savedPrefs.showDemo)
          : true
        : false;

    const initSort = params.get("sort") || savedPrefs.sort || "asc";
    const state = {
      sort: initSort === "alpha" ? "alpha" : "asc",
      series: "all",
      domain: "all",
      query: params.get("q") || "",
      showDemo: defaultShowDemo
    };

    const sortBtns = document.querySelectorAll("[data-char-sort]");
    const domainBtns = document.querySelectorAll("[data-char-domain]");
    const seriesSelect = document.getElementById("char-series-select");
    const filterInput = document.getElementById("char-filter-input");
    const demoToggleBtn = document.getElementById("char-demo-toggle");
    const alphaBar = document.getElementById("char-alpha-bar");
    const alphaLettersEl = document.getElementById("char-alpha-letters");
    const countBadge = document.getElementById("char-result-count");
    const demoBannerSlot = document.getElementById("char-demo-banner-slot");

    if (filterInput && state.query) filterInput.value = state.query;

    function getActivePool() {
      const src = state.showDemo && characters.length === 0 ? demoArchetypes : characters;
      return src.map((c) => {
        const tier = tierBySlug[c.tier_slug] || tierBySlug["pending"];
        return Object.assign({}, c, {
          _tier: tier,
          _order: tier ? tier.order : 999,
          _domain: tier ? tier.domain : "unranked",
          _isDemo: state.showDemo && characters.length === 0
        });
      });
    }

    function populateSeriesDropdown(pool) {
      if (!seriesSelect) return;
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
      const modHtml = (c.modifiers || [])
        .map((m) => `<span class="mod-chip">${escapeHTML(m)}</span>`)
        .join("");
      const dims = c.dims || {};
      const dimOrder = ["破", "控", "御", "速", "域", "算", "性"];
      const dimsHtml = dimOrder
        .map((k) => {
          const val = dims[k] || "〔缺〕";
          const fullRow = k === "域" || k === "性" ? "full-row" : "";
          return `<div class="dim-cell ${fullRow}"><span class="dim-key">${k}</span><span class="dim-val">${formatEvidenceBadges(val)}</span></div>`;
        })
        .join("");

      const cardLinkAttr = c._isDemo
        ? `href="#demo-${c.slug}" data-demo-slug="${c.slug}"`
        : `href="${resolveUrl("character/" + c.slug + ".html")}"`;

      return `
        <a class="char-card" ${cardLinkAttr}>
          <div class="char-card-head">
            <div style="display:flex;align-items:center;gap:12px;min-width:0">
              <div class="char-avatar">${
                c.image_url
                  ? `<img src="${escapeHTML(c.image_url)}" alt="${escapeHTML(c.name)}" loading="lazy">`
                  : escapeHTML(c.name.slice(0, 1))
              }</div>
              <div class="char-title-group">
                <h3 class="char-name">${escapeHTML(c.name)}</h3>
                <div class="char-series">${escapeHTML(c.series || "未知出处")}${
        c.realm ? " · " + escapeHTML(c.realm) : ""
      }</div>
              </div>
            </div>
            <span class="char-rating-pill mono">⊙ ${escapeHTML(t ? t.code : "待定")}</span>
          </div>
          <div class="char-modifiers">
            <span class="mod-chip" style="color:var(--accent-blue)">${escapeHTML(t ? t.name : "待定")} · #${t ? String(t.order).padStart(2, "0") : "—"}</span>
            <span class="mod-chip mono">首字母 ${escapeHTML(c.initial || "#")}</span>
            ${modHtml}
            ${c._isDemo ? '<span class="mod-chip" style="color:var(--accent-gold);border-color:var(--border-gold)">第三版示例</span>' : ""}
          </div>
          <div class="dims-mini-grid">${dimsHtml}</div>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:12.5px;color:var(--text-secondary)">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHTML(c.summary || "")}</span>
            <span style="color:var(--accent-gold);white-space:nowrap;font-weight:500">七维档案 ${ICONS.arrowUpRight}</span>
          </div>
        </a>`;
    }

    function openDemoModal(c) {
      const modal = document.getElementById("demo-char-modal");
      const body = document.getElementById("demo-char-modal-body");
      if (!modal || !body) return;
      const t = c._tier;
      const radarSvg = buildHeptadRadarSVG(c.dims || {}, t ? t.order : 30);
      const dimRows = ["破", "控", "域", "御", "速", "算", "性"]
        .map(
          (k) => `
          <tr>
            <th style="width:88px">维度「${k}」</th>
            <td>${formatEvidenceBadges((c.dims && c.dims[k]) || "〔缺〕")}</td>
          </tr>`
        )
        .join("");

      const fullWritingHtml = c.full_writing
        ? `<blockquote style="margin:0 0 16px;padding:12px 15px;background:var(--bg-subtle);border:1px solid var(--border-hairline);border-left:2.5px solid var(--accent-gold);border-radius:0 9px 9px 0;font-size:13px;color:var(--text-primary);line-height:1.7"><strong>第三版「完整书写」展开：</strong>${formatEvidenceBadges(c.full_writing)}</blockquote>`
        : "";

      body.innerHTML = `
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px">
          <div>
            <div class="detail-code-pill mono" style="margin-bottom:8px">⊙ ${escapeHTML(t.code)} · ${escapeHTML(t.name)}（#${String(t.order).padStart(2, "0")}）</div>
            <h2 style="margin:0;font-size:21px;letter-spacing:-0.015em">${escapeHTML(c.name)}</h2>
            <div style="color:var(--text-muted);font-size:12.5px;margin-top:4px">${escapeHTML(c.alias || "")} ｜ ${escapeHTML(c.series || "")}</div>
          </div>
          <a class="btn btn-surface" href="${resolveUrl("tier/" + t.slug + ".html")}">所属量级（⊙${escapeHTML(t.code)}）${ICONS.arrowUpRight}</a>
        </div>
        ${fullWritingHtml}
        <div class="heptad-modal-grid">
          <div class="heptad-radar-box">
            ${radarSvg}
            <span style="font-size:11px;color:var(--text-muted)">衡天⊙ 七维浑仪示意</span>
          </div>
          <div>
            <p style="color:var(--text-secondary);margin:0 0 12px;line-height:1.7;font-size:13.8px">${escapeHTML(c.summary || "")}</p>
            <div style="font-size:12.5px;color:var(--accent-gold);margin-bottom:10px">可信度依据：${formatEvidenceBadges(c.credibility || "—")}</div>
            <div class="char-modifiers">
              <span class="mod-chip mono">拼音首字母：${escapeHTML(c.initial)} (${escapeHTML(c.pinyin)})</span>
              ${(c.modifiers || []).map((m) => `<span class="mod-chip">${escapeHTML(m)}</span>`).join("")}
            </div>
          </div>
        </div>
        <div class="compact-table-wrap">
          <table class="compact-table" style="min-width:0"><tbody>${dimRows}</tbody></table>
        </div>
      `;
      modal.classList.add("open");
      syncScrollLock();
    }

    function render() {
      sortBtns.forEach((b) => b.classList.toggle("active", b.dataset.charSort === state.sort));
      domainBtns.forEach((b) => b.classList.toggle("active", b.dataset.charDomain === state.domain));
      if (demoToggleBtn) {
        demoToggleBtn.style.display = characters.length === 0 ? "inline-flex" : "none";
        demoToggleBtn.classList.toggle("active", state.showDemo);
        demoToggleBtn.textContent = state.showDemo ? "隐藏示例卡" : "显示 6 组第三版示例卡";
      }

      if (demoBannerSlot) {
        if (characters.length === 0 && state.showDemo) {
          demoBannerSlot.innerHTML = `
            <div class="notice-banner">
              <strong>第三版标准示例模式：</strong>正式角色库当前待录入（0 条）。下方展示 6 组《衡天⊙ 第三版》完整书写与七维评定演示卡，可直接在上方切换<strong>「按量级从小到大」</strong>与<strong>「按首字母 A–Z 排序」</strong>。
            </div>`;
        } else {
          demoBannerSlot.innerHTML = "";
        }
      }

      const pool = getActivePool();
      populateSeriesDropdown(pool);

      if (pool.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        if (countBadge) countBadge.textContent = "正式收录 0 位";
        mount.innerHTML = `
          <div class="empty-state-box">
            <div class="empty-icon mono">⊙</div>
            <h3 style="margin:0 0 10px;font-size:18px">正式角色档案库 · 待录入</h3>
            <p style="color:var(--text-secondary);margin:0 auto 20px;max-width:520px;line-height:1.75;font-size:13.8px">
              本站已采用<strong>《衡天⊙ 多维战力量级体系（第三版）》</strong>，旧版单维角色数据已清空。
              在 <code>data/characters.json</code> 录入角色数据并运行 <code>python3 build_site.py</code> 即可生成正式档案。
            </p>
            <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap">
              <button type="button" class="btn btn-primary" id="empty-open-demo">开启 6 组第三版示例角色卡</button>
              <a class="btn btn-surface" href="${resolveUrl("rules.html")}">查阅《衡天⊙ 第三版》全文</a>
            </div>
          </div>`;
        const btn = document.getElementById("empty-open-demo");
        if (btn) {
          btn.addEventListener("click", () => {
            state.showDemo = true;
            safeSetJSON(localStorage, STORAGE_KEYS.charPrefs, {
              sort: state.sort,
              showDemo: true
            });
            render();
          });
        }
        rebuildHeadingCache();
        return;
      }

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
        countBadge.textContent = state.showDemo
          ? `示例 ${filtered.length} / ${pool.length}`
          : `收录 ${filtered.length} / ${pool.length}`;
      }

      if (filtered.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        mount.innerHTML = `
          <div class="empty-state-box">
            <div class="empty-icon">${ICONS.search}</div>
            <h3 style="margin:0 0 8px;font-size:17px">没有符合筛选条件的角色</h3>
            <p style="color:var(--text-muted);margin:0;font-size:13.5px">请调整搜索关键词、作品或量级区间。</p>
          </div>`;
        rebuildHeadingCache();
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
                has ? `data-char-letter="${L}" title="跳转至首字母 ${L}"` : "disabled"
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
            const list = buckets[L].slice().sort((a, b) =>
              String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name))
            );
            return `
              <section class="tier-group-block" id="char-letter-${L}">
                <div class="tier-group-header">
                  <h2 class="tier-group-title"><span class="letter-badge mono">${L}</span> 首字母 ${L}</h2>
                  <span class="tier-group-sub">${list.length} 位角色</span>
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
          <section class="tier-group-block" id="char-scale-list">
            <div class="tier-group-header">
              <h2 class="tier-group-title">按主档量级从小到大排列（低量级 → 高量级）</h2>
              <span class="tier-group-sub">${sorted.length} 位角色</span>
            </div>
            <div class="char-grid">${sorted.map(renderCharCard).join("")}</div>
          </section>`;
      }

      mount.querySelectorAll("[data-demo-slug]").forEach((card) => {
        card.addEventListener("click", (e) => {
          e.preventDefault();
          const slug = card.getAttribute("data-demo-slug");
          const found = pool.find((x) => x.slug === slug);
          if (found) openDemoModal(found);
        });
      });

      if (location.hash && location.hash.startsWith("#demo-")) {
        const targetSlug = location.hash.slice(6);
        const found = pool.find((x) => x.slug === targetSlug);
        if (found) openDemoModal(found);
      }

      rebuildHeadingCache();
    }

    sortBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.sort = btn.dataset.charSort;
        safeSetJSON(localStorage, STORAGE_KEYS.charPrefs, {
          sort: state.sort,
          showDemo: state.showDemo
        });
        render();
      });
    });

    domainBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.domain = btn.dataset.charDomain;
        render();
      });
    });

    if (seriesSelect) {
      seriesSelect.addEventListener("change", () => {
        state.series = seriesSelect.value;
        render();
      });
    }

    if (filterInput) {
      filterInput.addEventListener("input", () => {
        state.query = filterInput.value.trim();
        render();
      });
    }

    if (demoToggleBtn) {
      demoToggleBtn.addEventListener("click", () => {
        state.showDemo = !state.showDemo;
        safeSetJSON(localStorage, STORAGE_KEYS.charPrefs, {
          sort: state.sort,
          showDemo: state.showDemo
        });
        render();
      });
    }

    const demoModal = document.getElementById("demo-char-modal");
    const demoClose = document.getElementById("demo-char-close");
    if (demoModal && demoClose) {
      const closeDemo = () => {
        demoModal.classList.remove("open");
        syncScrollLock();
      };
      demoClose.addEventListener("click", closeDemo);
      demoModal.addEventListener("click", (e) => {
        if (e.target === demoModal) closeDemo();
      });
    }

    render();
  }

  /* --------------------------------------------------------------------------
     9. Global Search Command Palette (Ctrl+K / Hero Bar) & Dedicated Search
     -------------------------------------------------------------------------- */
  function runSearchQuery(rawQuery, typeFilter) {
    const index = window.__POWERWIKI_INDEX__ || [];
    const q = (rawQuery || "").trim().toLowerCase();
    const tokens = q ? q.split(/\s+/).filter(Boolean) : [];

    const results = [];
    for (const item of index) {
      if (typeFilter && typeFilter !== "all" && item.type !== typeFilter) continue;
      if (tokens.length === 0) {
        results.push({ item, score: item.type === "tier" ? 50 : item.type === "char" ? 45 : 30 });
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
    char: "角色分类",
    rules: "衡天第三版",
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
        body.innerHTML = `<div style="padding:32px 16px;text-align:center;color:var(--text-muted);font-size:13px">未找到与「${escapeHTML(q)}」相关的条目，可尝试搜索「宇◆」「归因」「完整书写」「白矮星」「0#」「花岗岩」。</div>`;
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
        el.addEventListener("click", () => {
          closeModal();
        });
      });
    }

    function openModal() {
      const nav = document.getElementById("main-nav");
      if (nav) nav.classList.remove("open");
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
        mount.innerHTML = `<div class="empty-state-box"><div class="empty-icon">${ICONS.search}</div><h3 style="font-size:17px">没有找到匹配内容</h3><p style="color:var(--text-muted);font-size:13.5px">试试搜索代字（如 恒○、宇◆、外·门）、第三版新规则（如 归因与知情度审查、完整书写、超长篇）或材质名称（如 中子星、花岗岩）。</p></div>`;
        return;
      }

      mount.innerHTML = hits
        .map(
          (h) => `
          <a class="search-hit" style="background:var(--bg-surface-1);border-color:var(--border-hairline);padding:14px 18px;margin-bottom:8px" href="${resolveUrl(h.url)}">
            <div class="search-hit-top">
              <span class="search-hit-title" style="font-size:15px">${highlightSnippet(h.title, q)}</span>
              <span class="search-hit-type">${escapeHTML(h.badge || TYPE_LABELS[h.type] || h.type)}</span>
            </div>
            <div class="search-hit-snippet" style="font-size:13.2px">${highlightSnippet(h.text, q)}</div>
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

  /* Horizontal Wheel Helper for Single-Row Pill Rails */
  function initHorizontalRails() {
    document
      .querySelectorAll(".filter-Chips, .alpha-letters, .footprints-strip")
      .forEach((rail) => {
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

  /* --------------------------------------------------------------------------
     Boot
     -------------------------------------------------------------------------- */
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initMobileNav();
    recordFootprint();
    initSmartNavigation();
    initReadingProgress();
    renderHomeResumeHub();
    initHistoryModal();
    initDocumentReader();
    initTiersExplorer();
    initCharactersExplorer();
    initGlobalSearchModal();
    initDedicatedSearchPage();
    initHorizontalRails();
  });
})();
