/* ==========================================================================
   衡天⊙ PowerWiki — Client Interactive Engine (Zero External Dependencies)
   Supports: raw.githack.com, GitHub Pages, Live Preview, and offline file://
   ========================================================================== */
(function () {
  "use strict";

  const STORAGE_KEYS = {
    theme: "pw_theme_v2",
    progress: "pw_progress_v2",
    footprints: "pw_footprints_v2",
    navStack: "pw_nav_stack_v2",
    restoreScroll: "pw_restore_scroll_v2",
    tierPrefs: "pw_tier_prefs_v2",
    charPrefs: "pw_char_prefs_v2"
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
     1. Theme Management
     -------------------------------------------------------------------------- */
  function initTheme() {
    const btn = document.getElementById("theme-toggle-btn");
    const updateIcon = () => {
      if (!btn) return;
      const cur = document.documentElement.getAttribute("data-theme") || "dark";
      btn.innerHTML = cur === "dark" ? "☀️" : "🌙";
      btn.setAttribute("title", cur === "dark" ? "切换至浅色星历模式" : "切换至深空观测模式");
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
     2. Mobile Navigation Menu
     -------------------------------------------------------------------------- */
  function initMobileNav() {
    const btn = document.getElementById("mobile-menu-btn");
    const nav = document.getElementById("main-nav");
    if (!btn || !nav) return;
    btn.addEventListener("click", () => {
      nav.classList.toggle("open");
    });
    document.addEventListener("click", (e) => {
      if (!nav.contains(e.target) && !btn.contains(e.target)) {
        nav.classList.remove("open");
      }
    });
  }

  /* --------------------------------------------------------------------------
     3. Smart Back Button & Internal Navigation Stack
     -------------------------------------------------------------------------- */
  function initSmartNavigation() {
    let stack = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
    const currentUrl = location.href.split("#")[0];

    // Restore scroll if navigated back via Smart Back
    const restoreTarget = safeGetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, null);
    if (restoreTarget && restoreTarget.url === currentUrl) {
      sessionStorage.removeItem(STORAGE_KEYS.restoreScroll);
      requestAnimationFrame(() => {
        setTimeout(() => {
          window.scrollTo({ top: restoreTarget.scrollY || 0, behavior: "instant" });
        }, 40);
      });
    }

    // Push or update current page in stack
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

    // Keep current entry's scrollY updated
    let scrollTimer = null;
    window.addEventListener(
      "scroll",
      () => {
        if (scrollTimer) return;
        scrollTimer = setTimeout(() => {
          scrollTimer = null;
          const st = safeGetJSON(sessionStorage, STORAGE_KEYS.navStack, []);
          if (st.length > 0 && st[st.length - 1].url === currentUrl) {
            st[st.length - 1].scrollY = window.scrollY || 0;
            safeSetJSON(sessionStorage, STORAGE_KEYS.navStack, st);
          }
        }, 180);
      },
      { passive: true }
    );

    // Bind all Smart Back buttons
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
          curStack.pop(); // remove current
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
     4. Reading Progress Saving, Resume Toast & Recent Footprints
     -------------------------------------------------------------------------- */
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
    if (list.length > 16) list = list.slice(0, 16);
    safeSetJSON(localStorage, STORAGE_KEYS.footprints, list);
  }

  function initReadingProgress() {
    const topBar = document.getElementById("reading-progress-bar");
    const ringCircle = document.getElementById("dock-progress-circle");
    const tocPct = document.getElementById("toc-progress-pct");
    const backTopBtn = document.getElementById("dock-top-btn");
    const historyBtn = document.getElementById("history-open-btn");

    const isTrackableDoc =
      PAGE_TYPE === "doc" || PAGE_TYPE === "tier-detail" || PAGE_TYPE === "char-detail";

    // Mark header history button dot if any saved progress exists
    const updateHistoryDot = () => {
      if (!historyBtn) return;
      const prog = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const fp = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);
      if (Object.keys(prog).length > 0 || fp.length > 0) {
        historyBtn.classList.add("has-progress");
      } else {
        historyBtn.classList.remove("has-progress");
      }
    };
    updateHistoryDot();

    if (backTopBtn) {
      backTopBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    const headings = Array.from(
      document.querySelectorAll(".markdown-body h1[id], .markdown-body h2[id], .markdown-body h3[id]")
    );

    function getCurrentHeading() {
      const threshold = window.scrollY + 135;
      let active = headings[0] || null;
      for (const h of headings) {
        if (h.offsetTop <= threshold) {
          active = h;
        } else {
          break;
        }
      }
      return active;
    }

    function calcScrollPct() {
      const docEl = document.documentElement;
      const maxScroll = Math.max(1, docEl.scrollHeight - window.innerHeight);
      if (docEl.scrollHeight <= window.innerHeight + 40) return 100;
      return Math.min(100, Math.max(0, Math.round((window.scrollY / maxScroll) * 100)));
    }

    let saveTimer = null;
    function updateVisualProgress() {
      const pct = calcScrollPct();
      if (topBar) topBar.style.width = pct + "%";
      if (tocPct) tocPct.textContent = pct + "%";
      if (ringCircle) {
        const circumference = 126;
        ringCircle.style.strokeDashoffset = String(circumference - (circumference * pct) / 100);
      }

      if (isTrackableDoc) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
          const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
          const activeH = getCurrentHeading();
          const hText = activeH
            ? activeH.textContent.replace(/#$/, "").trim()
            : PAGE_TITLE;
          allProg[PAGE_ID] = {
            pageId: PAGE_ID,
            title: PAGE_TITLE,
            pct: pct,
            scrollY: Math.round(window.scrollY),
            headingId: activeH ? activeH.id : "",
            headingText: hText,
            ts: Date.now()
          };
          safeSetJSON(localStorage, STORAGE_KEYS.progress, allProg);
          updateHistoryDot();
        }, 220);
      }
    }

    window.addEventListener("scroll", updateVisualProgress, { passive: true });
    updateVisualProgress();

    // Show Resume Reading Toast if user returns to a doc page with saved progress
    if (isTrackableDoc && !location.hash) {
      const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const saved = allProg[PAGE_ID];
      const toast = document.getElementById("resume-toast");
      if (saved && saved.scrollY > 260 && saved.pct >= 2 && saved.pct <= 97 && toast) {
        const txtEl = document.getElementById("resume-toast-text");
        const goBtn = document.getElementById("resume-toast-btn");
        const closeBtn = document.getElementById("resume-toast-close");
        const secLabel = saved.headingText ? `「${saved.headingText}」` : "";
        if (txtEl) {
          txtEl.textContent = `上次读到 ${secLabel}（${saved.pct}%）`;
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
                setTimeout(() => hEl.classList.remove("flash-highlight"), 2200);
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
     5. Home Page Resume Hub & Global History Modal
     -------------------------------------------------------------------------- */
  function renderHomeResumeHub() {
    const hub = document.getElementById("home-resume-hub");
    if (!hub) return;

    const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
    const footprints = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);

    const docEntries = [
      {
        key: "rules.html",
        defaultTitle: "《衡天⊙ 多维战力量级体系（第二版）》",
        subtitle: "全文 11 部分 + 附则 · 核心判定与量级标准"
      },
      {
        key: "materials.html",
        defaultTitle: "《材质与破坏能量数据库（第二版）》",
        subtitle: "全文 8 部分 + 来源考据 · 强度/相变/引力束缚能"
      }
    ];

    const cardsHtml = docEntries
      .map((doc) => {
        const p = allProg[doc.key];
        const pct = p ? p.pct : 0;
        const statusText = p
          ? `上次读到：${escapeHTML(p.headingText || "开头")} · ${timeAgo(p.ts)}`
          : "尚未开始阅读 · 点击浏览全文";
        const actionLabel = p && p.scrollY > 120 ? "继续阅读 →" : "开始阅读 →";
        const href = resolveUrl(doc.key) + (p && p.headingId ? "#" + p.headingId : "");
        return `
        <a class="resume-card" href="${href}" data-resume-key="${doc.key}" data-resume-y="${p ? p.scrollY : 0}">
          <div class="resume-card-top">
            <div class="resume-doc-title">${doc.defaultTitle}</div>
            <span class="resume-pct-badge mono">${pct}%</span>
          </div>
          <div class="resume-bar-wrap">
            <div class="resume-bar-fill" style="width:${pct}%"></div>
          </div>
          <div class="resume-meta">
            <span>${statusText}</span>
            <strong style="color:var(--accent-gold)">${actionLabel}</strong>
          </div>
        </a>`;
      })
      .join("");

    let fpHtml = "";
    if (footprints.length > 0) {
      const pills = footprints
        .slice(0, 8)
        .map(
          (f) =>
            `<a class="footprint-pill" href="${resolveUrl(f.pageId)}"><span>${escapeHTML(f.title)}</span><span style="opacity:0.6;font-size:11px">${timeAgo(f.ts)}</span></a>`
        )
        .join("");
      fpHtml = `
        <div class="recent-footprints">
          <span class="footprint-label">最近浏览足迹：</span>
          ${pills}
          <button type="button" class="chip-btn" id="home-clear-history" style="margin-left:auto;font-size:11.5px;padding:3px 10px">清空记录</button>
        </div>`;
    }

    hub.innerHTML = `
      <div class="section-head" style="margin-bottom:14px">
        <h2 class="section-title"><span class="dot"></span>阅读进度与浏览足迹</h2>
        <span class="section-sub">自动保存在本地浏览器，随时断点续读</span>
      </div>
      <div class="resume-grid">${cardsHtml}</div>
      ${fpHtml}
    `;

    hub.querySelectorAll("[data-resume-y]").forEach((link) => {
      link.addEventListener("click", (e) => {
        const y = Number(link.getAttribute("data-resume-y") || 0);
        const key = link.getAttribute("data-resume-key");
        if (y > 120 && key) {
          e.preventDefault();
          const targetUrl = new URL(resolveUrl(key), location.href).href.split("#")[0];
          safeSetJSON(sessionStorage, STORAGE_KEYS.restoreScroll, { url: targetUrl, scrollY: y });
          location.href = targetUrl;
        }
      });
    });

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

    function renderModalContent() {
      const allProg = safeGetJSON(localStorage, STORAGE_KEYS.progress, {});
      const footprints = safeGetJSON(localStorage, STORAGE_KEYS.footprints, []);
      const progList = Object.values(allProg).sort((a, b) => (b.ts || 0) - (a.ts || 0));

      let html = `<div style="margin-bottom:18px"><div style="font-weight:700;margin-bottom:10px;color:var(--accent-gold)">📖 文档阅读进度</div>`;
      if (progList.length === 0) {
        html += `<div style="color:var(--text-muted);font-size:13.5px;padding:10px 0">暂无已保存的文档阅读进度。打开《衡天体系标准》或《材质数据库》滚动阅读即可自动记录。</div>`;
      } else {
        html += progList
          .map(
            (p) => `
          <a class="search-hit js-resume-jump" href="${resolveUrl(p.pageId)}" data-jump-page="${p.pageId}" data-jump-y="${p.scrollY || 0}">
            <div class="search-hit-top">
              <span class="search-hit-title">${escapeHTML(p.title)}</span>
              <span class="search-hit-type mono">${p.pct}% · ${timeAgo(p.ts)}</span>
            </div>
            <div class="search-hit-snippet">上次位置：${escapeHTML(p.headingText || "文档起始处")}</div>
          </a>`
          )
          .join("");
      }
      html += `</div><div><div style="font-weight:700;margin-bottom:10px;color:var(--accent-blue)">🧭 最近访问页面</div>`;
      if (footprints.length === 0) {
        html += `<div style="color:var(--text-muted);font-size:13.5px;padding:8px 0">暂无最近页面足迹。</div>`;
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
            backdrop.classList.remove("open");
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
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", () => backdrop.classList.remove("open"));
    }
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("open");
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
     6. Document ScrollSpy TOC & Heading Copy Anchor
     -------------------------------------------------------------------------- */
  function initDocumentReader() {
    const sidebar = document.getElementById("doc-sidebar");
    const tocNav = document.getElementById("toc-nav");
    const tocFilter = document.getElementById("toc-filter-input");
    const dockTocBtn = document.getElementById("dock-toc-btn");

    // Copy heading link buttons
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
        anchor.textContent = "✓ 已复制";
        anchor.style.opacity = "1";
        setTimeout(() => {
          anchor.textContent = orig;
          anchor.style.opacity = "";
        }, 1400);
      });
    });

    if (!sidebar || !tocNav) return;

    const tocLinks = Array.from(tocNav.querySelectorAll(".toc-item"));
    const headingMap = tocLinks
      .map((link) => {
        const id = link.getAttribute("href").replace(/^#/, "");
        const el = document.getElementById(id);
        return el ? { link, el, id } : null;
      })
      .filter(Boolean);

    function onScrollSpy() {
      const scrollPos = window.scrollY + 135;
      let current = headingMap[0] || null;
      for (const item of headingMap) {
        if (item.el.offsetTop <= scrollPos) {
          current = item;
        } else {
          break;
        }
      }
      tocLinks.forEach((l) => l.classList.remove("active"));
      if (current) {
        current.link.classList.add("active");
      }
    }

    window.addEventListener("scroll", onScrollSpy, { passive: true });
    onScrollSpy();

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
        sidebar.classList.toggle("drawer-open");
      });
      tocLinks.forEach((link) => {
        link.addEventListener("click", () => {
          sidebar.classList.remove("drawer-open");
        });
      });
    }
  }

  /* --------------------------------------------------------------------------
     7. Interactive Tiers Explorer (tiers.html)
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
      sort: params.get("sort") || savedPrefs.sort || "asc", // asc | desc | alpha
      alphaKey: savedPrefs.alphaKey || "code", // code | full
      segment: params.get("seg") || savedPrefs.segment || "all",
      view: savedPrefs.view || "card", // card | table
      query: params.get("q") || ""
    };

    const sortBtns = document.querySelectorAll("[data-tier-sort]");
    const segBtns = document.querySelectorAll("[data-tier-seg]");
    const viewBtns = document.querySelectorAll("[data-tier-view]");
    const alphaKeyBtns = document.querySelectorAll("[data-alpha-key]");
    const filterInput = document.getElementById("tier-filter-input");
    const clearBtn = document.getElementById("tier-filter-clear");
    const alphaBar = document.getElementById("tier-alpha-bar");
    const alphaLettersEl = document.getElementById("tier-alpha-letters");
    const countBadge = document.getElementById("tier-result-count");

    if (filterInput && state.query) filterInput.value = state.query;

    function persistPrefs() {
      safeSetJSON(localStorage, STORAGE_KEYS.tierPrefs, {
        sort: state.sort,
        alphaKey: state.alphaKey,
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
        t.full_pinyin,
        t.code_initial,
        t.full_initial
      ]
        .join(" ")
        .toLowerCase();
      return q.split(/\s+/).every((tok) => hay.includes(tok));
    }

    function renderCard(t) {
      const orderText = t.unranked ? "兜底暂存" : `#${String(t.order).padStart(2, "0")}`;
      return `
        <a class="tier-card" data-domain="${t.domain}" href="${resolveUrl("tier/" + t.slug + ".html")}">
          <div class="tier-card-top">
            <span class="tier-code-badge mono">⊙ ${escapeHTML(t.code)}</span>
            <span class="tier-order-num mono">${orderText} · 首字母 ${state.alphaKey === "code" ? t.code_initial : t.full_initial}</span>
          </div>
          <div class="tier-card-name">
            <span>${escapeHTML(t.name)}</span>
            <span style="font-size:12px;font-weight:500;color:var(--text-muted)">${escapeHTML(t.family)}</span>
          </div>
          <div class="tier-energy-line mono">${escapeHTML(t.energy)}</div>
          <div class="tier-scale-line">${escapeHTML(t.scale)}</div>
          <div class="tier-card-foot">
            <span>${escapeHTML(t.model)}</span>
            <span style="color:var(--accent-blue)">详情 ›</span>
          </div>
        </a>`;
    }

    function renderTable(list) {
      const rows = list
        .map((t) => {
          const orderText = t.unranked ? "—" : t.order;
          return `
          <tr>
            <td class="mono" style="color:var(--text-muted)">${orderText}</td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" class="tier-code-badge mono" style="display:inline-flex">⊙ ${escapeHTML(t.code)}</a></td>
            <td><a href="${resolveUrl("tier/" + t.slug + ".html")}" style="font-weight:700;color:var(--text-primary)">${escapeHTML(t.name)}</a></td>
            <td class="mono" style="color:var(--accent-gold)">${escapeHTML(t.energy)}</td>
            <td>${escapeHTML(t.scale)}</td>
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
      sortBtns.forEach((b) => b.classList.toggle("active", b.dataset.tierSort === state.sort));
      segBtns.forEach((b) => b.classList.toggle("active", b.dataset.tierSeg === state.segment));
      viewBtns.forEach((b) => b.classList.toggle("active", b.dataset.tierView === state.view));
      alphaKeyBtns.forEach((b) => b.classList.toggle("active", b.dataset.alphaKey === state.alphaKey));
      if (clearBtn) clearBtn.style.display = state.query ? "block" : "none";

      const filtered = tiers.filter(matchesTier);
      if (countBadge) countBadge.textContent = `共显示 ${filtered.length} 个档位`;

      if (filtered.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        mount.innerHTML = `
          <div class="empty-state-box">
            <div class="empty-icon">🔍</div>
            <h3 style="margin:0 0 8px">未找到匹配的量级档位</h3>
            <p style="color:var(--text-muted);margin:0 0 16px">请尝试更换搜索词或切换上方分段筛选条件。</p>
            <button type="button" class="btn btn-surface" id="reset-tier-filters">重置全部筛选</button>
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
        return;
      }

      // Alphabetical Mode
      if (state.sort === "alpha") {
        if (alphaBar) alphaBar.classList.add("visible");
        const initField = state.alphaKey === "code" ? "code_initial" : "full_initial";
        const pyField = state.alphaKey === "code" ? "code_pinyin" : "full_pinyin";

        const buckets = {};
        filtered.forEach((t) => {
          const letter = (t[initField] || "#").toUpperCase();
          if (!buckets[letter]) buckets[letter] = [];
          buckets[letter].push(t);
        });

        const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
        if (alphaLettersEl) {
          alphaLettersEl.innerHTML = alphabet
            .map((L) => {
              const has = buckets[L] && buckets[L].length > 0;
              return `<button type="button" class="alpha-key mono ${has ? "" : "disabled"}" ${
                has ? `data-jump-letter="${L}" title="${L} 组（${buckets[L].length} 项）"` : "disabled"
              }>${L}</button>`;
            })
            .join("");
          alphaLettersEl.querySelectorAll("[data-jump-letter]").forEach((btn) => {
            btn.addEventListener("click", () => {
              const target = document.getElementById("tier-letter-" + btn.dataset.jumpLetter);
              if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
            });
          });
        }

        const activeLetters = Object.keys(buckets).sort();
        mount.innerHTML = activeLetters
          .map((L) => {
            const items = buckets[L].slice().sort((a, b) => {
              const cmp = String(a[pyField]).localeCompare(String(b[pyField]));
              return cmp !== 0 ? cmp : a.order - b.order;
            });
            const body =
              state.view === "table"
                ? renderTable(items)
                : `<div class="tier-grid">${items.map(renderCard).join("")}</div>`;
            return `
              <section class="tier-group-block" id="tier-letter-${L}">
                <div class="tier-group-header">
                  <h2 class="tier-group-title"><span class="letter-badge mono">${L}</span> 拼音首字母 ${L}</h2>
                  <span class="tier-group-sub">本组共 ${items.length} 个量级档位（同音组内按量级由小到大排列）</span>
                </div>
                ${body}
              </section>`;
          })
          .join("");
        return;
      }

      // Scale Order Mode (从小到大 asc / 从大到小 desc)
      if (alphaBar) alphaBar.classList.remove("visible");

      const ranked = filtered.filter((t) => !t.unranked);
      const unranked = filtered.filter((t) => t.unranked);
      ranked.sort((a, b) => (state.sort === "asc" ? a.order - b.order : b.order - a.order));

      if (state.view === "table") {
        mount.innerHTML = renderTable(ranked.concat(unranked));
        return;
      }

      // Group ordered blocks preserving order direction
      const orderedGroupIds = [];
      ranked.concat(unranked).forEach((t) => {
        if (!orderedGroupIds.includes(t.group_id)) orderedGroupIds.push(t.group_id);
      });

      mount.innerHTML = orderedGroupIds
        .map((gid) => {
          const g = groupMap[gid];
          const gItems = ranked.concat(unranked).filter((t) => t.group_id === gid);
          return `
            <section class="tier-group-block" id="group-${gid}">
              <div class="tier-group-header">
                <h2 class="tier-group-title">${escapeHTML(g ? g.title : gid)}</h2>
                <span class="tier-group-sub">${escapeHTML(g ? g.subtitle : "")} · 显示 ${gItems.length} 档</span>
              </div>
              <div class="tier-grid">${gItems.map(renderCard).join("")}</div>
            </section>`;
        })
        .join("");
    }

    sortBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.sort = btn.dataset.tierSort;
        persistPrefs();
        render();
      });
    });

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

    alphaKeyBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.alphaKey = btn.dataset.alphaKey;
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
     8. Interactive Characters Explorer (characters.html)
     -------------------------------------------------------------------------- */
  function initCharactersExplorer() {
    const mount = document.getElementById("chars-explorer-mount");
    if (!mount || !window.__POWERWIKI_DATA__) return;

    const { tiers, characters, demoArchetypes } = window.__POWERWIKI_DATA__;
    const tierBySlug = {};
    tiers.forEach((t) => (tierBySlug[t.slug] = t));

    const savedPrefs = safeGetJSON(localStorage, STORAGE_KEYS.charPrefs, {});
    const state = {
      sort: savedPrefs.sort || "asc", // asc | desc | alpha
      series: "all",
      domain: "all",
      query: "",
      showDemo: characters.length === 0 ? Boolean(savedPrefs.showDemo) : false
    };

    const sortBtns = document.querySelectorAll("[data-char-sort]");
    const domainBtns = document.querySelectorAll("[data-char-domain]");
    const seriesSelect = document.getElementById("char-series-select");
    const filterInput = document.getElementById("char-filter-input");
    const demoToggleBtn = document.getElementById("char-demo-toggle");
    const alphaBar = document.getElementById("char-alpha-bar");
    const alphaLettersEl = document.getElementById("char-alpha-letters");
    const countBadge = document.getElementById("char-result-count");

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
            <span class="mod-chip" style="color:var(--accent-blue)">主档：${escapeHTML(t ? t.name : "待定")}（#${t ? t.order : "—"}）</span>
            <span class="mod-chip">首字母：${escapeHTML(c.initial || "#")}</span>
            ${modHtml}
            ${c._isDemo ? '<span class="mod-chip" style="color:var(--accent-gold);border-color:var(--border-gold)">体系演示样例</span>' : ""}
          </div>
          <div class="dims-mini-grid">${dimsHtml}</div>
          <div style="font-size:13px;color:var(--text-secondary);line-height:1.6">${escapeHTML(c.summary || "")}</div>
        </a>`;
    }

    function openDemoModal(c) {
      const modal = document.getElementById("demo-char-modal");
      const body = document.getElementById("demo-char-modal-body");
      if (!modal || !body) return;
      const t = c._tier;
      const dimRows = ["破", "控", "域", "御", "速", "算", "性"]
        .map(
          (k) => `
          <tr>
            <th style="width:90px">维度「${k}」</th>
            <td>${formatEvidenceBadges((c.dims && c.dims[k]) || "〔缺〕")}</td>
          </tr>`
        )
        .join("");

      body.innerHTML = `
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px">
          <div>
            <div class="detail-code-pill mono" style="margin-bottom:8px">⊙ ${escapeHTML(t.code)} · ${escapeHTML(t.name)}</div>
            <h2 style="margin:0;font-size:22px">${escapeHTML(c.name)}</h2>
            <div style="color:var(--text-muted);font-size:13px;margin-top:4px">${escapeHTML(c.alias || "")} ｜ ${escapeHTML(c.series || "")}</div>
          </div>
          <a class="btn btn-surface" href="${resolveUrl("tier/" + t.slug + ".html")}">查看所属量级（⊙${escapeHTML(t.code)}）›</a>
        </div>
        <p style="color:var(--text-secondary);margin:0 0 14px">${escapeHTML(c.summary || "")}</p>
        <div style="font-size:13px;color:var(--accent-gold);margin-bottom:10px">可信度依据：${formatEvidenceBadges(c.credibility || "—")}</div>
        <div class="table-scroll" style="margin:0">
          <table class="compact-table"><tbody>${dimRows}</tbody></table>
        </div>
        <div style="margin-top:14px;font-size:12.5px;color:var(--text-muted)">
          注：本条目为《衡天⊙ 多维战力量级体系（第二版）》1.5 / 8.3 节书写格式的交互演示样例，不计入正式角色库统计。
        </div>
      `;
      modal.classList.add("open");
    }

    function render() {
      sortBtns.forEach((b) => b.classList.toggle("active", b.dataset.charSort === state.sort));
      domainBtns.forEach((b) => b.classList.toggle("active", b.dataset.charDomain === state.domain));
      if (demoToggleBtn) {
        demoToggleBtn.style.display = characters.length === 0 ? "inline-flex" : "none";
        demoToggleBtn.classList.toggle("active", state.showDemo);
        demoToggleBtn.innerHTML = state.showDemo
          ? "✦ 关闭演示样例（返回正式空库）"
          : "✦ 预览体系书写演示样例（6 组）";
      }

      const pool = getActivePool();
      populateSeriesDropdown(pool);

      if (pool.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        if (countBadge) countBadge.textContent = "正式收录 0 位角色";
        mount.innerHTML = `
          <div class="empty-state-box">
            <div class="empty-icon">⊙</div>
            <h3 style="margin:0 0 10px;font-size:20px">正式角色档案库 · 待录入</h3>
            <p style="color:var(--text-secondary);margin:0 auto 18px;max-width:540px;line-height:1.75">
              本站已全面升级至<strong>《衡天⊙ 多维战力量级体系（第二版）》</strong>，旧版单维档位角色已清空重制。
              所有新角色将严格按<strong>七维评定表（破·控·域·御·速·算·性）</strong>与证据状态标记录入。
            </p>
            <div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap">
              <button type="button" class="btn btn-primary" id="empty-open-demo">✦ 开启 6 组演示卡片（体验首字母 / 量级排序）</button>
              <a class="btn btn-surface" href="${resolveUrl("rules.html")}">查阅《衡天⊙》定级标准</a>
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
          ? `演示模式：显示 ${filtered.length} / ${pool.length} 组样例`
          : `正式收录：显示 ${filtered.length} / ${pool.length} 位角色`;
      }

      if (filtered.length === 0) {
        if (alphaBar) alphaBar.classList.remove("visible");
        mount.innerHTML = `
          <div class="empty-state-box">
            <div class="empty-icon">🔍</div>
            <h3 style="margin:0 0 8px">没有符合筛选条件的角色</h3>
            <p style="color:var(--text-muted);margin:0">请调整搜索关键词、作品或量级区间。</p>
          </div>`;
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
                has ? `data-char-letter="${L}"` : "disabled"
              }>${L}</button>`;
            })
            .join("");
          alphaLettersEl.querySelectorAll("[data-char-letter]").forEach((btn) => {
            btn.addEventListener("click", () => {
              const el = document.getElementById("char-letter-" + btn.dataset.charLetter);
              if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
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
                  <h2 class="tier-group-title"><span class="letter-badge mono">${L}</span> 角色首字母 ${L}</h2>
                  <span class="tier-group-sub">共 ${list.length} 位角色</span>
                </div>
                <div class="char-grid">${list.map(renderCharCard).join("")}</div>
              </section>`;
          })
          .join("");
      } else {
        if (alphaBar) alphaBar.classList.remove("visible");
        const sorted = filtered.slice().sort((a, b) => {
          const diff = state.sort === "asc" ? a._order - b._order : b._order - a._order;
          return diff !== 0 ? diff : String(a.pinyin || a.name).localeCompare(String(b.pinyin || b.name));
        });
        const dirTitle =
          state.sort === "asc"
            ? "按主档量级从小到大排列（凡人 → 恒星 → 宇宙 → 论外）"
            : "按主档量级从大到小排列（论外 → 宇宙 → 恒星 → 凡人）";
        mount.innerHTML = `
          <section class="tier-group-block">
            <div class="tier-group-header">
              <h2 class="tier-group-title">${dirTitle}</h2>
              <span class="tier-group-sub">共 ${sorted.length} 位角色</span>
            </div>
            <div class="char-grid">${sorted.map(renderCharCard).join("")}</div>
          </section>`;
      }

      // Bind demo modal clicks if in demo mode
      mount.querySelectorAll("[data-demo-slug]").forEach((card) => {
        card.addEventListener("click", (e) => {
          e.preventDefault();
          const slug = card.getAttribute("data-demo-slug");
          const found = pool.find((x) => x.slug === slug);
          if (found) openDemoModal(found);
        });
      });
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
      demoClose.addEventListener("click", () => demoModal.classList.remove("open"));
      demoModal.addEventListener("click", (e) => {
        if (e.target === demoModal) demoModal.classList.remove("open");
      });
    }

    render();
  }

  /* --------------------------------------------------------------------------
     9. Global Search Engine (Ctrl+K Modal & search.html Page)
     -------------------------------------------------------------------------- */
  function runSearchQuery(rawQuery, typeFilter) {
    const index = window.__POWERWIKI_INDEX__ || [];
    const q = (rawQuery || "").trim().toLowerCase();
    const tokens = q ? q.split(/\s+/).filter(Boolean) : [];

    const results = [];
    for (const item of index) {
      if (typeFilter && typeFilter !== "all" && item.type !== typeFilter) continue;
      if (tokens.length === 0) {
        results.push({ item, score: item.type === "tier" ? 50 : 30 });
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
    const slice = (start > 0 ? "…" : "") + clean.slice(start, start + 150) + (start + 150 < clean.length ? "…" : "");
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
    tier: "量级档位",
    char: "角色档案",
    rules: "衡天体系标准",
    materials: "材质能量库"
  };

  function initGlobalSearchModal() {
    const trigger = document.getElementById("global-search-trigger");
    const backdrop = document.getElementById("search-modal");
    const input = document.getElementById("search-modal-input");
    const closeBtn = document.getElementById("search-modal-close");
    const body = document.getElementById("search-modal-results");
    const tabBtns = document.querySelectorAll("[data-search-tab]");

    if (!backdrop || !input || !body) return;
    let activeTab = "all";

    function renderHits() {
      const q = input.value;
      const hits = runSearchQuery(q, activeTab);
      if (hits.length === 0) {
        body.innerHTML = `<div style="padding:32px 16px;text-align:center;color:var(--text-muted)">未找到与「${escapeHTML(q)}」相关的条目，试试搜索「宇◆」「白矮星」「0#」「多击不认」「花岗岩」。</div>`;
        return;
      }
      body.innerHTML = hits
        .slice(0, 30)
        .map(
          (h) => `
          <a class="search-hit" href="${resolveUrl(h.url)}">
            <div class="search-hit-top">
              <span class="search-hit-title">${highlightSnippet(h.title, q)}</span>
              <span class="search-hit-type">${TYPE_LABELS[h.type] || h.type}</span>
            </div>
            <div class="search-hit-snippet">${highlightSnippet(h.text, q)}</div>
          </a>`
        )
        .join("");

      body.querySelectorAll(".search-hit").forEach((el) => {
        el.addEventListener("click", () => {
          backdrop.classList.remove("open");
        });
      });
    }

    function openModal() {
      backdrop.classList.add("open");
      renderHits();
      setTimeout(() => input.focus(), 30);
    }

    if (trigger) trigger.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", () => backdrop.classList.remove("open"));
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("open");
    });

    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        activeTab = btn.dataset.searchTab;
        tabBtns.forEach((b) => b.classList.toggle("active", b === btn));
        renderHits();
      });
    });

    input.addEventListener("input", renderHits);

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
        backdrop.classList.remove("open");
        const histModal = document.getElementById("history-modal");
        if (histModal) histModal.classList.remove("open");
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
      if (countEl) countEl.textContent = `匹配结果：${hits.length} 条`;

      if (hits.length === 0) {
        mount.innerHTML = `<div class="empty-state-box"><div class="empty-icon">🔍</div><h3>没有找到匹配内容</h3><p style="color:var(--text-muted)">试试搜索代字（如 恒○、宇◆、外·门）、规则术语（如 证伪五信号、图灵跃迁）或材质名称（如 中子星、玄武岩、GBU-57）。</p></div>`;
        return;
      }

      mount.innerHTML = hits
        .map(
          (h) => `
          <a class="search-hit" style="background:var(--bg-surface-1);border-color:var(--border-subtle);padding:15px 18px;margin-bottom:10px" href="${resolveUrl(h.url)}">
            <div class="search-hit-top">
              <span class="search-hit-title" style="font-size:16px">${highlightSnippet(h.title, q)}</span>
              <span class="search-hit-type">${TYPE_LABELS[h.type] || h.type}</span>
            </div>
            <div class="search-hit-snippet" style="font-size:13.8px">${highlightSnippet(h.text, q)}</div>
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
  });
})();
