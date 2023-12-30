// Define prompts

const userToken = "### Instruction:"
const assistantToken = "### Response:"

function basePrompt(inputPrompt) {
    return `### System: ${inputPrompt}`;
}


const systemPrompts = {
    "arXiv": `You are an AI that generates an long abstract in the style of an arXiv paper's abstract. It should be detailed and descriptive. Give no disclaimers.
Write a title at the top of the document, and the abstract below it.
${userToken}
Please write a one to three paragraph long abstract about the following:
{input}

${assistantToken}
Sure, here is the abstract, with the title first:
## Title:`,
    "reddit": `You are an AI that generates in the style of a Reddit post. Place a title at the top of the post, and the abstract below it.
${userToken}
The topic of the post is: "{input}"

${assistantToken}
## Title:`,
    "email": `You are an AI that generates in the style of an email. Place a title at the top of the email, and the contents of the email below it.
${userToken}
Please write an email about the following:
"{input}"

${assistantToken}
## Title:`,
    "blog": `You are an AI that generates in the style of a blog post. Place a title at the top of the post, and the contents of the blog post below it.
${userToken}
Write a blog post about the following topic:
"{input}"

${assistantToken}
## Title:`
};

// Create an AbortController
let abortWrite = new AbortController();

const stopWriteButton = document.getElementById('stop-write-button');
stopWriteButton.addEventListener('click', () => {
    abortWrite.abort();
    window.streaming = false;
    abortWrite = new AbortController();
    stopButton.style.display = 'none';
    typingAnimation.style.display = 'none';
});

const writeInput = document.querySelector('.write-input');
const writeDropdown = document.querySelector('.write-dropdown');

// writeInput.addEventListener('keydown', function (event) {
//     if (event.key === 'Enter' && !event.shiftKey) {
//         event.preventDefault();

//         if (window.streaming) {
//             return;
//         }
//         writeGenerate()
//     }
// });

const writeSubmit = document.getElementById('write-submit');

writeSubmit.addEventListener('click', () => {
    console.log("Hi")
    if (window.streaming) {
        return;
    }
    writeGenerate()
})

const outputContainer = document.getElementById('output-container');

const writeGenerate = () => {
    stopWriteButton.style.display = 'initial';
    // typingAnimation.style.display = 'initial';

    autosize.update(chatInput);
    writeInput.style.height = 'auto';

    // let sendOut = document.createElement('div');
    // sendOut.classList.add('send-out');
    // sendOut.innerText = chatInput.value;
    // chatInputContainer.appendChild(sendOut);
    // sendOut.addEventListener('animationend', () => {
    //     chatInputContainer.removeChild(sendOut);
    // });

    let message = basePrompt(systemPrompts[writeDropdown.value].replace('{input}', writeInput.value));
    // let sentMessageContainer = document.createElement('div');
    // sentMessageContainer.className = 'sent-message';

    // let sentMessageTextElement = document.createElement('div');
    // sentMessageTextElement.classList.add('message', 'user');

    // let content = document.createElement('div');
    // content.classList.add('message-bubble');

    // Process emoji
    message = emoji.replace_colons(message);

    console.log(message);

    // content.textContent = message;
    // chatMessages.scrollTop = chatMessages.scrollHeight;
    writeInput.value = '';
    // chatInput.disabled = true;
    window.streaming = true;

    num_tokens = 0
    first_token = true

    // function scrollToBottom() {
    //     function animation() {
    //         // chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
    //         if (chatMessages.scrollTop !== chatMessages.scrollHeight - chatMessages.clientHeight)
    //             chatMessages.scrollTop = chatMessages.scrollHeight;
    //         // console.log(chatMessages.scrollTop, chatMessages.scrollHeight - chatMessages.clientHeight);

    //         if (window.streaming) {
    //             requestAnimationFrame(animation);
    //         } else {
    //             return;
    //         }
    //     }

    //     requestAnimationFrame(animation);
    // }

    fetch('/write-stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message
        }),
        signal: abortWrite.signal
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error occurred while window.streaming tokens.');
            }

            // typingAnimation.style.display = 'none';

            let lastToken = "";
            let content;

            let result = "##"
            let html = "";

            let responseStream = new ReadableStream({
                start(controller) {
                    // scrollToBottom();
                    let reader = response.body.getReader();

                    function read() {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                controller.close();
                                stopWriteButton.style.display = 'none';
                                // typingAnimation.style.display = 'none';
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

                            // // Extract the strings using matchAll()
                            // let jsonObjects = Array.from(token.matchAll(regex), match => match[1].trim());

                            // jsonObjects.forEach(item => {
                            //     const regex = new RegExp(`{data: ${item}}`, 'gi');
                            //     token = token.replace(regex, '');
                            // });


                            // if (lastToken !== "text") {
                            //     lastToken = "text";
                            //     let receivedTokensContainer = document.createElement('div');
                            //     receivedTokensContainer.classList.add('message', 'bot');
                            //     chatMessages.appendChild(receivedTokensContainer);

                            //     content = document.createElement('div');
                            //     content.classList.add('message-bubble');
                            //     receivedTokensContainer.appendChild(content);
                            // }
                            token = emoji.replace_colons(token);
                            result += token;

                            // console.log(result);

                            //                             const markdownString = `# Hello Markdown!
                            // This is a simple markdown example.`;

                            // Convert the markdown string to HTML
                            displayHTML = marked.parse(result);

                            // console.log(displayHTML);

                            // Set the innerHTML of the markdown-content div
                            outputContainer.innerHTML = displayHTML;
                            // content.innerText = displayHTML + '▎';
                            // if (typeAnim === "CGPT") {
                            //     content.innerText = result + '▎';
                            // } else if (typeAnim === "Terminal") {
                            //     content.innerText = result.trim() + "▁";
                            // } else {
                            //     for (let i of token.split(/(?<!\n)(\s+)/)) {
                            //         if (i.trim() !== "") { // Check if the token is a word
                            //             let html = document.createElement('span');
                            //             if (typeAnim === "Perplexity") {
                            //                 html.classList.add('oi');
                            //             } else if (typeAnim === "Custom1") {
                            //                 html.classList.add('ls');
                            //             } else if (typeAnim === "Custom2") {
                            //                 html.classList.add('ul');
                            //             } else if (typeAnim === "Custom3") {
                            //                 html.classList.add('tg');
                            //             } else if (typeAnim === "Custom4") {
                            //                 html.classList.add('bi');
                            //             } else if (typeAnim === "Custom5") {
                            //                 html.classList.add('mi');
                            //             } else if (typeAnim === "Custom6") {
                            //                 html.classList.add('si');
                            //             } else if (typeAnim === "Custom7") {
                            //                 html.classList.add('ri');
                            //             } else if (typeAnim === "Custom8") {
                            //                 html.classList.add('fi');
                            //             }
                            //             if (i.includes("\n")) {
                            //                 console.log("newline");
                            //                 i = i.split(/\n/g);
                            //                 for (let j of i) {
                            //                     html.innerText = j;
                            //                     content.append("<br>")
                            //                     content.append(html);
                            //                 }
                            //             } else {
                            //                 html.innerText = i
                            //                 content.append(html);
                            //             }
                            //         }


                            //         else if (i.includes("\n")) {
                            //             console.log("newline");
                            //             let check = i;
                            //             i = i.split("\n");
                            //             for (let j of i) {
                            //                 html.innerText = i;
                            //                 console.log(check)
                            //                 if (check.startsWith("\n"))
                            //                     content.appendChild(document.createElement('br'));
                            //                 // delete i.length characters from check
                            //                 check = check.substring(1);
                            //                 content.append(html);
                            //             }
                            //         }

                            //         else if (i == " ") { // Token is a space
                            //             content.append(" ")
                            //         }
                            //         // if (i == " ") {
                            //         //     content.append(" ")
                            //         // } else {
                            //         //     console.log(i, token)
                            //         //     if (token.split(" ").length > 1 && token.split(" ")[1] != "") {
                            //         //         html.innerText = i;
                            //         //         content.append(html);
                            //         //         content.append(" ");
                            //         //     } else {
                            //         //         html.innerText = i;
                            //         //         content.append(html);
                            //         //     }
                            //         // }
                            //     }
                            //     // html.innerText = token;
                            //     // content.append(html);

                            //     // Check for format {"info": "Google Chrome", "task": "open", "success": true}
                            //     for (i of jsonObjects) {
                            //         try {
                            //             const jsonObject = JSON.parse(i);

                            //             let receivedTokensContainer = document.createElement('div');
                            //             // receivedTokensContainer.classList.add('received-tokens');
                            //             receivedTokensContainer.classList.add('message', 'bot');
                            //             chatMessages.appendChild(receivedTokensContainer);

                            //             content = document.createElement('div');
                            //             content.classList.add('message-bubble');

                            //             if (jsonObject["success"]) {
                            //                 content.innerHTML = emoji.replace_colons(`<strong>Task | </strong>${jsonObject["task"].charAt(0).toUpperCase() + jsonObject["task"].slice(1)}ed ` + jsonObject["info"] + " :heavy_check_mark:");
                            //             } else {
                            //                 content.innerHTML = emoji.replace_colons(`<strong>Task | </strong>${jsonObject["task"].charAt(0).toUpperCase() + jsonObject["task"].slice(1)}ed ` + jsonObject["info"] + " :x:");
                            //             }
                            //             receivedTokensContainer.appendChild(content);
                            //             lastToken = "info";

                            //         } catch (error) {
                            //             console.log(error)
                            //         }
                            //     }
                            // }

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
            if (abortWrite.aborted) {
                // Handle the abort event
                window.streaming = false;
                content.innerHTML = result;
                console.log(content);
            } else {
                console.error('Error:', error);
            }
        })

}

