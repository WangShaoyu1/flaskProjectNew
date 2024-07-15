$(document).ready(function () {
    // 获取查询字符串
    var queryString = window.location.search, // 创建 URLSearchParams 对象
        urlParams = new URLSearchParams(queryString), // 获取特定参数的值，例如 "paramName"
        paramValue = urlParams.get('chat_id');
    let currentChatId = null;
    let chatHistoryList = [];

    // Fetch and render chat history
    function loadChatHistory(cb) {
        $.ajax({
            url: '/chat/api/get_chats', method: 'GET', success: function (data) {
                chatHistoryList = data;
                $('#chat-history').empty();
                data.forEach(function (chat) {
                    // 创建聊天会话元素
                    var chatElement = $(`<li data-chat-id="${chat.conversation_id}">
                             <a href="${window.location.pathname}?chat_id=${chat.conversation_id}">${chat.title}</a>
                             <span class="delete-icon">&times</span>
                         </li>`)

                    if (chat.conversation_id === paramValue) {
                        chatElement.addClass('chat-history-active');
                    }

                    $('#chat-history').append(chatElement);
                });

                // 删除会话
                $(".delete-icon").click(function (event) {
                    event.stopPropagation();
                    var chatId = $(this).parent().data('chat-id');
                    deleteChat(chatId);
                });

                // 拉取聊天历史
                if (paramValue) {
                    currentChatId = paramValue;
                    loadMessages(paramValue);
                    $('#chat-title').text((data.find((ele => ele.conversation_id == paramValue)) || {}).title);
                } else {
                    $('#chat-title').text('新聊天');
                }

                cb && cb();
            }, error: function (error) {
                console.error('Error fetching chats:', error);
            }
        });
    }

    // Fetch and render message history
    function loadMessages(chatId) {
        $.ajax({
            url: `/chat/api/get_messages/${chatId}`, method: 'GET', success: function (data) {
                const chatMessages = $('#chat-messages');
                chatMessages.empty();
                data.forEach(message => {
                    // const messageClass = message.from_user ? 'from-user' : 'from-bot';
                    // chatMessages.append(`<div class="chat-message ${messageClass}"><p>${message.content}</p></div>`);
                    var messageElement = $('<div>').addClass(message.from_user ? 'user-message' : 'bot-message'),
                        contentElement = null;

                    if (!message.from_user) {
                        // 将 Markdown 内容转换为 HTML
                        contentElement = $('<div>').addClass('message-content').html(marked.parse(message.content));
                    } else {
                        contentElement = $('<div>').addClass('message-content').text(message.content);
                    }

                    messageElement.append(contentElement);
                    $('#chat-messages').append(messageElement)
                });
                $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
            }, error: function (error) {
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

        let currentChatId = paramValue ? paramValue : 0; // Use 0 for new chats
        // Disable the send button and change its text
        $('#send-message').prop('disabled', true).text('思考中...');

        $.ajax({
            url: `/chat/api/send_message`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({message, conversation_id: currentChatId}),
            success: function (response) {
                if (response.status === 'success') {
                    if (currentChatId) {
                        loadMessages(response.conversation_id);
                        // loadChatHistory(); // Refresh chat list to show new chat

                        $('#chat-message').val('');// 清空输入框
                    } else {
                        // If the user is creating a new chat, redirect to it
                        window.location = window.location.pathname + '?chat_id=' + response.conversation_id;
                    }

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

    // Function to delete chat
    function deleteChat(chatId) {
        $.ajax({
            url: '/chat/api/chat/' + chatId, method: 'DELETE', success: function (response) {
                if (response.status === 'success') {
                    loadChatHistory(() => {
                        $('#chat-title').text('');
                        $('#chat-messages').empty();

                        // If the user is creating a new chat, redirect to it
                        if (chatHistoryList.length > 0) {
                            window.location = window.location.pathname + '?chat_id=' + chatHistoryList[0].conversation_id;
                        } else {
                            window.location = window.location.pathname;
                        }
                    });

                } else {
                    alert('Failed to delete chat');
                }
            }, error: function (error) {
                console.error('Error fetching messages:', error);
            }
        })
    }

    // Enter key submits the message
    $('#chat-message').keypress(function (e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            $('#send-message').click();
        }
    });
    // Initial load
    loadChatHistory();
})

