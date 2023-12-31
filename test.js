const WebSocket = require('ws');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Replace 'ws://your-websocket-server-url' with the actual WebSocket server URL
const ws = new WebSocket('ws://127.0.0.1:8080');

ws.on('open', () => {
  console.log('Connected to WebSocket server');

  rl.setPrompt('Enter a JSON string (or type "exit" to quit): ');
  rl.prompt();

  rl.on('line', (jsonString) => {
    if (jsonString.toLowerCase() === 'exit') {
      ws.close();
      rl.close();
      return;
    }

    try {
      const jsonObject = JSON.parse(jsonString);

      ws.send(JSON.stringify(jsonObject));

      console.log('JSON sent:', jsonString);
    } catch (error) {
      console.error('Invalid JSON:', error.message);
    }

    rl.prompt();
  });
});

ws.on('message', (data) => {
  // parse into json
  var json = JSON.parse(data);
  console.log('Received response:', json);
});

ws.on('close', () => {
  console.log('WebSocket connection closed');
});

