// Things that IcePirate wants set up right from the beginning.
$(document).ready(function() {

    // Buttons with a 'href' attribute becomes pseudo-links. Mostly for forms.
    $('button[href]').click(function(thing) {
        location.href = $(this).attr('href');
    });

});
