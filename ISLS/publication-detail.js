(function () {
  var output = document.querySelector('[data-publication-detail]');
  if (!output) return;

  var LANG = document.documentElement.lang === 'ar' ? 'ar' : 'en';

  var NOT_FOUND = {
    en: 'Publication not found. <a href="publications.html">Return to publications.</a>',
    ar: 'لم يتم العثور على المنشور. <a href="publications.html">العودة إلى المنشورات.</a>',
  };

  function slugFromUrl() {
    var params = new URLSearchParams(window.location.search);
    return params.get('slug') || params.get('id') || '';
  }

  var slug = slugFromUrl();
  if (slug) {
    window.location.replace('publications/' + encodeURIComponent(slug) + '/' + window.location.hash);
  } else {
    output.innerHTML = '<p class="publication-empty">' + NOT_FOUND[LANG] + '</p>';
  }
})();
