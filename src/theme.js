const themeButton = document.querySelector('#theme');
const preferredDark = window.matchMedia('(prefers-color-scheme: dark)');
const root = document.documentElement;
let userTheme;
try {
  userTheme = localStorage.getItem('portfolio-theme');
} catch {
  // System preferences still work when local storage is unavailable.
}

function applyTheme() {
  const theme = userTheme ?? (preferredDark.matches ? 'dark' : 'light');
  root.dataset.theme = theme;
  if (themeButton) themeButton.textContent = theme === 'dark' ? 'Use light theme' : 'Use dark theme';
}

applyTheme();
preferredDark.addEventListener('change', applyTheme);
if (themeButton) {
  themeButton.hidden = false;
  themeButton.addEventListener('click', () => {
    userTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    try {
      localStorage.setItem('portfolio-theme', userTheme);
    } catch {
      // Keep the selected theme for the current page.
    }
  });
}

const menu = document.querySelector('.menu');
menu?.addEventListener('click', (event) => {
  const link = event.target.closest('a');
  if (!link) return;
  menu.open = false;
  if (link.getAttribute('href').startsWith('#')) {
    const target = document.getElementById(link.hash.slice(1));
    target?.setAttribute('tabindex', '-1');
    target?.focus({ preventScroll: true });
  }
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && menu?.open) {
    menu.open = false;
    menu.querySelector('summary').focus();
  }
});

const printButton = document.querySelector('#print');
if (printButton) {
  printButton.hidden = false;
  printButton.addEventListener('click', () => window.print());
}
