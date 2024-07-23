window.$(document).ready(function () {
    // Fetch and render chat history
    function loadChatHistory(cb) {
        const chat_id = utils.getQueryParam('chat_id');
        window.$.ajax({
            url: '/chat/api/get_chats', method: 'GET', success: function (data) {
                window.$('#chat-history').empty();
                data.forEach(function (chat) {
                    // 创建聊天会话元素
                    let chatElement = window.$(`<li data-chat-id="${chat.conversation_id}">
                             <a href="${window.location.pathname}?chat_id=${chat.conversation_id}">${chat.title}</a>
                             <span class="delete-icon">&times</span>
                         </li>`)

                    if (chat.conversation_id === utils.getQueryParam('chat_id')) {
                        chatElement.addClass('chat-history-active');
                    }

                    window.$('#chat-history').append(chatElement);
                });

                // 删除会话
                window.$(".delete-icon").click(function (event) {
                    event.stopPropagation();
                    let chatId = window.$(this).parent().data('chat-id');
                    deleteChat(chatId);
                });

                // 拉取聊天历史
                if (chat_id) {
                    loadMessages(chat_id);
                    window.$('#chat-title').text((data.find((ele => ele.conversation_id === chat_id)) || {}).title);
                } else {
                    window.$('#chat-title').text('新聊天');
                }

                cb && cb(data || []);
            }, error: function (error) {
                console.error('Error fetching chats:', error);
            }
        });
    }

    // Fetch and render message history
    function loadMessages(chatId) {
        window.$.ajax({
            url: `/chat/api/get_messages/${chatId}`, method: 'GET', success: function (data) {
                window.$('#chat-messages').empty();

                data.forEach(message => {
                    let messageElement = window.$('<div>').addClass(message.from_user ? 'user-message' : 'bot-message'),
                        contentElement;

                    if (!message.from_user) {
                        // 将 Markdown 内容转换为 HTML
                        // contentElement = window.$('<div>').addClass('message-content').html(marked.parse(message.content));
                        contentElement = window.$('<div>').addClass('message-content').html(markdownItEachTime(message.content));
                    } else {
                        contentElement = window.$('<div>').addClass('message-content').text(message.content);
                    }

                    messageElement.append(contentElement);
                    window.$('#chat-messages').append(messageElement)
                });
                utils.scrollToBottom("#chat-messages")
                initCopyEvent()
            }, error: function (error) {
                console.error('Error fetching messages:', error);
            }
        });
    }

    window.$('#send-message').on('click', function () {
        const stream = window.$('#stream-message').is(':checked');
        stream ? getStreamAnswer() : getAnswer();
    });

    function addStreamHTML(userInput, streamData = '') {
        const messages = [{from_user: true, content: userInput}, {from_user: false, content: streamData}];

        messages.forEach(message => {
            let messageElement = window.$('<div>').addClass(message.from_user ? 'user-message' : 'bot-message'),
                contentElement;

            if (message.from_user) {
                contentElement = window.$('<div>').addClass('message-content').text(message.content);
            } else {
                // 将 Markdown 内容转换为 HTML
                contentElement = window.$('<div>').addClass('message-content').text(streamData);
            }

            messageElement.append(contentElement);
            window.$('#chat-messages').append(messageElement)
        })
    }

    // 获取流式输出
    function getStreamAnswer() {
        const message = window.$('#chat-message-input').val();
        const chat_id = utils.getQueryParam('chat_id');
        if (!message.trim()) {
            alert('Please enter a message.');
            return;
        }
        let cumulativeText = '';
        // Disable the send button and change its text
        window.$('#send-message').prop('disabled', true).text('思考中...');
        addStreamHTML(message, '')

        // 创建 查询字符串
        const jsonData = {message: message, conversation_id: chat_id};
        const query = Object.keys(jsonData).reduce((a, b) => {
            a.push(encodeURIComponent(b) + '=' + encodeURIComponent(jsonData[b]));
            return a;
        }, []).join('&');
        // 创建包含查询参数的 URL
        const requestUrl = `/chat/api/send_message/stream?${query}`;

        const evtSource = new EventSource(requestUrl);
        const lastBotDom = window.$('#chat-messages div:last');

        evtSource.onmessage = function (e) {
            let chunkData = utils.isValidJson(e.data), is_last_char, conversation_id;
            if (chunkData) {
                is_last_char = chunkData["is_last_char"];
                conversation_id = chunkData["conversation_id"];
            }
            if (!is_last_char) {
                cumulativeText += e.data;
                // lastBotDom.html(marked.parse(cumulativeText));
                // console.log('markdownItEachTime-e:', markdownItEachTime(cumulativeText))
                lastBotDom.html(markdownItEachTime(cumulativeText));
            } else {
                evtSource.close();
                utils.resetInput();
                utils.updateQueryStringParameter("chat_id", conversation_id)
            }
            utils.scrollToBottom("#chat-messages")
        }

        evtSource.onerror = function (event) {
            utils.resetInput();
            console.error("EventSource failed:", event);
            evtSource.close();
        };

    }

    // 获取非流式输出
    function getAnswer() {
        const message = window.$('#chat-message-input').val();
        const chat_id = utils.getQueryParam('chat_id');
        if (!message.trim()) {
            alert('Please enter a message.');
            return;
        }

        // Disable the send button and change its text
        window.$('#send-message').prop('disabled', true).text('思考中...');

        window.$.ajax({
            url: `/chat/api/send_message`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({message, conversation_id: chat_id}),
            success: function (response) {
                const {status, conversation_id, chat_data = {}} = response;
                const {user_message, bot_message} = chat_data;
                if (status === 'success') {
                    const userContentElement = window.$(`<div class="user-message"><div class="message-content">${user_message}</div></div>`)
                    const botContentElement = window.$(`<div class="bot-message"><div class="message-content">${markdownItEachTime(bot_message)}</div></div>`)

                    window.$('#chat-messages').append([userContentElement, botContentElement]);
                    utils.scrollToBottom("#chat-messages")
                    if (!chat_id) {
                        // If the user is creating a new chat, redirect to it
                        utils.updateQueryStringParameter("chat_id", conversation_id)
                    }

                } else {
                    alert(response.message);
                }
                utils.resetInput();
            },
            error: function (error) {
                utils.resetInput();
                console.error('Error sending message:', error);
            }
        });
    }

    // Function to delete chat
    function deleteChat(chatId) {
        window.$.ajax({
            url: '/chat/api/chat/' + chatId, method: 'DELETE', success: function (response) {
                if (response.status === 'success') {
                    loadChatHistory(data => {
                        window.$('#chat-title').text('');
                        window.$('#chat-messages').empty();

                        // If the user is creating a new chat, redirect to it
                        if (data.length > 0) {
                            utils.updateQueryStringParameter("chat_id", data[0].conversation_id)
                        } else {
                            window.location.href = `${window.location.origin}${window.location.pathname}`;
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

    // init copy event for code
    function initCopyEvent() {
        window.$('.hl-code-header button').on('click', function () {
            let content = window.$(this).parent().next(".hljs").text(), that = window.$(this);
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
    function markdownItEachTime(content) {
        // console.log("content:", content);
        // 大模型返回的内容，markdown 格式初始化
        let md = window.markdownit({
            html: true, linkify: false, typographer: false, highlight: function (str, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return `<div class="hl-code"><div class="hl-code-header"><span>${lang}</span><button><img src="../../static/img/copy-code.svg" alt="">复制代码</button><span class="copy-done">已复制!</span></div><div class="hljs"><code>${hljs.highlight(str, {
                            language: lang, ignoreIllegals: true
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

    const utils = {
        // judge a string is a json string or not
        isValidJson: str => {
            if (typeof str !== "string") {
                return false;
            }
            try {
                return JSON.parse(str);  // 解析成功，字符串是合法的 JSON
            } catch (e) {
                return false; // 解析失败，字符串不是合法的 JSON
            }
        }, // add url search query
        updateQueryStringParameter: (key, value) => {
            const url = new URL(window.location);
            url.searchParams.set(key, value);
            window.history.pushState({}, '', url);
        }, getQueryParam: (name, url = window.location.search) => {
            const params = new URLSearchParams(url);
            return params.get(name);
        }, scrollToBottom: selector => {
            const $element = window.$(selector);
            $element.scrollTop($element.prop('scrollHeight'));
        }, resetInput: () => {
            window.$('#send-message').prop('disabled', false).text('发送');
            window.$('#chat-message-input').val('');// 清空输入框
        }
    }
    // Enter key submits the message
    window.$('#chat-message-input').keydown(e => {
        if (e.key === 'Enter' && !e.shiftKey && !window.$('#send-message').prop('disabled')) {
            e.preventDefault();
            window.$('#send-message').click();
        }
    });

    // Initial load
    loadChatHistory();
})

