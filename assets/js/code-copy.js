// Code Copy Button
(function() {
  document.querySelectorAll('pre code').forEach((codeBlock) => {
    const button = document.createElement('button');
    button.className = 'copy-btn';
    button.textContent = 'Copy';

    button.addEventListener('click', () => {
      navigator.clipboard.writeText(codeBlock.textContent).then(() => {
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
          button.textContent = 'Copy';
          button.classList.remove('copied');
        }, 2000);
      });
    });

    const pre = codeBlock.parentElement;
    const wrapper = document.createElement('div');
    wrapper.className = 'code-block';

    const header = document.createElement('div');
    header.className = 'code-header';

    const langClass = Array.from(codeBlock.classList).find(c => c.startsWith('language-'));
    const lang = langClass ? langClass.replace('language-', '') : 'code';

    const langSpan = document.createElement('span');
    langSpan.className = 'code-language';
    langSpan.textContent = lang;

    header.appendChild(langSpan);
    header.appendChild(button);

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
  });
})();
