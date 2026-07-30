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
    output.innerHTML = '<p class="publication-empty">لم يتم العثور على المنشور. <a href="publications.html">العودة إلى المنشورات.</a></p>';
  }
})();
