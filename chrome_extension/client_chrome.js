'use strict';

chrome.runtime.onInstalled.addListener(function() {
    const {SessionChangedRequest} = require('./chrome_pb.js');
    const {ChromeClient} = require('./chrome_grpc_web_pb.js');

    function onFocusChanged(windowId) {
        console.log(`${windowId} is focused`);

        let groupId = windowToSessionMap.get(windowId);
        chrome.tabGroups.get(groupId, group => {
            console.log(`groupId: ${groupId}, group: ${group}`);
        });
    }

    chrome.windows.onFocusChanged.addListener(onFocusChanged);

    let windowToSessionMap = new Map();
    windowToSessionMap.set(-1, -1);

    chrome.windows.getAll({populate: true}, windows => {
        console.log(windows);

        windowToSessionMap.clear();

        for (let window_ of windows) {
            for (let tab of window_.tabs) {
                if (tab.groupId != -1) {
                    windowToSessionMap.set(window_.id, tab.groupId);
                    break;
                }
            }
            windowToSessionMap.set(window_.id, -2);
        }

        // The assumption is that as we just started, the Chrome should still be focused.
        // It may be good to check in trackd though that Chrome's XWindow is indeed focused
        // when this plugin reports so.
        windows.getLastFocused({}, window_ => {
            onFocusChanged(window_.id);
        });
    });


    let client = new ChromeClient('http://localhost:3142', null, null);

    let request = new SessionChangedRequest();
    request.setSessionName('TestSession');

    client.session_changed(request, {}, (err, response) => {
        if (err) {
            console.log(`Unexpected error for sessionChange: code = ${err.code}` +
                        `, message = "${err.message}"`);
        }
    });
});
