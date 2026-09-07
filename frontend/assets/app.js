const PAGE_SIZE = 6;
const CARD_LINK_LIMIT = 2;
const API_BASE_URL = '/api';
const state = { items: [], page: 1, query: '', controller: null, detailsController: null, note: '' };
const $ = function (id) { return document.getElementById(id); };
const form = $('searchForm');
const input = $('searchInput');
const submit = $('searchBtn');
const section = $('results');
const grid = $('resultsGrid');
const title = $('resultsTitle');
const count = $('resultsCount');
const note = $('resultsNote');
const pager = $('pagination');
const modal = $('resourceModal');
const modalDialog = modal.querySelector('.resource-dialog');
const modalTitle = $('resourceModalTitle');
const modalCount = $('resourceModalCount');
const modalList = $('resourceModalList');
const modalClose = $('resourceModalClose');
let modalTrigger = null;

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function safeUrl(value, protocols) {
  if (typeof value !== 'string') return '';
  const trimmed = value.trim();
  const lower = trimmed.toLowerCase();
  if (protocols.includes('magnet:') && lower.startsWith('magnet:')) return trimmed;
  if (protocols.includes('ed2k:') && lower.startsWith('ed2k://')) return trimmed;
  if (protocols.includes('ftp:') && lower.startsWith('ftp://')) return trimmed;
  try {
    const url = new URL(trimmed, location.href);
    return protocols.includes(url.protocol) ? url.href : '';
  } catch (error) {
    return '';
  }
}

const linkPresentation = {
  magnet: { protocols: ['magnet:'], fallback: '磁力链接', badge: 'MAG' },
  ed2k: { protocols: ['ed2k:'], fallback: 'ED2K 链接', badge: 'ED2K' },
  ftp: { protocols: ['ftp:'], fallback: 'FTP 下载', badge: 'FTP' },
  torrent: { protocols: ['http:', 'https:'], fallback: '种子文件', badge: 'TORRENT' }
};

function usableLinks(item) {
  return (Array.isArray(item.downloadLinks) ? item.downloadLinks : [])
    .map(function (link) {
      const display = linkPresentation[link.type];
      return display
        ? Object.assign({}, link, { display: display, safe: safeUrl(link.url, display.protocols) })
        : Object.assign({}, link, { safe: '' });
    })
    .filter(function (link) { return link.safe; });
}

function linkBadge(link, index) {
  return link.display.badge + (link.type === 'magnet' ? ' ' + (index + 1) : '');
}

function downloadLink(link, index, modalItem) {
  const anchor = el('a', modalItem ? 'resource-item' : 'download');
  anchor.href = link.safe;
  anchor.title = link.title || link.display.fallback;
  if (link.type === 'torrent') {
    anchor.target = '_blank';
    anchor.rel = 'noopener noreferrer';
  }
  if (modalItem) {
    const order = el('span', 'resource-order', String(index + 1).padStart(2, '0'));
    const details = el('span', 'resource-info');
    details.append(el('strong', '', link.title || link.display.fallback), el('small', '', link.type.toUpperCase()));
    anchor.append(order, details, el('b', '', '打开'));
  } else {
    anchor.append(el('span', '', link.title || link.display.fallback), el('b', '', linkBadge(link, index)));
  }
  return anchor;
}

function loading() {
  section.classList.add('show');
  title.textContent = '正在为你搜寻';
  count.textContent = 'COLLECTING';
  note.hidden = true;
  pager.classList.remove('show');
  pager.replaceChildren();
  grid.replaceChildren(...Array.from({ length: 6 }, function () { return el('div', 'skeleton'); }));
}

function status(heading, message, symbol) {
  const box = el('div', 'status');
  box.append(el('strong', '', symbol), el('h3', '', heading), el('p', '', message));
  grid.replaceChildren(box);
  pager.classList.remove('show');
  pager.replaceChildren();
}

function poster(item, primaryLink) {
  const wrap = primaryLink ? el('a', 'poster-wrap') : el('div', 'poster-wrap');
  if (primaryLink) {
    wrap.href = primaryLink.safe;
    wrap.title = primaryLink.title || primaryLink.display.fallback;
    if (primaryLink.type === 'torrent') {
      wrap.target = '_blank';
      wrap.rel = 'noopener noreferrer';
    }
  }
  const fallback = el('div', 'placeholder', 'A');
  const url = safeUrl(item.posterUrl, ['http:', 'https:']);
  if (url) {
    const img = el('img', 'poster');
    img.src = url;
    img.alt = item.title ? '《' + item.title + '》海报' : '电影海报';
    img.loading = 'lazy';
    img.referrerPolicy = 'no-referrer';
    img.addEventListener('load', function () { fallback.remove(); }, { once: true });
    img.addEventListener('error', function () { img.remove(); }, { once: true });
    wrap.append(img);
  }
  wrap.append(fallback, el('div', 'shade'), el('span', 'badge', 'CINEMA PICK'));
  return wrap;
}

function openResources(item, links, trigger) {
  modalTrigger = trigger;
  modalTitle.textContent = item.title || '全部可用资源';
  modalCount.textContent = links.length + ' 个可用下载资源';
  modalList.replaceChildren(...links.map(function (link, index) {
    return downloadLink(link, index, true);
  }));
  modal.hidden = false;
  document.body.classList.add('modal-open');
  modalDialog.focus();
}

function closeResources() {
  if (modal.hidden) return;
  modal.hidden = true;
  document.body.classList.remove('modal-open');
  modalList.replaceChildren();
  if (modalTrigger && document.contains(modalTrigger)) modalTrigger.focus();
  modalTrigger = null;
}

function card(item, index) {
  const article = el('article', 'card');
  const links = usableLinks(item);
  article.append(poster(item, links[0]));
  const body = el('div', 'card-body');
  body.append(
    el('div', 'index', 'SELECTION ' + String(index + 1).padStart(2, '0')),
    el('h3', 'movie-title', item.title || '未命名影片')
  );
  const list = el('div', 'downloads');
  if (links.length) {
    const visibleLinkLimit = links.length > 3 ? CARD_LINK_LIMIT : links.length;
    links.slice(0, visibleLinkLimit).forEach(function (link, linkIndex) {
      list.append(downloadLink(link, linkIndex, false));
    });
    if (links.length > 3) {
      const more = el('button', 'show-more', 'Show More');
      more.type = 'button';
      more.setAttribute('aria-haspopup', 'dialog');
      more.append(el('span', '', ' +' + (links.length - CARD_LINK_LIMIT)));
      more.addEventListener('click', function () { openResources(item, links, more); });
      list.append(more);
    }
  } else {
    list.append(el('div', 'empty', item.detailsLoaded ? '暂未发现可用资源链接' : '正在加载海报与资源…'));
  }
  body.append(list);
  article.append(body);
  return article;
}

function pageButton(label, target, disabled, active) {
  const button = el('button', 'page' + (active ? ' active' : ''), label);
  button.type = 'button';
  button.disabled = disabled;
  if (active) button.setAttribute('aria-current', 'page');
  button.addEventListener('click', function () {
    state.page = target;
    render();
    loadVisibleDetails();
    section.scrollIntoView({ behavior: 'smooth' });
  });
  return button;
}

function pagination(total) {
  pager.replaceChildren();
  if (total <= 1) {
    pager.classList.remove('show');
    return;
  }
  pager.append(pageButton('上一页', state.page - 1, state.page === 1, false));
  for (let page = 1; page <= total; page += 1) {
    pager.append(pageButton(String(page), page, false, page === state.page));
  }
  pager.append(pageButton('下一页', state.page + 1, state.page === total, false));
  pager.classList.add('show');
}

function render() {
  const total = state.items.length;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  state.page = Math.min(state.page, pages);
  const start = (state.page - 1) * PAGE_SIZE;
  const visible = state.items.slice(start, start + PAGE_SIZE);
  title.textContent = state.query ? '“' + state.query + '” 的甄选结果' : '为你甄选';
  count.textContent = total ? total + ' 部作品 · 第 ' + state.page + ' / ' + pages + ' 页' : '0 部作品';
  note.textContent = state.note;
  note.hidden = !state.note;
  if (!visible.length) {
    status('未找到相关作品', '换一个关键词试试，也许会遇见另一部值得收藏的电影。', '∅');
    return;
  }
  grid.replaceChildren(...visible.map(function (item, itemIndex) { return card(item, start + itemIndex); }));
  pagination(pages);
}

async function loadVisibleDetails() {
  if (state.detailsController) state.detailsController.abort();
  const page = state.page;
  const start = (page - 1) * PAGE_SIZE;
  const visible = state.items.slice(start, start + PAGE_SIZE);
  const pending = visible.filter(function (item) { return !item.detailsLoaded; });
  if (!pending.length) return;
  state.detailsController = new AbortController();
  try {
    const response = await fetch(API_BASE_URL + '/details', {
      method: 'POST',
      signal: state.detailsController.signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ urls: pending.map(function (item) { return item.detailUrl; }) })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '详情加载失败');
    const details = new Map(data.results.map(function (item) { return [item.detailUrl, item]; }));
    state.items = state.items.map(function (item) {
      const detail = details.get(item.detailUrl);
      return detail ? Object.assign({}, item, detail) : item;
    });
    if (state.page === page) render();
  } catch (error) {
    if (error.name !== 'AbortError') console.error('详情加载失败:', error);
  }
}

async function search(query) {
  query = query.trim();
  if (!query) {
    input.focus();
    return;
  }
  closeResources();
  if (state.controller) state.controller.abort();
  if (state.detailsController) state.detailsController.abort();
  state.controller = new AbortController();
  state.query = query;
  state.page = 1;
  state.note = '';
  submit.disabled = true;
  submit.textContent = '搜寻中…';
  loading();
  section.scrollIntoView({ behavior: 'smooth' });
  try {
    const response = await fetch(API_BASE_URL + '/search?q=' + encodeURIComponent(query), {
      signal: state.controller.signal,
      headers: { Accept: 'application/json' }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '搜索服务暂时不可用');
    state.items = Array.isArray(data.results) ? data.results : [];
    state.note = (typeof data.note === 'string' ? data.note : '')
      + (data.elapsedMs !== undefined ? ' · 搜索用时 ' + data.elapsedMs + ' ms' : '');
    render();
    loadVisibleDetails();
  } catch (error) {
    if (error.name === 'AbortError') return;
    state.items = [];
    title.textContent = '搜索暂时中断';
    count.textContent = 'PLEASE RETRY';
    status('未能完成搜索', error.message || '请稍后重试。', '!');
  } finally {
    submit.disabled = false;
    submit.textContent = '开始探索';
  }
}

form.addEventListener('submit', function (event) {
  event.preventDefault();
  search(input.value);
});
document.querySelectorAll('#moviesPanel .suggestion').forEach(function (button) {
  button.addEventListener('click', function () {
    input.value = button.dataset.query;
    search(button.dataset.query);
  });
});
modalClose.addEventListener('click', closeResources);
modal.addEventListener('click', function (event) {
  if (event.target.hasAttribute('data-modal-close')) closeResources();
});
document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') closeResources();
});
