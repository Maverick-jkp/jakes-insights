// TOC Active Section Highlight
(function() {
  const toc = document.querySelector('.toc');
  if (!toc) return;

  const tocLinks = toc.querySelectorAll('a');
  const headings = Array.from(document.querySelectorAll('h2, h3')).filter(h => h.id);

  if (headings.length === 0) return;

  function updateActive() {
    let current = '';

    headings.forEach(heading => {
      const rect = heading.getBoundingClientRect();
      if (rect.top <= 100) {
        current = heading.id;
      }
    });

    tocLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  updateActive();
})();
