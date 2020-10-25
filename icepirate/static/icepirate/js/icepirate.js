// Things that IcePirate wants set up right from the beginning.
$(document).ready(function() {

    // Buttons with a 'href' attribute becomes pseudo-links. Mostly for forms.
    // Supports a `data-warning` attribute that can be used to warn the user
    // before proceeding.
    $('button[href]').click(function(thing) {
        var warning = $(this).attr('data-warning');
        if (!warning || confirm(warning)) {
            location.href = $(this).attr('href');
        }
    });

});

$.fn.setCursorPosition = function(position){
    if(this.length == 0) return this;
    return $(this).setSelection(position, position);
}

$.fn.setSelection = function(selectionStart, selectionEnd) {
    if(this.length == 0) return this;
    input = this[0];

    if (input.createTextRange) {
        var range = input.createTextRange();
        range.collapse(true);
        range.moveEnd('character', selectionEnd);
        range.moveStart('character', selectionStart);
        range.select();
    } else if (input.setSelectionRange) {
        input.focus();
        input.setSelectionRange(selectionStart, selectionEnd);
    }

    return this;
}

$.fn.focusEnd = function(){
    this.setCursorPosition(this.val().length);
            return this;
}
