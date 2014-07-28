(function ($) {
    $.fn.ajaxSubmit = function (options) {
        options['data'] = $(this).serialize();
        $.ajax(options);
        return false;
    },
    
    $.fn.reset = function () {
        $(this).each(function () {
            this.reset();
        });
    }

})(jQuery);
