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
                    $('#chat-title').text((data.find((ele => ele.conversation_id === paramValue)) || {}).title);
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
            url: `/chat/api/get_messages/${chatId}`,
            method: 'GET',
            success: function (data) {
                const chatMessages = $('#chat-messages');
                chatMessages.empty();
                data.forEach(message => {
                    var messageElement = $('<div>').addClass(message.from_user ? 'user-message' : 'bot-message'),
                        contentElement = null;

                    if (!message.from_user) {
                        // 将 Markdown 内容转换为 HTML
                        // contentElement = $('<div>').addClass('message-content').html(marked.parse(message.content));
                        contentElement = $('<div>').addClass('message-content').html(markdownitEachTime(message.content));
                    } else {
                        contentElement = $('<div>').addClass('message-content').text(message.content);
                    }

                    messageElement.append(contentElement);
                    $('#chat-messages').append(messageElement)
                });
                $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
                initCopyEvent()
            }, error: function (error) {
                console.error('Error fetching messages:', error);
            }
        });
    }

    $('#send-message').on('click', function () {
        const stream = $('#stream-message').is(':checked');
        stream ? getStreamAnswer() : getAnswer();
    });

    function addStreamHTML(userInput, setreamData = '') {
        const messages = [{from_user: true, content: userInput}, {from_user: false, content: setreamData}];

        messages.forEach(message => {
            var messageElement = $('<div>').addClass(message.from_user ? 'user-message' : 'bot-message'),
                contentElement = null;

            if (!message.from_user) {
                // 将 Markdown 内容转换为 HTML
                contentElement = $('<div>').addClass('message-content').text(setreamData);
            } else {
                contentElement = $('<div>').addClass('message-content').text(message.content);
            }

            messageElement.append(contentElement);
            $('#chat-messages').append(messageElement)
        })
    }

    // 获取流式输出
    function getStreamAnswer() {
        const message = $('#chat-message').val();
        if (!message.trim()) {
            alert('Please enter a message.');
            return;
        }
        let currentChatId = paramValue ? paramValue : 0; // Use 0 for new chats
        let cumulativeText = '';
        let n = 0;
        // Disable the send button and change its text

        $('#send-message').prop('disabled', true).text('思考中...');
        addStreamHTML(message, '')

        // 创建 查询字符串
        const jsonData = {message: message, conversation_id: currentChatId};
        const query = Object.keys(jsonData).reduce((a, b) => {
            a.push(encodeURIComponent(b) + '=' + encodeURIComponent(jsonData[b]));
            return a;
        }, []).join('&');
        // 创建包含查询参数的 URL
        const requestUrl = `/chat/api/send_message/stream?${query}`;

        const evtSource = new EventSource(requestUrl);

        evtSource.onmessage = function (e) {
            const lastBotDom = $('#chat-messages div:last');
            if (e.data !== 'end') {
                cumulativeText += e.data;
                // lastBotDom.html(marked.parse(cumulativeText));
                console.log('markdownitEachTime-e:', markdownitEachTime(cumulativeText))
                lastBotDom.html(markdownitEachTime(cumulativeText));
            } else {
                evtSource.close();
                $('#send-message').prop('disabled', false).text('发送');
                $('#chat-message').val('');// 清空输入框
            }
            $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
        }

        evtSource.onerror = function (event) {
            $('#send-message').prop('disabled', false).text('发送');
            $('#chat-message').val('');// 清空输入框
            console.error("EventSource failed:", event);
            evtSource.close();
        };

    }

    // 获取非流式输出
    function getAnswer() {
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
                        loadMessages(response.conversation_id); // 这块可以优化下，只在当前问答下做追加，而不是整个替换

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
                $('#send-message').prop('disabled', false).text('发送');
                $('#chat-message').val('');// 清空输入框
                console.error('Error sending message:', error);
            },
            complete: function () {
                // Re-enable the send button and restore its text
                $('#send-message').prop('disabled', false).text('发送');
            }
        });
    }

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

    // init copy enent for code
    function initCopyEvent() {
        $('.hl-code-header button').on('click', function () {
            var content = $(this).parent().next(".hljs").text(), that = $(this);
            that.hide()

            navigator.clipboard.writeText(content).then(function () {
                that.next(".copy-done").show();
                setTimeout(function () {
                    that.next(".copy-done").hide();
                    that.show();
                }, 3000);
            }).catch(function (error) {
                // 处理可能的错误
                console.error('Copy failed', error);
            });
        });
    }

    // format the text or code all time
    function markdownitEachTime(content) {
        console.log("content:", content);
        // 大模型返回的内容，markdown 格式初始化
        var md = window.markdownit({
            html: true,
            linkify: false,
            typographer: false,
            highlight: function (str, lang) {
                console.log("str:", str, lang)
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return `<div class="hl-code"><div class="hl-code-header"><span>${lang}</span><button><img src="../../static/img/copy-code.svg">复制代码</button><span class="copy-done">已复制!</span></div><div class="hljs"><code>${hljs.highlight(str, {
                            language: lang,
                            ignoreIllegals: true
                        }).value}</code></div></div>`
                    } catch (__) {
                        console.log(__, 'error')
                    }
                }
                return `<div class="hl-code"><div class="hl-code-header"><span>${lang}</span></div><div class="hljs"><code>${md.utils.escapeHtml(str)}</code></div></div>`
            }
        });
        return md.render(content)
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

