#!/usr/bin/env python3
"""
Builds a standalone interactive HTML documentation portal (docs/index.html)
from the markdown files in docs/.
"""

import json
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"

CHAPTERS = [
    {
        "id": "overview",
        "title": "Overview & Curriculum",
        "icon": "📖",
        "file": "README.md",
        "desc": "Architectural philosophy, four core pillars & roadmap"
    },
    {
        "id": "architecture",
        "title": "System Architecture",
        "icon": "🗺️",
        "file": "01_system_architecture.md",
        "desc": "End-to-end topology, sequence diagrams & 800ms latency budget"
    },
    {
        "id": "tech-stack",
        "title": "Technology Stack Deep Dive",
        "icon": "⚖️",
        "file": "02_technology_stack_deep_dive.md",
        "desc": "Pipecat vs LangChain, Playwright vs Meta API & trade-offs"
    },
    {
        "id": "codebase",
        "title": "Codebase Guided Tour",
        "icon": "🔍",
        "file": "03_codebase_walkthrough.md",
        "desc": "Module-by-module breakdown & WebSocket event contracts"
    },
    {
        "id": "playwright",
        "title": "WhatsApp Automation",
        "icon": "🌐",
        "file": "04_playwright_whatsapp_mechanics.md",
        "desc": "Chromium persistent context, QR survival & anti-bot mitigation"
    },
    {
        "id": "voice-agent",
        "title": "Voice Agent & Prompts",
        "icon": "🎙️",
        "file": "05_voice_agent_and_prompt_engineering.md",
        "desc": "Voice UX, Urdish code-switching & JSON function calling"
    },
    {
        "id": "audio-engineering",
        "title": "Frontend & Audio Engineering",
        "icon": "🎧",
        "file": "06_frontend_and_audio_engineering.md",
        "desc": "Acoustic Echo Cancellation (AEC), 16kHz sampling & CSS Orb"
    }
]

docs_data = []
for ch in CHAPTERS:
    p = DOCS_DIR / ch["file"]
    if p.exists():
        content = p.read_text(encoding="utf-8")
    else:
        content = f"# {ch['title']}\n\nContent not found."
    docs_data.append({
        "id": ch["id"],
        "title": ch["title"],
        "icon": ch["icon"],
        "desc": ch["desc"],
        "content": content
    })

docs_json = json.dumps(docs_data)

html_template = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pegham.ai — Architecture & Developer Documentation</title>
  
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📨</text></svg>">
  
  <!-- Tailwind CSS via CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Noto+Nastaliq+Urdu:wght@400;700&display=swap" rel="stylesheet">
  
  <!-- Marked.js for High Performance Markdown Parsing -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  
  <!-- Prism.js for Syntax Highlighting -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>

  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Inter', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
            urdu: ['Noto Nastaliq Urdu', 'serif']
          }},
          colors: {{
            darkbg: '#0a0d14',
            darksidebar: '#0d111a',
            darkcard: '#121722',
            bordercolor: '#1e2638',
            primary: '#10b981',
            accent: '#f59e0b',
            accentcoral: '#f43f5e'
          }}
        }}
      }}
    }}
  </script>

  <style>
    /* Custom Scrollbars */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #0a0d14;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #1e2638;
      border-radius: 9999px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: #334155;
    }}

    /* Markdown Typography Styling */
    .prose-pegham h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      color: #f8fafc;
      margin-top: 1rem;
      margin-bottom: 1.2rem;
      letter-spacing: -0.025em;
      border-bottom: 1px solid #1e2638;
      padding-bottom: 0.6rem;
    }}
    .prose-pegham h2 {{
      font-size: 1.4rem;
      font-weight: 700;
      color: #e2e8f0;
      margin-top: 2rem;
      margin-bottom: 0.8rem;
      letter-spacing: -0.02em;
    }}
    .prose-pegham h3 {{
      font-size: 1.15rem;
      font-weight: 600;
      color: #cbd5e1;
      margin-top: 1.4rem;
      margin-bottom: 0.5rem;
    }}
    .prose-pegham p {{
      color: #94a3b8;
      line-height: 1.7;
      margin-bottom: 1rem;
      font-size: 0.95rem;
    }}
    .prose-pegham ul, .prose-pegham ol {{
      margin-left: 1.25rem;
      margin-bottom: 1rem;
      color: #94a3b8;
    }}
    .prose-pegham ul {{ list-style-type: disc; }}
    .prose-pegham ol {{ list-style-type: decimal; }}
    .prose-pegham li {{
      margin-bottom: 0.35rem;
      line-height: 1.6;
    }}
    .prose-pegham a {{
      color: #38bdf8;
      text-decoration: none;
      border-bottom: 1px dashed #0284c7;
      transition: all 0.2s;
    }}
    .prose-pegham a:hover {{
      color: #7dd3fc;
      border-bottom-style: solid;
    }}
    .prose-pegham blockquote {{
      border-left: 3px solid #f59e0b;
      background: rgba(245, 158, 11, 0.06);
      padding: 0.75rem 1rem;
      border-radius: 0 0.5rem 0.5rem 0;
      margin: 1.2rem 0;
      color: #e2e8f0;
    }}
    .prose-pegham table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
      font-size: 0.88rem;
      border-radius: 0.5rem;
      overflow: hidden;
      border: 1px solid #1e2638;
    }}
    .prose-pegham th {{
      background: #121722;
      color: #f1f5f9;
      padding: 0.65rem 0.9rem;
      text-align: left;
      font-weight: 600;
      border-bottom: 1px solid #1e2638;
    }}
    .prose-pegham td {{
      padding: 0.6rem 0.9rem;
      border-bottom: 1px solid #171d2b;
      color: #cbd5e1;
    }}
    .prose-pegham tr:last-child td {{
      border-bottom: none;
    }}
    .prose-pegham tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .prose-pegham code:not(pre code) {{
      background: #161c28;
      color: #fbbf24;
      padding: 0.15rem 0.35rem;
      border-radius: 0.25rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85em;
      border: 1px solid #232b3d;
    }}
    .prose-pegham pre {{
      background: #0f141f !important;
      border: 1px solid #1e2638;
      border-radius: 0.75rem;
      padding: 1rem;
      margin: 1.2rem 0;
      overflow-x: auto;
    }}
    .prose-pegham pre code {{
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.86rem;
      line-height: 1.6;
    }}
    .prose-pegham hr {{
      border: none;
      border-top: 1px solid #1e2638;
      margin: 2rem 0;
    }}
  </style>
</head>
<body class="bg-darkbg text-slate-100 min-h-screen flex flex-col font-sans selection:bg-amber-500 selection:text-slate-900">

  <!-- Top Navigation Bar -->
  <header class="h-16 border-b border-bordercolor bg-darksidebar/90 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <span class="text-2xl select-none">📨</span>
      <div class="flex items-center space-x-2">
        <a href="/" class="font-bold text-base tracking-tight flex items-center gap-1.5 hover:opacity-90 transition">
          <span class="bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent font-extrabold">Pegham</span><span class="text-slate-300 font-semibold">.ai</span>
        </a>
        <span class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-amber-400 font-medium border border-slate-700">Docs Portal</span>
      </div>
    </div>

    <!-- Quick Search & Actions -->
    <div class="flex items-center space-x-3">
      <div class="relative hidden sm:block w-64">
        <input id="search-input" type="text" placeholder="Search documentation... (⌘K)" class="w-full bg-darkcard border border-bordercolor rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/60 transition">
        <kbd class="absolute right-2.5 top-1.5 text-[10px] bg-slate-800 text-slate-400 px-1 py-0.5 rounded border border-slate-700">/</kbd>
      </div>
      <a href="/" class="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 transition flex items-center gap-1.5">
        <span>🎙️ Open App</span>
      </a>
      <a href="https://github.com/jawadai/Pegham" target="_blank" rel="noreferrer" class="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 transition">
        GitHub
      </a>
    </div>
  </header>

  <!-- Main Layout -->
  <div class="flex-1 flex max-w-7xl w-full mx-auto">

    <!-- Left Sidebar / Tab List -->
    <aside class="w-72 border-r border-bordercolor bg-darksidebar/50 p-4 shrink-0 hidden md:block overflow-y-auto max-h-[calc(100vh-4rem)] sticky top-16">
      <p class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 px-2">Table of Contents</p>
      <nav id="sidebar-nav" class="space-y-1">
        <!-- Rendered by JS -->
      </nav>

      <div class="mt-8 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-400">
        <p class="font-semibold text-slate-200 mb-1">💡 Developer Note</p>
        <p class="text-[11px] leading-relaxed">This interactive docs portal works 100% offline and standalone directly from your disk.</p>
      </div>
    </aside>

    <!-- Content Viewport -->
    <main class="flex-1 p-6 md:p-10 max-w-4xl overflow-x-hidden">
      
      <!-- Chapter Header Card -->
      <div id="chapter-header" class="mb-6 p-5 rounded-2xl bg-darkcard border border-bordercolor flex items-center justify-between">
        <div class="flex items-center space-x-3.5">
          <span id="chapter-icon" class="text-3xl p-2.5 rounded-xl bg-slate-900 border border-slate-800">📖</span>
          <div>
            <span id="chapter-badge" class="text-[10px] font-semibold uppercase tracking-wider text-amber-400">Chapter 00</span>
            <h2 id="chapter-title" class="text-xl font-bold text-white tracking-tight">Overview & Curriculum</h2>
            <p id="chapter-desc" class="text-xs text-slate-400 mt-0.5">Architectural philosophy & roadmap</p>
          </div>
        </div>
        <div class="hidden sm:flex items-center space-x-2">
          <button id="copy-markdown-btn" onclick="copyCurrentContent()" class="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded bg-slate-900 border border-slate-800 transition flex items-center gap-1">
            <span>📋 Copy Markdown</span>
          </button>
        </div>
      </div>

      <!-- Rendered Markdown Content Container -->
      <article id="doc-content" class="prose-pegham">
        <!-- Markdown injected here -->
      </article>

      <!-- Bottom Pager Navigation -->
      <div class="mt-12 pt-6 border-t border-bordercolor flex items-center justify-between">
        <button id="prev-btn" onclick="navigateChapter(-1)" class="px-4 py-2 rounded-xl bg-darkcard border border-bordercolor text-xs font-medium text-slate-300 hover:text-white hover:border-slate-700 transition flex items-center gap-2">
          <span>← Previous</span>
        </button>
        <button id="next-btn" onclick="navigateChapter(1)" class="px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs font-semibold text-amber-400 hover:bg-amber-500/20 transition flex items-center gap-2">
          <span>Next Chapter →</span>
        </button>
      </div>

    </main>
  </div>

  <script>
    const chapters = {docs_json};
    let currentIdx = 0;

    // Initialize marked options
    marked.setOptions({{
      gfm: true,
      breaks: true
    }});

    // Build sidebar tabs
    const nav = document.getElementById("sidebar-nav");
    chapters.forEach((ch, idx) => {{
      const btn = document.createElement("button");
      btn.className = `w-full text-left px-3 py-2.5 rounded-xl text-xs font-medium transition flex items-center space-x-2.5 ${{
        idx === 0 ? 'bg-amber-500/15 text-amber-300 font-semibold border border-amber-500/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
      }}`;
      btn.id = `tab-${{ch.id}}`;
      btn.onclick = () => selectChapter(idx);
      btn.innerHTML = `
        <span class="text-base">${{ch.icon}}</span>
        <div class="truncate">
          <div class="truncate">${{ch.title}}</div>
        </div>
      `;
      nav.appendChild(btn);
    }});

    function selectChapter(idx) {{
      if (idx < 0 || idx >= chapters.length) return;
      currentIdx = idx;
      const ch = chapters[idx];

      // Update URL hash
      window.location.hash = ch.id;

      // Update tab active classes
      chapters.forEach((item, i) => {{
        const el = document.getElementById(`tab-${{item.id}}`);
        if (el) {{
          if (i === idx) {{
            el.className = "w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 transition flex items-center space-x-2.5";
          }} else {{
            el.className = "w-full text-left px-3 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 transition flex items-center space-x-2.5";
          }}
        }}
      }});

      // Update Header info
      document.getElementById("chapter-badge").textContent = `Chapter 0${{idx}}`;
      document.getElementById("chapter-icon").textContent = ch.icon;
      document.getElementById("chapter-title").textContent = ch.title;
      document.getElementById("chapter-desc").textContent = ch.desc;

      // Parse & render markdown
      const article = document.getElementById("doc-content");
      article.innerHTML = marked.parse(ch.content);

      // Re-trigger Prism syntax highlight
      Prism.highlightAllUnder(article);

      // Update Pager button visibility
      const prevBtn = document.getElementById("prev-btn");
      const nextBtn = document.getElementById("next-btn");
      prevBtn.style.visibility = idx === 0 ? "hidden" : "visible";
      nextBtn.style.visibility = idx === chapters.length - 1 ? "hidden" : "visible";
      if (idx > 0) prevBtn.querySelector("span").textContent = `← ${{chapters[idx - 1].title}}`;
      if (idx < chapters.length - 1) nextBtn.querySelector("span").textContent = `${{chapters[idx + 1].title}} →`;

      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function navigateChapter(delta) {{
      selectChapter(currentIdx + delta);
    }}

    function copyCurrentContent() {{
      const ch = chapters[currentIdx];
      navigator.clipboard.writeText(ch.content).then(() => {{
        const btn = document.getElementById("copy-markdown-btn");
        btn.innerHTML = "<span>✓ Copied!</span>";
        setTimeout(() => {{
          btn.innerHTML = "<span>📋 Copy Markdown</span>";
        }}, 2000);
      }});
    }}

    // Check hash on page load
    window.addEventListener("DOMContentLoaded", () => {{
      const hash = window.location.hash.replace("#", "");
      const foundIdx = chapters.findIndex(c => c.id === hash);
      if (foundIdx !== -1) {{
        selectChapter(foundIdx);
      }} else {{
        selectChapter(0);
      }}
    }});

    // Live search filter across chapters
    const searchInput = document.getElementById("search-input");
    searchInput.addEventListener("input", (e) => {{
      const q = e.target.value.toLowerCase().trim();
      chapters.forEach((ch) => {{
        const btn = document.getElementById(`tab-${{ch.id}}`);
        const match = ch.title.toLowerCase().includes(q) || ch.content.toLowerCase().includes(q);
        btn.style.display = match ? "flex" : "none";
      }});
    }});

    // Keyboard shortcut (/) to focus search
    window.addEventListener("keydown", (e) => {{
      if (e.key === "/" && document.activeElement !== searchInput) {{
        e.preventDefault();
        searchInput.focus();
      }}
    }});
  </script>
</body>
</html>
"""

output_path = DOCS_DIR / "index.html"
output_path.write_text(html_template, encoding="utf-8")
print(f"Successfully generated interactive documentation portal at: {output_path}")
