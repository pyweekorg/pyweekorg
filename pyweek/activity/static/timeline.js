function isScrolledIntoView(elem)
{
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();

    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}

jQuery(function ($) {
    function updateTimestamps() {
        var now = new Date().getTime();
        $('#timeline time').each(function() {
            const tstr = $(this).attr('datetime');
            const dt = new Date(tstr + 'Z').getTime();

            let age = (now - dt) / 1000;
            age |= 0;
            if (age < 60) {
                $(this).text('A few seconds ago');
                return;
            }

            age = (age + 30) / 60;
            age |= 0;

            if (age == 1) {
                $(this).text('A minute ago');
                return;
            }
            else if (age < 60) {
                $(this).text(age + ' minutes ago');
                return;
            }

            age = (age + 30) / 60;
            age |= 0;

            if (age == 1) {
                $(this).text('An hour ago');
                return;
            } else if (age < 24) {
                $(this).text(age + ' hours ago');
                return;
            }

            age = (age + 12) / 24;
            age |= 0;

            if (age == 1) {
                $(this).text('Yesterday');
            } else {
                $(this).text(age + ' days ago');
            }
        });
    }
    updateTimestamps();
    setInterval(updateTimestamps, 10000);


    function checkScroll() {
        let ev = $('#more-events');
        if (!ev.length || !isScrolledIntoView(ev)) {
            return;
        }
        stopScrollCheck();

        let last_id = $('#timeline article:last').attr('data-id');
        if (!last_id) {
            ev.remove();
            return;
        }
        ev.addClass('loading');

        $.ajax(location.pathname + '?before=' + last_id, {
            dataType: 'html',
            success: (html) => {
                ev.remove();
                $('#timeline').append(html);

                if ($('#more-events').length) {
                    startScrollCheck();
                }
            }
        });
    }

    var pollScroll;

    function startScrollCheck() {
        $(window).on('scroll', checkScroll);
        pollScroll = setInterval(checkScroll, 500);
    }
    function stopScrollCheck() {
        $(window).off('scroll', checkScroll);
        if (pollScroll) {
            clearInterval(pollScroll);
            pollScroll = null;
        }
    }
    startScrollCheck();

    var new_html;

    function pollNew() {
        let first_id = $('#timeline article:first').attr('data-id');
        if (!first_id) {
            first_id = '0';
        }
        $.ajax(location.pathname + '?after=' + first_id, {
            dataType: 'json',
            success: (json) => {
                if (json.num == 0) {
                    $('#new-events').remove();
                    new_html = '';
                    return;
                }

                new_html = json.html;

                if (!$('#new-events').length) {
                    const but = $('<div id="new-events"><span class="but"></span></div>');
                    but.prependTo('#timeline');

                    but.on('click', () => {
                        if (json.more) {
                            $('#timeline article').remove();
                        }
                        $('#timeline').prepend(new_html);
                        updateTimestamps();
                        $(but).remove();
                        window.scrollTo(0, 0);
                    });
                }

                $('#new-events .but').text(
                    'Show ' + json.num + ' new event' + ((json.num != 1) ? 's' : '')
                );
            },
            complete: () => {
                setTimeout(pollNew, 60000);
            }
        });
    }

    setTimeout(pollNew, 60000);
});
