const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Small DOM double for behavior tests; visual layout still needs a browser.
class Element {
  constructor(tag = 'div') {
    this.tag = tag;
    this.children = [];
    this.attrs = {};
    this.listeners = {};
    this.dataset = {};
    this.value = '';
    this.hidden = false;
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  get childElementCount() { return this.children.length; }
  setAttribute(name, value) { this.attrs[name] = value; }
  focus() { this.focused = true; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  fire(name, data = {}) { this.listeners[name]({ preventDefault() {}, ...data }); }
}
const source = fs.readFileSync(path.join(__dirname, '../frontend/assets/books.js'), 'utf8');
function setup({ demo = true, fetch = () => { throw new Error('Unexpected network request'); } } = {}) {
  const ids = {};
  const get = (id) => ids[id] ||= new Element();
  const suggestions = [new Element('button')];
  suggestions[0].dataset.query = '红楼梦';
  let closed = 0;
  const document = { getElementById: get, createElement: (tag) => new Element(tag), querySelectorAll: () => suggestions };
  vm.runInNewContext(demo ? source.replace('const DEMO_MODE = false;', 'const DEMO_MODE = true;') : source.replace('const DEMO_MODE = true;', 'const DEMO_MODE = false;'), {
    document, URL, AbortController, fetch, closeResources: () => closed++
  });
  return { get, suggestions, closed: () => closed };
}
const flush = () => new Promise((resolve) => setImmediate(resolve));
const descendants = (element) => [element, ...element.children.flatMap(descendants)];

test('tabs support selection, keyboard navigation and independent inputs', () => {
  const { get, closed } = setup();
  get('searchInput').value = '电影';
  get('bookSearchInput').value = '红楼梦';
  get('booksTab').fire('click');
  assert.equal(get('moviesPanel').hidden, true);
  assert.equal(get('booksPanel').hidden, false);
  assert.equal(get('booksTab').attrs['aria-selected'], 'true');
  get('booksTab').fire('keydown', { key: 'ArrowLeft' });
  assert.equal(get('moviesTab').focused, true);
  assert.equal(get('booksPanel').hidden, true);
  assert.equal(get('searchInput').value, '电影');
  assert.equal(get('bookSearchInput').value, '红楼梦');
  assert.equal(closed(), 2);
});

test('demo search shows formats without fake download links or API calls', async () => {
  const { get, suggestions } = setup();
  suggestions[0].fire('click');
  assert.equal(get('bookResults').attrs['aria-busy'], 'true');
  await flush();
  assert.equal(get('bookResultsCount').textContent, '1 本书 · 演示结果');
  const nodes = descendants(get('bookResultsGrid'));
  const downloads = nodes.filter((n) => n.tag === 'button');
  assert.equal(downloads.length, 3);
  assert.ok(downloads.every((n) => n.disabled));
  assert.equal(nodes.filter((n) => n.tag === 'a').length, 0);
  assert.equal(get('bookSearchBtn').disabled, false);
});

test('empty search does nothing and unknown titles show demo empty state', async () => {
  const { get } = setup();
  get('bookSearchForm').fire('submit');
  assert.equal(get('bookSearchInput').focused, true);
  get('bookSearchInput').value = '不存在的演示书';
  get('bookSearchForm').fire('submit');
  await flush();
  assert.equal(get('bookResultsCount').textContent, '0 本书 · 演示结果');
  assert.ok(descendants(get('bookResultsGrid')).some((n) => n.textContent === '未找到相关电子书'));
});

test('future API mode renders ordered safe links and handles missing service', async () => {
  let missing = false;
  const { get } = setup({ demo: false, fetch: async (url) => {
    assert.ok(url.startsWith('/api/books/search?q='));
    return missing ? { status: 404, ok: false } : { status: 200, ok: true, json: async () => ({ results: [{
      title: '<b>Book</b>', downloadLinks: [
        { url: 'javascript:alert(1)' }, { url: 'https://example.org/a.epub', format: 'EPUB' },
        { url: 'https://user:pass@example.org/b.pdf' }, { url: 'https://example.org/c.pdf', format: 'PDF' }
      ]
    }] }) };
  } });
  get('bookSearchInput').value = 'Book';
  get('bookSearchForm').fire('submit');
  await flush();
  const links = descendants(get('bookResultsGrid')).filter((n) => n.tag === 'a');
  assert.deepEqual(links.map((n) => n.href), ['https://example.org/a.epub', 'https://example.org/c.pdf']);
  assert.ok(descendants(get('bookResultsGrid')).some((n) => n.textContent === '<b>Book</b>'));
  missing = true;
  get('bookSearchForm').fire('submit');
  await flush();
  assert.ok(descendants(get('bookResultsGrid')).some((n) => n.textContent === '电子书服务尚未接入，请稍后再试。'));
});

test('rapid searches ignore stale responses and cancel previous request', async () => {
  const requests = [];
  const { get } = setup({ demo: false, fetch: (url, options) => new Promise((resolve) => requests.push({ resolve, signal: options.signal })) });
  get('bookSearchInput').value = 'first';
  get('bookSearchForm').fire('submit');
  get('bookSearchInput').value = 'second';
  get('bookSearchForm').fire('submit');
  assert.equal(requests[0].signal.aborted, true);
  requests[1].resolve({ ok: true, json: async () => ({ results: [{ title: 'second' }] }) });
  await flush();
  requests[0].resolve({ ok: true, json: async () => ({ results: [{ title: 'first' }] }) });
  await flush();
  assert.equal(get('bookResultsTitle').textContent, '“second” 的电子书');
  assert.ok(descendants(get('bookResultsGrid')).some((n) => n.textContent === 'second'));
  assert.equal(get('bookSearchBtn').disabled, false);
});