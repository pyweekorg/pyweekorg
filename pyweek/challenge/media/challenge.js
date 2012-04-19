function getWindowHeight() {
    var windowHeight = 0;
    if (typeof(window.innerHeight) == 'number') {
        windowHeight = window.innerHeight;    }
    else if (document.documentElement && document.documentElement.clientHeight) {
        windowHeight = document.documentElement.clientHeight;
    }
    else if (document.body && document.body.clientHeight) {
        windowHeight = document.body.clientHeight;
    }
    return windowHeight;
}

function setFooter() {
    // only run if there is a <div id="wrapper"> present on the page.
    if (document.getElementById('wrapper')) {
        var windowHeight = getWindowHeight();
        if (windowHeight > 0) {
            // Find the height of body content
            var contentHeight = document.getElementById('wrapper').offsetHeight;
            var footerElement = document.getElementById('footer');
            var footerHeight  = footerElement.offsetHeight;
	    var totalHeight = contentHeight + footerHeight;
            if (windowHeight > totalHeight) {
                footerElement.style.position = 'relative';
                footerElement.style.top = (windowHeight - totalHeight) + 'px';
            }
            else {
                footerElement.style.position = 'static';
            }
        }
    }
}

window.onload = function() {
    setFooter();
}

