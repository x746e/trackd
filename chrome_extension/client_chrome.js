'use strict';

chrome.runtime.onInstalled.addListener(function() {
    const {SessionChangedRequest} = require('./chrome_pb.js');
    const {ChromeClient} = require('./chrome_grpc_web_pb.js');

    let client = new ChromeClient('http://localhost:3141', null, null);

    let request = new SessionChangedRequest();
    request.setSessionName('TestSession');

    client.session_changed(request, {}, (err, response) => {
        if (err) {
            console.log(`Unexpected error for sessionChange: code = ${err.code}` +
                        `, message = "${err.message}"`);
        } else {
            console.log(response.getMessage());
        }
    });
});
