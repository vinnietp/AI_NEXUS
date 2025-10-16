// Unified modal handler for Chapters, Events, etc.
(function () {
  function openOverlay(overlay) {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    // optional: lock scroll
    document.body.style.overflow = 'hidden';
  }

  function closeOverlay(overlay, { clearHashIfMatches = true } = {}) {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    // Optional: clean the hash if it was used to open this overlay
    if (
      clearHashIfMatches &&
      location.hash &&
      ('#' + overlay.id) === location.hash
    ) {
      history.replaceState(null, '', location.pathname + location.search);
    }
  }

  // Auto-open overlay if URL has a hash that matches a modal (e.g., #eventModal or #chapterModal)
  function autoOpenFromHash() {
    if (!location.hash) return;
    const el = document.querySelector(location.hash);
    if (el && el.classList.contains('modal-overlay')) {
      openOverlay(el);
    }
  }

  // File input helper: show selected filename + preview
  function bindFileInputs(scope = document) {
    scope.addEventListener('change', function (e) {
      const input = e.target;
      if (!input.matches('.file-input')) return;

      const wrapper = input.closest('.file-input-wrapper');
      const nameEl = wrapper ? wrapper.querySelector('.file-name') : null;
      const previewEl = wrapper ? wrapper.querySelector('.file-preview') : null;
      const file = input.files && input.files[0];

      if (file) {
        if (nameEl) nameEl.textContent = file.name;
        if (previewEl) {
          const url = URL.createObjectURL(file);
          previewEl.src = url;
          previewEl.style.display = 'block';
        }
      } else {
        if (nameEl) nameEl.textContent = 'No file chosen';
        if (previewEl) {
          previewEl.removeAttribute('src');
          previewEl.style.display = 'none';
        }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    // OPEN: any element with .js-open-modal and data-modal="#id"
    document.querySelectorAll('.js-open-modal[data-modal]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const selector = btn.getAttribute('data-modal');
        const overlay = document.querySelector(selector);
        if (overlay && overlay.classList.contains('modal-overlay')) {
          openOverlay(overlay);
        }
      });
    });

    // CLOSE: via .js-close-modal button/link inside the overlay
    document.addEventListener('click', (e) => {
      const closeBtn = e.target.closest('.js-close-modal');
      if (closeBtn) {
        const overlay = closeBtn.closest('.modal-overlay');
        if (overlay) {
          e.preventDefault();
          closeOverlay(overlay);
        }
      }
    });

    // CLOSE: click on the backdrop area
    document.addEventListener('click', (e) => {
      const overlay = e.target.classList.contains('modal-overlay') ? e.target : null;
      if (overlay && overlay.classList.contains('is-open')) {
        closeOverlay(overlay);
      }
    });

    // CLOSE: Esc key closes any open overlay
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.is-open').forEach((overlay) => {
          closeOverlay(overlay);
        });
      }
    });

    // Support deep-link / server redirect with hash (#eventModal, #chapterModal)
    autoOpenFromHash();

    // Enhance file inputs globally
    bindFileInputs(document);
  });
})();

// To disable dates before today
document.addEventListener("DOMContentLoaded", function() {
  const today = new Date().toISOString().split("T")[0]; // YYYY-MM-DD
  document.querySelectorAll('input[type="date"]').forEach(el => {
    el.min = today;   // disallow earlier dates
  });
});

// EDIT CLUBS + EVENTS (delegated)
// OPEN (delegated): prevent navigation, prefill if edit button
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.js-open-modal[data-modal]');
  if (!btn) return;

  e.preventDefault(); // important for <a href="#...">

  const byId = (id) => document.getElementById(id);

  // ---- Prefill when editing CLUBS ----
  if (btn.classList.contains('js-edit-club')) {
    const id    = btn.dataset.id || '';
    const name  = btn.dataset.name || '';
    const coord = btn.dataset.coordinator || '';
    const cat   = btn.dataset.category || '';
    const type  = (btn.dataset.type || '').toLowerCase();
    const desc  = btn.dataset.description || '';
    const imgUrl  = btn.dataset.imageUrl || '';   // absolute/relative URL
    const imgName = btn.dataset.imageName || '';  // filename only (optional)

    if (byId('editClubId'))           byId('editClubId').value = id;
    if (byId('editClubName'))         byId('editClubName').value = name;
    if (byId('editCoordinator'))      byId('editCoordinator').value = coord;
    if (byId('editCategory'))         byId('editCategory').value = cat;
    if (byId('editCoordinatorType'))  byId('editCoordinatorType').value = (type === 'faculty' ? 'faculty' : 'student');
    if (byId('editDescription'))      byId('editDescription').value = desc;

    // Existing image → show filename + preview
    const clubFile = byId('editClubLogo');
    if (clubFile) {
      // Clear any newly selected file
      clubFile.value = '';
      const wrapper  = clubFile.closest('.file-input-wrapper');
      if (wrapper) {
        const nameEl  = wrapper.querySelector('.file-name');
        const preview = wrapper.querySelector('.file-preview');
        if (imgUrl) {
          if (nameEl)  nameEl.textContent = imgName || imgUrl.split('/').pop();
          if (preview) { preview.src = imgUrl; preview.style.display = 'block'; }
        } else {
          if (nameEl)  nameEl.textContent = 'No file chosen';
          if (preview) { preview.removeAttribute('src'); preview.style.display = 'none'; }
        }
      }
    }
  }

  // ---- Prefill when editing EVENTS ----
  if (btn.classList.contains('js-edit-event')) {
    // Read from data-* attributes placed on the Edit button/link
    const id    = btn.dataset.id || '';
    const name  = btn.dataset.name || '';
    const club  = btn.dataset.clubId || '';
    const coord = btn.dataset.coordinator || '';
    const venue = btn.dataset.venue || '';
    const sDate = btn.dataset.startDate || '';  // "YYYY-MM-DD"
    const sTime = btn.dataset.startTime || '';  // "HH:MM"
    const eDate = btn.dataset.endDate || '';    // "YYYY-MM-DD"
    const eTime = btn.dataset.endTime || '';    // "HH:MM"
    const maxp  = btn.dataset.maxParticipants || '';
    const status= (btn.dataset.status || 'upcoming').toLowerCase();
    const desc  = btn.dataset.description || '';
    const imgUrl  = btn.dataset.imageUrl || '';
    const imgName = btn.dataset.imageName || '';

    if (byId('editEventId'))               byId('editEventId').value = id;
    if (byId('editEventName'))             byId('editEventName').value = name;
    if (byId('editOrganisingClub'))        byId('editOrganisingClub').value = club;
    if (byId('editEventCoordinator'))      byId('editEventCoordinator').value = coord;
    if (byId('editVenue'))                 byId('editVenue').value = venue;

    if (byId('editStartDate'))             byId('editStartDate').value = sDate;
    if (byId('editStartTime'))             byId('editStartTime').value = sTime;
    if (byId('editEndDate'))               byId('editEndDate').value = eDate;
    if (byId('editEndTime'))               byId('editEndTime').value = eTime;

    if (byId('editMaxParticipants'))       byId('editMaxParticipants').value = maxp;
    if (byId('editStatus'))                byId('editStatus').value = status;
    if (byId('editEventDescription'))      byId('editEventDescription').value = desc;

    // Allow editing past-dated events despite global min=today
    const today = new Date().toISOString().split('T')[0]; // "YYYY-MM-DD"
    const relaxMin = (inputId, value) => {
      const el = byId(inputId);
      if (!el) return;
      if (value && value < today) el.min = value; // allow past date already saved
      else el.min = today;                        // otherwise keep today's guard
    };
    relaxMin('editStartDate', sDate);
    relaxMin('editEndDate',   eDate);

    // Existing image → show filename + preview
    const eventFile = byId('editEventImage');
    if (eventFile) {
      eventFile.value = '';
      const wrapper   = eventFile.closest('.file-input-wrapper');
      if (wrapper) {
        const nameEl  = wrapper.querySelector('.file-name');
        const preview = wrapper.querySelector('.file-preview');
        if (imgUrl) {
          if (nameEl)  nameEl.textContent = imgName || imgUrl.split('/').pop();
          if (preview) { preview.src = imgUrl; preview.style.display = 'block'; }
        } else {
          if (nameEl)  nameEl.textContent = 'No file chosen';
          if (preview) { preview.removeAttribute('src'); preview.style.display = 'none'; }
        }
      }
    }
  }

// ---- Prefill when editing COLLEGES ----
if (btn.classList.contains('js-edit-college')) {
  const byId = (id) => document.getElementById(id);

  const id    = btn.dataset.id || '';
  const name  = btn.dataset.name || '';
  const email = btn.dataset.email || '';
  const loc   = btn.dataset.location || '';
  const auth  = btn.dataset.authorityName || '';
  const role  = btn.dataset.authorityRole || '';
  const phone = btn.dataset.phone || '';
  const desc  = btn.dataset.description || '';
  const status= (btn.dataset.status || 'active').toLowerCase();

  if (byId('editCollegeId'))           byId('editCollegeId').value = id;
  if (byId('editCollegeName'))         byId('editCollegeName').value = name;
  if (byId('editEmail'))               byId('editEmail').value = email;
  if (byId('editLocation'))            byId('editLocation').value = loc;
  if (byId('editAuthorityName'))       byId('editAuthorityName').value = auth;
  if (byId('editAuthorityRole'))       byId('editAuthorityRole').value = role;
  if (byId('editPhone'))               byId('editPhone').value = phone;
  if (byId('editCollegeDescription'))  byId('editCollegeDescription').value = desc;
  if (byId('editCollegeStatus'))       byId('editCollegeStatus').value = status;
}

// ---- Prefill when editing COORDINATORS ----
if (btn.classList.contains('js-edit-coordinator')) {
  const byId = (id) => document.getElementById(id);

  const id        = btn.dataset.id || '';
  const name      = btn.dataset.name || '';
  const clubId    = btn.dataset.clubId || '';
  const collegeId = btn.dataset.collegeId || '';
  const dept      = btn.dataset.facultyDept || '';
  const role      = btn.dataset.roleType || '';
  const email     = btn.dataset.email || '';
  const phone     = btn.dataset.phone || '';
  const desc      = btn.dataset.description || '';
  const status    = (btn.dataset.status || 'active').toLowerCase();
  const imgUrl    = btn.dataset.imageUrl || '';
  const imgName   = btn.dataset.imageName || '';

  if (byId('editCoordinatorId')) byId('editCoordinatorId').value = id;
  if (byId('editCoordName'))     byId('editCoordName').value = name;
  if (byId('editClubSelect'))    byId('editClubSelect').value = clubId;
  if (byId('editCollegeSelect')) byId('editCollegeSelect').value = collegeId;
  if (byId('editFacultyDept'))   byId('editFacultyDept').value = dept;
  if (byId('editRoleType'))      byId('editRoleType').value = role;
  if (byId('editCoordEmail'))    byId('editCoordEmail').value = email;
  if (byId('editCoordPhone'))    byId('editCoordPhone').value = phone;
  if (byId('editCoordDesc'))     byId('editCoordDesc').value = desc;
  if (byId('editCoordStatus'))   byId('editCoordStatus').value = status;

  // Existing image filename + preview
  const input = byId('editCoordImage');
  if (input) {
    input.value = '';
    const wrap = input.closest('.file-input-wrapper');
    if (wrap) {
      const nameEl = wrap.querySelector('.file-name');
      const preview = wrap.querySelector('.file-preview');
      if (imgUrl) {
        if (nameEl)  nameEl.textContent = imgName || imgUrl.split('/').pop();
        if (preview) { preview.src = imgUrl; preview.style.display = 'block'; }
      } else {
        if (nameEl)  nameEl.textContent = 'No file chosen';
        if (preview) { preview.removeAttribute('src'); preview.style.display = 'none'; }
      }
    }
  }
}
//Edit announcements
// ---- Prefill when editing ANNOUNCEMENTS (matches your modal IDs) ----
if (btn.classList.contains('js-edit-announcement')) {
  const $ = (id) => document.getElementById(id);

  const id       = btn.dataset.id || '';
  const title    = btn.dataset.title || '';

  // content is JSON-encoded in the data-* attribute to safely carry newlines/quotes
  let content = '';
  try {
    content = btn.dataset.content ? JSON.parse(btn.dataset.content) : '';
  } catch (e) {
    content = btn.dataset.content || '';
  }

  const clubId   = btn.dataset.clubId || '';
  const priority = (btn.dataset.priority || 'normal').toLowerCase();
  const audience = (btn.dataset.audience || 'all_members').toLowerCase();
  const status   = (btn.dataset.status || 'draft').toLowerCase();

  const pDate = btn.dataset.publishDate || '';
  const pTime = btn.dataset.publishTime || '';
  const eDate = btn.dataset.expireDate || '';
  const eTime = btn.dataset.expireTime || '';

  const pinned    = btn.dataset.pinned === '1';
  const sendEmail = btn.dataset.sendEmail === '1';

  if ($('editAnnId'))          $('editAnnId').value = id;
  if ($('editAnnTitle'))       $('editAnnTitle').value = title;
  if ($('editAnnContent'))     $('editAnnContent').value = content;

  if ($('editAnnClub'))        $('editAnnClub').value = clubId;
  if ($('editPriority'))       $('editPriority').value = priority;
  if ($('editAudience'))       $('editAudience').value = audience;
  if ($('editAnnStatus'))      $('editAnnStatus').value = status;

  if ($('editPublishDate'))    $('editPublishDate').value = pDate;
  if ($('editPublishTime'))    $('editPublishTime').value = pTime;
  if ($('editExpireDate'))     $('editExpireDate').value = eDate;
  if ($('editExpireTime'))     $('editExpireTime').value = eTime;

  if ($('editSendEmail'))      $('editSendEmail').checked = sendEmail;
  if ($('editPinned'))         $('editPinned').checked = pinned;
}

  // Open the modal
  const selector = btn.getAttribute('data-modal');
  const overlay = document.querySelector(selector);
  if (overlay && overlay.classList.contains('modal-overlay')) {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
});

//sorting function based on select box
// === Ultra-short generic table filter + sort (reusable) ===

// === Ultra-short generic table filter + sort (reusable) ===
(function () {
  function q(s){ return typeof s==='string' ? document.querySelector(s) : s; }
  function text(el){ return el ? el.textContent.trim() : ''; }
  function field(row, key){
  const k = String(key).toLowerCase();

  // dataset key normalization: "club-id" -> "clubId"
  const toCamel = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  const d = row.dataset || {};
  const dk = toCamel(k);

  // 1) Prefer data-* on the row
  if (d[dk] != null && d[dk] !== '') return d[dk];

  // 2) Prefer explicit cell with data-col
  const byCol = row.querySelector(`[data-col="${k}"]`);
  if (byCol) return byCol.textContent.trim();

  // 3) Legacy fallbacks (kept for older tables shaped like clubs)
  const tds = row.querySelectorAll('td');
  if (k === 'name')         return (tds[0]?.textContent || '').trim();
  if (k === 'coordinator')  return (tds[1]?.textContent || '').trim();
  if (k === 'status')       return (tds[4]?.textContent || '').trim().toLowerCase();

  return '';
}
  function dateVal(s){ const t=Date.parse(s||''); return Number.isFinite(t)?t:0; }
  function numVal(v){ const n=parseFloat(String(v).replace(/[^0-9.-]/g,'')); return Number.isFinite(n)?n:0; }

  // NEW: options.filterKey lets you choose which data-* to filter on (default 'status')
  window.initFilterSort = function ({ tbody, status, sort, search, emptyColspan=6, filterKey } = {}) {
    const tb=q(tbody), sf=status&&q(status), so=sort&&q(sort), se=search&&q(search);
    if (!tb) return;
    const base=[...tb.querySelectorAll('tr')];
    const coll = new Intl.Collator(undefined,{sensitivity:'base'});

    // if the select has data-filter-key, prefer that; else use param; else 'status'
    const detectKey = () => {
      if (sf && sf.getAttribute) {
        const k = sf.getAttribute('data-filter-key');
        if (k) return k.toLowerCase();
      }
      return (filterKey || 'status').toLowerCase();
    };

    function render(rows){
      tb.innerHTML='';
      if(!rows.length){ tb.innerHTML=`<tr><td colspan="${emptyColspan}" style="text-align:center;opacity:.7;">No results</td></tr>`; return; }
      rows.forEach(r=>tb.appendChild(r));
    }

    function apply(){
      let rows = base.slice();

      // Search (multi-field)
      if (se && se.value.trim()){
        const qv = se.value.trim().toLowerCase();
        rows = rows.filter(r => ([
          field(r,'name'), field(r,'coordinator'), field(r,'club'),
          field(r,'department'), field(r,'email')
        ].join(' ').toLowerCase().includes(qv)));
      }

      // Filter (status by default; can be custom via data-filter-key or filterKey option)
// Filter (status by default; can be custom via data-filter-key or filterKey option)
if (sf && sf.value && sf.value.toLowerCase()!=='all'){
  const key = detectKey(); // e.g., 'status' or 'club-id'
  const want = sf.value.toLowerCase();
  rows = rows.filter(r => (String(field(r, key)).toLowerCase() === want));
}
      // Sort
      if (so){
        const m = (so.value||'none').toLowerCase();
        if (m==='name')        rows.sort((a,b)=>coll.compare(field(a,'name'), field(b,'name')));
        else if (m==='coordinator') rows.sort((a,b)=>coll.compare(field(a,'coordinator'), field(b,'coordinator')));
        else if (m==='club')   rows.sort((a,b)=>coll.compare(field(a,'club'), field(b,'club')));
        else if (m==='members')rows.sort((a,b)=>numVal(field(b,'members'))-numVal(field(a,'members')));
        else if (m==='newest') rows.sort((a,b)=>dateVal(field(b,'created'))-dateVal(field(a,'created')));
        else if (m==='oldest') rows.sort((a,b)=>dateVal(field(a,'created'))-dateVal(field(b,'created')));
      }

      render(rows);
    }

    if (se){ const f=se.closest('form'); if (f) f.addEventListener('submit', e=>e.preventDefault()); se.addEventListener('input', apply); }
    if (sf) sf.addEventListener('change', apply);
    if (so) so.addEventListener('change', apply);

    apply();
  };
})();

// Initialize for Clubs page soring
document.addEventListener('DOMContentLoaded', () => {
  initFilterSort({
    tbody: '[data-table="clubs"] tbody',
    status: '#statusFilter',
    sort:   '#sortBy',
    // If your search input has an id="clubSearch", keep the next line; else remove it.
    // search: '#clubSearch',
    emptyColspan: 6
  });
});

// Initialize for Events page sorting
document.addEventListener('DOMContentLoaded', function () {
  if (window.initFilterSort) {
    initFilterSort({
      tbody: '[data-table="events"] tbody',
      status: '#eventStatusFilter',
      sort:   '#eventSortBy',
      search: '#eventSearch',
      emptyColspan: 7
    });
  }
});

// Initialize for Colleges page sorting/search/filter
document.addEventListener('DOMContentLoaded', () => {
  if (window.initFilterSort) {
    initFilterSort({
      tbody:  '[data-table="colleges"] tbody',
      status: '#collegeStatusFilter',
      sort:   '#collegeSortBy',
      search: '#collegeSearch',
      emptyColspan: 7
    });
  }
});

// Initialize for Coordinators page
document.addEventListener('DOMContentLoaded', () => {
  if (window.initFilterSort) {
    initFilterSort({
      tbody:  '[data-table="coordinators"] tbody',
      status: '#coordClubFilter',     // filter select
      sort:   '#coordSortBy',         // sort select
      search: '#coordinatorSearch',   // search input
      emptyColspan: 6,
      filterKey: 'club-id'            // filter by data-club-id on rows
    });
  }
});
