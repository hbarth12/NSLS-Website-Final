(function () {
  var pickers = document.querySelectorAll('[data-pdf-picker]');

  pickers.forEach(function (picker) {
    var select = picker.querySelector('[data-pdf-select]');
    var link = picker.querySelector('[data-pdf-download]');
    if (!select || !link) return;

    function sync() {
      var option = select.options[select.selectedIndex];
      if (!option) return;
      link.setAttribute('href', option.value);
      if (option.dataset.filename) {
        link.setAttribute('download', option.dataset.filename);
      }
    }

    select.addEventListener('change', sync);
    sync();
  });
})();
