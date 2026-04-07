/*
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*/
/*
 * WebSocket helper utilities for CAM-AI
 *
 * Provides:
 *  - WSAsync(): Promise-based WebSocket wrapper with request/response tracking
 *  - nextMessage(): await next incoming WebSocket message
 *
 * Protocol:
 *  - Each outgoing message gets a "tracker" ID
 *  - Server responses must include the same tracker
 *  - Optional callback mode for streaming responses
 */

function createWebSocket(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);

    ws.onopen = () => resolve(ws);
    ws.onerror = (err) => reject(err);
  });
}

function WSAsync(url) {
  return new Promise((resolve, reject) => {
    let result = {};
    // Incremental request ID
    result.tracker = 0;
    // Create WebSocket connection
    result.socket = new WebSocket(url);
    // Handle connection errors (auto-retry)
    result.socket.onerror = ((event) => {
      console.error("WebSocket error:", url);
      setTimeout(function(){
        console.log("Retry...");
        resolve(WSAsync(url));
      },10000);
      
    });
    // Connection established
    result.socket.onopen = (() => {
      // Store pending promises and callbacks by tracker ID
      result.promiselist = {};
      result.callbacklist = {};
      result.socket.onclose = function(e) {
        console.log('Websocket closed');
      };
      // Handle incoming messages
      result.socket.onmessage = function(e) {
        // NOTE: expects JSON messages here
        let received = JSON.parse(e.data);
        // Callback mode (streaming / partial responses)
        if (received.callback) {
          if (result.callbacklist[received.tracker]) {
            result.callbacklist[received.tracker](e.data);
          };  
        } else {
          // Resolve corresponding promise
          result.promiselist[received.tracker](received.data);
        };  
      };
      /*
       * Send a message and wait for response
       *
       * @param {object} data - payload
       * @param {function} [callback] - optional streaming callback
       * @returns {Promise<any>}
       */
      result.sendandwait = ((data, callback) => {
        return new Promise((resolve, reject) => {
          sendpacket = {};
          sendpacket.tracker = result.tracker;
          sendpacket.data = data;
          // Register promise resolver
          result.promiselist[result.tracker] = ((data) => {
            resolve(data);
          });
          if (callback) {
            result.callbacklist[result.tracker] = callback; 
          };  
          // Increment tracker (with wrap-around)
          if (result.tracker >= 1000000000000) {
            result.tracker = 0;
          } else {
            result.tracker += 1;
          };
          //console.log('Sent:',sendpacket)
          // Send JSON message
          result.socket.send(JSON.stringify(sendpacket))
        });
      });
      resolve(result);
    });
  });
};

/*
 * Wait for the next WebSocket message (one-shot)
 *
 * @param {WebSocket} ws
 * @param {AbortSignal} [signal]
 * @returns {Promise<string|Blob|ArrayBuffer>}
 */
function nextMessage(ws, { signal } = {}) {
  return new Promise((resolve, reject) => {
    const onMsg = (ev) => {
      cleanup();
      resolve(ev.data);
    };
    const onErr = () => {
      cleanup();
      reject(new Error('WebSocket error'));
    };
    const onClose = () => {
      cleanup();
      reject(new Error('WebSocket closed'));
    };
    const onAbort = () => {
      cleanup();
      reject(new DOMException('Aborted','AbortError'));
    };
    const cleanup = () => {
      ws.removeEventListener('message', onMsg);
      ws.removeEventListener('error', onErr);
      ws.removeEventListener('close', onClose);
      signal?.removeEventListener('abort', onAbort);
    };
    ws.addEventListener('message', onMsg, { once: true });
    ws.addEventListener('error', onErr, { once: true });
    ws.addEventListener('close', onClose, { once: true });
    signal?.addEventListener('abort', onAbort);
  });
}

// Nutzung:
// const data = await nextMessage(ws); // string oder Blob/ArrayBuffer

