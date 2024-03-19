// import diff from "microdiff";
// const diff = microdiff.diff;
import fastDiff from 'https://cdn.jsdelivr.net/npm/fast-diff@1.3.0/+esm'
import { markedHighlight } from 'https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm';

console.log(marked, markedHighlight)

function formatMarkdown(text) {
    // Split the text into an array of lines
    const lines = text.split('\n');

    // Initialize an empty array to store the processed lines
    const processedLines = [];

    // Flag to track if we are inside a code block
    let inCodeBlock = false;

    // Iterate over each line
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Check if the line starts a code block
        if (line.startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            processedLines.push(line);
        } else if (inCodeBlock) {
            // If inside a code block, add the line as is
            processedLines.push(line);
        } else {
            // If outside a code block, add a new line if the current line is not empty
            if (line.trim() !== '') {
                processedLines.push(line);
                processedLines.push('');
            }
        }
    }

    // Join the processed lines back into a single string
    const preformattedText = processedLines.join('\n');

    return preformattedText;
}

function decodeHTMLEntities(text) {
    // Regular expression to match HTML entities
    const entityRegex = /&(amp|lt|gt|quot|#39);/g;

    // Define a mapping for HTML entities to their corresponding characters
    const entityMap = {
        amp: '&',
        lt: '<',
        gt: '>',
        quot: '"',
        '#39': "'"
        // Add more entities as needed
    };

    // Replace HTML entities with their corresponding characters
    return text.replace(entityRegex, (match, entity) => {
        // Check if the entity is present in the map
        if (entityMap.hasOwnProperty(entity)) {
            return entityMap[entity];
        } else {
            // If the entity is not in the map, return the original match
            return match;
        }
    });
}

// Example usage:
const htmlString = 'This &quot;example&quot; is &lt;b&gt;encoded&lt;/b&gt;.';
const decodedString = decodeHTMLEntities(htmlString);
console.log(decodedString);


// const marked = new Marked(
//     // markedHighlight({
//     //     langPrefix: 'hljs language-',
//     //     highlight(code, lang, info) {
//     //         const language = hljs.getLanguage(lang) ? lang : 'plaintext';
//     //         return hljs.highlight(code, { language }).value;
//     //     }
//     // })
// );

// marked.setOptions(
//     markedHighlight({
//         langPrefix: 'hljs language-',
//         highlight(code, lang, info) {
//             const language = hljs.getLanguage(lang) ? lang : 'plaintext';
//             return hljs.highlight(code, { language }).value;
//         }
//     })
// );

hljs.configure({
    ignoreUnescapedHTML: true
})

// Define the function to apply highlighting to the change text
function applyHighlighting(message, result) {
    const differences = fastDiff(message, result);
    console.log(differences)

    let highlightedResult = '';
    differences.forEach(([type, text]) => {
        if (type === 1) {
            highlightedResult += `<ins>${text}</ins>`; // for additions
        } else if (type === -1) {
            highlightedResult += `<del>${text}</del>`; // for removals
        } else {
            highlightedResult += text; // unchanged parts
        }
    });

    return highlightedResult;
}

// Write a function to set <del> to hidden when data-value = 3, <ins> to hidden when data-value = 1, and none hidden when data-value = 2

function setDisplayStyle(elements, displayStyle) {
    elements.forEach(element => {
        element.style.display = displayStyle || '';
    });
}

function toggleHighlighting(dataValue) {
    const delElements = document.querySelectorAll('del');
    const insElements = document.querySelectorAll('ins');

    console.log(dataValue)

    const displayStyle = {
        '1': { del: '', ins: 'none' },
        '2': { del: '', ins: '' },
        '3': { del: 'none', ins: '' }
    };

    const { del: delDisplay, ins: insDisplay } = displayStyle[dataValue] || {};

    setDisplayStyle(delElements, delDisplay);
    setDisplayStyle(insElements, insDisplay);
}

const buttons = document.querySelectorAll('.toggle button');

buttons.forEach(button => {
    button.addEventListener('click', function () {
        // Remove 'active' class from all buttons
        buttons.forEach(btn => btn.classList.remove('active'));

        // Add 'active' class to the clicked button
        this.classList.add('active');

        // Get the selected option value
        const selectedOption = this.getAttribute('data-value');
        console.log('Selected Option:', selectedOption);

        // Set the display style based on the selected option
        toggleHighlighting(selectedOption);
    });
});


let num_tokens, ts, base_time, displayHTML, first_token = true;

// Define prompts

function basePrompt(inputPrompt) {
    return `### System: ${inputPrompt}`;
}

const systemPrompt = `You are an AI writing assistant. Your job is improve the given text.
You should write out the full text with your new changes.
You should not write anything that is not related to the given text.
Once you are finished writing an edited version of the text, you will write under the header "### Changes:" what you have changed.
${userToken}
Here is the text I would like you to fix:
{input}

${assistantToken}
Sure, here's the new edited text:
`;

// Create an AbortController
let abortFeedback = new AbortController();

const stopFeedbackButton = document.getElementById('stop-feedback-button');
stopFeedbackButton.addEventListener('click', () => {
    abortFeedback.abort();
    window.streaming = false;
    abortFeedback = new AbortController();
    stopButton.style.display = 'none';
    typingAnimation.style.display = 'none';
});

const feedbackInput = document.querySelector('#feedback-input');

const feedbackSubmit = document.getElementById('feedback-submit');

feedbackSubmit.addEventListener('click', () => {
    console.log("Hi")
    if (window.streaming) {
        return;
    }
    feedbackGenerate()
})

const feedbackOutputContainer = document.getElementById('feedback-output-container');

const feedbackGenerate = () => {
    stopFeedbackButton.style.display = 'initial';
    // typingAnimation.style.display = 'initial';

    autosize.update(chatInput);
    feedbackInput.style.height = 'auto';

    // let sendOut = document.createElement('div');
    // sendOut.classList.add('send-out');
    // sendOut.innerText = chatInput.value;
    // chatInputContainer.appendChild(sendOut);
    // sendOut.addEventListener('animationend', () => {
    //     chatInputContainer.removeChild(sendOut);
    // });

    let baseInput = feedbackInput.value;

    let message = basePrompt(systemPrompt.replace('{input}', feedbackInput.value));
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
    feedbackInput.value = '';
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
        signal: abortFeedback.signal
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error occurred while window.streaming tokens.');
            }

            // typingAnimation.style.display = 'none';

            let lastToken = "";
            let content;

            let fullResult = ""
            let html = "";

            let responseStream = new ReadableStream({
                start(controller) {
                    // scrollToBottom();
                    let reader = response.body.getReader();

                    function read() {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                controller.close();
                                stopFeedbackButton.style.display = 'none';
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
                            fullResult += token;

                            // console.log(result);

                            // const markdownString = `# Hello Markdown!
                            // This is a simple markdown example.`;

                            // Apply highlighting using the function
                            // let highlightedText = applyHighlighting(baseInput, fullResult);

                            // console.log(highlightedText)

                            // highlightedText = highlightedText.replace(/\n/g, '\n\n');

                            // // Convert the markdown string to HTML
                            // displayHTML = marked.parse(highlightedText);


                            // console.log(highlightedText)

                            let out = fullResult;


                            // Convert the markdown string to HTML
                            displayHTML = marked.parse(formatMarkdown(out.split("### Changes")[0]));
                            console.log(displayHTML)
                            let inputHTML = marked.parse(formatMarkdown(baseInput))
                            let highlightedText = applyHighlighting(inputHTML, decodeHTMLEntities(displayHTML));

                            highlightedText += out.split("### Changes")[1] ? (`<ins>${marked.parse(formatMarkdown("### Changes" + out.split("### Changes")[1]))}</ins>`) : "";

                            console.log(highlightedText)

                            // Set the innerHTML of the markdown-content div
                            feedbackOutputContainer.innerHTML = `<span>${highlightedText}</span>`;
                            hljs.highlightAll()

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
            if (abortFeedback.aborted) {
                // Handle the abort event
                window.streaming = false;
                content.innerHTML = fullResult;
                console.log(content);
            } else {
                console.error('Error:', error);
            }
        })

}

