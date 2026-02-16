/* ==================== State ==================== */
let cvData = {};
let themes = [];
let selectedTheme = 'classic';
let saveTimeout = null;
let isSaving = false;

/* ==================== API ==================== */
const api = {
  async get(path) {
    const res = await fetch(path);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res;
  },

  async post(path, body) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res;
  },

  async getCv() {
    const res = await this.get('/api/cv');
    return res.json();
  },

  async saveCv(data) {
    const res = await this.post('/api/cv', data);
    return res.json();
  },

  async getThemes() {
    const res = await this.get('/api/themes');
    return res.json();
  },

  async build(theme, lang) {
    const body = {};
    if (theme) body.theme = theme;
    if (lang) body.lang = lang;
    const res = await this.post('/api/build', body);
    return res.json();
  },

  async validate(data) {
    const res = await this.post('/api/validate', data);
    return res.json();
  },

  async initProject() {
    const res = await this.post('/api/init', {});
    return res.json();
  },

  async getStatus() {
    const res = await this.get('/api/status');
    return res.json();
  },
};

/* ==================== Navigation ==================== */
function setPage(pageName) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById('page-' + pageName);
  if (page) page.classList.add('active');

  const navItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
  if (navItem) navItem.classList.add('active');

  const titles = {
    editor: 'CV Editor',
    preview: 'Preview',
    themes: 'Themes',
    build: 'Build & Download',
    export: 'Export',
    ai: 'AI Tools',
    import: 'Import',
    settings: 'Settings',
  };
  document.getElementById('page-title').textContent = titles[pageName] || 'resumake';

  if (pageName === 'preview') refreshPreview();
  if (pageName === 'themes') renderThemes();
  if (pageName === 'build' || pageName === 'ai') populateAllThemeSelects();
  if (pageName === 'settings') loadSettings();
}

/* ==================== Save Status ==================== */
function updateSaveStatus(status, text) {
  const dot = document.querySelector('.status-dot');
  const label = document.querySelector('.status-text');
  dot.className = 'status-dot ' + (status || '');
  label.textContent = text || 'Saved';
}

/* ==================== Toast Notifications ==================== */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ==================== Loading ==================== */
function showLoading(text) {
  document.getElementById('loading-text').textContent = text || 'Loading...';
  document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
  document.getElementById('loading-overlay').style.display = 'none';
}

/* ==================== Section Toggle ==================== */
function toggleSection(name) {
  const section = document.getElementById('section-' + name);
  if (section) section.classList.toggle('collapsed');
}

/* ==================== Data Helpers ==================== */
function getNestedValue(obj, path) {
  return path.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : '', obj);
}

function setNestedValue(obj, path, value) {
  const keys = path.split('.');
  let current = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (current[key] === undefined || current[key] === null) {
      current[key] = isNaN(keys[i + 1]) ? {} : [];
    }
    current = current[key];
  }
  current[keys[keys.length - 1]] = value;
}

/* ==================== Auto-Save ==================== */
function scheduleSave() {
  clearTimeout(saveTimeout);
  updateSaveStatus('saving', 'Saving...');
  saveTimeout = setTimeout(async () => {
    try {
      isSaving = true;
      await api.saveCv(cvData);
      updateSaveStatus('', 'Saved');
    } catch (e) {
      updateSaveStatus('error', 'Save failed');
      showToast('Failed to save: ' + e.message, 'error');
    } finally {
      isSaving = false;
      saveTimeout = null;
    }
  }, 800);
}

async function saveNow() {
  clearTimeout(saveTimeout);
  saveTimeout = null;
  updateSaveStatus('saving', 'Saving...');
  try {
    await api.saveCv(cvData);
    updateSaveStatus('', 'Saved');
    showToast('CV saved successfully', 'success');
  } catch (e) {
    updateSaveStatus('error', 'Save failed');
    showToast('Failed to save: ' + e.message, 'error');
  }
}

/* ==================== Validate ==================== */
async function validateCV() {
  try {
    const result = await api.validate(cvData);
    if (result.valid) {
      dismissValidation();
      showToast('CV is valid! No errors found.', 'success');
    } else {
      showValidationErrors(result.errors);
      showToast(`${result.errors.length} validation error(s) found.`, 'error');
    }
  } catch (e) {
    showToast('Validation failed: ' + e.message, 'error');
  }
}

function showValidationErrors(errors) {
  const banner = document.getElementById('validation-banner');
  const list = document.getElementById('validation-errors');
  list.innerHTML = '';
  errors.forEach(e => {
    const li = document.createElement('li');
    li.innerHTML = e.field
      ? `<strong>${escHtml(e.field)}:</strong> ${escHtml(e.message)}`
      : escHtml(e.message);
    list.appendChild(li);
  });
  banner.style.display = 'block';
}

function dismissValidation() {
  document.getElementById('validation-banner').style.display = 'none';
}

/* ==================== Form Binding ==================== */
function bindSimpleInputs() {
  document.querySelectorAll('[data-path]').forEach(input => {
    const path = input.getAttribute('data-path');
    const value = getNestedValue(cvData, path);
    input.value = value || '';

    input.addEventListener('input', () => {
      setNestedValue(cvData, path, input.value);
      scheduleSave();
    });
  });
}

/* ==================== Skills Editor ==================== */
function bindSkillsInputs() {
  const technicalInput = document.getElementById('skills-technical');
  const leadershipInput = document.getElementById('skills-leadership');

  if (!cvData.skills) cvData.skills = {};

  technicalInput.value = (cvData.skills.technical || []).join(', ');
  leadershipInput.value = (cvData.skills.leadership || []).join(', ');

  technicalInput.addEventListener('input', () => {
    cvData.skills.technical = technicalInput.value.split(',').map(s => s.trim()).filter(Boolean);
    scheduleSave();
  });

  leadershipInput.addEventListener('input', () => {
    cvData.skills.leadership = leadershipInput.value.split(',').map(s => s.trim()).filter(Boolean);
    scheduleSave();
  });

  renderLanguages();
}

/* ==================== Language List ==================== */
function renderLanguages() {
  const container = document.getElementById('languages-list');
  if (!cvData.skills) cvData.skills = {};
  if (!cvData.skills.languages) cvData.skills.languages = [];

  container.innerHTML = '';
  cvData.skills.languages.forEach((lang, idx) => {
    container.innerHTML += `
      <div class="list-item">
        <div class="list-item-header">
          <span class="list-item-title">${escHtml(lang.name || 'New Language')}</span>
          <div class="list-item-actions">
            <button class="btn-remove" onclick="removeLanguage(${idx})" title="Remove">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Language</label>
            <input type="text" value="${escHtml(lang.name || '')}" onchange="updateLanguage(${idx}, 'name', this.value)">
          </div>
          <div class="form-group">
            <label>Level</label>
            <select onchange="updateLanguage(${idx}, 'level', this.value)">
              <option value="native" ${lang.level === 'native' ? 'selected' : ''}>Native</option>
              <option value="fluent" ${lang.level === 'fluent' ? 'selected' : ''}>Fluent</option>
              <option value="professional" ${lang.level === 'professional' ? 'selected' : ''}>Professional</option>
              <option value="basic" ${lang.level === 'basic' ? 'selected' : ''}>Basic</option>
            </select>
          </div>
        </div>
      </div>
    `;
  });
}

function updateLanguage(idx, field, value) {
  cvData.skills.languages[idx][field] = value;
  scheduleSave();
  renderLanguages();
}

function removeLanguage(idx) {
  if (!confirm('Remove this language?')) return;
  cvData.skills.languages.splice(idx, 1);
  scheduleSave();
  renderLanguages();
}

/* ==================== Generic List Editors ==================== */
function renderListSection(section) {
  const container = document.getElementById(section + '-list');
  if (!container) return;
  const items = cvData[section] || [];
  container.innerHTML = '';

  items.forEach((item, idx) => {
    const html = buildListItemHtml(section, item, idx);
    container.innerHTML += html;
  });
}

function buildListItemHtml(section, item, idx) {
  const titleDisplay = getItemTitle(section, item) || `Item ${idx + 1}`;

  let fieldsHtml = '';
  const fields = getFieldsForSection(section);

  fields.forEach(field => {
    if (field.type === 'bullets') {
      fieldsHtml += buildBulletsHtml(section, idx, item.bullets || []);
    } else if (field.fullWidth) {
      fieldsHtml += `
        <div class="form-group">
          <label>${field.label}</label>
          ${field.type === 'textarea'
            ? `<textarea rows="2" onchange="updateListItem('${section}', ${idx}, '${field.key}', this.value)">${escHtml(item[field.key] || '')}</textarea>`
            : `<input type="${field.type || 'text'}" value="${escHtml(String(item[field.key] ?? ''))}" onchange="updateListItem('${section}', ${idx}, '${field.key}', this.value)">`
          }
        </div>
      `;
    } else {
      fieldsHtml += `
        <div class="form-group">
          <label>${field.label}</label>
          <input type="${field.type || 'text'}" value="${escHtml(String(item[field.key] ?? ''))}" onchange="updateListItem('${section}', ${idx}, '${field.key}', this.value)">
        </div>
      `;
    }
  });

  return `
    <div class="list-item">
      <div class="list-item-header">
        <span class="list-item-title">${escHtml(titleDisplay)}</span>
        <div class="list-item-actions">
          <button class="btn-remove" onclick="removeListItem('${section}', ${idx})" title="Remove">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>
      <div class="form-row">${fieldsHtml}</div>
    </div>
  `;
}

function getItemTitle(section, item) {
  switch (section) {
    case 'experience': return item.title ? `${item.title}${item.org ? ' — ' + item.org : ''}` : '';
    case 'education': return item.degree ? `${item.degree}${item.institution ? ', ' + item.institution : ''}` : '';
    case 'certifications': return item.name || '';
    case 'volunteering': return item.title ? `${item.title}${item.org ? ' — ' + item.org : ''}` : '';
    case 'testimonials': return item.name ? `${item.name}${item.org ? ' — ' + item.org : ''}` : '';
    case 'publications': return item.title || '';
    case 'links': return item.label || '';
    default: return item.title || item.name || item.label || '';
  }
}

function getFieldsForSection(section) {
  switch (section) {
    case 'links':
      return [
        { key: 'label', label: 'Label', type: 'text' },
        { key: 'url', label: 'URL', type: 'url' },
      ];
    case 'experience':
      return [
        { key: 'title', label: 'Job Title', type: 'text' },
        { key: 'org', label: 'Organization', type: 'text' },
        { key: 'start', label: 'Start Date', type: 'text' },
        { key: 'end', label: 'End Date', type: 'text' },
        { key: 'description', label: 'Description', type: 'textarea', fullWidth: true },
        { type: 'bullets' },
      ];
    case 'education':
      return [
        { key: 'degree', label: 'Degree', type: 'text' },
        { key: 'institution', label: 'Institution', type: 'text' },
        { key: 'start', label: 'Start Year', type: 'text' },
        { key: 'end', label: 'End Year', type: 'text' },
        { key: 'description', label: 'Description', type: 'textarea', fullWidth: true },
        { key: 'details', label: 'Details', type: 'textarea', fullWidth: true },
      ];
    case 'certifications':
      return [
        { key: 'name', label: 'Certification Name', type: 'text' },
        { key: 'org', label: 'Issuing Organization', type: 'text' },
        { key: 'start', label: 'Start', type: 'text' },
        { key: 'end', label: 'End / Expiry', type: 'text' },
        { key: 'description', label: 'Description', type: 'textarea', fullWidth: true },
      ];
    case 'volunteering':
      return [
        { key: 'title', label: 'Role', type: 'text' },
        { key: 'org', label: 'Organization', type: 'text' },
        { key: 'start', label: 'Start Date', type: 'text' },
        { key: 'end', label: 'End Date', type: 'text' },
        { key: 'description', label: 'Description', type: 'textarea', fullWidth: true },
      ];
    case 'testimonials':
      return [
        { key: 'name', label: 'Name', type: 'text' },
        { key: 'role', label: 'Role', type: 'text' },
        { key: 'org', label: 'Organization', type: 'text' },
        { key: 'quote', label: 'Quote', type: 'textarea', fullWidth: true },
      ];
    case 'publications':
      return [
        { key: 'title', label: 'Title', type: 'text' },
        { key: 'venue', label: 'Venue / Journal', type: 'text' },
        { key: 'year', label: 'Year', type: 'number' },
      ];
    default:
      return [];
  }
}

function buildBulletsHtml(section, itemIdx, bullets) {
  let html = '<div class="form-group" style="grid-column:1/-1"><label>Key Achievements</label><div class="bullets-editor">';
  bullets.forEach((bullet, bIdx) => {
    html += `
      <div class="bullet-item">
        <input type="text" value="${escHtml(bullet)}" onchange="updateBullet('${section}', ${itemIdx}, ${bIdx}, this.value)">
        <button class="btn-remove" onclick="removeBullet('${section}', ${itemIdx}, ${bIdx})" title="Remove">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    `;
  });
  html += `</div><button class="btn btn-sm btn-ghost" onclick="addBullet('${section}', ${itemIdx})" style="margin-top:4px">+ Add Bullet</button></div>`;
  return html;
}

/* ==================== List CRUD ==================== */
function addListItem(section, template) {
  if (section === 'skills.languages') {
    if (!cvData.skills) cvData.skills = {};
    if (!cvData.skills.languages) cvData.skills.languages = [];
    cvData.skills.languages.push({ ...template });
    renderLanguages();
  } else {
    if (!cvData[section]) cvData[section] = [];
    cvData[section].push({ ...template });
    renderListSection(section);
  }
  scheduleSave();
}

function removeListItem(section, idx) {
  if (!cvData[section]) return;
  if (!confirm('Remove this item?')) return;
  cvData[section].splice(idx, 1);
  renderListSection(section);
  scheduleSave();
}

function updateListItem(section, idx, key, value) {
  if (!cvData[section] || !cvData[section][idx]) return;
  if (key === 'year') {
    cvData[section][idx][key] = parseInt(value) || 0;
  } else {
    cvData[section][idx][key] = value;
  }
  scheduleSave();
  // Update title in header
  const container = document.getElementById(section + '-list');
  if (container) {
    const items = container.querySelectorAll('.list-item');
    if (items[idx]) {
      const titleEl = items[idx].querySelector('.list-item-title');
      if (titleEl) {
        titleEl.textContent = getItemTitle(section, cvData[section][idx]) || `Item ${idx + 1}`;
      }
    }
  }
}

/* ==================== Bullet CRUD ==================== */
function addBullet(section, itemIdx) {
  if (!cvData[section][itemIdx].bullets) cvData[section][itemIdx].bullets = [];
  cvData[section][itemIdx].bullets.push('');
  renderListSection(section);
  scheduleSave();
}

function removeBullet(section, itemIdx, bulletIdx) {
  if (!confirm('Remove this bullet?')) return;
  cvData[section][itemIdx].bullets.splice(bulletIdx, 1);
  renderListSection(section);
  scheduleSave();
}

function updateBullet(section, itemIdx, bulletIdx, value) {
  cvData[section][itemIdx].bullets[bulletIdx] = value;
  scheduleSave();
}

/* ==================== Photo Upload ==================== */
const MAX_PHOTO_SIZE = 5 * 1024 * 1024; // 5MB

async function uploadPhoto(input) {
  const file = input.files[0];
  if (!file) return;

  if (file.size > MAX_PHOTO_SIZE) {
    showToast('Photo must be smaller than 5MB.', 'error');
    input.value = '';
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    showLoading('Uploading photo...');
    const res = await fetch('/api/upload-photo', { method: 'POST', body: formData });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Upload failed');

    cvData.photo = result.filename;
    renderPhotoPreview();
    showToast('Photo uploaded successfully', 'success');
  } catch (e) {
    showToast('Upload failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

function renderPhotoPreview() {
  const el = document.getElementById('photo-preview');
  if (cvData.photo) {
    el.innerHTML = `<img src="/api/assets/${encodeURIComponent(cvData.photo)}" alt="Profile photo">`;
    el.style.borderColor = 'var(--color-primary)';
    el.style.borderStyle = 'solid';
  } else {
    el.innerHTML = `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
    el.style.borderColor = '';
    el.style.borderStyle = '';
  }
}

/* ==================== Preview ==================== */
async function refreshPreview() {
  // Flush any pending auto-save so the preview reflects latest edits
  clearTimeout(saveTimeout);
  saveTimeout = null;
  try {
    await api.saveCv(cvData);
    updateSaveStatus('', 'Saved');
  } catch (e) {
    // Continue to show preview even if save fails
  }

  const theme = document.getElementById('preview-theme')?.value || '';
  const lang = document.getElementById('preview-lang')?.value || 'en';
  const frame = document.getElementById('preview-frame');

  let url = '/api/preview?lang=' + encodeURIComponent(lang);
  if (theme) url += '&theme=' + encodeURIComponent(theme);

  frame.src = url;
}

/* ==================== Themes ==================== */
function renderThemes() {
  const grid = document.getElementById('themes-grid');
  grid.innerHTML = '';

  themes.forEach(theme => {
    const colors = theme.colors || {};
    const fonts = theme.fonts || {};
    const name = theme.name || 'unknown';
    const isSelected = name === selectedTheme;
    const escapedName = escHtml(name);
    const safeName = name.replace(/'/g, "\\'");

    grid.innerHTML += `
      <div class="theme-card ${isSelected ? 'selected' : ''}" onclick="selectTheme('${safeName}')">
        <div class="theme-name">${escapedName}</div>
        <div class="theme-colors">
          <div class="theme-swatch" style="background:#${escHtml(colors.primary || '333')}" data-label="Primary"></div>
          <div class="theme-swatch" style="background:#${escHtml(colors.accent || '666')}" data-label="Accent"></div>
          <div class="theme-swatch" style="background:#${escHtml(colors.text_light || 'fff')}" data-label="Light"></div>
          <div class="theme-swatch" style="background:#${escHtml(colors.text_muted || '999')}" data-label="Muted"></div>
          <div class="theme-swatch" style="background:#${escHtml(colors.text_body || '333')}" data-label="Body"></div>
        </div>
        <div class="theme-meta">
          <strong>Fonts:</strong> ${escHtml(fonts.heading || 'Default')} / ${escHtml(fonts.body || 'Default')}
        </div>
      </div>
    `;
  });
}

function selectTheme(name) {
  selectedTheme = name;
  renderThemes();
  syncThemeSelects();
  showToast(`Theme set to "${name}"`, 'info');
}

function syncThemeSelects() {
  ['preview-theme', 'build-theme'].forEach(id => {
    const select = document.getElementById(id);
    if (select) select.value = selectedTheme;
  });
}

/* ==================== Build ==================== */
async function buildCV() {
  const btn = document.getElementById('btn-build');
  const resultDiv = document.getElementById('build-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;margin:0"></span> Building...';

  try {
    // Save first
    await api.saveCv(cvData);
    const theme = document.getElementById('build-theme')?.value || '';
    const lang = document.getElementById('build-lang')?.value || 'en';
    const result = await api.build(theme, lang);

    resultDiv.className = 'build-result';
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <strong>Build successful!</strong><br>
      <span style="color:var(--text-secondary)">${escHtml(result.filename)} (${escHtml(result.size)})</span><br>
      <a href="/api/download/${encodeURIComponent(result.filename)}" download>Download ${escHtml(result.filename)}</a>
    `;
    showToast('CV built successfully!', 'success');
  } catch (e) {
    resultDiv.className = 'build-result error';
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `<strong>Build failed:</strong> ${escHtml(e.message)}`;
    showToast('Build failed: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Build & Download
    `;
  }
}

/* ==================== Export ==================== */
async function exportCV(format) {
  try {
    showLoading('Exporting as ' + format.toUpperCase() + '...');
    await api.saveCv(cvData);

    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(err.detail);
    }

    const blob = await res.blob();
    const disposition = res.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `cv.${format}`;

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`Exported as ${format.toUpperCase()}`, 'success');
  } catch (e) {
    showToast('Export failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

/* ==================== Utility ==================== */
function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/* ==================== Populate Theme Selects ==================== */
function populateAllThemeSelects() {
  ['preview-theme', 'build-theme', 'ai-tailor-theme', 'ai-cover-theme', 'ai-bio-theme'].forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = '<option value="">(Default — Classic)</option>';
    themes.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name.charAt(0).toUpperCase() + t.name.slice(1);
      if (t.name === selectedTheme) opt.selected = true;
      select.appendChild(opt);
    });
  });
}

/* ==================== Custom Sections ==================== */
const KNOWN_KEYS = new Set([
  'name', 'title', 'photo', 'contact', 'links', 'skills', 'profile',
  'testimonials', 'experience', 'education', 'volunteering', 'references',
  'certifications', 'publications',
]);

function getCustomSections() {
  const sections = {};
  for (const [key, value] of Object.entries(cvData)) {
    if (!KNOWN_KEYS.has(key) && Array.isArray(value)) {
      sections[key] = value;
    }
  }
  return sections;
}

function renderCustomSections() {
  const container = document.getElementById('custom-sections-container');
  if (!container) return;
  container.innerHTML = '';

  const custom = getCustomSections();
  for (const [sectionKey, items] of Object.entries(custom)) {
    const displayName = sectionKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const sectionId = 'custom-' + sectionKey;

    // Infer fields from the first item, or use a generic title/description
    let fields = [];
    if (items.length > 0) {
      fields = Object.keys(items[0]).map(k => ({
        key: k,
        label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        type: (typeof items[0][k] === 'string' && items[0][k].length > 80) ? 'textarea' : 'text',
        fullWidth: typeof items[0][k] === 'string' && items[0][k].length > 80,
      }));
    }

    let itemsHtml = '';
    items.forEach((item, idx) => {
      const title = escHtml(item.title || item.name || item.label || `Item ${idx + 1}`);
      let fieldsHtml = '';
      fields.forEach(field => {
        if (field.fullWidth) {
          fieldsHtml += `
            <div class="form-group">
              <label>${escHtml(field.label)}</label>
              <textarea rows="2" onchange="updateCustomItem('${sectionKey}', ${idx}, '${field.key}', this.value)">${escHtml(String(item[field.key] ?? ''))}</textarea>
            </div>`;
        } else {
          fieldsHtml += `
            <div class="form-group">
              <label>${escHtml(field.label)}</label>
              <input type="text" value="${escHtml(String(item[field.key] ?? ''))}" onchange="updateCustomItem('${sectionKey}', ${idx}, '${field.key}', this.value)">
            </div>`;
        }
      });

      itemsHtml += `
        <div class="list-item">
          <div class="list-item-header">
            <span class="list-item-title">${title}</span>
            <div class="list-item-actions">
              <button class="btn-remove" onclick="removeCustomItem('${sectionKey}', ${idx})" title="Remove">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="form-row">${fieldsHtml}</div>
        </div>`;
    });

    container.innerHTML += `
      <section class="card" id="section-${sectionId}">
        <div class="card-header" onclick="toggleSection('${sectionId}')">
          <h2>${escHtml(displayName)}</h2>
          <svg class="chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div class="card-body">
          <div class="list-editor">${itemsHtml}</div>
          <button class="btn btn-sm btn-ghost btn-add" onclick="addCustomItem('${sectionKey}')">+ Add ${escHtml(displayName)} Item</button>
        </div>
      </section>`;
  }
}

function updateCustomItem(section, idx, key, value) {
  if (cvData[section] && cvData[section][idx]) {
    cvData[section][idx][key] = value;
    scheduleSave();
  }
}

function removeCustomItem(section, idx) {
  if (!cvData[section]) return;
  if (!confirm('Remove this item?')) return;
  cvData[section].splice(idx, 1);
  renderCustomSections();
  scheduleSave();
}

function addCustomItem(section) {
  if (!cvData[section] || cvData[section].length === 0) return;
  // Clone the structure from the first item with empty values
  const template = {};
  for (const key of Object.keys(cvData[section][0])) {
    template[key] = '';
  }
  cvData[section].push(template);
  renderCustomSections();
  scheduleSave();
}

/* ==================== Render All Lists ==================== */
function renderAllLists() {
  ['links', 'experience', 'education', 'certifications', 'volunteering', 'testimonials', 'publications'].forEach(section => {
    renderListSection(section);
  });
  renderCustomSections();
}

/* ==================== AI Tools ==================== */
function getJobDescription() {
  const jd = document.getElementById('ai-job-description')?.value?.trim();
  if (!jd) {
    showToast('Please enter a job description first.', 'warning');
    return null;
  }
  return jd;
}

function showAiResult(id, html) {
  const el = document.getElementById(id);
  el.innerHTML = html;
  el.style.display = 'block';
}

async function runTailor() {
  const jd = getJobDescription();
  if (!jd) return;

  const theme = document.getElementById('ai-tailor-theme')?.value || '';
  const lang = document.getElementById('ai-tailor-lang')?.value || 'en';

  try {
    showLoading('Tailoring CV...');
    await api.saveCv(cvData);
    const res = await api.post('/api/tailor/build', {
      job_description: jd,
      lang,
      theme: theme || null,
    });
    const result = await res.json();
    showAiResult('tailor-result', `
      <strong>Tailored CV ready!</strong><br>
      <a href="${escHtml(result.download)}" download>${escHtml(result.filename)}</a>
    `);
    showToast('CV tailored successfully!', 'success');
  } catch (e) {
    showAiResult('tailor-result', `<strong>Error:</strong> ${escHtml(e.message)}`);
    showToast('Tailor failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runCoverLetter() {
  const jd = getJobDescription();
  if (!jd) return;

  const theme = document.getElementById('ai-cover-theme')?.value || '';
  const lang = document.getElementById('ai-cover-lang')?.value || 'en';

  try {
    showLoading('Generating cover letter...');
    await api.saveCv(cvData);
    const res = await api.post('/api/cover-letter/build', {
      job_description: jd,
      lang,
      theme: theme || null,
    });
    const result = await res.json();
    showAiResult('cover-result', `
      <strong>Cover letter ready!</strong><br>
      <a href="${escHtml(result.download)}" download>${escHtml(result.filename)}</a>
    `);
    showToast('Cover letter generated!', 'success');
  } catch (e) {
    showAiResult('cover-result', `<strong>Error:</strong> ${escHtml(e.message)}`);
    showToast('Cover letter failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runATS() {
  const jd = getJobDescription();
  if (!jd) return;

  try {
    showLoading('Analyzing ATS keywords...');
    await api.saveCv(cvData);
    const res = await api.post('/api/ats', { job_description: jd });
    const result = await res.json();

    let html = '<strong>ATS Analysis</strong>';
    if (result.score !== undefined) {
      html += `<div class="ats-score">Match Score: <strong>${escHtml(String(result.score))}%</strong></div>`;
    }
    if (result.matched && result.matched.length) {
      html += `<div class="ats-section"><strong>Matched Keywords:</strong><div class="ats-tags matched">`;
      result.matched.forEach(k => { html += `<span class="ats-tag matched">${escHtml(k)}</span>`; });
      html += '</div></div>';
    }
    if (result.missing && result.missing.length) {
      html += `<div class="ats-section"><strong>Missing Keywords:</strong><div class="ats-tags missing">`;
      result.missing.forEach(k => { html += `<span class="ats-tag missing">${escHtml(k)}</span>`; });
      html += '</div></div>';
    }
    if (result.suggestions && result.suggestions.length) {
      html += '<div class="ats-section"><strong>Suggestions:</strong><ul>';
      result.suggestions.forEach(s => { html += `<li>${escHtml(s)}</li>`; });
      html += '</ul></div>';
    }

    showAiResult('ats-result', html);
    showToast('ATS analysis complete!', 'success');
  } catch (e) {
    showAiResult('ats-result', `<strong>Error:</strong> ${escHtml(e.message)}`);
    showToast('ATS analysis failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runSuggest() {
  try {
    showLoading('Getting AI suggestions...');
    await api.saveCv(cvData);
    const res = await api.post('/api/suggest', {});
    const result = await res.json();

    let html = '<strong>Improvement Suggestions</strong>';
    if (result.suggestions && result.suggestions.length) {
      html += '<ul class="suggest-list">';
      result.suggestions.forEach(s => {
        html += '<li>';
        if (s.section) html += `<strong>${escHtml(s.section)}:</strong> `;
        html += escHtml(s.suggested || s.reason || '');
        if (s.original && s.suggested) {
          html += `<div class="suggest-diff"><span class="suggest-original">${escHtml(s.original)}</span> → <span class="suggest-new">${escHtml(s.suggested)}</span></div>`;
        }
        html += '</li>';
      });
      html += '</ul>';
    }
    if (result.general && result.general.length) {
      html += '<div class="suggest-general"><strong>General Advice</strong><ul class="suggest-list">';
      result.general.forEach(g => { html += `<li>${escHtml(g)}</li>`; });
      html += '</ul></div>';
    }
    if (!result.suggestions?.length && !result.general?.length) {
      html += `<pre>${escHtml(JSON.stringify(result, null, 2))}</pre>`;
    }

    showAiResult('suggest-result', html);
    showToast('Suggestions ready!', 'success');
  } catch (e) {
    showAiResult('suggest-result', `<strong>Error:</strong> ${escHtml(e.message)}`);
    showToast('Suggestions failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function runBio() {
  const theme = document.getElementById('ai-bio-theme')?.value || '';
  const lang = document.getElementById('ai-bio-lang')?.value || 'en';

  try {
    showLoading('Generating bio...');
    await api.saveCv(cvData);
    const res = await api.post('/api/bio/build', {
      lang,
      theme: theme || null,
    });
    const result = await res.json();
    showAiResult('bio-result', `
      <strong>Bio ready!</strong><br>
      <a href="${escHtml(result.download)}" download>${escHtml(result.filename)}</a>
    `);
    showToast('Bio generated!', 'success');
  } catch (e) {
    showAiResult('bio-result', `<strong>Error:</strong> ${escHtml(e.message)}`);
    showToast('Bio generation failed: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

/* ==================== Import ==================== */
async function importCV(format, input) {
  const file = input.files[0];
  if (!file) return;

  if (!confirm('This will replace your current cv.yaml. Continue?')) {
    input.value = '';
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    showLoading('Importing CV...');
    const res = await fetch(`/api/import?fmt=${encodeURIComponent(format)}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Import failed');
    }
    const result = await res.json();

    // Reload CV data into editor
    cvData = result.cv || await api.getCv();
    bindSimpleInputs();
    bindSkillsInputs();
    renderAllLists();
    renderPhotoPreview();

    showToast(`CV imported from ${format} successfully!`, 'success');
    setPage('editor');
  } catch (e) {
    showToast('Import failed: ' + e.message, 'error');
  } finally {
    hideLoading();
    input.value = '';
  }
}

/* ==================== Settings ==================== */
async function loadSettings() {
  try {
    const res = await api.get('/api/settings');
    const settings = await res.json();

    // Update provider status indicators
    updateProviderStatus('anthropic', settings.anthropic_configured, settings.anthropic_api_key);
    updateProviderStatus('openai', settings.openai_configured, settings.openai_api_key);

    // Show masked keys as placeholders (don't fill value — that would send mask back)
    const anthropicInput = document.getElementById('settings-anthropic-key');
    const openaiInput = document.getElementById('settings-openai-key');

    anthropicInput.value = '';
    anthropicInput.placeholder = settings.anthropic_configured ? settings.anthropic_api_key : 'sk-ant-api03-...';

    openaiInput.value = '';
    openaiInput.placeholder = settings.openai_configured ? settings.openai_api_key : 'sk-...';

    // Hint text showing current status
    document.getElementById('hint-anthropic-key').textContent =
      settings.anthropic_configured ? 'Currently configured. Leave blank to keep existing key.' : '';
    document.getElementById('hint-openai-key').textContent =
      settings.openai_configured ? 'Currently configured. Leave blank to keep existing key.' : '';

    // Non-secret fields: fill actual values
    document.getElementById('settings-openai-base-url').value = settings.openai_base_url || '';
    document.getElementById('settings-openai-model').value = settings.openai_model || '';
  } catch (e) {
    showToast('Failed to load settings: ' + e.message, 'error');
  }
}

function updateProviderStatus(provider, configured, maskedKey) {
  const el = document.getElementById('status-' + provider);
  if (!el) return;
  const dot = el.querySelector('.provider-dot');
  const badge = el.querySelector('.provider-badge');
  if (configured) {
    dot.className = 'provider-dot configured';
    badge.className = 'provider-badge configured';
    badge.textContent = maskedKey || 'Configured';
  } else {
    dot.className = 'provider-dot';
    badge.className = 'provider-badge';
    badge.textContent = 'Not configured';
  }
}

async function saveSettings() {
  const body = {};

  // Only send keys that the user actually typed (non-empty input value)
  const anthropicKey = document.getElementById('settings-anthropic-key').value;
  const openaiKey = document.getElementById('settings-openai-key').value;
  const baseUrl = document.getElementById('settings-openai-base-url').value;
  const model = document.getElementById('settings-openai-model').value;

  if (anthropicKey) body.anthropic_api_key = anthropicKey;
  if (openaiKey) body.openai_api_key = openaiKey;
  // Always send base_url and model (they're not secrets)
  body.openai_base_url = baseUrl;
  body.openai_model = model;

  try {
    showLoading('Saving settings...');
    const res = await api.post('/api/settings', body);
    const settings = await res.json();

    updateProviderStatus('anthropic', settings.anthropic_configured, settings.anthropic_api_key);
    updateProviderStatus('openai', settings.openai_configured, settings.openai_api_key);

    // Clear key inputs and update placeholders
    const anthropicInput = document.getElementById('settings-anthropic-key');
    const openaiInput = document.getElementById('settings-openai-key');
    anthropicInput.value = '';
    openaiInput.value = '';
    anthropicInput.placeholder = settings.anthropic_configured ? settings.anthropic_api_key : 'sk-ant-api03-...';
    openaiInput.placeholder = settings.openai_configured ? settings.openai_api_key : 'sk-...';

    document.getElementById('hint-anthropic-key').textContent =
      settings.anthropic_configured ? 'Currently configured. Leave blank to keep existing key.' : '';
    document.getElementById('hint-openai-key').textContent =
      settings.openai_configured ? 'Currently configured. Leave blank to keep existing key.' : '';

    showToast('Settings saved!', 'success');
  } catch (e) {
    showToast('Failed to save settings: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

function toggleKeyVisibility(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === 'password' ? 'text' : 'password';
}

/* ==================== Initialization ==================== */
async function init() {
  showLoading('Loading resumake...');

  try {
    // Check project status
    const status = await api.getStatus();

    // If no cv.yaml, initialize the project
    if (!status.has_cv) {
      showLoading('Initializing project...');
      await api.initProject();
      showToast('Project initialized with example CV', 'info');
    }

    // Load themes
    try {
      themes = await api.getThemes();
    } catch (e) {
      console.warn('Could not load themes:', e);
      themes = [];
    }

    // Load CV data
    cvData = await api.getCv();

    // Bind form inputs
    bindSimpleInputs();
    bindSkillsInputs();
    renderAllLists();
    renderPhotoPreview();
    populateAllThemeSelects();

    // Set up navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        setPage(item.getAttribute('data-page'));
        // Close mobile nav if open
        document.querySelector('.sidebar').classList.remove('open');
        document.getElementById('nav-overlay').classList.remove('open');
      });
    });

    updateSaveStatus('', 'Ready');
    showToast('CV loaded successfully', 'success');

  } catch (e) {
    console.error('Initialization error:', e);
    showToast('Failed to load: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

// Mobile navigation
function toggleMobileNav() {
  document.querySelector('.sidebar').classList.toggle('open');
  document.getElementById('nav-overlay').classList.toggle('open');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault();
    saveNow();
  }
});

// Warn before closing with unsaved changes
window.addEventListener('beforeunload', (e) => {
  if (saveTimeout || isSaving) {
    e.preventDefault();
  }
});

// Start the app
init();
