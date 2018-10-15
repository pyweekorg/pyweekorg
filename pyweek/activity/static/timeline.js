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
});
