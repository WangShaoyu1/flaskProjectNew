$(document).ready(function () {
    let currentChatId = null;

    // Fetch and render chat history
    function loadChats() {
        $.ajax({
            url: '/chat/api/get_chats',
            method: 'GET',
            success: function (data) {
                $('#chat-history').empty();
                data.forEach(function (chat) {
                    var chatElement = $('<li>').text(chat.title).data('chat-id', chat.id);
                    chatElement.click(function () {
                        var chatId = $(this).data('chat-id');
                        loadMessages(chatId);
                        $('#chat-title').text(chat.title);
                        $('#chat-title').data('chat-id', chatId);
                    });
                    $('#chat-history').append(chatElement);
                });
            },
            error: function (error) {
                console.error('Error fetching chats:', error);
            }
        });
    }

    function loadMessages(chatId) {
        $.ajax({
            url: `/chat/api/get_messages/${chatId}`,
            method: 'GET',
            success: function (data) {
                const chatMessages = $('#chat-messages');
                chatMessages.empty();
                data.forEach(message => {
                    // const messageClass = message.from_user ? 'from-user' : 'from-bot';
                    // chatMessages.append(`<div class="chat-message ${messageClass}"><p>${message.content}</p></div>`);
                    var messageElement = $('<div>').addClass(message.from_user ? 'user-message' : 'bot-message');
                    var contentElement = $('<div>').addClass('message-content').text(message.content);

                    messageElement.append(contentElement);
                    $('#chat-messages').append(messageElement)
                });
                $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
            },
            error: function (error) {
                console.error('Error fetching messages:', error);
            }
        });
    }

    $('#send-message').on('click', function () {
        const message = $('#chat-message').val();
        if (!message.trim()) {
            alert('Please enter a message.');
            return;
        }

        const chatId = currentChatId ? currentChatId : 0; // Use 0 for new chats
        // Disable the send button and change its text
        $('#send-message').prop('disabled', true).text('思考中...');

        $.ajax({
            url: `/chat/api/send_message/${chatId}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({message}),
            success: function (response) {
                if (response.status === 'success') {
                    currentChatId = response.chat_id; // Update current chat ID for new chats
                    loadMessages(currentChatId);
                    loadChats(); // Refresh chat list to show new chat
                    $('#chat-message').val('');
                } else {
                    alert(response.message);
                }
            },
            error: function (error) {
                console.error('Error sending message:', error);
            },
            complete: function () {
                // Re-enable the send button and restore its text
                $('#send-message').prop('disabled', false).text('发送');
            }
        });
    });
    // Enter key submits the message
    $('#chat-message').keypress(function (e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            $('#send-message').click();
        }
    });
    // Initial load
    loadChats();
});
