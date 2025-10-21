// === MODAL HANDLER (unmodified) ===
(function () {
  function openOverlay(overlay) {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeOverlay(overlay, { clearHashIfMatches = true } = {}) {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (
      clearHashIfMatches &&
      location.hash &&
      ('#' + overlay.id) === location.hash
    ) {
      history.replaceState(null, '', location.pathname + location.search);
    }
  }
  function autoOpenFromHash() {
    if (!location.hash) return;
    const el = document.querySelector(location.hash);
    if (el && el.classList.contains('modal-overlay')) openOverlay(el);
  }
  function bindFileInputs(scope = document) {
    scope.addEventListener('change', (e) => {
      const input = e.target;
      if (!input.matches('.file-input')) return;
      const wrap = input.closest('.file-input-wrapper');
      const nameEl = wrap?.querySelector('.file-name');
      const prev = wrap?.querySelector('.file-preview');
      const file = input.files && input.files[0];
      if (file) {
        if (nameEl) nameEl.textContent = file.name;
        if (prev) {
          const url = URL.createObjectURL(file);
          prev.src = url;
          prev.style.display = 'block';
        }
      } else {
        if (nameEl) nameEl.textContent = 'No file chosen';
        if (prev) {
          prev.removeAttribute('src');
          prev.style.display = 'none';
        }
      }
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-open-modal[data-modal]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const sel = btn.getAttribute('data-modal');
        const ov = document.querySelector(sel);
        if (ov && ov.classList.contains('modal-overlay')) openOverlay(ov);
      });
    });
    document.addEventListener('click', (e) => {
      const c = e.target.closest('.js-close-modal');
      if (c) {
        const o = c.closest('.modal-overlay');
        if (o) {
          e.preventDefault();
          closeOverlay(o);
        }
      }
    });
    document.addEventListener('click', (e) => {
      const ov = e.target.classList.contains('modal-overlay') ? e.target : null;
      if (ov && ov.classList.contains('is-open')) closeOverlay(ov);
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape')
        document
          .querySelectorAll('.modal-overlay.is-open')
          .forEach((o) => closeOverlay(o));
    });
    autoOpenFromHash();
    bindFileInputs(document);
  });
})();

// === DISABLE PAST DATES ===
document.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach((el) => (el.min = today));
});

// === GENERIC SORT/FILTER (same as before, untouched) ===
(function () {
  function q(s) { return typeof s === 'string' ? document.querySelector(s) : s; }
  function field(row, key) {
    const k = String(key).toLowerCase();
    const toCamel = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const d = row.dataset || {};
    const dk = toCamel(k);
    if (d[dk] != null && d[dk] !== '') return d[dk];
    const byCol = row.querySelector(`[data-col="${k}"]`);
    if (byCol) return byCol.textContent.trim();
    const tds = row.querySelectorAll('td');
    if (k === 'name') return (tds[0]?.textContent || '').trim();
    if (k === 'coordinator') return (tds[1]?.textContent || '').trim();
    if (k === 'status') return (tds[4]?.textContent || '').trim().toLowerCase();
    return '';
  }
  function dateVal(s) { const t = Date.parse(s || ''); return Number.isFinite(t) ? t : 0; }
  function numVal(v) { const n = parseFloat(String(v).replace(/[^0-9.-]/g, '')); return Number.isFinite(n) ? n : 0; }

  window.initFilterSort = function ({ tbody, status, sort, search, emptyColspan = 6, filterKey } = {}) {
    const tb = q(tbody), sf = status && q(status), so = sort && q(sort), se = search && q(search);
    if (!tb) return;
    const base = [...tb.querySelectorAll('tr')];
    const coll = new Intl.Collator(undefined, { sensitivity: 'base' });

    const detectKey = () => (sf?.getAttribute('data-filter-key') || filterKey || 'status').toLowerCase();
    const render = (rows) => {
      tb.innerHTML = '';
      if (!rows.length)
        tb.innerHTML = `<tr><td colspan="${emptyColspan}" style="text-align:center;opacity:.7;">No results</td></tr>`;
      rows.forEach((r) => tb.appendChild(r));
    };
    function apply() {
      let rows = base.slice();
      if (se && se.value.trim()) {
        const qv = se.value.trim().toLowerCase();
        rows = rows.filter((r) =>
          [field(r, 'name'), field(r, 'coordinator'), field(r, 'club'), field(r, 'department'), field(r, 'email')]
            .join(' ')
            .toLowerCase()
            .includes(qv)
        );
      }
      if (sf && sf.value && sf.value.toLowerCase() !== 'all') {
        const key = detectKey(), want = sf.value.toLowerCase();
        rows = rows.filter((r) => String(field(r, key)).toLowerCase() === want);
      }
      if (so) {
        const m = (so.value || 'none').toLowerCase();
        if (m === 'name') rows.sort((a, b) => coll.compare(field(a, 'name'), field(b, 'name')));
        else if (m === 'coordinator') rows.sort((a, b) => coll.compare(field(a, 'coordinator'), field(b, 'coordinator')));
        else if (m === 'club') rows.sort((a, b) => coll.compare(field(a, 'club'), field(b, 'club')));
        else if (m === 'members') rows.sort((a, b) => numVal(field(b, 'members')) - numVal(field(a, 'members')));
        else if (m === 'newest') rows.sort((a, b) => dateVal(field(b, 'created')) - dateVal(field(a, 'created')));
        else if (m === 'oldest') rows.sort((a, b) => dateVal(field(a, 'created')) - dateVal(field(b, 'created')));
      }
      render(rows);
    }
    if (se) { const f = se.closest('form'); if (f) f.addEventListener('submit', (e) => e.preventDefault()); se.addEventListener('input', apply); }
    if (sf) sf.addEventListener('change', apply);
    if (so) so.addEventListener('change', apply);
    apply();
  };
})();

// === INIT SORTERS ===
document.addEventListener('DOMContentLoaded', () => {
  if (window.initFilterSort) {
    initFilterSort({ tbody: '[data-table="clubs"] tbody', status: '#statusFilter', sort: '#sortBy', emptyColspan: 6 });
    initFilterSort({ tbody: '[data-table="events"] tbody', status: '#eventStatusFilter', sort: '#eventSortBy', search: '#eventSearch', emptyColspan: 7 });
    initFilterSort({ tbody: '[data-table="colleges"] tbody', status: '#collegeStatusFilter', sort: '#collegeSortBy', search: '#collegeSearch', emptyColspan: 7 });
    initFilterSort({ tbody: '[data-table="coordinators"] tbody', status: '#coordClubFilter', sort: '#coordSortBy', search: '#coordinatorSearch', emptyColspan: 6, filterKey: 'club-id' });
  }
});



// === CLUB SEARCH + FEATURED CARD + DELETE ===
// --- Clubs: first-letter search + featured card (with DELETE modal -> form submit) ---
document.addEventListener('DOMContentLoaded', function () {
  try {
    const input  = document.querySelector('.search-bar input[name="q"]');
    const select = document.getElementById('clubChoices');
    const card   = document.getElementById('featuredCard');
    if (!input || !select || !card) return;

    // Featured card parts
    const elTitle   = document.getElementById('fcTitle');
    const elDesc    = document.getElementById('fcDesc');
    const elImg     = document.getElementById('fcImage');
    const elMembers = document.getElementById('fcMembers');
    const elCoord   = document.getElementById('fcCoordinator');
    const btnEdit   = document.getElementById('fcEditBtn');
    const btnDel    = document.getElementById('fcDeleteBtn');

    // 🔴 Delete modal + form (calls /clubs/delete)
    const delModal   = document.getElementById('deleteConfirmModal');
    const delConfirm = document.getElementById('confirmDeleteBtn');
    const delCancel  = document.getElementById('cancelDeleteBtn');
    const delClose   = document.getElementById('closeDeleteModal');
    const delForm    = document.getElementById('deleteClubForm');
    const delInput   = document.getElementById('deleteClubId');
    const delBodyP   = delModal?.querySelector('.delete-modal-body p');

    let clubPendingDelete = null;

    function openDeleteModal(club) {
      clubPendingDelete = club;
      if (delBodyP) {
        delBodyP.textContent = `Are you sure you want to remove "${club.name}"?`;
      }
      delModal.hidden = false;
    }
    function closeDeleteModal() {
      delModal.hidden = true;
      clubPendingDelete = null;
    }
    // close on buttons / backdrop
    if (delCancel) delCancel.onclick = closeDeleteModal;
    if (delClose)  delClose.onclick  = closeDeleteModal;
    if (delModal) {
      delModal.addEventListener('click', (e) => {
        if (e.target === delModal) closeDeleteModal();
      });
    }
    // submit form on confirm
    if (delConfirm) {
      delConfirm.onclick = () => {
        if (!clubPendingDelete || !delForm || !delInput) return;
        delInput.value = clubPendingDelete.id; // set hidden input
        delForm.submit(); // POST -> /clubs/delete (Flask route)
      };
    }

    // Build clubs list from table rows
    const rows = [...document.querySelectorAll('table[data-table="clubs"] tbody tr[data-name]')];
    const clubs = rows.map((row) => {
      const edit = row.querySelector('.js-edit-club');
      return {
        id:        edit?.dataset.id || row.dataset.id || '',
        name:      (row.dataset.name || '').trim(),
        desc:      edit?.dataset.description || '',
        imageUrl:  edit?.dataset.imageUrl || '',
        imageName: edit?.dataset.imageName || '',
        coordinator: row.dataset.coordinator || '',
        members:     row.dataset.members || 0,
        row,
        editBtn:   edit
      };
    });

    function resetCard() {
      card.hidden = true;
      elTitle.textContent = '';
      elDesc.textContent  = '';
      if (elMembers) elMembers.textContent = '0';
      if (elCoord)   elCoord.textContent   = '—';
      if (elImg) { elImg.removeAttribute('src'); elImg.style.display = 'none'; }
    }
    function escapeHtml(s) {
      return (s || '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    }
    function showSelect(items, disabled = false) {
      select.innerHTML = items.map(c =>
        `<option value="${escapeHtml(c.id)}"${disabled ? ' disabled' : ''}>${escapeHtml(c.name)}</option>`
      ).join('');
      select.hidden = false;
    }

    function fillCard(c) {
      elTitle.textContent = c.name || '—';
      elDesc.textContent  = c.desc  || 'No description provided.';
      if (elMembers) elMembers.textContent = String(c.members || 0);
      if (elCoord)   elCoord.textContent   = c.coordinator || '—';

      if (c.imageUrl) {
        elImg.src = c.imageUrl; elImg.alt = c.imageName || c.name || 'Club image';
        elImg.style.display = '';
      } else {
        elImg.removeAttribute('src'); elImg.alt = ''; elImg.style.display = 'none';
      }

      if (btnEdit) btnEdit.onclick = (e) => { e.preventDefault(); c.editBtn?.click(); };
      if (btnDel)  btnDel.onclick  = (e) => { e.preventDefault(); openDeleteModal(c); };
    }

    // init
    resetCard();

    // Input → first-letter matches
    input.addEventListener('input', () => {
      const v = input.value.trim();
      if (!v) { select.hidden = true; resetCard(); return; }
      const matches = clubs
        .filter(c => c.name.toLowerCase().startsWith(v[0].toLowerCase()))
        .sort((a,b) => a.name.localeCompare(b.name));
      showSelect(matches.length ? matches : [{id:'', name:'No matches'}], !matches.length);
    });

    // Select → show card, then hide dropdown
    select.addEventListener('change', () => {
      const id = select.value;
      const club = clubs.find(c => c.id === id);
      if (!club) return;
      fillCard(club);
      card.hidden = false;
      select.hidden = true;
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!select.contains(e.target) && !input.contains(e.target)) select.hidden = true;
    });

    // ESC → hide dropdown + card
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { select.hidden = true; resetCard(); input.blur(); }
    });
  } catch (err) {
    console.error('[clubs] Script error:', err);
  }
});
