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

  async getPreviewUrl(theme, lang) {
    let url = '/api/preview?lang=' + encodeURIComponent(lang || 'en');
    if (theme) url += '&theme=' + encodeURIComponent(theme);
    return url;
  },

  async build() {
    const res = await this.post('/api/build', {});
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
  };
  document.getElementById('page-title').textContent = titles[pageName] || 'resumake';

  if (pageName === 'preview') refreshPreview();
  if (pageName === 'themes') renderThemes();
  if (pageName === 'build') populateBuildSelects();
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
    }
  }, 800);
}

async function saveNow() {
  clearTimeout(saveTimeout);
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
      showToast('CV is valid! No errors found.', 'success');
    } else {
      const errorList = result.errors.map(e => `${e.field}: ${e.message}`).join('\n');
      showToast('Validation errors found. Check console for details.', 'error');
      console.error('Validation errors:', result.errors);
    }
  } catch (e) {
    showToast('Validation failed: ' + e.message, 'error');
  }
}

/* ==================== Form Binding ==================== */
function bindSimpleInputs() {
  document.querySelectorAll('[data-path]').forEach(input => {
    const path = input.getAttribute('data-path');
    const value = getNestedValue(cvData, path);
    if (input.tagName === 'TEXTAREA') {
      input.value = value || '';
    } else {
      input.value = value || '';
    }

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
          <span class="list-item-title">${lang.name || 'New Language'}</span>
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
  cvData[section][itemIdx].bullets.splice(bulletIdx, 1);
  renderListSection(section);
  scheduleSave();
}

function updateBullet(section, itemIdx, bulletIdx, value) {
  cvData[section][itemIdx].bullets[bulletIdx] = value;
  scheduleSave();
}

/* ==================== Photo Upload ==================== */
async function uploadPhoto(input) {
  const file = input.files[0];
  if (!file) return;

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
    el.innerHTML = `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
    el.style.borderColor = 'var(--color-primary)';
    el.style.borderStyle = 'solid';
  }
}

/* ==================== Preview ==================== */
function refreshPreview() {
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

    grid.innerHTML += `
      <div class="theme-card ${isSelected ? 'selected' : ''}" onclick="selectTheme('${name}')">
        <div class="theme-name">${name}</div>
        <div class="theme-colors">
          <div class="theme-swatch" style="background:#${colors.primary || '333'}" data-label="Primary"></div>
          <div class="theme-swatch" style="background:#${colors.accent || '666'}" data-label="Accent"></div>
          <div class="theme-swatch" style="background:#${colors.text_light || 'fff'}" data-label="Light"></div>
          <div class="theme-swatch" style="background:#${colors.text_muted || '999'}" data-label="Muted"></div>
          <div class="theme-swatch" style="background:#${colors.text_body || '333'}" data-label="Body"></div>
        </div>
        <div class="theme-meta">
          <strong>Fonts:</strong> ${fonts.heading || 'Default'} / ${fonts.body || 'Default'}
        </div>
      </div>
    `;
  });
}

function selectTheme(name) {
  selectedTheme = name;
  renderThemes();
  showToast(`Theme set to "${name}"`, 'info');
}

/* ==================== Build ==================== */
function populateBuildSelects() {
  populateThemeSelect('build-theme');
}

function populateThemeSelect(selectId) {
  const select = document.getElementById(selectId);
  if (!select || select.options.length > 1) return;
  select.innerHTML = '<option value="">(Default — Classic)</option>';
  themes.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.name;
    opt.textContent = t.name.charAt(0).toUpperCase() + t.name.slice(1);
    if (t.name === selectedTheme) opt.selected = true;
    select.appendChild(opt);
  });
}

async function buildCV() {
  const btn = document.getElementById('btn-build');
  const resultDiv = document.getElementById('build-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;margin:0"></span> Building...';

  try {
    // Save first
    await api.saveCv(cvData);
    const result = await api.build();

    resultDiv.className = 'build-result';
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <strong>Build successful!</strong><br>
      <span style="color:var(--text-secondary)">${result.filename} (${result.size})</span><br>
      <a href="/api/download/${encodeURIComponent(result.filename)}" download>Download ${result.filename}</a>
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
  ['preview-theme', 'build-theme'].forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = '<option value="">(Default — Classic)</option>';
    themes.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name.charAt(0).toUpperCase() + t.name.slice(1);
      select.appendChild(opt);
    });
  });
}

/* ==================== Render All Lists ==================== */
function renderAllLists() {
  ['links', 'experience', 'education', 'certifications', 'volunteering', 'publications'].forEach(section => {
    renderListSection(section);
  });
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

// Start the app
init();
