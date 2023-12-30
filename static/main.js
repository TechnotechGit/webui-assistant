const chatContainer = document.querySelector('.chat-container');
const chatButton = document.querySelector('#chat-button');
const writeContainer = document.querySelector('.write-container');
const writeButton = document.querySelector('#write-button');
const settingsContainer = document.querySelector('.settings-container');
const settingsButton = document.querySelector('#settings-button');

const titleBar = document.querySelector('.title-bar');

const tabHandler = class {
    constructor() {
        this.tab = null;
        // element, display, button, title-bar y/n
        this.tab_elems = { "chat": [chatContainer, "flex", chatButton, true], "write": [writeContainer, "block", writeButton, true], "settings": [settingsContainer, "block", settingsButton, false] };
    }

    set(value) {
        this.tab = value;
        let tabKeys = Object.keys(this.tab_elems);
        // Tabs = chat, settings
        for (let i = 0; i < tabKeys.length; i++) {
            console.log(this.tab, tabKeys[i]);
            if (this.tab === tabKeys[i]) {
                this.tab_elems[tabKeys[i]][0].style.display = this.tab_elems[tabKeys[i]][1];
                this.tab_elems[tabKeys[i]][2].classList.add('active');
            } else {
                this.tab_elems[tabKeys[i]][0].style.display = 'none';
                this.tab_elems[tabKeys[i]][2].classList.remove('active');
            }
        }
        if (this.tab_elems[this.tab][3]) {
            titleBar.style.display = 'flex';
        } else {
            titleBar.style.display = 'none';
        }
    }

    get() {
        return this.tab;
    }
};
window.tab = new tabHandler();
window.tab.set('chat');

const themes = {
    1: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-1)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-1)',
        "--bot-border": 'var(--bot-border-1)',
    },
    2: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-2)',
        "--bot-color": 'var(--bot-color-2)',
        "--bot-background-color": 'var(--bot-background-color-2)',
        "--bot-border": 'var(--bot-border-1)',
    },
    3: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-3)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-3)',
        "--bot-border": 'var(--bot-border-1)',
    },
    4: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-4)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-4)',
        "--bot-border": 'var(--bot-border-1)',
    },
    5: {
        "--font": 'var(--font-5)',
        "--background": 'var(--background-5)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-5)',
        "--bot-border": 'var(--bot-border-5)',
    },
    6: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-6)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-6)',
        "--bot-border": 'var(--bot-border-1)',
    },
    7: {
        "--font": 'var(--font-1)',
        "--background": 'var(--background-7)',
        "--bot-color": 'var(--bot-color-1)',
        "--bot-background-color": 'var(--bot-background-color-7)',
        "--bot-border": 'var(--bot-border-7)',
    }
}

const themeHandler = class {
    constructor() {
        this.theme = null;
        // Get from local storage
        if (localStorage.getItem('theme'))
            this.theme = localStorage.getItem('theme');
        else
            this.theme = '1';
        console.log(this.theme);
    }

    set(value) {
        this.theme = value;
        document.documentElement.style.setProperty('--font', themes[this.theme]['--font']);
        document.documentElement.style.setProperty('--background', themes[this.theme]['--background']);
        document.documentElement.style.setProperty('--bot-color', themes[this.theme]['--bot-color']);
        document.documentElement.style.setProperty('--bot-background-color', themes[this.theme]['--bot-background-color']);
        document.documentElement.style.setProperty('--bot-border', themes[this.theme]['--bot-border']);

        localStorage.setItem('theme', this.theme);
    }

    update() {
        this.theme = localStorage.getItem('theme');
    }

    get() {
        return this.theme;
    }
}
window.theme = new themeHandler();
window.theme.set(window.theme.get());

// Settings

// Theme button
const themeInput = document.querySelector('#theme-input');
themeInput.value = window.theme.get();

themeInput.addEventListener('change', (event) => {
    window.theme.set(event.target.value);
})

// Model Settings

const modelSettings = class {
    constructor() {
        this.temperature = 0.7;
        this.top_p = 0.9;
        this.top_k = 32000;
        this.max_tokens = 1024;
        this.repetition_penalty = 1.0;
        this.min_p = 0.02;
    }

    update() {
        localStorage.setItem('temperature', this.temperature);
        localStorage.setItem('top_p', this.top_p);
        localStorage.setItem('top_k', this.top_k);
        localStorage.setItem('max_tokens', this.max_tokens);
        localStorage.setItem('repetition_penalty', this.repetition_penalty);
        localStorage.setItem('min_p', this.min_p);
    }

    retrieve() {
        const settings = {
            temperature: localStorage.getItem('temperature'),
            top_p: localStorage.getItem('top_p'),
            top_k: localStorage.getItem('top_k'),
            max_tokens: localStorage.getItem('max_tokens'),
            repetition_penalty: localStorage.getItem('repetition_penalty'),
            min_p: localStorage.getItem('min_p'),
        };

        if (Object.values(settings).some(value => value == null || value == NaN || value == "")) {
            return null;
        }

        Object.assign(this, settings);
        return true;
    }

    get() {
        return {
            temperature: this.temperature,
            top_p: this.top_p,
            top_k: this.top_k,
            max_tokens: this.max_tokens,
            repetition_penalty: this.repetition_penalty,
            min_p: this.min_p,
        };
    }

    set(key, value) {
        if (Object.keys(this).includes(key)) {
            this[key] = value;
        }
    }
}

// Map to HTML inputs
const temperatureInput = document.querySelector('#temperature-input');
const topPInput = document.querySelector('#top-p-input');
const topKInput = document.querySelector('#top-k-input');
const maxTokensInput = document.querySelector('#max-tokens-input');
const repetitionPenaltyInput = document.querySelector('#repetition-penalty-input');
const minPInput = document.querySelector('#min-p-input');

window.settings = new modelSettings();

if (window.settings.retrieve() !== null) {
    console.log("yes")
    window.settings.retrieve();
}
// else {
//     window.settings.set('temperature', temperatureInput.value);
//     window.settings.set('top_p', topPInput.value);
//     window.settings.set('top_k', topKInput.value);
//     window.settings.set('max_tokens', maxTokensInput.value);
//     window.settings.set('repetition_penalty', repetitionPenaltyInput.value);
//     window.settings.set('min_p', minPInput.value);
// }

temperatureInput.value = window.settings.get().temperature;
topPInput.value = window.settings.get().top_p;
topKInput.value = window.settings.get().top_k;
maxTokensInput.value = window.settings.get().max_tokens;
repetitionPenaltyInput.value = window.settings.get().repetition_penalty;
minPInput.value = window.settings.get().min_p;

window.settings.update();

temperatureInput.addEventListener('change', (event) => {
    window.settings.set('temperature', event.target.value);
    window.settings.update();
})

topPInput.addEventListener('change', (event) => {
    window.settings.set('top_p', event.target.value);
    window.settings.update();
})

topKInput.addEventListener('change', (event) => {
    window.settings.set("top_k", event.target.value);
    window.settings.update();
})

maxTokensInput.addEventListener('change', (event) => {
    window.settings.set("max_tokens", event.target.value);
    window.settings.update();
})

repetitionPenaltyInput.addEventListener('change', (event) => {
    window.settings.set("repetition_penalty", event.target.value);
    window.settings.update();
})

minPInput.addEventListener('change', (event) => {
    window.settings.set("min_p", event.target.value);
    window.settings.update();
})

function sendDataToFlask(data, route) {
    fetch(route, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

sendDataToFlask(window.settings.get(), '/edit_settings');

window.model = "Unknown";

const titleElem = document.querySelector('.title')
const tsMeter = document.querySelector('.ts-meter')

function updateTitle() {
    if (window.model) {
        titleElem.innerHTML = `${window.model}&ThickSpace;|&ThickSpace;Temp: ${Number(window.settings.get().temperature).toFixed(2)}`;
    }
}

chatButton.addEventListener('click', () => {
    tab.set('chat');
    sendDataToFlask(window.settings.get(), '/edit_settings');
    updateTitle()
})

writeButton.addEventListener('click', () => {
    tab.set('write');
    sendDataToFlask(window.settings.get(), '/edit_settings');
    updateTitle()
})

settingsButton.addEventListener('click', () => {
    tab.set('settings');
    sendDataToFlask(window.settings.get(), '/edit_settings');
    updateTitle()
})

function getModelName() {
    fetch('/get-model')
        .then(response => response.json())
        .then(data => {
            if (data.model) {
                window.model = data.model;
            }
            else {
                window.model = "Unknown";
            }
            updateTitle()
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

getModelName()

const emoji = new EmojiConvertor();
emoji.replace_mode = 'unified';
emoji.allow_native = true;

autosize(document.querySelectorAll('textarea'));
function lerp(a, b, t) {
    return a * (1 - t) + b * t;
}

let chatMessages = document.getElementById('chat-messages');
let chatInput = document.getElementById('chat-input');
chatInput.focus();
let chatInputContainer = document.querySelector('.input-container');
window.streaming = false;

// Options: CGPT, Perplexity, Terminal, Custom1, Custom2, Custom3, Custom4, Custom5, Custom6, Custom7, Custom8
let typeAnim = "Custom3";
const typingAnimation = document.getElementById('typing-animation');

// Create an AbortController
let abort = new AbortController();

const stopButton = document.getElementById('stop-button');
stopButton.addEventListener('click', () => {
    abort.abort();
    window.streaming = false;
    abort = new AbortController();
    stopButton.style.display = 'none';
    typingAnimation.style.display = 'none';
});

chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();

        if (window.streaming) {
            return;
        }

        stopButton.style.display = 'initial';
        typingAnimation.style.display = 'initial';

        autosize.update(chatInput);
        chatInput.style.height = 'auto';

        let sendOut = document.createElement('div');
        sendOut.classList.add('send-out');
        sendOut.innerText = chatInput.value;
        chatInputContainer.appendChild(sendOut);
        sendOut.addEventListener('animationend', () => {
            chatInputContainer.removeChild(sendOut);
        });

        let message = chatInput.value;
        let sentMessageContainer = document.createElement('div');
        sentMessageContainer.className = 'sent-message';

        let sentMessageTextElement = document.createElement('div');
        sentMessageTextElement.classList.add('message', 'user');

        let content = document.createElement('div');
        content.classList.add('message-bubble');

        // Process emoji
        message = emoji.replace_colons(message);

        content.textContent = message;
        sentMessageTextElement.appendChild(content);
        sentMessageContainer.appendChild(sentMessageTextElement);
        chatMessages.appendChild(sentMessageContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        chatInput.value = '';
        // chatInput.disabled = true;
        window.streaming = true;

        num_tokens = 0
        first_token = true

        function scrollToBottom() {
            function animation() {
                // chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
                if (chatMessages.scrollTop !== chatMessages.scrollHeight - chatMessages.clientHeight)
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                // console.log(chatMessages.scrollTop, chatMessages.scrollHeight - chatMessages.clientHeight);

                if (window.streaming) {
                    requestAnimationFrame(animation);
                } else {
                    return;
                }
            }

            requestAnimationFrame(animation);
        }

        fetch('/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            }),
            signal: abort.signal
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error occurred while window.streaming tokens.');
                }

                typingAnimation.style.display = 'none';

                let lastToken = "";
                let content;

                let result = ""
                let html = "";

                let responseStream = new ReadableStream({
                    start(controller) {
                        scrollToBottom();
                        let reader = response.body.getReader();

                        function read() {
                            reader.read().then(({ done, value }) => {
                                if (done) {
                                    controller.close();
                                    stopButton.style.display = 'none';
                                    typingAnimation.style.display = 'none';
                                    window.streaming = false;
                                    getModelName()

                                    return;
                                }
                                if (first_token) {
                                    base_time = Date.now();
                                    first_token = false
                                } else {
                                    // calc time
                                    num_tokens++
                                    ts = num_tokens / ((Date.now() - base_time) / 1000)
                                    console.log((Date.now() - base_time).toFixed(2), num_tokens, ts)
                                    tsMeter.innerText = `${ts.toFixed(2)} t/s`
                                }

                                let token = new TextDecoder().decode(value);

                                const regex = /{data:\s*([^]*)}/gs

                                // Extract the strings using matchAll()
                                let jsonObjects = Array.from(token.matchAll(regex), match => match[1].trim());

                                jsonObjects.forEach(item => {
                                    const regex = new RegExp(`{data: ${item}}`, 'gi');
                                    token = token.replace(regex, '');
                                });


                                if (lastToken !== "text") {
                                    lastToken = "text";
                                    let receivedTokensContainer = document.createElement('div');
                                    receivedTokensContainer.classList.add('message', 'bot');
                                    chatMessages.appendChild(receivedTokensContainer);

                                    content = document.createElement('div');
                                    content.classList.add('message-bubble');
                                    receivedTokensContainer.appendChild(content);
                                }
                                result += token;
                                token = emoji.replace_colons(token);
                                if (typeAnim === "CGPT") {
                                    content.innerText = result + '▎';
                                } else if (typeAnim === "Terminal") {
                                    content.innerText = result.trim() + "▁";
                                } else {
                                    for (let i of token.split(/(?<!\n)(\s+)/)) {
                                        if (i.trim() !== "") { // Check if the token is a word
                                            let html = document.createElement('span');
                                            if (typeAnim === "Perplexity") {
                                                html.classList.add('oi');
                                            } else if (typeAnim === "Custom1") {
                                                html.classList.add('ls');
                                            } else if (typeAnim === "Custom2") {
                                                html.classList.add('ul');
                                            } else if (typeAnim === "Custom3") {
                                                html.classList.add('tg');
                                            } else if (typeAnim === "Custom4") {
                                                html.classList.add('bi');
                                            } else if (typeAnim === "Custom5") {
                                                html.classList.add('mi');
                                            } else if (typeAnim === "Custom6") {
                                                html.classList.add('si');
                                            } else if (typeAnim === "Custom7") {
                                                html.classList.add('ri');
                                            } else if (typeAnim === "Custom8") {
                                                html.classList.add('fi');
                                            }
                                            if (i.includes("\n")) {
                                                console.log("newline");
                                                i = i.split(/\n/g);
                                                for (let j of i) {
                                                    html.innerText = j;
                                                    content.append("<br>")
                                                    content.append(html);
                                                }
                                            } else {
                                                html.innerText = i
                                                content.append(html);
                                            }
                                        }


                                        else if (i.includes("\n")) {
                                            console.log("newline");
                                            let check = i;
                                            i = i.split("\n");
                                            for (let j of i) {
                                                html.innerText = i;
                                                console.log(check)
                                                if (check.startsWith("\n"))
                                                    content.appendChild(document.createElement('br'));
                                                // delete i.length characters from check
                                                check = check.substring(1);
                                                content.append(html);
                                            }
                                        }

                                        else if (i == " ") { // Token is a space
                                            content.append(" ")
                                        }
                                        // if (i == " ") {
                                        //     content.append(" ")
                                        // } else {
                                        //     console.log(i, token)
                                        //     if (token.split(" ").length > 1 && token.split(" ")[1] != "") {
                                        //         html.innerText = i;
                                        //         content.append(html);
                                        //         content.append(" ");
                                        //     } else {
                                        //         html.innerText = i;
                                        //         content.append(html);
                                        //     }
                                        // }
                                    }
                                    // html.innerText = token;
                                    // content.append(html);

                                    // Check for format {"info": "Google Chrome", "task": "open", "success": true}
                                    for (i of jsonObjects) {
                                        try {
                                            const jsonObject = JSON.parse(i);

                                            let receivedTokensContainer = document.createElement('div');
                                            // receivedTokensContainer.classList.add('received-tokens');
                                            receivedTokensContainer.classList.add('message', 'bot');
                                            chatMessages.appendChild(receivedTokensContainer);

                                            content = document.createElement('div');
                                            content.classList.add('message-bubble');

                                            if (jsonObject["success"]) {
                                                content.innerHTML = emoji.replace_colons(`<strong>Task | </strong>${jsonObject["task"].charAt(0).toUpperCase() + jsonObject["task"].slice(1)}ed ` + jsonObject["info"] + " :heavy_check_mark:");
                                            } else {
                                                content.innerHTML = emoji.replace_colons(`<strong>Task | </strong>${jsonObject["task"].charAt(0).toUpperCase() + jsonObject["task"].slice(1)}ed ` + jsonObject["info"] + " :x:");
                                            }
                                            receivedTokensContainer.appendChild(content);
                                            lastToken = "info";

                                        } catch (error) {
                                            console.log(error)
                                        }
                                    }
                                }

                                read();
                            });
                        }

                        read();
                    }
                });

                let responseStreamText = new Response(responseStream, {
                    headers: { 'Content-Type': 'text/plain' }
                });

                return responseStreamText;
            })
            .catch(error => {
                // console.log("Hi")
                if (controller.aborted) {
                    // Handle the abort event
                    window.streaming = false;
                    content.innerHTML = result;
                    console.log(content);
                } else {
                    console.error('Error:', error);
                }
            })

    }
});


// Input listeners
const host_input = document.getElementById("host-input")
const host_input_error = document.createElement("style")
host_input.parentElement.append(host_input_error)
let regex = `^(?=.*[a-zA-Z0-9])[^.\s]+(?:\.[a-zA-Z0-9-]+)+(?::\d{1,5})?$`
regex = new RegExp(regex)
host_input.oninput = (e) => {
    console.log(host_input_error)
    if (!regex.test(e.target.value))
        host_input_error.innerHTML = `.input-container-error:has(#${host_input.id})::after {content: 'Host URL does not fit requirements'}`
    else
        host_input_error.innerHTML = `.input-container-error:has(#${host_input.id})::after {content: ''}`
}

host_input.onkeydown = (e) => {
    if (e.key == " ") {
        e.preventDefault()
        return
    }
}