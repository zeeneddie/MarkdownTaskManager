/**
 * Playwright HCI-CRS Epic/Feature/Story Viewer
 * Opens a browser with a visual hierarchy of all epics, features and stories
 * Data is fetched from the Brown Paper DB API endpoints
 */
const { chromium } = require('playwright');

const API_BASE = 'http://127.0.0.1:8000/api';

async function main() {
    const browser = await chromium.launch({
        headless: false,
        slowMo: 50
    });
    const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

    console.log('Fetching HCI-CRS sessions from database...');

    // Step 1: Find HCI-CRS session
    let sessions;
    try {
        const resp = await fetch(`${API_BASE}/brown-paper/db/sessions`);
        if (!resp.ok) throw new Error(`API error: ${resp.status} ${await resp.text()}`);
        sessions = await resp.json();
    } catch (e) {
        console.error('Failed to fetch sessions:', e.message);
        console.log('\nTrying in-memory sessions instead...');

        // Fallback: try the in-memory session list
        try {
            const resp2 = await fetch(`${API_BASE}/brown-paper/marqed/sessions`);
            if (resp2.ok) {
                const data = await resp2.json();
                sessions = { sessions: data.sessions || [] };
            }
        } catch (e2) {
            console.error('Also failed to fetch in-memory sessions:', e2.message);
        }
    }

    // Find HCI-CRS session
    let hciSession = null;
    let epicsData = null;

    if (sessions && sessions.sessions) {
        hciSession = sessions.sessions.find(s =>
            (s.application_name || '').toLowerCase().includes('hci') ||
            (s.root_path || '').toLowerCase().includes('hci-crs')
        );
    }

    if (hciSession) {
        console.log(`Found HCI-CRS session: ${hciSession.id} (${hciSession.application_name})`);

        // Step 2: Fetch epics hierarchy
        try {
            const resp = await fetch(`${API_BASE}/brown-paper/db/sessions/${hciSession.id}/epics`);
            if (resp.ok) {
                epicsData = await resp.json();
                console.log(`Loaded ${epicsData.summary.total_epics} epics, ${epicsData.summary.total_features} features, ${epicsData.summary.total_stories} stories`);
            }
        } catch (e) {
            console.warn('DB epics fetch failed, trying in-memory:', e.message);
        }
    }

    // If no DB data, try to get from in-memory session
    if (!epicsData && sessions && sessions.sessions) {
        for (const s of sessions.sessions) {
            const sid = s.id || s.session_id;
            try {
                const resp = await fetch(`${API_BASE}/brown-paper/marqed/${sid}/results`);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.tasks && data.tasks.epics) {
                        epicsData = {
                            session_id: sid,
                            epics: data.tasks.epics.map((e, i) => ({
                                epic_number: i + 1,
                                name: e.title || e.name,
                                description: e.description || '',
                                priority: e.priority || 'medium',
                                complexity: e.complexity || 'medium',
                                source_domain: e.source_domain || e.domain || '',
                                function_points: e.function_points || e.fp || 0,
                                story_points: e.story_points || e.sp || 0,
                                feature_count: (e.features || []).length,
                                story_count: (e.features || []).reduce((sum, f) => sum + (f.stories || []).length, 0),
                                features: (e.features || []).map(f => ({
                                    title: f.title || f.name,
                                    description: f.description || '',
                                    estimated_sp: f.estimated_sp || f.sp || 0,
                                    story_count: (f.stories || []).length,
                                    stories: f.stories || []
                                }))
                            })),
                            summary: {
                                total_epics: (data.tasks.epics || []).length,
                                total_features: (data.tasks.features || []).length,
                                total_stories: (data.tasks.stories || []).length,
                                total_function_points: data.tasks.fp_analysis?.total_fp || 0,
                                total_story_points: data.tasks.summary?.total_sp || 0
                            }
                        };
                        hciSession = s;
                        console.log(`Found in-memory data for session ${sid}`);
                        break;
                    }
                }
            } catch (e) { /* skip */ }
        }
    }

    // Step 3: Render the viewer page
    const html = buildViewerHTML(hciSession, epicsData, sessions);
    await page.setContent(html);

    console.log('\nViewer is open. Close the browser to exit.');
    console.log('Use the expand/collapse buttons to drill down into features and stories.');

    // Keep browser open until manually closed
    await page.waitForEvent('close', { timeout: 0 }).catch(() => {});
    await browser.close();
}

function buildViewerHTML(session, epicsData, allSessions) {
    const hasData = epicsData && epicsData.epics && epicsData.epics.length > 0;
    const summary = epicsData?.summary || {};
    const sessionName = session?.application_name || 'HCI-CRS';

    let epicsHTML = '';
    if (hasData) {
        epicsHTML = epicsData.epics.map((epic, idx) => {
            const featuresHTML = (epic.features || []).map((feat, fIdx) => {
                const storiesHTML = (feat.stories || []).map((story, sIdx) => {
                    const storyType = story.type || story.story_type || 'user_story';
                    const typeBadgeClass = storyType.includes('technical') ? 'badge-technical'
                        : storyType.includes('enabler') ? 'badge-enabler'
                        : 'badge-user';
                    const ac = story.acceptance_criteria || [];
                    return `
                        <div class="story-item">
                            <div class="story-header">
                                <span class="story-type-badge ${typeBadgeClass}">${storyType.replace(/_/g, ' ')}</span>
                                <span class="story-title">${escapeHtml(story.title || story.name || `Story ${sIdx + 1}`)}</span>
                                <span class="story-sp">${story.estimated_sp || story.sp || '?'} SP</span>
                            </div>
                            ${story.description ? `<div class="story-desc">${escapeHtml(story.description)}</div>` : ''}
                            ${ac.length > 0 ? `
                                <div class="story-ac">
                                    <strong>Acceptance Criteria (${ac.length}):</strong>
                                    <ul>${ac.map(a => `<li>${escapeHtml(typeof a === 'string' ? a : a.description || a.criterion || JSON.stringify(a))}</li>`).join('')}</ul>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');

                return `
                    <div class="feature-item">
                        <div class="feature-header" onclick="toggleSection(this)">
                            <span class="toggle-icon">&#9654;</span>
                            <span class="feature-title">${escapeHtml(feat.title || `Feature ${fIdx + 1}`)}</span>
                            <span class="feature-meta">
                                <span class="pill">${feat.story_count || 0} stories</span>
                                <span class="pill sp">${feat.estimated_sp || 0} SP</span>
                            </span>
                        </div>
                        ${feat.description ? `<div class="feature-desc">${escapeHtml(feat.description)}</div>` : ''}
                        <div class="section-children" style="display:none;">
                            ${storiesHTML || '<div class="empty">Geen stories gevonden</div>'}
                        </div>
                    </div>
                `;
            }).join('');

            const priorityClass = epic.priority === 'critical' ? 'priority-critical'
                : epic.priority === 'high' ? 'priority-high'
                : epic.priority === 'medium' ? 'priority-medium'
                : 'priority-low';

            return `
                <div class="epic-card">
                    <div class="epic-header" onclick="toggleSection(this)">
                        <span class="toggle-icon">&#9654;</span>
                        <span class="epic-number">Epic ${epic.epic_number || idx + 1}</span>
                        <span class="epic-name">${escapeHtml(epic.name)}</span>
                        <div class="epic-badges">
                            <span class="pill ${priorityClass}">${epic.priority || 'medium'}</span>
                            <span class="pill">${epic.complexity || '?'}</span>
                            <span class="pill">${epic.feature_count || 0} features</span>
                            <span class="pill">${epic.story_count || 0} stories</span>
                            <span class="pill fp">${epic.function_points || 0} FP</span>
                            <span class="pill sp">${epic.story_points || 0} SP</span>
                        </div>
                    </div>
                    ${epic.source_domain ? `<div class="epic-domain">Domein: ${escapeHtml(epic.source_domain)}</div>` : ''}
                    ${epic.description ? `<div class="epic-desc">${escapeHtml(epic.description)}</div>` : ''}
                    <div class="section-children" style="display:none;">
                        ${featuresHTML || '<div class="empty">Geen features gevonden</div>'}
                    </div>
                </div>
            `;
        }).join('');
    } else {
        // Show available sessions or error
        const sessionList = (allSessions?.sessions || []).map(s => `
            <div class="session-item">
                <strong>${escapeHtml(s.application_name || 'Unnamed')}</strong>
                <span class="pill">${s.epic_count || 0} epics</span>
                <span style="color:#888; font-size:0.85em;">${s.id}</span>
                ${s.root_path ? `<div style="color:#666; font-size:0.8em;">${escapeHtml(s.root_path)}</div>` : ''}
            </div>
        `).join('') || '<div class="empty">Geen sessies gevonden in de database</div>';

        epicsHTML = `
            <div class="no-data">
                <h2>Geen HCI-CRS epics gevonden</h2>
                <p>Voer eerst de brown paper workflow uit voor HCI-CRS, of controleer of de backend draait op port 8000.</p>
                <h3>Beschikbare sessies:</h3>
                ${sessionList}
                <div style="margin-top: 20px;">
                    <p><strong>Tip:</strong> Voer de workflow uit met:</p>
                    <pre>cd frontend && node playwright-brown-paper.js</pre>
                </div>
            </div>
        `;
    }

    return `<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>HCI-CRS - Epics, Features &amp; Stories</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 30px;
        }
        header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 30px; padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        h1 { color: #f39c12; font-size: 1.8em; }
        h1 span { color: #3498db; font-weight: 300; }
        .summary-bar {
            display: flex; gap: 20px; flex-wrap: wrap;
        }
        .summary-stat {
            background: rgba(255,255,255,0.08); padding: 12px 20px;
            border-radius: 10px; text-align: center;
        }
        .summary-stat .value { font-size: 1.8em; font-weight: 700; color: #f39c12; }
        .summary-stat .label { font-size: 0.8em; color: #999; margin-top: 4px; }
        .controls {
            margin-bottom: 20px; display: flex; gap: 10px;
        }
        .controls button {
            background: rgba(52, 152, 219, 0.3); border: 1px solid #3498db;
            color: #3498db; padding: 8px 16px; border-radius: 6px;
            cursor: pointer; font-size: 0.9em;
        }
        .controls button:hover { background: rgba(52, 152, 219, 0.5); }

        .epic-card {
            background: rgba(255,255,255,0.06); border-radius: 12px;
            margin-bottom: 16px; border-left: 4px solid #3498db;
            overflow: hidden;
        }
        .epic-header {
            display: flex; align-items: center; gap: 12px;
            padding: 16px 20px; cursor: pointer;
            transition: background 0.2s;
        }
        .epic-header:hover { background: rgba(255,255,255,0.05); }
        .toggle-icon {
            font-size: 0.8em; transition: transform 0.2s;
            color: #3498db; min-width: 16px;
        }
        .toggle-icon.open { transform: rotate(90deg); }
        .epic-number {
            background: #3498db; color: white; padding: 4px 10px;
            border-radius: 6px; font-weight: 600; font-size: 0.85em;
            white-space: nowrap;
        }
        .epic-name { font-weight: 600; font-size: 1.1em; flex: 1; }
        .epic-badges { display: flex; gap: 6px; flex-wrap: wrap; }
        .epic-domain {
            padding: 4px 20px 4px 52px; font-size: 0.85em; color: #8e8ea0;
            font-style: italic;
        }
        .epic-desc {
            padding: 8px 20px 12px 52px; font-size: 0.9em; color: #aaa;
            line-height: 1.5;
        }

        .pill {
            display: inline-block; padding: 3px 10px; border-radius: 12px;
            font-size: 0.78em; font-weight: 500;
            background: rgba(255,255,255,0.1); color: #ccc;
        }
        .pill.fp { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
        .pill.sp { background: rgba(155, 89, 182, 0.2); color: #9b59b6; }
        .priority-critical { background: rgba(231, 76, 60, 0.3); color: #e74c3c; }
        .priority-high { background: rgba(243, 156, 18, 0.3); color: #f39c12; }
        .priority-medium { background: rgba(52, 152, 219, 0.2); color: #3498db; }
        .priority-low { background: rgba(149, 165, 166, 0.2); color: #95a5a6; }

        .section-children { padding: 0 20px 16px 36px; }

        .feature-item {
            background: rgba(255,255,255,0.04); border-radius: 8px;
            margin-bottom: 10px; border-left: 3px solid #9b59b6;
            overflow: hidden;
        }
        .feature-header {
            display: flex; align-items: center; gap: 10px;
            padding: 12px 16px; cursor: pointer;
            transition: background 0.2s;
        }
        .feature-header:hover { background: rgba(255,255,255,0.04); }
        .feature-title { font-weight: 500; flex: 1; }
        .feature-meta { display: flex; gap: 6px; }
        .feature-desc {
            padding: 4px 16px 10px 42px; font-size: 0.85em; color: #999;
        }

        .story-item {
            background: rgba(255,255,255,0.03); border-radius: 6px;
            padding: 12px 16px; margin-bottom: 8px;
            border-left: 3px solid #2ecc71;
        }
        .story-header {
            display: flex; align-items: center; gap: 10px;
        }
        .story-type-badge {
            padding: 2px 8px; border-radius: 4px; font-size: 0.75em;
            font-weight: 600; text-transform: uppercase;
        }
        .badge-user { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
        .badge-technical { background: rgba(52, 152, 219, 0.2); color: #3498db; }
        .badge-enabler { background: rgba(243, 156, 18, 0.2); color: #f39c12; }
        .story-title { flex: 1; font-weight: 500; font-size: 0.95em; }
        .story-sp { color: #9b59b6; font-weight: 600; font-size: 0.85em; }
        .story-desc {
            margin-top: 6px; font-size: 0.85em; color: #999; line-height: 1.4;
        }
        .story-ac {
            margin-top: 8px; font-size: 0.82em; color: #888;
        }
        .story-ac ul { margin: 4px 0 0 20px; }
        .story-ac li { margin-bottom: 3px; }

        .empty { color: #666; font-style: italic; padding: 12px; }
        .no-data { text-align: center; padding: 60px 20px; }
        .no-data h2 { color: #f39c12; margin-bottom: 16px; }
        .no-data h3 { color: #3498db; margin: 20px 0 10px; }
        .no-data pre {
            background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;
            display: inline-block; margin-top: 8px;
        }
        .session-item {
            background: rgba(255,255,255,0.06); padding: 12px 16px;
            border-radius: 8px; margin-bottom: 8px; text-align: left;
            display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
        }
    </style>
</head>
<body>
    <header>
        <h1>${escapeHtml(sessionName)} <span>Epic / Feature / Story Viewer</span></h1>
        ${hasData ? `
        <div class="summary-bar">
            <div class="summary-stat">
                <div class="value">${summary.total_epics || 0}</div>
                <div class="label">Epics</div>
            </div>
            <div class="summary-stat">
                <div class="value">${summary.total_features || 0}</div>
                <div class="label">Features</div>
            </div>
            <div class="summary-stat">
                <div class="value">${summary.total_stories || 0}</div>
                <div class="label">Stories</div>
            </div>
            <div class="summary-stat">
                <div class="value">${summary.total_function_points || 0}</div>
                <div class="label">Function Points</div>
            </div>
            <div class="summary-stat">
                <div class="value">${summary.total_story_points || 0}</div>
                <div class="label">Story Points</div>
            </div>
        </div>
        ` : ''}
    </header>

    ${hasData ? `
    <div class="controls">
        <button onclick="expandAll()">Alles uitklappen</button>
        <button onclick="collapseAll()">Alles inklappen</button>
        <button onclick="expandLevel('epic')">Alleen Epics</button>
        <button onclick="expandLevel('feature')">Epics + Features</button>
    </div>
    ` : ''}

    <div id="epics-container">
        ${epicsHTML}
    </div>

    <script>
        function toggleSection(header) {
            const children = header.parentElement.querySelector('.section-children');
            const icon = header.querySelector('.toggle-icon');
            if (children) {
                const isOpen = children.style.display !== 'none';
                children.style.display = isOpen ? 'none' : 'block';
                icon.classList.toggle('open', !isOpen);
            }
        }

        function expandAll() {
            document.querySelectorAll('.section-children').forEach(el => el.style.display = 'block');
            document.querySelectorAll('.toggle-icon').forEach(el => el.classList.add('open'));
        }

        function collapseAll() {
            document.querySelectorAll('.section-children').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.toggle-icon').forEach(el => el.classList.remove('open'));
        }

        function expandLevel(level) {
            collapseAll();
            // Always expand epics
            document.querySelectorAll('.epic-card > .section-children').forEach(el => el.style.display = 'block');
            document.querySelectorAll('.epic-header .toggle-icon').forEach(el => el.classList.add('open'));

            if (level === 'feature') {
                document.querySelectorAll('.feature-item > .section-children').forEach(el => el.style.display = 'block');
                document.querySelectorAll('.feature-header .toggle-icon').forEach(el => el.classList.add('open'));
            }
        }
    </script>
</body>
</html>`;
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
