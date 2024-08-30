const ENDPOINT_DOMAIN = 'localhost';
const ENDPOINT_PORT = '8000';
const WS_ENDPOINT = 'ws/data/';
const ENDPOINT_URL = `${ENDPOINT_DOMAIN}:${ENDPOINT_PORT}`;

function escape(s) {
    return s.replace(
        /[^0-9A-Za-z ]/g,
        c => "&#" + c.charCodeAt(0) + ";"
    );
}

function getEmailTemplate(email) {
    return `
        <div class="message">
            <p style="width: 7%">${email.uid || ''}</p>
            <p style="width: 30%"><b>${email.subject || ''}</b></p>
            <p>${email.from_inbox_address || ''}</p>
            <p>${escape(email.sender_address) || ''}</p>
            <p>${email.date_sent.replace(' ', '<br>')}</p>
            <p>${email.date_received.replace(' ', '<br>')}</p>
            <p style="width: 30%">${email.body || ''}</p>
            <p>${escape(email.attachments_names) || ''}</p>
            <p>${escape(email.attachments_ids) || ''}</p>
        </div>
    `;
}
            
$(document).ready(function() {
    console.log('hi there');

    const socket = new WebSocket(`ws://${ENDPOINT_URL}/${WS_ENDPOINT}`);
    const $progressText = $('#progress_text');
    const $progress = $('#progress');

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log(data.message);
        $progressText.text(data.message);

        if (data.count !== undefined) {
            let percent = (data.count / data.total) * 100;
            $progressText.text(`${data.message} (${data.count}/${data.total})`);
            $progress.css('width', percent + '%');
        }

        if (data.email !== undefined) {
            var email = data.email;
            var emailHTML = getEmailTemplate(email);
            $('#messages_container').append(emailHTML);
        }

        if (data.message === 'Нет новых сообщений' || data.message === 'Готово') {
            $progress.css('width', '100%');
        }
    };

    socket.onopen = function(event) {
        socket.send(JSON.stringify({
            'message': 'start_fetching'
        }));
    };

    socket.onclose = function(event) {
        $progressText.text('Отключено');
        console.log('Соединение закрыто');
    };

    socket.onerror = function(error) {
        $progressText.text('Ошибка соединения');
        console.error('Ошибка соединения: ' + error);
    };

});
