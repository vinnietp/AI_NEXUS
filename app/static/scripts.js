
// === TIME SELECT HELPERS ===
function updateTimeHidden(hourId, minuteId, timeId) {
  const hourEl = document.getElementById(hourId);
  const minuteEl = document.getElementById(minuteId);
  const timeEl = document.getElementById(timeId);
  if (hourEl && minuteEl && timeEl) {
    const hour = (hourEl.value || '00').padStart(2, '0');
    const minute = (minuteEl.value || '00').padStart(2, '0');
    timeEl.value = `${hour}:${minute}`;
  }
}

function updateTimeHidden12(hourId, minuteId, ampmId, timeId) {
  const hourEl = document.getElementById(hourId);
  const minuteEl = document.getElementById(minuteId);
  const ampmEl = document.getElementById(ampmId);
  const timeEl = document.getElementById(timeId);
  if (hourEl && minuteEl && ampmEl && timeEl) {
    let hour = parseInt(hourEl.value, 10);
    const minute = (minuteEl.value || '00').padStart(2, '0');
    const ampm = ampmEl.value;
    if (ampm === 'PM' && hour !== 12) hour += 12;
    if (ampm === 'AM' && hour === 12) hour = 0;
    const hour24 = hour.toString().padStart(2, '0');
    timeEl.value = `${hour24}:${minute}`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Bind time select updates for announcement modals
  function bindTimeSelects() {
    // Publish time for create modal (12-hour)
    const publishHour = document.getElementById('publish_hour');
    const publishMinute = document.getElementById('publish_minute');
    const publishAmpm = document.getElementById('publish_ampm');
    if (publishHour && publishMinute && publishAmpm) {
      publishHour.addEventListener('change', () => updateTimeHidden12('publish_hour', 'publish_minute', 'publish_ampm', 'publish_time'));
      publishMinute.addEventListener('change', () => updateTimeHidden12('publish_hour', 'publish_minute', 'publish_ampm', 'publish_time'));
      publishAmpm.addEventListener('change', () => updateTimeHidden12('publish_hour', 'publish_minute', 'publish_ampm', 'publish_time'));
      // Initial update
      updateTimeHidden12('publish_hour', 'publish_minute', 'publish_ampm', 'publish_time');
    }

    // Expire time for create modal (12-hour)
    const expireHour = document.getElementById('expire_hour');
    const expireMinute = document.getElementById('expire_minute');
    const expireAmpm = document.getElementById('expire_ampm');
    if (expireHour && expireMinute && expireAmpm) {
      expireHour.addEventListener('change', () => updateTimeHidden12('expire_hour', 'expire_minute', 'expire_ampm', 'expire_time'));
      expireMinute.addEventListener('change', () => updateTimeHidden12('expire_hour', 'expire_minute', 'expire_ampm', 'expire_time'));
      expireAmpm.addEventListener('change', () => updateTimeHidden12('expire_hour', 'expire_minute', 'expire_ampm', 'expire_time'));
      // Initial update
      updateTimeHidden12('expire_hour', 'expire_minute', 'expire_ampm', 'expire_time');
    }



    // Start time for event create modal (12-hour)
    const startHour = document.getElementById('start_hour');
    const startMinute = document.getElementById('start_minute');
    const startAmpm = document.getElementById('start_ampm');
    if (startHour && startMinute && startAmpm) {
      startHour.addEventListener('change', () => updateTimeHidden12('start_hour', 'start_minute', 'start_ampm', 'start_time'));
      startMinute.addEventListener('change', () => updateTimeHidden12('start_hour', 'start_minute', 'start_ampm', 'start_time'));
      startAmpm.addEventListener('change', () => updateTimeHidden12('start_hour', 'start_minute', 'start_ampm', 'start_time'));
      // Initial update
      updateTimeHidden12('start_hour', 'start_minute', 'start_ampm', 'start_time');
    }

    // End time for event create modal (12-hour)
    const endHour = document.getElementById('end_hour');
    const endMinute = document.getElementById('end_minute');
    const endAmpm = document.getElementById('end_ampm');
    if (endHour && endMinute && endAmpm) {
      endHour.addEventListener('change', () => updateTimeHidden12('end_hour', 'end_minute', 'end_ampm', 'end_time'));
      endMinute.addEventListener('change', () => updateTimeHidden12('end_hour', 'end_minute', 'end_ampm', 'end_time'));
      endAmpm.addEventListener('change', () => updateTimeHidden12('end_hour', 'end_minute', 'end_ampm', 'end_time'));
      // Initial update
      updateTimeHidden12('end_hour', 'end_minute', 'end_ampm', 'end_time');
    }

    // Start time for event edit modal (12-hour)
    const editStartHour = document.getElementById('editStartHour');
    const editStartMinute = document.getElementById('editStartMinute');
    const editStartAmpm = document.getElementById('editStartAmpm');
    if (editStartHour && editStartMinute && editStartAmpm) {
      editStartHour.addEventListener('change', () => updateTimeHidden12('editStartHour', 'editStartMinute', 'editStartAmpm', 'editStartTime'));
      editStartMinute.addEventListener('change', () => updateTimeHidden12('editStartHour', 'editStartMinute', 'editStartAmpm', 'editStartTime'));
      editStartAmpm.addEventListener('change', () => updateTimeHidden12('editStartHour', 'editStartMinute', 'editStartAmpm', 'editStartTime'));
      // Initial update
      updateTimeHidden12('editStartHour', 'editStartMinute', 'editStartAmpm', 'editStartTime');
    }

    // End time for event edit modal (12-hour)
    const editEndHour = document.getElementById('editEndHour');
    const editEndMinute = document.getElementById('editEndMinute');
    const editEndAmpm = document.getElementById('editEndAmpm');
    if (editEndHour && editEndMinute && editEndAmpm) {
      editEndHour.addEventListener('change', () => updateTimeHidden12('editEndHour', 'editEndMinute', 'editEndAmpm', 'editEndTime'));
      editEndMinute.addEventListener('change', () => updateTimeHidden12('editEndHour', 'editEndMinute', 'editEndAmpm', 'editEndTime'));
      editEndAmpm.addEventListener('change', () => updateTimeHidden12('editEndHour', 'editEndMinute', 'editEndAmpm', 'editEndTime'));
      // Initial update
      updateTimeHidden12('editEndHour', 'editEndMinute', 'editEndAmpm', 'editEndTime');
    }
  }

  // Bind on load
  bindTimeSelects();

  // Re-bind when modals open (in case they are loaded dynamically)
  document.addEventListener('modal:open', bindTimeSelects);
});

// === MODAL HANDLER ===
(function () {
  function openOverlay(overlay) {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    //added
    overlay.dispatchEvent(new CustomEvent('modal:open', { bubbles: true }));
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
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const sel = btn.getAttribute('data-modal');
        const ov = document.querySelector(sel);
        if (ov && ov.classList.contains('modal-overlay')) openOverlay(ov);
      });
    });

    // Handle edit modal population for all entities
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.js-edit-club, .js-edit-event, .js-edit-college, .js-edit-coordinator, .js-edit-member, .js-edit-announcement');
      if (btn) {
        const classList = btn.classList;
        if (classList.contains('js-edit-event')) {
          const id = btn.dataset.id;
          const name = btn.dataset.name;
          const clubId = btn.dataset.clubId;
          const coordinator = btn.dataset.coordinator;
          const venue = btn.dataset.venue;
          const startDate = btn.dataset.startDate;
          const startTime = btn.dataset.startTime;
          const endDate = btn.dataset.endDate;
          const endTime = btn.dataset.endTime;
          const maxParticipants = btn.dataset.maxParticipants;
          const status = btn.dataset.status;
          const description = btn.dataset.description;
          const imageUrl = btn.dataset.imageUrl;

          // Populate form fields
          document.getElementById('editEventId').value = id || '';
          document.getElementById('editEventName').value = name || '';
          document.getElementById('editOrganisingClub').value = clubId || '';
          document.getElementById('editEventCoordinator').value = coordinator || '';
          document.getElementById('editVenue').value = venue || '';
          document.getElementById('editStartDate').value = startDate || '';
          document.getElementById('editStartTime').value = startTime || '';
          document.getElementById('editEndDate').value = endDate || '';
          document.getElementById('editEndTime').value = endTime || '';
          document.getElementById('editMaxParticipants').value = maxParticipants || '';
 //          document.getElementById('editStatus').value = status || '';
             document.getElementById('editStatus').value = (status || 'upcoming').toLowerCase();
            // fire change so status-aware date rules run immediately
          document.getElementById('editStatus').dispatchEvent(new Event('change', { bubbles: true }));

document.getElementById('editEventDescription').value = description || '';

          // Handle image preview
          const fileWrap = document.getElementById('editEventImage').closest('.file-input-wrapper');
          const img = fileWrap?.querySelector('.file-preview');
          const nameEl = fileWrap?.querySelector('.file-name');
          if (imageUrl && img) {
            img.src = imageUrl;
            img.style.display = 'block';
            if (nameEl) nameEl.textContent = 'Current image';
          } else {
            if (img) {
              img.removeAttribute('src');
              img.style.display = 'none';
            }
            if (nameEl) nameEl.textContent = 'No file chosen';
          }
        } else if (classList.contains('js-edit-club')) {
          setTimeout(() => {
            const id = btn.dataset.id;
            const name = btn.dataset.name;
            const category = btn.dataset.category;
            const description = btn.dataset.description;
            const imageUrl = btn.dataset.imageUrl;
            const status = btn.dataset.status;

            // Populate form fields
            document.getElementById('editClubId').value = id || '';
            document.getElementById('editClubName').value = name || '';
            document.getElementById('editCategory').value = category || '';
            document.getElementById('editDescription').value = description || '';
//            document.getElementById('editClubStatus').value = status || 'active';
            document.getElementById('editClubStatus').value =
  (btn.dataset.status || 'active').toLowerCase() === 'inactive' ? 'inactive' : 'active';


            // Handle image preview
            const fileWrap = document.getElementById('editClubLogo').closest('.file-input-wrapper');
            const img = fileWrap?.querySelector('.file-preview');
            const nameEl = fileWrap?.querySelector('.file-name');
            if (imageUrl && img) {
              img.src = imageUrl;
              img.style.display = 'block';
              if (nameEl) nameEl.textContent = 'Current logo';
            } else {
              if (img) {
                img.removeAttribute('src');
                img.style.display = 'none';
              }
              if (nameEl) nameEl.textContent = 'No file chosen';
            }
          }, 0);
        } else if (classList.contains('js-edit-college')) {
          const id = btn.dataset.id;
          const name = btn.dataset.name;
          const location = btn.dataset.location;
          const authorityName = btn.dataset.authorityName;
          const authorityRole = btn.dataset.authorityRole;
          const email = btn.dataset.email;
          const phone = btn.dataset.phone;
          const status = btn.dataset.status;
          const description = btn.dataset.description;

          // Populate form fields
          document.getElementById('editCollegeId').value = id || '';
          document.getElementById('editCollegeName').value = name || '';
          document.getElementById('editLocation').value = location || '';
          document.getElementById('editAuthorityName').value = authorityName || '';
          document.getElementById('editAuthorityRole').value = authorityRole || '';
          document.getElementById('editEmail').value = email || '';
          document.getElementById('editPhone').value = phone || '';
          document.getElementById('editCollegeStatus').value = status || '';
          document.getElementById('editCollegeDescription').value = description || '';
        } else if (classList.contains('js-edit-coordinator')) {
          const id = btn.dataset.id;
          const name = btn.dataset.name;
          const clubId = btn.dataset.clubId;
          const collegeId = btn.dataset.collegeId;
          const facultyDept = btn.dataset.facultyDept;
          const roleType = btn.dataset.roleType;
          const email = btn.dataset.email;
          const phone = btn.dataset.phone;
          const description = btn.dataset.description;
          const status = btn.dataset.status;
          const imageUrl = btn.dataset.imageUrl;

          // Populate form fields
          document.getElementById('editCoordinatorId').value = id || '';
          document.getElementById('editCoordName').value = name || '';
          document.getElementById('editClubSelect').value = clubId || '';
          document.getElementById('editCollegeSelect').value = collegeId || '';
          document.getElementById('editFacultyDept').value = facultyDept || '';
          document.getElementById('editRoleType').value = roleType || '';
          document.getElementById('editCoordEmail').value = email || '';
          document.getElementById('editCoordPhone').value = phone || '';
          document.getElementById('editCoordDesc').value = description || '';
          document.getElementById('editCoordStatus').value = status || 'active';

          // Handle image preview
          const fileWrap = document.getElementById('editCoordImage').closest('.file-input-wrapper');
          const img = fileWrap?.querySelector('.file-preview');
          const nameEl = fileWrap?.querySelector('.file-name');
          if (imageUrl && img) {
            img.src = imageUrl;
            img.style.display = 'block';
            if (nameEl) nameEl.textContent = 'Current image';
          } else {
            if (img) {
              img.removeAttribute('src');
              img.style.display = 'none';
            }
            if (nameEl) nameEl.textContent = 'No file chosen';
          }
    } else if (classList.contains('js-edit-member')) {
  // Wait until the modal is rendered
  setTimeout(() => {
    const id          = btn.dataset.id || '';
    const name        = btn.dataset.name || '';
    const clubIds     = (btn.dataset.clubIds || '').split(',').map(s => s.trim()).filter(Boolean);
    const collegeId   = btn.dataset.collegeId || '';
    const facultyDept = btn.dataset.facultyDept || '';
    const email       = btn.dataset.email || '';
    const phone       = btn.dataset.phone || '';
    const description = btn.dataset.description || '';
    const status      = (btn.dataset.status || 'active').toLowerCase();
    const imageUrl    = btn.dataset.imageUrl || '';
    const imageName   = btn.dataset.imageName || '';

    // Basic fields
    const idEl   = document.getElementById('editMemberId');
    const nameEl = document.getElementById('editMemberName');
    const colSel = document.getElementById('editMemberCollegeSelect');
    const deptEl = document.getElementById('editMemberFacultyDept');
    const emEl   = document.getElementById('editMemberEmail');
    const phEl   = document.getElementById('editMemberPhone');
    const descEl = document.getElementById('editMemberDesc');
    const stEl   = document.getElementById('editMemberStatus');

    if (idEl)   idEl.value = id;
    if (nameEl) nameEl.value = name;
    if (colSel) colSel.value = collegeId || '';
    if (deptEl) deptEl.value = facultyDept;
    if (emEl)   emEl.value = email;
    if (phEl)   phEl.value = phone;
    if (descEl) descEl.value = description;
    if (stEl)   stEl.value = (status === 'inactive') ? 'inactive' : 'active';

    // --- Clubs multi-select (Choices.js) ---
    const clubSel = document.getElementById('editMemberClubSelect');
    if (clubSel) {
      const want = new Set(clubIds.map(String));

      // 1) Mark <option> selections in the native select
      Array.from(clubSel.options).forEach(opt => {
        opt.selected = want.has(String(opt.value));
      });

      // 2) Sync the Choices UI if present
      if (clubSel._choices) {
        clubSel._choices.removeActiveItems();                // clear previous
        clubSel._choices.setChoiceByValue(Array.from(want)); // select by values
      } else {
        clubSel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    // Image preview
    const fileWrap = document.getElementById('editMemberImage')?.closest('.file-input-wrapper');
    const imgPrev  = fileWrap?.querySelector('.file-preview');
    const nameEl2  = fileWrap?.querySelector('.file-name');
    if (imgPrev && nameEl2) {
      if (imageUrl) {
        imgPrev.src = imageUrl;
        imgPrev.style.display = 'block';
        nameEl2.textContent = imageName || 'Current image';
      } else {
        imgPrev.removeAttribute('src');
        imgPrev.style.display = 'none';
        nameEl2.textContent = 'No file chosen';
      }
    }
  }, 0);
}

else if (classList.contains('js-edit-announcement')) {
          setTimeout(() => {
            const id = btn.dataset.id;
            const title = btn.dataset.title;
            const content = btn.dataset.content;
            const clubId = btn.dataset.clubId;
            const status = btn.dataset.status;
            const publishDate = btn.dataset.publishDate;
            const publishTime = btn.dataset.publishTime;
            const expireDate = btn.dataset.expireDate;
            const expireTime = btn.dataset.expireTime;
            const priority = btn.dataset.priority;
            const audience = btn.dataset.audience;
            const sendEmail = btn.dataset.sendEmail;
            const pinned = btn.dataset.pinned;

            // Populate form fields
            document.getElementById('editAnnId').value = id || '';
            document.getElementById('editAnnTitle').value = title || '';
            document.getElementById('editAnnContent').value = content || '';
            document.getElementById('editAnnClub').value = clubId || '';
            document.getElementById('editAnnStatus').value = status || '';
            document.getElementById('editPublishDate').value = publishDate || '';
            document.getElementById('editPublishTime').value = publishTime || '';
            document.getElementById('editExpireDate').value = expireDate || '';
            document.getElementById('editExpireTime').value = expireTime || '';
            document.getElementById('editPriority').value = priority || '';
            document.getElementById('editAudience').value = audience || '';
             // ✅ Auto-check based on dataset (supports "1"/"0" and "true"/"false")
    const pinnedEl    = document.getElementById('editPinned');
    const sendEmailEl = document.getElementById('editSendEmail');

    if (pinnedEl)    pinnedEl.checked    = (btn.dataset.pinned === '1' || btn.dataset.pinned === 'true');
    if (sendEmailEl) sendEmailEl.checked = (btn.dataset.sendEmail === '1' || btn.dataset.sendEmail === 'true');
  }, 0);
        }
      }
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
//document.addEventListener('DOMContentLoaded', () => {
//  const today = new Date().toISOString().split('T')[0];
//  document.querySelectorAll('input[type="date"]').forEach((el) => (el.min = today));
//});
//To enable past edates for edit events
// === EVENTS (EDIT): status-aware date requirements ===
document.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];

  function setReq(el, on) { if (!el) return; on ? el.setAttribute('required','required') : el.removeAttribute('required'); }
  function setMin(el, v)  { if (!el) return; v ? el.setAttribute('min', v) : el.removeAttribute('min'); el.setCustomValidity(''); }

  function wireEventEditRules() {
    const scope   = document.getElementById('eventEditModal');
    if (!scope) return;

    const status  = scope.querySelector('#editStatus');
    const sDate   = scope.querySelector('#editStartDate');
    const sTime   = scope.querySelector('#editStartTime');
    const eDate   = scope.querySelector('#editEndDate');
    const eTime   = scope.querySelector('#editEndTime');

    function apply() {
      const isUpcoming = (status?.value || '').toLowerCase() === 'upcoming';

      // UPCOMING → start is required; end optional; dates >= today
      setReq(sDate, isUpcoming);
      setReq(sTime, isUpcoming);
      setReq(eDate, false);
      setReq(eTime, false);

      // Only enforce min=today for UPCOMING; allow past dates for completed/cancelled
      setMin(sDate, isUpcoming ? today : null);
      setMin(eDate, isUpcoming ? today : null);
    }

    apply();
    status?.addEventListener('change', apply);
    scope.addEventListener('modal:open', apply); // re-apply every time the modal opens
  }

  wireEventEditRules();
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
    if (k === 'college') return (tds[2]?.textContent || '').trim();
    if (k === 'email') return (tds[3]?.textContent || '').trim();
    if (k === 'status') return (tds[5]?.textContent || '').trim().toLowerCase();
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
          [field(r, 'name'), field(r, 'coordinator'), field(r, 'club'), field(r, 'college'), field(r, 'email')]
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
        else if (m === 'department') rows.sort((a, b) => coll.compare(field(a, 'department'), field(b, 'department')));
        else if (m === 'email') rows.sort((a, b) => coll.compare(field(a, 'email'), field(b, 'email')));
      }
      render(rows);
    }
    if (se) { const f = se.closest('form'); if (f) f.addEventListener('submit', (e) => e.preventDefault()); se.addEventListener('input', apply); }
    if (sf) sf.addEventListener('change', apply);
    if (so) so.addEventListener('change', apply);
    apply();
  };
})();

//To enable past dates in edit events and disable in create events
// === EVENTS: unified status-aware date rules (Create + Edit) ===
document.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  const setReq = (el, on) => { if (!el) return; on ? el.setAttribute('required','required') : el.removeAttribute('required'); };
  const setMin = (el, v)  => { if (!el) return; v ? el.setAttribute('min', v) : el.removeAttribute('min'); el.setCustomValidity(''); };

  function wireEventDateRules({ scopeId, statusSel, sDateSel, sTimeSel, eDateSel, eTimeSel }) {
    const scope = document.getElementById(scopeId); if (!scope) return;
    const status = scope.querySelector(statusSel);
    const sDate  = scope.querySelector(sDateSel);
    const sTime  = scope.querySelector(sTimeSel);
    const eDate  = scope.querySelector(eDateSel);
    const eTime  = scope.querySelector(eTimeSel);

    function apply() {
      const isUpcoming = (status?.value || '').toLowerCase() === 'upcoming';

      // Required only for upcoming
      setReq(sDate, isUpcoming);
      setReq(sTime, isUpcoming);
      setReq(eDate, false);
      setReq(eTime, false);

      // Min only for upcoming; allow past dates for completed/cancelled
      setMin(sDate, isUpcoming ? today : null);
      setMin(eDate, isUpcoming ? (sDate?.value || today) : null);

      // keep end >= start if both set
      if (eDate?.value && sDate?.value && eDate.value < sDate.value) {
        eDate.value = sDate.value;
      }
    }

    status?.addEventListener('change', apply);
    sDate?.addEventListener('change', apply);
    scope.addEventListener('modal:open', apply);
    apply();
  }

  // Create modal
  wireEventDateRules({
    scopeId:  'eventModal',
    statusSel:'#status',
    sDateSel: 'input[name="start_date"]',
    sTimeSel: 'select[name="start_time"]',
    eDateSel: 'input[name="end_date"]',
    eTimeSel: 'select[name="end_time"]',
  });

  // Edit modal
  wireEventDateRules({
    scopeId:  'eventEditModal',
    statusSel:'#editStatus',
    sDateSel: '#editStartDate',
    sTimeSel: '#editStartTime',
    eDateSel: '#editEndDate',
    eTimeSel: '#editEndTime',
  });
});
/////////////////////

// === GENERAL SEARCH WITH DROPDOWN + FEATURED CARD ===
function initSearch({ inputId, choicesId, cardId, containerSelector, itemSelector, cardFields, searchFields, hasDelete = false, prefix = 'fe', type = '' }) {
  const input = document.getElementById(inputId);
  const choices = document.getElementById(choicesId);
  const card = document.getElementById(cardId);
  if (!input || !choices || !card) return;

  // Build items from container
  const items = [...document.querySelectorAll(containerSelector + ' ' + itemSelector)].map((row) => {
    const edit = row.querySelector('.js-edit-club, .js-edit-event, .js-edit-college, .js-edit-coordinator, .js-edit-member, .js-edit-announcement');
    const item = {
      id: edit?.dataset.id || row.dataset.id || '',
      name: (row.dataset.name || row.dataset.title || '').trim(),
      row,
      editBtn: edit
    };
    // Add card fields
    cardFields.forEach(field => {
      if (field === 'participants') {
        item[field] = edit?.dataset[field] || edit?.dataset.maxParticipants || row.dataset[field] || '';
      } else {
        item[field] = edit?.dataset[field] || row.dataset[field] || '';
      }
    });
    return item;
  });

  function resetCard() {
    card.hidden = true;
    // Reset card elements based on cardFields
    cardFields.forEach(field => {
      const el = document.getElementById(prefix + field.charAt(0).toUpperCase() + field.slice(1));
      if (el) {
        if (field === 'imageUrl') {
          el.removeAttribute('src');
          el.style.display = 'none';
        } else {
          el.textContent = '';
        }
      }
    });
  }

  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'<','>':'>','"':'"',"'":'&#39;'}[m]));
  }

  function showChoices(matches, disabled = false) {
    choices.innerHTML = matches.map(item =>
      `<div class="dropdown-item" data-id="${escapeHtml(item.id)}"${disabled ? ' disabled' : ''}>${escapeHtml(item.name)}</div>`
    ).join('');
    choices.hidden = false;
  }

  function fillCard(item) {
    cardFields.forEach(field => {
      const el = document.getElementById(prefix + field.charAt(0).toUpperCase() + field.slice(1));
      if (el) {
        if (field === 'imageUrl') {
          if (item[field]) {
            el.src = item[field];
            el.alt = item.imageName || item.name || 'Image';
            el.style.display = '';
          } else {
            el.removeAttribute('src');
            el.style.display = 'none';
          }
        } else {
          let text = item[field] || '—';
          if (field === 'club' && text !== '—') {
            text = '<strong>Club - </strong>' + text;
          } else if (field === 'startDateTime' && text !== '—' && (cardId === 'featuredEventCard' || cardId === 'searchFeaturedEventCard')) {
            // Parse "YYYY-MM-DD at HH:MM" to "DD-MM-YYYY & HH:MM AM/PM"
            const parts = text.split(' at ');
            if (parts.length === 2) {
              const datePart = parts[0]; // YYYY-MM-DD
              const timePart = parts[1]; // HH:MM
              const [year, month, day] = datePart.split('-');
              const formattedDate = `${day}-${month}-${year}`;
              // Convert HH:MM to 12-hour with AM/PM
              const [hour, minute] = timePart.split(':');
              const hourInt = parseInt(hour, 10);
              const ampm = hourInt >= 12 ? 'PM' : 'AM';
              const hour12 = hourInt % 12 || 12;
              const formattedTime = `${hour12}:${minute} ${ampm}`;
              text = `<strong>Date & Time - </strong>${formattedDate} & ${formattedTime}`;
            }
          } else if (field === 'venue' && text !== '—' && (cardId === 'featuredEventCard' || cardId === 'searchFeaturedEventCard')) {
            text = '<strong>Venue - </strong>' + text;
          }
          el.innerHTML = text;
        }
      }
    });
    const btnEdit = document.getElementById(prefix + 'EditBtn');
    if (btnEdit) btnEdit.onclick = (e) => { e.preventDefault(); item.editBtn?.click(); };
    if (hasDelete) {
      const btnDel = document.getElementById(prefix + 'DeleteBtn');
      if (btnDel) btnDel.onclick = (e) => { e.preventDefault(); openDeleteModal({ ...item, type }); };
    }
    card.hidden = false;
  }

  // init
  resetCard();

  // Input → matches containing the input as substring
  input.addEventListener('input', () => {
    const v = input.value.trim();
    if (!v) { choices.hidden = true; resetCard(); return; }
    const matches = items
      .filter(item => searchFields.some(field => (item[field] || '').toLowerCase().includes(v.toLowerCase())))
      .sort((a,b) => a.name.localeCompare(b.name));
    if (matches.length === 0) {
      choices.hidden = true;
      resetCard();
    } else if (matches.length === 1) {
      fillCard(matches[0]);
      choices.hidden = true;
    } else {
      showChoices(matches);
      resetCard();
    }
  });

  // Select → show card, then hide dropdown
  choices.addEventListener('click', (e) => {
    if (e.target.classList.contains('dropdown-item')) {
      const id = e.target.dataset.id;
      const item = items.find(i => i.id === id);
      if (!item) return;
      fillCard(item);
      choices.hidden = true;
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!choices.contains(e.target) && !input.contains(e.target)) choices.hidden = true;
  });

  // ESC → hide dropdown + card
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { choices.hidden = true; resetCard(); input.blur(); }
  });

  // Handle "View Details" clicks for upcoming events
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.event-btn');
    if (btn && btn.textContent.trim() === 'View Details') {
      e.preventDefault();
      const item = {
        id: btn.dataset.id,
        name: btn.dataset.name,
        club: btn.dataset.club,
        venue: btn.dataset.venue,
        description: btn.dataset.description,
        imageUrl: btn.dataset.imageUrl,
        imageName: btn.dataset.imageName,
        participants: btn.dataset.participants,
        coordinator: btn.dataset.coordinator,
        status: btn.dataset.status,
        colleges: btn.dataset.colleges,
        startDateTime: btn.dataset.startDateTime
      };
      // Use the upcoming featured card
      const card = document.getElementById('upcomingFeaturedEventCard');
      const cardFields = ['name', 'club', 'venue', 'description', 'imageUrl', 'imageName', 'participants', 'coordinator', 'status', 'colleges', 'startDateTime'];
      cardFields.forEach(field => {
        const el = document.getElementById('ufe' + field.charAt(0).toUpperCase() + field.slice(1));
        if (el) {
          if (field === 'imageUrl') {
            if (item[field]) {
              el.src = item[field];
              el.alt = item.imageName || item.name || 'Image';
              el.style.display = '';
            } else {
              el.removeAttribute('src');
              el.style.display = 'none';
            }
          } else {
            let text = item[field] || '—';
            if (field === 'club' && text !== '—') {
              text = '<strong>Club - </strong>' + text;
            } else if (field === 'startDateTime' && text !== '—') {
              // Parse "YYYY-MM-DD at HH:MM" to "DD-MM-YYYY & HH:MM AM/PM"
              const parts = text.split(' at ');
              if (parts.length === 2) {
                const datePart = parts[0]; // YYYY-MM-DD
                const timePart = parts[1]; // HH:MM
                const [year, month, day] = datePart.split('-');
                const formattedDate = `${day}-${month}-${year}`;
                // Convert HH:MM to 12-hour with AM/PM
                const [hour, minute] = timePart.split(':');
                const hourInt = parseInt(hour, 10);
                const ampm = hourInt >= 12 ? 'PM' : 'AM';
                const hour12 = hourInt % 12 || 12;
                const formattedTime = `${hour12}:${minute} ${ampm}`;
                text = `<strong>Date & Time - </strong>${formattedDate} & ${formattedTime}`;
              }
            } else if (field === 'venue' && text !== '—') {
              text = '<strong>Venue - </strong>' + text;
            }
            el.innerHTML = text;
          }
        }
      });
      card.hidden = false;
      card.scrollIntoView({ behavior: 'smooth' });

      // Set up Edit and Delete buttons for upcoming featured event card
      const btnEdit = document.getElementById('ufeEditBtn');
      if (btnEdit) {
        btnEdit.onclick = (e) => {
          e.preventDefault();
          // Find the edit button from the events table
          const editBtns = document.querySelectorAll('[data-table="events"] tbody tr .js-edit-event');
          const editBtn = Array.from(editBtns).find(btn => btn.dataset.id === item.id);
          if (editBtn) editBtn.click();
        };
      }
      const btnDel = document.getElementById('ufeDeleteBtn');
      if (btnDel) {
        btnDel.onclick = (e) => {
          e.preventDefault();
          openDeleteModal({ id: item.id, name: item.name, type: 'event' });
        };
      }
      // Set up Close button for upcoming featured event card
      const btnClose = document.getElementById('ufeCloseBtn');
      if (btnClose) {
        btnClose.onclick = (e) => {
          e.preventDefault();
          card.hidden = true;
        };
      }
    }
  });
}

// === INIT SORTERS ===
document.addEventListener('DOMContentLoaded', () => {
  if (window.initFilterSort) {
    initFilterSort({ tbody: '[data-table="clubs"] tbody', status: '#statusFilter', sort: '#sortBy', emptyColspan: 6 });
    initFilterSort({ tbody: '[data-table="events"] tbody', status: '#eventStatusFilter', sort: '#eventSortBy', emptyColspan: 7 });
    initFilterSort({ tbody: '[data-table="colleges"] tbody', status: '#collegeStatusFilter', sort: '#collegeSortBy', emptyColspan: 7 });
    initFilterSort({ tbody: '[data-table="coordinators"] tbody', status: '#coordClubFilter', sort: '#coordSortBy', emptyColspan: 6, filterKey: 'club-id' });
    initFilterSort({ tbody: '[data-table="members"] tbody', status: '#memberStatusFilter', sort: '#memberSortBy', emptyColspan: 7, filterKey: 'status' });
  }




//SORT END
// === GENERAL SEARCH WITH DROPDOWN + FEATURED CARD ===
  // Init searches
  initSearch({
    inputId: 'clubSearch',
    choicesId: 'clubChoices',
    cardId: 'featuredCard',
    containerSelector: '[data-table="clubs"]',
    itemSelector: 'tbody tr[data-name]',
    cardFields: ['name', 'description', 'imageUrl', 'imageName', 'members', 'coordinator'],
    searchFields: ['name'],
    hasDelete: true,
    type: 'club'
  });

  // Set up Close button for featured club card
  const feCloseBtn = document.getElementById('feCloseBtn');
  if (feCloseBtn) {
    feCloseBtn.onclick = (e) => {
      e.preventDefault();
      document.getElementById('featuredCard').hidden = true;
    };
  }

  initSearch({
    inputId: 'eventSearch',
    choicesId: 'eventChoices',
    cardId: 'searchFeaturedEventCard',
    containerSelector: '[data-table="events"]',
    itemSelector: 'tbody tr[data-name]',
    cardFields: ['name', 'club', 'venue', 'description', 'imageUrl', 'imageName', 'participants', 'coordinator', 'status', 'colleges', 'startDateTime'],
    searchFields: ['name'],
    hasDelete: true,
    prefix: 'sfe',
    type: 'event'
  });

  // Set up Close button for search featured event card
  const sfeCloseBtn = document.getElementById('sfeCloseBtn');
  if (sfeCloseBtn) {
    sfeCloseBtn.onclick = (e) => {
      e.preventDefault();
      document.getElementById('searchFeaturedEventCard').hidden = true;
    };
  }

  initSearch({
    inputId: 'collegeSearch',
    choicesId: 'collegeChoices',
    cardId: 'featuredCollegeCard',
    containerSelector: '[data-table="colleges"]',
    itemSelector: 'tbody tr[data-name]',
    cardFields: ['name', 'location', 'email', 'status'],
    searchFields: ['name'],
    hasDelete: true,
    prefix: 'fc',
    type: 'college'
  });

  initSearch({
    inputId: 'coordinatorSearch',
    choicesId: 'coordinatorChoices',
    cardId: 'featuredCoordinatorCard',
    containerSelector: '[data-table="coordinators"]',
    itemSelector: 'tbody tr[data-name]',
    cardFields: ['name', 'description', 'club', 'department', 'email', 'phone', 'imageUrl'],
    searchFields: ['name', 'club', 'department', 'email'],
    hasDelete: true,
    prefix: 'fco',
    type: 'coordinator'
  });



  initSearch({
    inputId: 'annSearch',
    choicesId: 'annChoices',
    cardId: 'featuredAnnCard',
    containerSelector: '#annList',
    itemSelector: '.announcement-card',
    cardFields: ['title', 'content', 'club', 'status'],
    searchFields: ['title', 'content', 'club'],
    hasDelete: true,
    prefix: 'fa',
    type: 'announcement'
  });

  initSearch({
    inputId: 'memberSearch',
    choicesId: 'memberChoices',
    cardId: 'featuredMemberCard',
    containerSelector: '[data-table="members"]',
    itemSelector: 'tbody tr[data-name]',
    cardFields: ['name', 'description', 'club', 'college', 'email', 'phone', 'imageUrl'],
    searchFields: ['name', 'club', 'college', 'email'],
    hasDelete: true,
    prefix: 'fm',
    type: 'member'
  });

  // Set up Close button for featured college card
  const fcCloseBtn = document.getElementById('fcCloseBtn');
  if (fcCloseBtn) {
    fcCloseBtn.onclick = (e) => {
      e.preventDefault();
      document.getElementById('featuredCollegeCard').hidden = true;
    };
  }

  // Set up Close button for featured announcement card
  const faCloseBtn = document.getElementById('faCloseBtn');
  if (faCloseBtn) {
    faCloseBtn.onclick = (e) => {
      e.preventDefault();
      document.getElementById('featuredAnnCard').hidden = true;
    };
  }

  // Set up Close button for featured member card
  const fmCloseBtn = document.getElementById('fmCloseBtn');
  if (fmCloseBtn) {
    fmCloseBtn.onclick = (e) => {
      e.preventDefault();
      document.getElementById('featuredMemberCard').hidden = true;
    };
  }
});

// === GENERIC DELETE MODAL ===
let pendingDelete = null;

function openDeleteModal(item) {
  pendingDelete = item;
  const delModal = document.getElementById('deleteConfirmModal');
  const delBodyP = delModal?.querySelector('.delete-modal-body p');
  if (delBodyP) {
    delBodyP.textContent = `Are you sure you want to remove "${item.name}"?`;
  }
  delModal.hidden = false;
}

function closeDeleteModal() {
  const delModal = document.getElementById('deleteConfirmModal');
  delModal.hidden = true;
  pendingDelete = null;
}

document.addEventListener('DOMContentLoaded', () => {
  const delModal = document.getElementById('deleteConfirmModal');
  const delConfirm = document.getElementById('confirmDeleteBtn');
  const delCancel = document.getElementById('cancelDeleteBtn');
  const delClose = document.getElementById('closeDeleteModal');

  if (delCancel) delCancel.onclick = closeDeleteModal;
  if (delClose) delClose.onclick = closeDeleteModal;
  if (delModal) {
    delModal.addEventListener('click', (e) => {
      if (e.target === delModal) closeDeleteModal();
    });
  }
  if (delConfirm) {
    delConfirm.onclick = () => {
      if (!pendingDelete) return;
      const {id, type} = pendingDelete;
      const formId = `delete${type.charAt(0).toUpperCase() + type.slice(1)}Form`;
      const inputId = `delete${type.charAt(0).toUpperCase() + type.slice(1)}Id`;
      const form = document.getElementById(formId);
      const input = document.getElementById(inputId);
      if (form && input) {
        input.value = id;
        form.submit();
      }
    };
  }

  // Handle delete button clicks for all entities
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.js-delete-club, .js-delete-event, .js-delete-college, .js-delete-coordinator, .js-delete-member, .js-delete-announcement');
    if (btn) {
      // Prevent default anchor navigation/hash change which can interfere when inside forms
      e.preventDefault();
      const classList = btn.classList;
      let type;
      if (classList.contains('js-delete-club')) type = 'club';
      else if (classList.contains('js-delete-event')) type = 'event';
      else if (classList.contains('js-delete-college')) type = 'college';
      else if (classList.contains('js-delete-coordinator')) type = 'coordinator';
      else if (classList.contains('js-delete-member')) type = 'member';
      else if (classList.contains('js-delete-announcement')) type = 'announcement';
      const id = btn.dataset.id;
      const name = btn.dataset.name;
      openDeleteModal({id, name, type});
    }
  });
});

//Multi select in members
// === ENHANCE ALL <select multiple> WITH Choices.js ===
document.addEventListener('DOMContentLoaded', () => {
  if (typeof Choices === 'undefined') return; // fallback if CDN blocked
  document.querySelectorAll('select[multiple]').forEach((sel) => {
    if (sel.dataset.choicesInit) return;       // Avoid double-init
    const inst = new Choices(sel, {
      removeItemButton: true,
      placeholder: true,
      placeholderValue: 'Select options',
      searchPlaceholderValue: 'Search...',
      shouldSort: true,
    });
    sel._choices = inst;                       // <-- store instance for later
    sel.dataset.choicesInit = 'true';
  });
});



//PAGINATION

// === GENERIC PAGER (tables OR cards) ===
(function () {
  function initPager({
    container,            // parent element that holds the items (tbody or div)
    itemSelector,         // 'tr' for tables, '.announcement-card' for cards
    pager,                // nav element for pagination buttons
    perPage = 5,          // items per page
    requireDataId = true, // only paginate items with data-id (safe for tables/cards)
  } = {}) {
    const root = typeof container === 'string' ? document.querySelector(container) : container;
    const pg   = typeof pager === 'string' ? document.querySelector(pager) : pager;
    if (!root || !pg) return;

    let items = [];
    let page = 1;

    function collect() {
      items = [...root.querySelectorAll(itemSelector)];
      if (requireDataId) items = items.filter(el => el.dataset && el.dataset.id);
      page = 1;
    }

    function totalPages() {
      return Math.max(1, Math.ceil(items.length / perPage));
    }

    function renderControls(total) {
      const prevDisabled = page === 1, nextDisabled = page === total;
      const btn = (label, go, { disabled = false, active = false } = {}) =>
        `<button class="page-btn${active ? ' active' : ''}${disabled ? ' disabled' : ''}"
                 data-go="${go}" ${disabled ? 'disabled' : ''}>${label}</button>`;

      const windowSize = 5;
      let start = Math.max(1, page - Math.floor(windowSize / 2));
      let end   = Math.min(total, start + windowSize - 1);
      start     = Math.max(1, end - windowSize + 1);

      let html = btn('Prev', String(page - 1), { disabled: prevDisabled });
      for (let p = start; p <= end; p++) html += btn(String(p), String(p), { active: p === page });
      html += btn('Next', String(page + 1), { disabled: nextDisabled });

      pg.innerHTML = html;
    }

    function render() {
      const total = totalPages();
      const start = (page - 1) * perPage;
      const end   = start + perPage;

      items.forEach((el, i) => { el.style.display = (i >= start && i < end) ? '' : 'none'; });

      pg.style.display = items.length > perPage ? 'flex' : 'none';
      renderControls(total);
    }

    pg.addEventListener('click', (e) => {
      const b = e.target.closest('.page-btn');
      if (!b || b.classList.contains('disabled')) return;

      const total = totalPages();
      const label = b.textContent.trim();
      const go    = Number(b.dataset.go);

      if (label === 'Prev') page = Math.max(1, page - 1);
      else if (label === 'Next') page = Math.min(total, page + 1);
      else if (!Number.isNaN(go)) page = Math.min(total, Math.max(1, go));

      render();
    });

    // Recompute when container changes (your sort/filter rewrites DOM)
    const mo = new MutationObserver(() => { collect(); render(); });
    mo.observe(root, { childList: true });

    collect(); render();
  }

  // Expose for reuse
  window.initPager = initPager;
})();

//clubs pagination
document.addEventListener('DOMContentLoaded', () => {
  initPager({
    container: '[data-table="clubs"] tbody',
    itemSelector: 'tr',
    pager: '#clubsPagination',
    perPage: 5
  });
});

//events pagination
document.addEventListener('DOMContentLoaded', () => {
  initPager({
    container: '[data-table="events"] tbody',
    itemSelector: 'tr',
    pager: '#eventsPagination',
    perPage: 5
  });
});
//colleges pagination
initPager({
  container: '[data-table="colleges"] tbody',
  itemSelector: 'tr',
  pager: '#collegesPagination',
  perPage: 5
});

//coordinators pagination
initPager({
  container: '[data-table="coordinators"] tbody',
  itemSelector: 'tr',
  pager: '#coordinatorsPagination',
  perPage: 5
});

//announcement page
document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('#annList');
  const cards = list ? list.querySelectorAll('.announcement-card') : [];
  console.log('[ann pager] found list:', !!list, 'cards:', cards.length);

  initPager({
    container: '#annList',
    itemSelector: '.announcement-card',
    pager: '#annPagination',
    perPage: 5,        // adjust page size as you like
    requireDataId: true
  });
});

//members pagination
document.addEventListener('DOMContentLoaded', () => {
  initPager({
    container: '[data-table="members"] tbody',
    itemSelector: 'tr',
    pager: '#membersPagination',
    perPage: 5
  });
});
