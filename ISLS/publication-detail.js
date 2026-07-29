(function () {
  var output = document.querySelector('[data-publication-detail]');
  if (!output) return;

  function slugFromUrl() {
    var params = new URLSearchParams(window.location.search);
    return params.get('slug') || params.get('id') || '';
  }

  var slug = slugFromUrl();
  if (slug) {
    window.location.replace('publications/' + encodeURIComponent(slug) + '/' + window.location.hash);
  } else {
    output.innerHTML = '<p class="publication-empty">Publication not found. <a href="publications.html">Return to publications.</a></p>';
  }
})();
