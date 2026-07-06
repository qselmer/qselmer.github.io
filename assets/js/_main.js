/* ==========================================================================
jQuery plugin settings and other scripts

NOTE: You need to run `npm run uglify` for changes here to reflect on the site.
========================================================================== */

$(document).ready(function () {
  // detect OS/browser preference
  let browserPref = window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
  
  // Set the theme on page load or when explicitly called
  var setTheme = function (theme_to_set) {
    var theme = theme_to_set;
    if (theme === 'auto') {
      theme = browserPref;
      $("#theme-icon").removeClass("fa-sun fa-moon").addClass("fa-desktop");
    } else if (theme === 'dark') {
      $("#theme-icon").removeClass("fa-sun fa-desktop").addClass("fa-moon");
    } else { // light
      $("#theme-icon").removeClass("fa-moon fa-desktop").addClass("fa-sun");
    }
  
    if (theme === 'dark') {
      $("html").attr("data-theme", "dark");
    } else {
      $("html").removeAttr("data-theme");
    }
  };
  
  const stored_theme = localStorage.getItem("theme");
  setTheme(stored_theme || 'auto');
  
  // if user has chosen auto, follow OS changes
  window
    .matchMedia('(prefers-color-scheme: dark)')
    .addEventListener("change", (e) => {
      if (localStorage.getItem("theme") === 'auto' || !localStorage.getItem("theme")) {
        browserPref = e.matches ? "dark" : "light";
        setTheme('auto');
      }
    });
  
  // Toggle the theme manually
  var toggleTheme = function () {
    const current_theme = localStorage.getItem("theme") || 'auto';
    var new_theme;
  
    if (current_theme === 'light') {
      new_theme = 'dark';
    } else if (current_theme === 'dark') {
      new_theme = 'auto';
    } else { // auto
      new_theme = 'light';
    }
  
    localStorage.setItem("theme", new_theme);
    setTheme(new_theme);
  };
  $('#theme-toggle').on('click', toggleTheme);

  // These should be the same as the settings in _variables.scss
  const scssLarge = 925; // pixels

  // Sticky footer
  var bumpIt = function () {
    $("body").css("margin-bottom", $(".page__footer").outerHeight(true));
  },
    didResize = false;

  bumpIt();

  $(window).resize(function () {
    didResize = true;
  });
  setInterval(function () {
    if (didResize) {
      didResize = false;
      bumpIt();
    }
  }, 250);

  // FitVids init
  fitvids();

  // Follow menu drop down
  $(".author__urls-wrapper button").on("click", function () {
    $(".author__urls").fadeToggle("fast", function () { });
    $(".author__urls-wrapper button").toggleClass("open");
  });

  // Restore the follow menu if toggled on a window resize
  jQuery(window).on('resize', function () {
    if ($('.author__urls.social-icons').css('display') == 'none' && $(window).width() >= scssLarge) {
      $(".author__urls").css('display', 'block')
    }
  });

  // init smooth scroll, this needs to be slightly more than then fixed masthead height
  $("a").smoothScroll({ 
    offset: -75, // needs to match $masthead-height
    preventDefault: false,
  }); 

  // add lightbox class to all image links
  // Add "image-popup" to links ending in image extensions,
  // but skip any <a> that already contains an <img>
  $("a[href$='.jpg'],\
  a[href$='.jpeg'],\
  a[href$='.JPG'],\
  a[href$='.png'],\
  a[href$='.gif'],\
  a[href$='.webp']")
      .not(':has(img)')
      .addClass("image-popup");

  // 1) Wrap every <p><img> (except emoji images) in an <a> pointing at the image, and give it the lightbox class
  $('p > img').not('.emoji').each(function() {
    var $img = $(this);
    // skip if it’s already wrapped in an <a.image-popup>
    if ( ! $img.parent().is('a.image-popup') ) {
      $('<a>')
        .addClass('image-popup')
        .attr('href', $img.attr('src'))
        .insertBefore($img)   // place the <a> right before the <img>
        .append($img);        // move the <img> into the <a>
    }
  });

  // Magnific-Popup options
  $(".image-popup").magnificPopup({
    type: 'image',
    tLoading: 'Loading image #%curr%...',
    gallery: {
      enabled: true,
      navigateByImgClick: true,
      preload: [0, 1] // Will preload 0 - before current, and 1 after the current image
    },
    image: {
      tError: '<a href="%url%">Image #%curr%</a> could not be loaded.',
    },
    removalDelay: 500, // Delay in milliseconds before popup is removed
    // Class that is added to body when popup is open.
    // make it unique to apply your CSS animations just to this exact popup
    mainClass: 'mfp-zoom-in',
    callbacks: {
      beforeOpen: function () {
        // just a hack that adds mfp-anim class to markup
        this.st.image.markup = this.st.image.markup.replace('mfp-figure', 'mfp-figure mfp-with-anim');
      }
    },
    closeOnContentClick: true,
    midClick: true // allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source.
  });

});
