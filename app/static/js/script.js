document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const messageInput = document.getElementById('message');
    const messageText = messageInput.value;
    const conversationId = "{{ chat.conversation_id }}";

    fetch('/chat/api/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ conversation_id: conversationId, message: messageText })
    })
    .then(response => response.json())
    .then(data => {
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML += `<div class="message"><strong>Me:</strong> ${messageText}</div>`;
        chatBox.innerHTML += `<div class="message"><strong>AI:</strong> ${data.message}</div>`;
        messageInput.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;
    });
});
