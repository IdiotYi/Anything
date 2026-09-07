(() => {
  'use strict';

  const DEMO_MODE = false;
  const PAGE_SIZE = 6;
  const BOOK_SEARCH_ENDPOINT = '/api/books/search';
  const get = (id) => document.getElementById(id);
  const tabs = [get('moviesTab'), get('booksTab')];
  const panels = [get('moviesPanel'), get('booksPanel')];
  const form = get('bookSearchForm');
  const input = get('bookSearchInput');
  const button = get('bookSearchBtn');
  const results = get('bookResults');
  const grid = get('bookResultsGrid');
  const heading = get('bookResultsTitle');
  const count = get('bookResultsCount');
  const pager = get('bookPagination');
  let controller = null;
  let requestId = 0;

  const state = {
    books: [],
    page: 1,
    query: ''
  };

  const demoBooks = [
    { title: '红楼梦', author: '曹雪芹', language: '中文', description: '以贾、史、王、薛四大家族为背景的中国古典文学名著。', formats: ['EPUB', 'PDF', 'TXT'] },
    { title: '西游记', author: '吴承恩', language: '中文', description: '师徒四人一路西行的中国古典神话小说。', formats: ['EPUB', 'TXT'] },
    { title: 'Pride and Prejudice', author: 'Jane Austen', language: 'English', description: '简·奥斯汀关于爱情、家庭与社会观念的经典小说。', formats: ['EPUB', 'PDF'] }
  ];

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function selectTab(index, focus = false) {
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
    });
    if (typeof closeResources === 'function') closeResources();
    if (focus) tabs[index].focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(index));
    tab.addEventListener('keydown', (event) => {
      let next;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') next = 1 - index;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        selectTab(next, true);
      }
    });
  });

  async function searchBooks(query, signal) {
    if (DEMO_MODE) {
      const keyword = query.toLocaleLowerCase();
      return demoBooks.filter((book) =>
        (book.title + ' ' + book.author).toLocaleLowerCase().includes(keyword)
      ).map((book) => ({ ...book, demo: true, downloadLinks: [] }));
    }
    const response = await fetch(BOOK_SEARCH_ENDPOINT + '?q=' + encodeURIComponent(query), {
      signal, headers: { Accept: 'application/json' }
    });
    if (response.status === 404 || response.status === 501) {
      throw new Error('电子书服务尚未接入，请稍后再试。');
    }
    if (!response.ok) throw new Error('电子书搜索暂时不可用，请稍后重试。');
    const data = await response.json();
    if (!data || data.success === false || !Array.isArray(data.results)) {
      throw new Error('电子书服务返回的数据格式不正确。');
    }
    return data.results.filter((book) => book && typeof book.title === 'string');
  }

  function httpUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : '';
    } catch (_) {
      return '';
    }
  }

  function renderCard(book) {
    const card = node('article', 'card book-card');

    // (2) 书的图片 (封面)
    const coverWrap = node('div', 'book-cover-wrap');
    const coverImgUrl = httpUrl(book.coverUrl);
    if (coverImgUrl) {
      const img = node('img', 'book-cover-image');
      img.src = coverImgUrl;
      img.alt = book.title || '封面';
      img.loading = 'lazy';
      img.onerror = () => {
        img.remove();
        if (!coverWrap.querySelector('.book-cover-placeholder')) {
          coverWrap.append(renderFallbackCover(book));
        }
      };
      coverWrap.append(img);
    } else {
      coverWrap.append(renderFallbackCover(book));
    }

    // 卡片主体
    const body = node('div', 'card-body book-card-body');

    // (1) 书名
    const title = node('h3', 'book-title', book.title || '未知书名');
    title.title = book.title || '';

    // (3) 作者名字
    const author = node('p', 'book-author');
    author.append(node('span', 'meta-label', '作者：'), node('span', 'meta-val', book.author || '未知作者'));

    // (4) 电子书格式以及大小
    const formatSizeText = [book.format, book.filesize].filter(Boolean).join(' · ') || '未知';
    const formatSize = node('p', 'book-format-size');
    formatSize.append(node('span', 'meta-label', '格式大小：'), node('span', 'meta-val', formatSizeText));

    // (5) 语言
    const language = node('p', 'book-language');
    language.append(node('span', 'meta-label', '语言：'), node('span', 'meta-val', book.language || '未知'));

    // (6) 下载地址
    const links = node('div', 'downloads book-downloads');
    if (book.demo) {
      (book.formats || []).forEach((fmt) => {
        const placeholder = node('button', 'download book-demo-download', fmt + ' 下载 · 待接入');
        placeholder.type = 'button';
        placeholder.disabled = true;
        links.append(placeholder);
      });
    } else {
      const validLinks = Array.isArray(book.downloadLinks) ? book.downloadLinks : [];
      validLinks.forEach((link) => {
        const url = link && httpUrl(link.url);
        if (!url) return;
        const anchor = node('a', 'download book-download-link');
        anchor.href = url;
        anchor.target = '_blank';
        anchor.rel = 'noopener noreferrer';
        anchor.append(node('span', '', link.title || '下载电子书'), node('b', '', link.format || '下载'));
        links.append(anchor);
      });

      if (!links.childElementCount && book.downloadUrl) {
        const directUrl = httpUrl(book.downloadUrl);
        if (directUrl) {
          const anchor = node('a', 'download book-download-link');
          anchor.href = directUrl;
          anchor.target = '_blank';
          anchor.rel = 'noopener noreferrer';
          const dlText = book.format ? '下载 ' + book.format : '点击下载';
          anchor.append(node('span', '', dlText), node('b', '', book.format || '下载'));
          links.append(anchor);
        }
      }

      if (!links.childElementCount) {
        links.append(node('p', 'empty', '暂无可用下载链接'));
      }
    }

    body.append(title, author, formatSize, language, links);
    card.append(coverWrap, body);
    return card;
  }

  function renderFallbackCover(book) {
    const placeholder = node('div', 'book-cover-placeholder');
    placeholder.append(
      node('span', 'book-cover-label', book.demo ? 'DEMO' : 'EBOOK'),
      node('strong', '', (book.title || '书').slice(0, 2))
    );
    return placeholder;
  }

  function pageButton(label, target, disabled, active) {
    const button = node('button', 'page' + (active ? ' active' : ''), label);
    button.type = 'button';
    button.disabled = Boolean(disabled);
    if (active) button.setAttribute('aria-current', 'page');
    button.addEventListener('click', () => {
      state.page = target;
      renderCurrentPage();
      const resultsSection = get('bookResults');
      if (resultsSection && typeof resultsSection.scrollIntoView === 'function') {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
    return button;
  }

  function renderPagination(total) {
    if (!pager) return;
    pager.replaceChildren();
    if (total <= 1) {
      if (typeof pager.classList?.remove === 'function') pager.classList.remove('show');
      return;
    }

    pager.append(pageButton('上一页', state.page - 1, state.page === 1, false));

    // Show compact pages if too many
    let startPage = Math.max(1, state.page - 2);
    let endPage = Math.min(total, state.page + 2);
    if (endPage - startPage < 4) {
      if (startPage === 1) endPage = Math.min(total, startPage + 4);
      else if (endPage === total) startPage = Math.max(1, endPage - 4);
    }

    if (startPage > 1) {
      pager.append(pageButton('1', 1, false, state.page === 1));
      if (startPage > 2) {
        const ellipsis = node('span', 'page disabled', '…');
        pager.append(ellipsis);
      }
    }

    for (let page = startPage; page <= endPage; page += 1) {
      pager.append(pageButton(String(page), page, false, page === state.page));
    }

    if (endPage < total) {
      if (endPage < total - 1) {
        const ellipsis = node('span', 'page disabled', '…');
        pager.append(ellipsis);
      }
      pager.append(pageButton(String(total), total, false, state.page === total));
    }

    pager.append(pageButton('下一页', state.page + 1, state.page === total, false));
    if (typeof pager.classList?.add === 'function') pager.classList.add('show');
  }

  function renderCurrentPage() {
    const total = state.books.length;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    state.page = Math.min(state.page, totalPages);
    const startIndex = (state.page - 1) * PAGE_SIZE;
    const currentSlice = state.books.slice(startIndex, startIndex + PAGE_SIZE);

    heading.textContent = '“' + state.query + '” 的电子书';
    count.textContent = total + ' 本书' + (DEMO_MODE ? ' · 演示结果' : ' · 第 ' + state.page + ' / ' + totalPages + ' 页');

    if (currentSlice.length) {
      grid.replaceChildren(...currentSlice.map(renderCard));
      renderPagination(totalPages);
    } else {
      if (pager && typeof pager.classList?.remove === 'function') pager.classList.remove('show');
      showStatus('未找到相关电子书', DEMO_MODE
        ? '当前仅有演示数据，可搜索“红楼梦”“西游记”或“Pride and Prejudice”。真实书库待后端接入。'
        : '尝试使用其他书名或作者名称。');
    }
  }

  function showStatus(title, message) {
    const box = node('div', 'status');
    box.append(node('strong', '', '阅'), node('h3', '', title), node('p', '', message));
    grid.replaceChildren(box);
    if (pager) {
      pager.replaceChildren();
      if (typeof pager.classList?.remove === 'function') pager.classList.remove('show');
    }
  }

  async function search(query) {
    query = query.trim();
    if (!query || query.length > 80) {
      input.focus();
      return;
    }
    if (controller) controller.abort();
    controller = new AbortController();
    const id = ++requestId;
    button.disabled = true;
    button.textContent = '搜索中…';
    results.setAttribute('aria-busy', 'true');
    heading.textContent = '正在查找“' + query + '”';
    count.textContent = '';
    if (pager && typeof pager.classList?.remove === 'function') pager.classList.remove('show');
    grid.replaceChildren(...Array.from({ length: 3 }, () => node('div', 'skeleton')));

    try {
      const books = await searchBooks(query, controller.signal);
      if (id !== requestId) return;
      state.books = books;
      state.page = 1;
      state.query = query;
      renderCurrentPage();
    } catch (error) {
      if (id !== requestId || error.name === 'AbortError') return;
      heading.textContent = '搜索暂时中断';
      count.textContent = '';
      showStatus('未能完成搜索', error.message || '请检查网络后重试。');
    } finally {
      if (id === requestId) {
        button.disabled = false;
        button.textContent = '搜索电子书';
        results.setAttribute('aria-busy', 'false');
      }
    }
  }

  const demoNotice = get('bookDemoNotice');
  if (demoNotice) demoNotice.hidden = !DEMO_MODE;
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    search(input.value);
  });
  document.querySelectorAll('.book-suggestion').forEach((suggestion) => {
    suggestion.addEventListener('click', () => {
      input.value = suggestion.dataset.query;
      search(input.value);
    });
  });
})();