const state = { token: sessionStorage.getItem("brandcraft_token"), user: null, authMode: "register", brand: null, interview: null };
const views = ["landing-view", "auth-view", "dashboard-view", "interview-view", "report-view"];

function byId(id) { return document.getElementById(id); }
function escapeHtml(value = "") { return String(value).replace(/[&<>'"]/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" })[char]); }
function showView(id) { views.forEach(view => { byId(view).hidden = view !== id; }); document.body.classList.toggle("brand-dashboard-active", id === "report-view"); window.scrollTo({ top: 0, behavior: "smooth" }); }
function toast(message, error = false) { const el = byId("toast"); el.textContent = message; el.className = `toast show${error ? " error" : ""}`; window.clearTimeout(toast.timer); toast.timer = window.setTimeout(() => { el.className = "toast"; }, 3500); }
function setError(id, message = "") { byId(id).textContent = message; }
function setLoading(button, loading, label) { if (!button) return; button.disabled = loading; button.dataset.label ??= button.textContent; button.textContent = loading ? label : button.dataset.label; }

async function api(path, options = {}) {
  const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) };
  const isAuthRequest = path === "ai/login/" || path === "ai/register/";
  if (state.token && !isAuthRequest) headers.Authorization = `Token ${state.token}`;
  const response = await fetch(`/api/${path}`, { ...options, headers });
  const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && state.token && !isAuthRequest) {
      clearAuth();
      showAuth("login");
    }
    const details = payload && typeof payload === "object" ? Object.values(payload).flat().join(" ") : "";
    throw new Error(details || "Something went wrong. Please try again.");
  }
  return payload;
}

function updateNavigation() {
  document.querySelectorAll("[data-public-only]").forEach(el => { el.hidden = Boolean(state.token); });
  document.querySelectorAll("[data-auth-only]").forEach(el => { el.hidden = !state.token; });
  byId("user-label").hidden = !state.user;
  byId("user-label").textContent = state.user ? state.user.username : "";
}

function clearAuth() {
  state.token = null;
  state.user = null;
  state.brand = null;
  sessionStorage.removeItem("brandcraft_token");
  updateNavigation();
}

function showAuth(mode) {
  state.authMode = mode;
  const login = mode === "login";
  byId("auth-eyebrow").textContent = login ? "WELCOME BACK" : "WELCOME";
  byId("auth-title").textContent = login ? "Continue building your brand." : "Start your brand strategy";
  byId("auth-description").textContent = login ? "Log in to continue where you left off." : "Create an account to save brands and strategy reports.";
  byId("auth-submit").textContent = login ? "Log in" : "Create account";
  byId("auth-switch-copy").textContent = login ? "New to Brandcraft?" : "Already have an account?";
  byId("auth-switch").textContent = login ? "Create an account" : "Log in";
  byId("auth-password").autocomplete = login ? "current-password" : "new-password";
  byId("password-help").hidden = login;
  setError("auth-error");
  byId("auth-form").reset();
  showView("auth-view");
  byId("auth-username").focus();
}

async function submitAuth(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = byId("auth-submit");
  setError("auth-error");
  setLoading(button, true, "Please wait...");
  try {
    const payload = await api(`ai/${state.authMode === "login" ? "login" : "register"}/`, { method: "POST", body: JSON.stringify({ username: form.username.value.trim(), password: form.password.value }) });
    state.token = payload.token;
    state.user = { username: payload.username };
    sessionStorage.setItem("brandcraft_token", state.token);
    updateNavigation();
    toast(state.authMode === "login" ? "Welcome back." : "Your account is ready.");
    await showDashboard();
  } catch (error) { setError("auth-error", error.message); } finally { setLoading(button, false); }
}

async function showDashboard() {
  if (!state.token) return showAuth("login");
  showView("dashboard-view");
  byId("brand-list").innerHTML = "<p class='card-meta'>Loading your brands...</p>";
  try {
    const brands = await api("brands/");
    renderBrands(brands);
  } catch (error) { byId("brand-list").innerHTML = `<p class='form-error'>${escapeHtml(error.message)}</p>`; }
}

function renderBrands(brands) {
  byId("empty-brands").hidden = brands.length > 0;
  byId("brand-list").innerHTML = brands.map(brand => {
    const status = brand.strategy_report ? "Strategy saved" : brand.interview_data.some(item => item.answer) ? "Interview in progress" : "Ready to interview";
    return `<article class="brand-card"><div><p class="card-meta">${escapeHtml(brand.industry)}</p><h2>${escapeHtml(brand.name)}</h2><p>${escapeHtml(brand.description || "No description yet.")}</p></div><div><p class="card-meta">${escapeHtml(status)}</p><button class="button button-quiet" data-action="open-brand" data-brand-id="${brand.id}">${brand.strategy_report ? "Open strategy" : "Continue"} <span aria-hidden="true">-></span></button></div></article>`;
  }).join("");
}

async function submitBrand(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type='submit']");
  setError("brand-error"); setLoading(button, true, "Creating...");
  try {
    const brand = await api("brands/create/", { method: "POST", body: JSON.stringify({ name: form.name.value, industry: form.industry.value, description: form.description.value }) });
    form.reset(); byId("brand-form-panel").hidden = true; toast("Brand created. Let’s shape its direction."); await openInterview(brand);
  } catch (error) { setError("brand-error", error.message); } finally { setLoading(button, false); }
}

async function openBrand(id) {
  try {
    const brand = await api(`brands/${id}/`);
    if (brand.strategy_report) return openReport(brand);
    await openInterview(brand);
  } catch (error) { toast(error.message, true); }
}

async function openInterview(brand) {
  state.brand = brand;
  byId("interview-brand-name").textContent = brand.name;
  byId("interview-question").textContent = "Preparing your first question...";
  byId("generate-report-button").hidden = true;
  byId("answer-form").hidden = false;
  setError("interview-error"); showView("interview-view");
  try { const data = await api("ai/start/", { method: "POST", body: JSON.stringify({ brand_id: brand.id }) }); renderInterview(data); }
  catch (error) { setError("interview-error", error.message); }
}

function renderInterview(data) {
  state.interview = data;
  const completed = data.progress.completed;
  byId("progress-bar").style.width = `${(completed / data.progress.total) * 100}%`;
  byId("progress-copy").textContent = `${completed} of ${data.progress.total} answered`;
  byId("mode-badge").textContent = data.mode === "mock" ? "DEMO MODE" : "LIVE AI";
  byId("question-number").textContent = data.complete ? "INTERVIEW COMPLETE" : `QUESTION ${Math.min(completed + 1, data.progress.total)} OF ${data.progress.total}`;
  byId("interview-question").textContent = data.complete ? "You have given the strategy enough to work with." : data.question;
  byId("answer-form").hidden = data.complete;
  byId("generate-report-button").hidden = !data.complete;
  if (data.complete) byId("generate-report-button").hidden = false;
  byId("interview-answer").value = "";
}

async function submitAnswer(event) {
  event.preventDefault();
  const answer = byId("interview-answer").value.trim();
  if (!answer) return setError("interview-error", "Write a short answer before continuing.");
  const button = event.currentTarget.querySelector("button[type='submit']"); setError("interview-error"); setLoading(button, true, "Saving...");
  try { const data = await api("ai/start/", { method: "POST", body: JSON.stringify({ brand_id: state.brand.id, answer }) }); renderInterview(data); }
  catch (error) { setError("interview-error", error.message); } finally { setLoading(button, false); }
}

async function generateReport() {
  const button = byId("generate-report-button"); setLoading(button, true, "Building strategy..."); setError("interview-error");
  try { const data = await api("ai/report/", { method: "POST", body: JSON.stringify({ brand_id: state.brand.id }) }); openReport({ ...state.brand, ...data, strategy_report: data.report }); toast("Your strategy is saved."); }
  catch (error) { setError("interview-error", error.message); } finally { setLoading(button, false); }
}

async function openReport(brand) {
  state.brand = brand; showView("report-view"); byId("report-content").innerHTML = "<p class='card-meta'>Loading your brand workspace...</p>";
  try {
    let current = brand;
    let data = brand.strategy_data ? { report: brand.strategy_report, strategy_data: brand.strategy_data, mode: brand.report_mode } : await api(`ai/report/${brand.id}/`);
    if ((data.strategy_data.feature_version || 0) < 2) {
      data = await api("ai/report/", { method: "POST", body: JSON.stringify({ brand_id: brand.id }) });
      current = { ...brand, ...data, strategy_report: data.report };
      state.brand = current;
    }
    renderReport(data, current);
  }
  catch (error) { byId("report-content").innerHTML = `<p class='form-error'>${escapeHtml(error.message)}</p>`; }
}

function renderConsistencyCheck(result) {
  if (!result) return "<p class='feature-empty'>Paste real copy above to check voice, audience fit, and claims.</p>";
  return `<div class="guardian-result"><div class="guardian-score"><strong>${Number(result.score) || 0}</strong><span>/ 100</span></div><div><strong>${escapeHtml(result.verdict || "Review complete")}</strong><p>${(result.checks || []).map(item => `<span class="guardian-check ${escapeHtml(item.status)}"><b>${escapeHtml(item.name)}</b> ${escapeHtml(item.detail)}</span>`).join("")}</p></div></div><ul class="guardian-recommendations">${(result.recommendations || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderReport(data, brand = state.brand) {
  const strategy = data.strategy_data || {};
  const name = brand?.name || "Your brand";
  const industry = brand?.industry || "Brand strategy";
  const personality = strategy.personality || [];
  const directions = strategy.directions || [];
  const selected = directions.find(item => item.id === strategy.selected_direction_id) || strategy.selected_direction || null;
  const visual = selected?.visual_direction || strategy.visual_direction || {};
  const launch = selected?.launch_kit || strategy.launch_kit || null;
  const suggestions = strategy.audience_suggestions || [strategy.audience || "Your current audience", `First-time ${industry.toLowerCase()} buyers`, `People looking for ${strategy.core_value_proposition || "a better solution"}`];
  const variants = strategy.audience_variants || [];
  byId("report-mode").textContent = data.mode === "mock" ? "DEMO MODE · YOUR BRAND KIT" : "LIVE AI · YOUR BRAND KIT";
  byId("dashboard-avatar").textContent = name.trim().slice(0, 1).toUpperCase() || "B";
  byId("report-content").innerHTML = `
    <section class="brand-hero dashboard-panel" id="brand-overview"><div class="brand-hero-art" aria-hidden="true"><span>${escapeHtml(name.slice(0, 1).toUpperCase())}</span></div><div class="brand-hero-copy"><p class="dashboard-eyebrow">${escapeHtml(industry)} · FOUNDER-LED POSITIONING</p><h2>${escapeHtml(name)}</h2><p class="brand-hero-description">${escapeHtml(brand?.description || strategy.core_value_proposition || "")}</p><div class="personality-tags">${personality.map(item => `<span>${escapeHtml(item)}</span>`).join("")}</div></div></section>
    <section class="dashboard-panel overview-panel"><div class="panel-heading"><h2>Brand Foundation</h2><button class="panel-link" data-action="edit-brand">Edit</button></div><dl class="overview-list"><div><dt>Core promise</dt><dd>${escapeHtml(strategy.core_value_proposition || strategy.positioning || "Complete the founder interview to define this.")}</dd></div><div><dt>Current audience</dt><dd>${escapeHtml(strategy.audience || "Not set")}</dd></div><div><dt>Founder goal</dt><dd>${escapeHtml((brand?.interview_data || []).map(item => item.answer).filter(Boolean)[5] || "Not set")}</dd></div><div><dt>Voice signals</dt><dd>${personality.map(escapeHtml).join(" · ")}</dd></div></dl></section>
    <section class="feature-panel feature-panel-wide" id="brand-battle"><div class="feature-heading"><div><p class="dashboard-eyebrow">02 · POSITIONING</p><h2>Brand Battle</h2><p>Compare three strategic choices. Each keeps your core value intact and changes how the market should perceive it.</p></div><span class="feature-count">${directions.length} directions</span></div><div class="battle-grid">${directions.length ? directions.map(direction => `<article class="battle-card ${selected?.id === direction.id ? "is-selected" : ""}"><p class="battle-lens">${escapeHtml(direction.lens)}</p><h3>${escapeHtml(direction.title)}</h3><p class="battle-position">${escapeHtml(direction.positioning)}</p><div class="battle-detail"><span>VOICE</span><p>${escapeHtml(direction.voice)}</p></div><div class="battle-tradeoffs"><p><b>Edge</b> ${escapeHtml(direction.strength)}</p><p><b>Watch</b> ${escapeHtml(direction.tradeoff)}</p></div><button class="dashboard-button ${selected?.id === direction.id ? "primary" : ""}" data-action="select-direction" data-direction-id="${escapeHtml(direction.id)}">${selected?.id === direction.id ? "Selected" : "Build this direction"}</button></article>`).join("") : `<p class="feature-empty">Complete the interview to generate brand directions from your product, audience, and constraints.</p>`}</div></section>
    <section class="feature-panel" id="audience-shifter"><div class="feature-heading"><div><p class="dashboard-eyebrow">03 · SEGMENT TESTING</p><h2>Audience Shifter</h2><p>Hold the same promise constant. Change the audience, angle, and tone.</p></div></div><form id="audience-form" class="feature-form"><label>Audience A<input name="audience" value="${escapeHtml(suggestions[0] || "")}" maxlength="140" required></label><label>Audience B<input name="audience" value="${escapeHtml(suggestions[1] || "")}" maxlength="140" required></label><label>Audience C<input name="audience" value="${escapeHtml(suggestions[2] || "")}" maxlength="140"></label><p class="form-error" id="audience-error" role="alert"></p><button class="dashboard-button primary" type="submit">Compare audiences</button></form><div class="audience-results">${variants.length ? variants.map(item => `<article><span>${escapeHtml(item.tone || item.angle || "Audience")}</span><h3>${escapeHtml(item.segment)}</h3><p class="audience-headline">${escapeHtml(item.headline)}</p><p>${escapeHtml(item.message)}</p><small>UNCHANGED VALUE · ${escapeHtml(item.core_value_proposition || strategy.core_value_proposition || "")}</small></article>`).join("") : `<p class="feature-empty">Run a comparison to see the same offer reframed for each segment.</p>`}</div></section>
    <section class="feature-panel" id="consistency-guardian"><div class="feature-heading"><div><p class="dashboard-eyebrow">04 · CONTENT REVIEW</p><h2>Consistency Guardian</h2><p>Check a real caption, ad, or website paragraph against your selected voice.</p></div></div><form id="consistency-form" class="feature-form"><label for="consistency-copy">Content to review</label><textarea id="consistency-copy" name="content" rows="5" maxlength="5000" placeholder="Paste a caption, ad, or website paragraph to review." required></textarea><p class="form-error" id="consistency-error" role="alert"></p><button class="dashboard-button primary" type="submit">Check this content</button></form><div id="consistency-result" class="consistency-result">${renderConsistencyCheck(strategy.consistency_check)}</div></section>
    <section class="feature-panel feature-panel-wide" id="visual-direction"><div class="feature-heading"><div><p class="dashboard-eyebrow">05 · VISUAL SYSTEM</p><h2>Visual Direction Generator</h2><p>Palette, type, shape language, imagery, and logo concepts generated for the direction you chose.</p></div></div>${selected ? `<div class="visual-system"><div class="visual-palette">${(visual.palette || []).map(color => `<article><span style="--swatch:${escapeHtml(color.hex)}"></span><b>${escapeHtml(color.name)}</b><small>${escapeHtml(color.hex)}</small></article>`).join("")}</div><div class="visual-specs"><article><small>TYPOGRAPHY</small><p>${escapeHtml(visual.typography || selected.typography || "")}</p></article><article><small>SHAPE LANGUAGE</small><p>${escapeHtml(visual.shapes || selected.shape_language || "")}</p></article><article><small>IMAGERY DIRECTION</small><p>${escapeHtml(visual.imagery || "")}</p></article></div><div class="logo-direction-grid">${(visual.logo_concepts || []).map(item => `<article><span>${escapeHtml(item.name)}</span><p>${escapeHtml(item.description)}</p></article>`).join("")}</div></div>` : `<p class="feature-empty">Choose a Brand Battle direction to generate its visual system.</p>`}</section>
    <section class="feature-panel feature-panel-wide" id="launch-kit"><div class="feature-heading"><div><p class="dashboard-eyebrow">06 · FOUNDER TO LAUNCH</p><h2>Launch Kit</h2><p>Practical messaging and launch actions drawn from your selected strategy.</p></div>${launch ? `<button class="dashboard-button" data-action="export-brand">Export PDF</button>` : ""}</div>${launch ? `<div class="launch-kit-grid"><article class="launch-message"><small>WEBSITE HEADLINE</small><h3>${escapeHtml(launch.website_headline)}</h3><p>${escapeHtml(launch.website_subhead)}</p><strong>${escapeHtml(launch.primary_cta)}</strong></article><article><small>LAUNCH IDEAS</small><ol>${(launch.launch_ideas || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol></article><article><small>FIRST WEEK</small><ol>${(launch.first_week || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol></article></div><div class="social-post-grid">${(launch.social_posts || []).map(item => `<article><small>${escapeHtml(item.channel)}</small><p>${escapeHtml(item.copy)}</p><button class="panel-link" data-action="copy-text" data-copy-text="${escapeHtml(item.copy)}">Copy post</button></article>`).join("")}</div>` : `<p class="feature-empty">Select a direction to generate launch messaging, social posts, and a first-week plan.</p>`}</section>`;
}

async function selectBrandDirection(directionId) {
  try {
    const data = await api("ai/directions/select/", { method: "POST", body: JSON.stringify({ brand_id: state.brand.id, direction_id: directionId }) });
    state.brand.strategy_data = data.strategy_data;
    renderReport({ strategy_data: data.strategy_data, mode: state.brand.report_mode }, state.brand);
    toast("Direction selected. Visuals and launch copy updated.");
  } catch (error) { toast(error.message); }
}

async function compareAudiences(form) {
  const audiences = Array.from(form.querySelectorAll("input[name='audience']"), input => input.value.trim()).filter(Boolean);
  const button = form.querySelector("button[type='submit']");
  setError("audience-error"); setLoading(button, true, "Comparing...");
  try {
    const data = await api("ai/audience-shifts/", { method: "POST", body: JSON.stringify({ brand_id: state.brand.id, audiences }) });
    state.brand.strategy_data.audience_variants = data.variants;
    renderReport({ strategy_data: state.brand.strategy_data, mode: state.brand.report_mode }, state.brand);
  } catch (error) { setError("audience-error", error.message); }
  finally { setLoading(button, false); }
}

async function reviewConsistency(form) {
  const content = form.elements.content.value.trim();
  const button = form.querySelector("button[type='submit']");
  setError("consistency-error"); setLoading(button, true, "Reviewing...");
  try {
    const result = await api("ai/consistency-check/", { method: "POST", body: JSON.stringify({ brand_id: state.brand.id, content }) });
    state.brand.strategy_data.consistency_check = result;
    renderReport({ strategy_data: state.brand.strategy_data, mode: state.brand.report_mode }, state.brand);
  } catch (error) { setError("consistency-error", error.message); }
  finally { setLoading(button, false); }
}

function openBrandEditor() {
  const form = byId("brand-edit-form");
  form.elements.name.value = state.brand?.name || "";
  form.elements.industry.value = state.brand?.industry || "";
  form.elements.description.value = state.brand?.description || "";
  setError("brand-edit-error");
  byId("brand-edit-dialog").showModal();
}

async function saveBrandEdit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type='submit']");
  setError("brand-edit-error");
  setLoading(button, true, "Saving...");
  try {
    const updated = await api(`brands/${state.brand.id}/`, {
      method: "PATCH",
      body: JSON.stringify({ name: form.elements.name.value.trim(), industry: form.elements.industry.value.trim(), description: form.elements.description.value.trim() }),
    });
    state.brand = { ...state.brand, ...updated };
    renderReport({ strategy_data: state.brand.strategy_data, mode: state.brand.report_mode }, state.brand);
    byId("brand-edit-dialog").close();
    toast("Brand details saved.");
  } catch (error) {
    setError("brand-edit-error", error.message);
  } finally {
    setLoading(button, false);
  }
}

function exportBrandKit() { window.print(); }

async function logout(showMessage = true) { try { if (state.token) await api("ai/logout/", { method: "POST" }); } catch (_) {} clearAuth(); showView("landing-view"); if (showMessage) toast("You have been logged out."); }

document.addEventListener("click", event => {
  const element = event.target.closest("[data-action]"); const action = element?.dataset.action; if (!action) return;
  if (action === "home") { event.preventDefault(); showView("landing-view"); }
  if (action === "show-login") showAuth("login"); if (action === "show-register") showAuth("register"); if (action === "show-dashboard") showDashboard(); if (action === "logout") logout();
  if (action === "show-brand-form") byId("brand-form-panel").hidden = false; if (action === "hide-brand-form") byId("brand-form-panel").hidden = true;
  if (action === "open-brand") openBrand(element.dataset.brandId); if (action === "restart-interview" && state.brand) openInterview(state.brand);
  if (action === "edit-brand") openBrandEditor(); if (action === "close-edit") byId("brand-edit-dialog").close(); if (action === "export-brand") exportBrandKit(); if (action === "brand-notice") toast("Your brand strategy is ready.");
  if (action === "select-direction" && state.brand) selectBrandDirection(element.dataset.directionId);
  if (action === "dashboard-section") { const target = byId(element.dataset.target); target?.scrollIntoView({ behavior: "smooth", block: "start" }); document.querySelectorAll(".brand-step[aria-current='step']").forEach(step => { step.classList.remove("current"); step.removeAttribute("aria-current"); }); element.classList.add("current"); element.setAttribute("aria-current", "step"); }
  if (action === "copy-text") navigator.clipboard?.writeText(element.dataset.copyText || "").then(() => toast("Copied to clipboard.")).catch(() => toast("Clipboard access is unavailable."));
});
document.addEventListener("submit", event => { if (event.target.id === "audience-form") { event.preventDefault(); compareAudiences(event.target); } if (event.target.id === "consistency-form") { event.preventDefault(); reviewConsistency(event.target); } });
byId("auth-form").addEventListener("submit", submitAuth); byId("auth-switch").addEventListener("click", () => showAuth(state.authMode === "login" ? "register" : "login")); byId("brand-form").addEventListener("submit", submitBrand); byId("answer-form").addEventListener("submit", submitAnswer); byId("generate-report-button").addEventListener("click", generateReport);
byId("brand-edit-form").addEventListener("submit", saveBrandEdit);
(async function init() { updateNavigation(); if (!state.token) return; try { state.user = await api("ai/me/"); updateNavigation(); await showDashboard(); } catch (_) {} })();
