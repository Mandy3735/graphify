import { createRoot } from 'react-dom/client';
import { App } from './App';
import './style.css';
createRoot(document.getElementById('root')!).render(<App />);
if ('serviceWorker' in navigator && import.meta.env.PROD)
  navigator.serviceWorker.register('/sw.js').catch(() => {});
// A history restoration must never restore another session's private React state.
window.addEventListener('pageshow', (e) => {
  if (e.persisted) window.location.reload();
});

window.addEventListener('pagehide', () => {
  const root = document.getElementById('root');
  if (root) root.hidden = true;
});
