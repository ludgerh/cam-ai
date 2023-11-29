function WSAsync(url) {
  return new Promise((resolve, reject) => {
    let result = {};
    result.tracker = 0;
    result.socket = new WebSocket(url);
    result.socket.onerror = ((event) => {
      console.error("WebSocket error:", url);
      setTimeout(function(){
        console.log("Retry...");
        resolve(WSAsync(url));
      },10000);
      
    });
    result.socket.onopen = (() => {
      result.promiselist = {};
      result.callbacklist = {};
      result.socket.onclose = function(e) {
        console.log('Websocket closed');
      };
      result.socket.onmessage = function(e) {
        received = JSON.parse(e.data);
        //console.log('Received:',received)
        if (received.callback) {
          if (result.callbacklist[received.tracker]) {
            result.callbacklist[received.tracker](e.data);
          };  
        } else {
          result.promiselist[received.tracker](received.data);
        };  
      };
      result.sendandwait = ((data, callback) => {
        return new Promise((resolve, reject) => {
          sendpacket = {};
          sendpacket.tracker = result.tracker;
          sendpacket.data = data;
          result.promiselist[result.tracker] = ((data) => {
            resolve(data);
          });
          if (callback) {
            result.callbacklist[result.tracker] = callback; 
          };  
          if (result.tracker >= 1000000000) {
            result.tracker = 0;
          } else {
            result.tracker += 1;
          };
          //console.log('Sent:',sendpacket)
          result.socket.send(JSON.stringify(sendpacket))
        });
      });
      resolve(result);
    });
  });
};

