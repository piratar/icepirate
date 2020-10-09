function check_send_to_all(initial_call) {
    var checked = $('#id_send_to_all').is(':checked');

    $mailing_list = $('#id_include_mailing_list');
    $boxes = $('#id_membergroups input[type="checkbox"]')

    if (!checked) {
        // Initial values should be determined by form data, not JavaScript.
        if (!initial_call) {
            $mailing_list.prop('checked', false);
        }
        $mailing_list.removeAttr('disabled');
        $boxes.removeAttr('disabled');
    }
    else {
        // Initial values should be determined by form data, not JavaScript.
        if (!initial_call) {
            $mailing_list.prop('checked', true);
            $boxes.prop('checked', false);
        }
        $mailing_list.attr('disabled', true);
        $boxes.attr('disabled', true);
    }
}

$(function() {
    $('#id_send_to_all').click(function() {
        check_send_to_all(false);
    });

    check_send_to_all(true);

    $('#id_subject').focusEnd();
});
