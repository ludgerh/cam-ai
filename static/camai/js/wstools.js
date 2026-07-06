/*
camai/static/camai/git/js/wstools.js
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
    // The result object is stable for the whole logical connection. On a
    // reconnect we swap out result.socket in place, so callers keep their
    // handle and never end up holding a dead socket while an unused orphan
    // stays open on the server (the old retry path did exactly that):
    const result = {};
    result.tracker = 0;
    result.promiselist = {};
    result.callbacklist = {};
    // Resolve the outer promise only once, on the first successful open:
    let resolved = false;
    // Reconnect guard: at most one pending retry per logical connection, so a
    // burst of error/close events cannot spawn several parallel sockets:
    let retryTimer = null;

    function scheduleRetry() {
      if (retryTimer !== null) {
        return;
      }
      retryTimer = setTimeout(() => {
        retryTimer = null;
        console.log("WSAsync reconnect:", url);
        connect();
      }, 10000);
    }

    function connect() {
      // Tear down the previous socket first, so a dead one is closed promptly
      // and can never linger as a counted-but-unused connection on the server:
      const oldSocket = result.socket;
      if (oldSocket) {
        // Detach handlers so the old socket's own close/error cannot trigger
        // a second reconnect once we have already replaced it:
        oldSocket.onopen = null;
        oldSocket.onerror = null;
        oldSocket.onclose = null;
        oldSocket.onmessage = null;
        try {
          oldSocket.close();
        } catch (e) {
          // Ignore: the socket may already be closing or closed.
        }
      }

      const socket = new WebSocket(url);
      result.socket = socket;

      socket.onopen = () => {
        // Handle incoming messages
        socket.onmessage = (e) => {
          // NOTE: expects JSON messages here
          const received = JSON.parse(e.data);
          if (received.callback) {
            if (result.callbacklist[received.tracker]) {
              result.callbacklist[received.tracker](e.data);
            }
          } else {
            // A resolver may be gone after a reconnect (in-flight requests do
            // not survive a socket swap), so guard before calling it:
            if (result.promiselist[received.tracker]) {
              result.promiselist[received.tracker](received.data);
            }
          }
        };
        if (!resolved) {
          resolved = true;
          resolve(result);
        }
      };

      socket.onerror = (event) => {
        console.error("WebSocket error:", url);
        scheduleRetry();
      };

      socket.onclose = (e) => {
        console.log("Websocket closed");
        // Reconnect only on unexpected closes. A clean close from the server
        // (code 1000) is intentional - e.g. access denied - so we stay down:
        if (e.code !== 1000) {
          scheduleRetry();
        }
      };
    }

    /*
     * Send a message and wait for response
     *
     * @param {object} data - payload
     * @param {function} [callback] - optional streaming callback
     * @returns {Promise<any>}
     */
    result.sendandwait = ((data, callback) => {
      return new Promise((resolveSend, rejectSend) => {
        // Use a local object (the original leaked sendpacket as an implicit
        // global, shared across concurrent sends):
        const sendpacket = {};
        sendpacket.tracker = result.tracker;
        sendpacket.data = data;
        // Register promise resolver
        result.promiselist[result.tracker] = ((data) => {
          resolveSend(data);
        });
        if (callback) {
          result.callbacklist[result.tracker] = callback;
        }
        // Increment tracker (with wrap-around)
        if (result.tracker >= 1000000000000) {
          result.tracker = 0;
        } else {
          result.tracker += 1;
        }
        // Send JSON message
        result.socket.send(JSON.stringify(sendpacket));
      });
    });

    // Open the first connection.
    connect();
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

// Usage:
// const data = await nextMessage(ws); // string oder Blob/ArrayBuffer

