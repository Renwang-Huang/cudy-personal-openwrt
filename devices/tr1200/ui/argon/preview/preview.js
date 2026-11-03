/* Demonstration controls only. This fixture performs no RPC or login requests. */
(() => {
  const root = document.documentElement;
  const mode = new URLSearchParams(location.search).get('mode') || 'normal';
  root.dataset.argonMode = ['light', 'dark', 'normal'].includes(mode) ? mode : 'normal';
  const controls = document.createElement('div');
  controls.className = 'preview-toolbar';
  const label = document.createElement('label');
  label.textContent = '外观 ';
  const select = document.createElement('select');
  select.setAttribute('aria-label', '外观模式');
  [['normal','跟随系统'],['light','浅色'],['dark','深色']].forEach(([value, text]) => select.add(new Option(text, value)));
  select.value = root.dataset.argonMode;
  select.addEventListener('change', () => root.dataset.argonMode = select.value);
  label.append(select);
  controls.append(label);
  const link = document.createElement('a');
  const login = Boolean(document.querySelector('.login-page'));
  link.href = login ? 'overview.html' : 'login.html';
  link.textContent = login ? '概览预览' : '登录页预览';
  controls.append(link);
  if (login) {
    controls.classList.add('preview-page-links');
    document.body.append(controls);
    const note = document.createElement('p');
    note.className = 'preview-login-note';
    note.textContent = '本地界面预览 · 无需输入账号密码';
    const form = document.querySelector('form');
    form.prepend(note);
    form.querySelectorAll('input:not([type=submit])').forEach(input => { input.disabled = true; input.value = ''; });
    form.addEventListener('submit', event => { event.preventDefault(); location.href = 'overview.html'; });
  } else {
    document.querySelector('.header-actions').append(controls);
    const menu = document.querySelector('#mainmenu');
    menu.style.display = '';
    const nav = document.createElement('ul'); nav.className = 'nav';
    [['状态','status'],['系统','system'],['网络','network'],['外观设置','services']].forEach(([text,icon], index) => {
      const li = document.createElement('li');
      const a = document.createElement('a'); a.href = '#'; a.className = index === 0 ? 'active' : '';
      const iconUrl = new URL(`assets/argon/icon/${icon}.svg`, location.href).href;
      a.innerHTML = `<span class="menu-icon" data-icon="${icon}" style="--menu-icon:url('${iconUrl}')"></span>`;
      a.append(document.createTextNode(text));
      a.addEventListener('click', event => { event.preventDefault(); setMenu(false); });
      li.append(a); nav.append(li);
    });
    menu.append(nav);
    const mask = document.querySelector('.darkMask');
    const button = document.querySelector('.showSide');
    const setMenu = open => {
      menu.classList.toggle('active', open);
      mask.classList.toggle('active', open);
      button.classList.toggle('active', open);
      document.querySelector('.main-right').classList.toggle('active', open);
      button.setAttribute('aria-expanded', String(open));
    };
    button.addEventListener('click', () => setMenu(!menu.classList.contains('active')));
    mask.addEventListener('click', () => setMenu(false));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') setMenu(false); });
  }
})();
