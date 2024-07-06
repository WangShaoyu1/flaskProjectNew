const translations = {
    en: {
        welcome: "Welcome to Flask Chat App",
        lead: "This is a simple chat application using Flask and OpenAI GPT-4.",
        login: "Login",
        register: "Register",
        logout: "Logout",
        chats: "Chats",
        chatDetail: "Chat Detail",
        send: "Send",
        email: "Email",
        password: "Password",
        rememberMe: "Remember Me",
        username: "Username",
        confirmPassword: "Confirm Password",
        enterEmail: "Enter email",
        enterPassword: "Enter password",
        enterUsername: "Enter username",
        confirmPassword: "Confirm password",
        startChat: "Start Chatting",
        enterChatMsg:"Please enter a message..."
    },
    zh: {
        welcome: "欢迎使用 Flask 聊天应用",
        lead: "这是一个使用 Flask 和 OpenAI GPT-4 的简单聊天应用程序。",
        login: "登录",
        register: "注册",
        logout: "登出",
        chats: "聊天",
        chatDetail: "聊天详情",
        send: "发送",
        email: "电子邮件",
        password: "密码",
        rememberMe: "记住我",
        username: "用户名",
        confirmPassword: "确认密码",
        enterEmail: "输入电子邮件",
        enterPassword: "输入密码",
        enterUsername: "输入用户名",
        confirmPassword: "确认密码",
        startChat: "开始聊天",
        enterChatMsg:"请输入一条消息..."
    },
    ja: {
        welcome: "Flaskチャットアプリへようこそ",
        lead: "これは、FlaskとOpenAI GPT-4を使用したシンプルなチャットアプリケーションです。",
        login: "ログイン",
        register: "登録",
        logout: "ログアウト",
        chats: "チャット",
        chatDetail: "チャットの詳細",
        send: "送信",
        email: "メール",
        password: "パスワード",
        rememberMe: "私を覚えてますか",
        username: "ユーザー名",
        confirmPassword: "パスワードを認証する",
        enterEmail: "メールアドレスを入力",
        enterPassword: "パスワードを入力",
        enterUsername: "ユーザー名を入力",
        confirmPassword: "パスワードを確認",
        startChat: "チャットを始める",
        enterChatMsg:"メッセージを入力してください..."
    },
    fr: {
        welcome: "Bienvenue sur Flask Chat App",
        lead: "Ceci est une application de chat simple utilisant Flask et OpenAI GPT-4.",
        login: "Connexion",
        register: "S'inscrire",
        logout: "Se déconnecter",
        chats: "Discussions",
        chatDetail: "Détail du chat",
        send: "Envoyer",
        email: "E-mail",
        password: "Mot de passe",
        rememberMe: "Souviens-toi de moi",
        username: "Nom d'utilisateur",
        confirmPassword: "Confirmez le mot de passe",
        enterEmail: "Entrez votre e-mail",
        enterPassword: "Entrez le mot de passe",
        enterUsername: "Entrez le nom d'utilisateur",
        confirmPassword: "Confirmez le mot de passe",
        startChat: "Commencer à discuter",
        enterChatMsg:"Veuillez entrer un message..."
    },
    de: {
        welcome: "Willkommen bei Flask Chat App",
        lead: "Dies ist eine einfache Chat-Anwendung mit Flask und OpenAI GPT-4.",
        login: "Anmelden",
        register: "Registrieren",
        logout: "Abmelden",
        chats: "Chats",
        chatDetail: "Chat-Details",
        send: "Senden",
        email: "Email",
        password: "Passwort",
        rememberMe: "Erinnere dich an mich",
        username: "Benutzername",
        confirmPassword: "Bestätige das Passwort",
        enterEmail: "E-Mail eingeben",
        enterPassword: "Passwort eingeben",
        enterUsername: "Benutzernamen eingeben",
        confirmPassword: "Passwort bestätigen",
        startChat: "Chat starten",
        enterChatMsg:"Bitte geben Sie eine Nachricht ein..."
    }
};

function changeLanguage() {
    const language = document.getElementById('language-select').value;
    localStorage.setItem('language', language);
    applyTranslations(language);
}

function applyTranslations(language) {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        element.textContent = translations[language][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.setAttribute('placeholder', translations[language][key]);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLanguage = localStorage.getItem('language') || 'zh';
    document.getElementById('language-select').value = savedLanguage;
    applyTranslations(savedLanguage);
});
